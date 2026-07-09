"""Shared helpers for the autopilot-video pipeline (v2).

Stdlib-only at module level — scripts that need third-party deps import them lazily.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CONFIG_DIR = PROJECT_ROOT / "config"

# v2 data directories
DATA_DIR = PROJECT_ROOT / "data"
TRENDS_DIR = DATA_DIR / "trends"
NICHES_DIR = DATA_DIR / "selected_niches"
SCRIPTS_DATA_DIR = DATA_DIR / "scripts"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Pricing per 1K tokens (USD) — keep in sync with .claude/rules/cost-rules.md
MODEL_PRICING = {
    "claude-fable-5": {"input": 0.0100, "output": 0.0500},
    "claude-sonnet-4-6": {"input": 0.0030, "output": 0.0150},
    "claude-haiku-4-5": {"input": 0.0010, "output": 0.0050},
}

EXIT_FAILURE = 1
EXIT_COST_LIMIT = 2
EXIT_MISSING_CONFIG = 3


def load_dotenv() -> None:
    """Minimal .env loader — values already in the environment win."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def costs_log_path() -> Path:
    return LOGS_DIR / f"costs_{today()}.json"


def read_costs() -> dict:
    path = costs_log_path()
    if path.exists():
        return json.loads(path.read_text())
    return {"date": today(), "total_usd": 0.0, "entries": []}


def daily_cost_limit() -> float:
    return float(os.environ.get("DAILY_COST_LIMIT_USD", "5.00"))


def check_cost_limit(script: str) -> None:
    """Exit(2) if today's spend already meets the daily limit."""
    spent = read_costs()["total_usd"]
    limit = daily_cost_limit()
    if spent >= limit:
        print(
            f"[{script}] Daily cost limit reached: ${spent:.4f} >= ${limit:.2f}. "
            "Refusing to make API calls.",
            file=sys.stderr,
        )
        sys.exit(EXIT_COST_LIMIT)


def log_cost(script: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Append one API call's cost to today's log atomically. Returns cost in USD."""
    pricing = MODEL_PRICING[model]
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    total = input_cost + output_cost

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    data = read_costs()
    data["entries"].append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "script": script,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(total, 6),
    })
    data["total_usd"] = round(sum(e["cost_usd"] for e in data["entries"]), 6)

    fd, tmp = tempfile.mkstemp(dir=LOGS_DIR, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, costs_log_path())

    print(f"[{script}] {model}: in={input_tokens} out={output_tokens} → ${total:.4f} "
          f"(today: ${data['total_usd']:.4f}/{daily_cost_limit():.2f})")
    return total


# ── v1 output helpers (kept for backward compat) ─────────────────────────────

def write_output(name: str, payload) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / name
    path.write_text(json.dumps(payload, indent=2))
    return path


def read_output(name: str):
    path = OUTPUTS_DIR / name
    if not path.exists():
        print(f"Missing expected input file: {path}", file=sys.stderr)
        sys.exit(EXIT_MISSING_CONFIG)
    return json.loads(path.read_text())


# ── v2 data helpers ───────────────────────────────────────────────────────────

def write_data_json(path: Path, payload) -> Path:
    """Atomically write JSON to any path; creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def read_data_json(path: Path):
    """Read JSON from path; exit(3) if missing."""
    if not path.exists():
        print(f"Missing expected input file: {path}", file=sys.stderr)
        sys.exit(EXIT_MISSING_CONFIG)
    return json.loads(path.read_text())


def read_prompt(name: str) -> str:
    """Read a prompt template from prompts/ directory; exit(3) if missing."""
    path = PROMPTS_DIR / name
    if not path.exists():
        print(f"Missing prompt template: {path}", file=sys.stderr)
        sys.exit(EXIT_MISSING_CONFIG)
    return path.read_text()


# ── misc ──────────────────────────────────────────────────────────────────────

def is_dry_run(argv: list[str] | None = None) -> bool:
    return "--dry-run" in (argv if argv is not None else sys.argv[1:])


def require_env(script: str, *names: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        print(f"[{script}] Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(EXIT_MISSING_CONFIG)
