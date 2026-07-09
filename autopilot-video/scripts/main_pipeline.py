"""Step 8 — orchestrator. Runs steps 1-7 in order, sends a Telegram summary,
and serves a FastAPI control surface.

Usage:
  python scripts/main_pipeline.py --dry-run     # run the chain once in dry-run, no server
  python scripts/main_pipeline.py --once        # run the chain once for real, no server
  python scripts/main_pipeline.py               # start FastAPI server (PORT env or 8000)
                                                #   GET  /health
                                                #   POST /run?dry_run=true|false
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime

from common import (
    DATA_DIR,
    LOGS_DIR,
    PROJECT_ROOT,
    is_dry_run,
    load_dotenv,
    read_costs,
    today,
)

SCRIPT = "main_pipeline"

PIPELINE_STEPS = [
    "trend_researcher",
    "niche_selector",
    "script_generator",
    "video_assembler",
    "thumbnail_gen",
    "approval_gate",
    "multi_uploader",
]


def send_telegram(text: str) -> None:
    """Best-effort Telegram notification; never crashes the pipeline."""
    import requests

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[{SCRIPT}] (telegram not configured) {text}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
    except Exception as exc:
        print(f"[{SCRIPT}] Telegram alert failed: {exc}", file=sys.stderr)


def build_summary(completed: list[str], elapsed_s: float) -> str:
    """Pipeline summary: steps, approvals, uploads, cost."""
    lines = [f"✅ Pipeline COMPLETE ({elapsed_s:.0f}s)",
             f"Steps: {' → '.join(completed)}"]

    approved_path = DATA_DIR / f"approved_{today()}.json"
    if approved_path.exists():
        doc = json.loads(approved_path.read_text())
        lines.append(f"Approved: {len(doc.get('approved', []))} | "
                     f"Rejected: {len(doc.get('rejected', []))}")

    uploads_path = LOGS_DIR / f"uploads_{today()}.json"
    if uploads_path.exists():
        uploads = json.loads(uploads_path.read_text())
        ok = sum(1 for u in uploads if not u.get("error"))
        failed = sum(1 for u in uploads if u.get("error"))
        lines.append(f"Uploads: {ok} ok, {failed} failed → {uploads_path.name}")

    costs = read_costs()
    lines.append(f"API cost today: ${costs['total_usd']:.4f}")
    return "\n".join(lines)


def run_pipeline_sync(dry_run: bool = False) -> dict:
    """Run every step in order; stop at the first failure."""
    started = time.monotonic()
    completed: list[str] = []
    for step in PIPELINE_STEPS:
        cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / f"{step}.py")]
        if dry_run:
            cmd.append("--dry-run")
        print(f"[{SCRIPT}] ── running {step} {'(dry-run)' if dry_run else ''}")
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)

        if result.returncode != 0:
            msg = (f"❌ Pipeline FAILED at step: {step} "
                   f"(exit {result.returncode})\nTime: {datetime.now()}")
            print(f"[{SCRIPT}] {msg}", file=sys.stderr)
            if not dry_run:
                send_telegram(msg)
            return {"status": "failed", "failed_step": step,
                    "exit_code": result.returncode, "completed": completed}
        completed.append(step)

    summary = build_summary(completed, time.monotonic() - started)
    print(f"[{SCRIPT}] {summary}")
    if not dry_run:
        send_telegram(summary)
    return {"status": "complete", "completed": completed}


def serve() -> None:
    """FastAPI control surface: GET /health, POST /run?dry_run=true."""
    import threading

    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="autopilot-video")
    state = {"last_run": None, "running": False}

    @app.get("/health")
    def health():
        return {"status": "ok", "ts": datetime.now().isoformat(timespec="seconds"),
                "running": state["running"], "last_run": state["last_run"]}

    @app.post("/run")
    def run(dry_run: bool = False):
        if state["running"]:
            return {"status": "already_running"}

        def task():
            state["running"] = True
            try:
                state["last_run"] = run_pipeline_sync(dry_run=dry_run)
            finally:
                state["running"] = False

        threading.Thread(target=task, daemon=True).start()
        return {"status": "started", "dry_run": dry_run,
                "steps": PIPELINE_STEPS}

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


def main() -> None:
    load_dotenv()
    if is_dry_run():
        outcome = run_pipeline_sync(dry_run=True)
        sys.exit(0 if outcome["status"] == "complete" else 1)
    if "--once" in sys.argv[1:]:
        outcome = run_pipeline_sync(dry_run=False)
        sys.exit(0 if outcome["status"] == "complete" else 1)
    serve()


if __name__ == "__main__":
    main()
