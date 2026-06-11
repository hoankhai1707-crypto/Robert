"""Step 8 — orchestrator. Runs the pipeline steps in order, alerts via Telegram,
and serves a FastAPI control surface.

Usage:
  python scripts/main_pipeline.py --dry-run     # run the chain once in dry-run, no server
  python scripts/main_pipeline.py --once        # run the chain once for real, no server
  python scripts/main_pipeline.py               # start FastAPI server on :8000
                                                #   GET  /health
                                                #   POST /run?dry_run=true|false
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import PROJECT_ROOT, is_dry_run, load_dotenv, today

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


def run_pipeline_sync(dry_run: bool = False) -> dict:
    """Run every step in order; stop at the first failure."""
    results = []
    for step in PIPELINE_STEPS:
        cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / f"{step}.py")]
        if dry_run:
            cmd.append("--dry-run")
        print(f"[{SCRIPT}] ── running {step} {'(dry-run)' if dry_run else ''}")
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)

        if result.returncode != 0:
            msg = f"Pipeline FAILED at step: {step}\nTime: {datetime.now()}"
            print(f"[{SCRIPT}] {msg}", file=sys.stderr)
            if not dry_run:
                send_telegram(msg)
            return {"status": "failed", "failed_step": step, "completed": results}
        results.append(step)

    success_msg = (f"Pipeline COMPLETE. Check uploads log: "
                   f"./logs/uploads_{today()}.json")
    print(f"[{SCRIPT}] {success_msg}")
    if not dry_run:
        send_telegram(success_msg)
    return {"status": "complete", "completed": results}


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

    uvicorn.run(app, host="0.0.0.0", port=8000)


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
