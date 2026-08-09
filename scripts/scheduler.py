#!/usr/bin/env python3
"""
Morning workflow scheduler — wakes at 4:00 AM daily and runs run_morning_workflow.sh.
Run once as a background process: nohup python3 scheduler.py &
"""

import subprocess
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
WORKFLOW_SCRIPT = SCRIPT_DIR / "run_morning_workflow.sh"
LOG_DIR = SCRIPT_DIR / "logs"
SCHEDULER_LOG = LOG_DIR / "scheduler.log"
TARGET_HOUR = 4
TARGET_MINUTE = 0


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    print(line, end="", flush=True)
    with open(SCHEDULER_LOG, "a") as f:
        f.write(line)


def next_4am() -> datetime:
    now = datetime.now()
    target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_workflow() -> None:
    log("Triggering morning workflow...")
    try:
        result = subprocess.run(
            [str(WORKFLOW_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if result.returncode == 0:
            log("Morning workflow completed successfully.")
        else:
            log(f"Morning workflow exited with code {result.returncode}. stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        log("ERROR: Morning workflow timed out after 15 minutes.")
    except Exception as exc:
        log(f"ERROR: {exc}")


def main() -> None:
    log("Scheduler started. Waiting for next 4:00 AM run.")
    while True:
        wake = next_4am()
        sleep_secs = (wake - datetime.now()).total_seconds()
        log(f"Next run scheduled at {wake.strftime('%Y-%m-%d %H:%M:%S')} — sleeping {sleep_secs/3600:.2f} hours.")
        time.sleep(max(sleep_secs, 0))
        run_workflow()
        # Small buffer so we don't re-fire in the same minute
        time.sleep(90)


if __name__ == "__main__":
    main()
