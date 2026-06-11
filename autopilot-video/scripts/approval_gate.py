"""Step 6 — send each video's thumbnail to Telegram with Approve/Reject buttons,
wait for the decision, auto-approve on timeout.

Input:  outputs/scripts_YYYY-MM-DD.json + outputs/thumbnails/<slug>.jpg
Output: outputs/approvals_YYYY-MM-DD.json  ({"<slug>": true|false, ...})
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

from common import (
    EXIT_FAILURE,
    OUTPUTS_DIR,
    is_dry_run,
    load_dotenv,
    read_output,
    require_env,
    today,
    write_output,
)

SCRIPT = "approval_gate"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
POLL_INTERVAL_S = 5


def timeout_minutes() -> int:
    return int(os.environ.get("APPROVAL_TIMEOUT_MINUTES", "30"))


async def send_telegram_preview(script: dict) -> int:
    """Send the thumbnail photo with Approve/Reject inline buttons. Returns message_id."""
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    slug = script["slug"]
    keyboard = [[
        InlineKeyboardButton("Approve", callback_data=f"approve_{slug}"),
        InlineKeyboardButton("Reject", callback_data=f"reject_{slug}"),
    ]]
    caption = (f"Title: {script['title']}\n"
               f"Platform: {script['platform']}\n"
               f"Hook: {script['hook']}")
    with open(THUMBS_DIR / f"{slug}.jpg", "rb") as photo:
        message = await bot.send_photo(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            photo=photo,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    return message.message_id


async def wait_for_decision(slug: str) -> bool:
    """Poll bot.get_updates every 5s for approve_/reject_ callbacks.

    Timeout (APPROVAL_TIMEOUT_MINUTES from .env) → warn and auto-approve (True).
    """
    from telegram import Bot

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
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
                await cq.answer("Approved")  # clears the spinner
                return True
            if cq.data == f"reject_{slug}":
                await cq.answer("Rejected")
                return False
        await asyncio.sleep(POLL_INTERVAL_S)

    print(f"[{SCRIPT}] Timeout - auto-approving ({slug})")
    return True


async def run_gate(scripts: list[dict]) -> dict[str, bool]:
    approvals: dict[str, bool] = {}
    for script in scripts:
        slug = script["slug"]
        msg_id = await send_telegram_preview(script)
        print(f"[{SCRIPT}] Sent preview for {slug} (message_id={msg_id}) — waiting for decision")
        approvals[slug] = await wait_for_decision(slug)
        print(f"[{SCRIPT}] {slug}: {'APPROVED' if approvals[slug] else 'REJECTED'}")
    return approvals


def main() -> None:
    load_dotenv()
    scripts = read_output(f"scripts_{today()}.json")

    if is_dry_run():
        print(f"[{SCRIPT}] DRY-RUN — no Telegram calls; auto-approving all")
        print(f"[{SCRIPT}] Would send {len(scripts)} previews with Approve/Reject buttons, "
              f"poll get_updates every {POLL_INTERVAL_S}s, "
              f"timeout {timeout_minutes()}min → auto-approve")
        approvals = {s["slug"]: True for s in scripts}
    else:
        require_env(SCRIPT, "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
        try:
            approvals = asyncio.run(run_gate(scripts))
        except Exception as exc:
            print(f"[{SCRIPT}] FAILED: {exc}", file=sys.stderr)
            sys.exit(EXIT_FAILURE)

    path = write_output(f"approvals_{today()}.json", approvals)
    approved = sum(approvals.values())
    print(f"[{SCRIPT}] {approved}/{len(approvals)} approved → {path}")


if __name__ == "__main__":
    main()
