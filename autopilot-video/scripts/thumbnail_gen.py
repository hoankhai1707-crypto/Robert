"""Step 5 — cv2 frame extraction + Haiku text + PIL rendering per video.

Input:  data/scripts/script_*.json, outputs/videos/final_*.mp4
Output: outputs/thumbnails/thumb_<slug>_001.jpg
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    OUTPUTS_DIR,
    PROJECT_ROOT,
    SCRIPTS_DATA_DIR,
    check_cost_limit,
    is_dry_run,
    load_dotenv,
    log_cost,
    require_env,
)

SCRIPT = "thumbnail_gen"
MODEL = "claude-haiku-4-5"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
FRAME_AT_SECONDS = 2.0


def find_video(slug: str) -> Path | None:
    matches = sorted(VIDEOS_DIR.glob(f"final_{slug}_*.mp4"))
    return matches[-1] if matches else None


def extract_frame_cv2(video: Path, at_seconds: float) -> bytes | None:
    """Extract a single frame at `at_seconds` using cv2."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, at_seconds * 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    ok, buf = cv2.imencode(".jpg", frame)
    return bytes(buf) if ok else None


def get_platform_dims(platform: str) -> tuple[int, int]:
    try:
        cfg = json.loads((CONFIG_DIR / "platform_config.json").read_text())
        specs = cfg["platforms"].get(platform, {})
        return specs.get("width", 1080), specs.get("height", 1920)
    except Exception:
        return 1080, 1920


def render_thumbnail(frame_bytes: bytes | None, text: str,
                     width: int, height: int, out: Path) -> None:
    import io
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    if frame_bytes:
        img = Image.open(io.BytesIO(frame_bytes)).convert("RGB").resize((width, height))
    else:
        img = Image.new("RGB", (width, height), color=(15, 15, 30))

    blurred = img.filter(ImageFilter.GaussianBlur(radius=15))

    ttf_files = sorted(FONTS_DIR.glob("*.ttf"))
    font_size = max(40, width // 12)
    if ttf_files:
        try:
            font = ImageFont.truetype(str(ttf_files[0]), font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    draw = ImageDraw.Draw(blurred, "RGBA")
    cx, cy = width // 2, height // 2

    bbox = draw.textbbox((cx, cy), text.upper(), font=font, anchor="mm", stroke_width=3)
    pad = 20
    draw.rectangle(
        (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
        fill=(0, 0, 0, 160),
    )
    draw.text((cx, cy), text.upper(), font=font, anchor="mm",
              fill="white", stroke_width=3, stroke_fill="black")

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    blurred.convert("RGB").save(str(out), "JPEG", quality=95)


async def get_haiku_text(client, script: dict) -> tuple[str, object]:
    response = await client.messages.create(
        model=MODEL,
        max_tokens=60,
        messages=[{
            "role": "user",
            "content": (
                f"Write a punchy 3-6 word thumbnail caption for this video:\n"
                f"Title: {script['title']}\n"
                f"Hook: {script['hook']}\n"
                f"Reply with ONLY the caption, no quotes, no period at end."
            ),
        }],
    )
    return response.content[0].text.strip(), response


async def process_all(script_files: list[Path]) -> int:
    import anthropic
    client = anthropic.AsyncAnthropic()
    failures = 0

    for sf in script_files:
        script = json.loads(sf.read_text())
        slug = script["slug"]
        platform = script.get("platform", "youtube_shorts")
        width, height = get_platform_dims(platform)
        out = THUMBS_DIR / f"thumb_{slug}_001.jpg"

        # Frame extraction via cv2
        video = find_video(slug)
        frame_bytes = None
        if video:
            frame_bytes = extract_frame_cv2(video, FRAME_AT_SECONDS)
            if frame_bytes:
                print(f"[{SCRIPT}] {slug}: cv2 frame at {FRAME_AT_SECONDS}s from {video.name}")
            else:
                print(f"[{SCRIPT}] {slug}: cv2 extraction failed — using gradient background")
        else:
            print(f"[{SCRIPT}] {slug}: no video found — using gradient background")

        # Haiku text generation
        check_cost_limit(SCRIPT)
        try:
            thumb_text, response = await get_haiku_text(client, script)
            log_cost(SCRIPT, MODEL,
                     response.usage.input_tokens, response.usage.output_tokens)
            print(f"[{SCRIPT}] {slug}: Haiku caption → '{thumb_text}'")
        except Exception as exc:
            print(f"[{SCRIPT}] {slug}: Haiku failed: {exc} — using title", file=sys.stderr)
            thumb_text = script["title"][:32]

        # PIL render
        try:
            render_thumbnail(frame_bytes, thumb_text, width, height, out)
            print(f"[{SCRIPT}] {slug}: rendered {width}×{height} → {out}")
        except Exception as exc:
            print(f"[{SCRIPT}] {slug}: PIL render failed: {exc}", file=sys.stderr)
            failures += 1

    return failures


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    script_files = sorted(SCRIPTS_DATA_DIR.glob("script_*.json"))

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no cv2, no Haiku, no PIL")
        if script_files:
            for sf in script_files:
                s = json.loads(sf.read_text())
                platform = s.get("platform", "youtube_shorts")
                w, h = get_platform_dims(platform)
                print(f"  {s['slug']}: cv2 frame at {FRAME_AT_SECONDS}s → "
                      f"Haiku caption ({MODEL}) → PIL {w}×{h} → "
                      f"thumb_{s['slug']}_001.jpg")
        else:
            print(f"  (no script files in {SCRIPTS_DATA_DIR})")
        return

    require_env(SCRIPT, "ANTHROPIC_API_KEY")
    if not script_files:
        print(f"[{SCRIPT}] No script files in {SCRIPTS_DATA_DIR}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    failures = asyncio.run(process_all(script_files))
    if failures:
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
