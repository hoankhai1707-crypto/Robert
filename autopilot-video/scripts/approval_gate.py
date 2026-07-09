"""Step 6 — Telegram approval gate: preview each video, wait for Approve/Reject.

Input:  data/scripts/script_*.json, outputs/thumbnails/thumb_<slug>_001.jpg,
        outputs/videos/final_<slug>_001.mp4
Output: data/approved_YYYY-MM-DD.json  ({"approved": [...], "rejected": [...]})
        Rejected videos move to outputs/rejected/.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from common import (
    DATA_DIR,
    EXIT_FAILURE,
    OUTPUTS_DIR,
    SCRIPTS_DATA_DIR,
    is_dry_run,
    load_dotenv,
    require_env,
    today,
    write_data_json,
)

SCRIPT = "approval_gate"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
REJECTED_DIR = OUTPUTS_DIR / "rejected"
POLL_INTERVAL_S = 5
DEFAULT_TIMEOUT_MINUTES = 60


def timeout_minutes() -> int:
    return int(os.environ.get("APPROVAL_TIMEOUT_MINUTES", str(DEFAULT_TIMEOUT_MINUTES)))


def find_video(slug: str) -> Path | None:
    matches = sorted(VIDEOS_DIR.glob(f"final_{slug}_*.mp4"))
    return matches[-1] if matches else None


def find_thumb(slug: str) -> Path | None:
    matches = sorted(THUMBS_DIR.glob(f"thumb_{slug}_*.jpg"))
    return matches[-1] if matches else None


async def send_preview(bot, script: dict) -> None:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    slug = script["slug"]
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{slug}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{slug}"),
    ]])
    caption = (f"🎬 {script['title']}\n"
               f"Platform: {script.get('platform', 'youtube_shorts')}\n"
               f"Hook: {script['hook']}\n"
               f"⏰ Auto-approve in {timeout_minutes()} min")

    thumb = find_thumb(slug)
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if thumb and thumb.exists():
        with open(thumb, "rb") as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo,
                                 caption=caption, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)


async def wait_for_decision(bot, slug: str) -> bool:
    """Poll get_updates every 5s. Timeout → warn + auto-approve."""
    deadline = time.monotonic() + timeout_minutes() * 60
    offset = None

    while time.monotonic() < deadline:
        updates = await bot.get_updates(offset=offset, timeout=0)
        for update in updates:
            offset = update.update_id + 1
            cq = update.callback_query
            if cq is None or not cq.data:
                continue
            if cq.data == f"approve_{slug}":
                await cq.answer("Approved ✅")
                return True
            if cq.data == f"reject_{slug}":
                await cq.answer("Rejected ❌")
                return False
        await asyncio.sleep(POLL_INTERVAL_S)

    print(f"[{SCRIPT}] Timeout - auto-approving ({slug})")
    return True


async def run_gate(scripts: list[dict]) -> dict:
    from telegram import Bot

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    approved, rejected = [], []
    for script in scripts:
        slug = script["slug"]
        await send_preview(bot, script)
        print(f"[{SCRIPT}] Preview sent for {slug} — waiting for decision "
              f"(timeout {timeout_minutes()}min)")
        if await wait_for_decision(bot, slug):
            approved.append(slug)
            print(f"[{SCRIPT}] {slug}: APPROVED")
        else:
            rejected.append(slug)
            print(f"[{SCRIPT}] {slug}: REJECTED")
    return {"approved": approved, "rejected": rejected}


def move_rejected(rejected: list[str]) -> None:
    """Move rejected videos out of the upload path into outputs/rejected/."""
    if not rejected:
        return
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    for slug in rejected:
        video = find_video(slug)
        if video and video.exists():
            dest = REJECTED_DIR / video.name
            shutil.move(str(video), str(dest))
            print(f"[{SCRIPT}] Moved rejected video → {dest}")


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    script_files = sorted(SCRIPTS_DATA_DIR.glob("script_*.json"))
    scripts = [json.loads(sf.read_text()) for sf in script_files]
    out_path = DATA_DIR / f"approved_{today()}.json"

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no Telegram calls; auto-approving all")
        print(f"[{SCRIPT}] Would send {len(scripts)} previews (thumbnail + "
              f"Approve/Reject buttons), poll every {POLL_INTERVAL_S}s, "
              f"timeout {timeout_minutes()}min → auto-approve")
        print(f"[{SCRIPT}] Rejected videos would move to {REJECTED_DIR}")
        result = {
            "approved": [s["slug"] for s in scripts],
            "rejected": [],
            "decided_at": datetime.now().isoformat(timespec="seconds"),
        }
        write_data_json(out_path, result)
        print(f"[{SCRIPT}] DRY-RUN output → {out_path} "
              f"({len(result['approved'])} approved, 0 rejected)")
        return

    require_env(SCRIPT, "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
    if not scripts:
        print(f"[{SCRIPT}] No script files in {SCRIPTS_DATA_DIR}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    try:
        result = asyncio.run(run_gate(scripts))
    except Exception as exc:
        print(f"[{SCRIPT}] FAILED: {exc}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    move_rejected(result["rejected"])
    result["decided_at"] = datetime.now().isoformat(timespec="seconds")
    write_data_json(out_path, result)
    print(f"[{SCRIPT}] {len(result['approved'])}/{len(scripts)} approved → {out_path}")


if __name__ == "__main__":
    main()
