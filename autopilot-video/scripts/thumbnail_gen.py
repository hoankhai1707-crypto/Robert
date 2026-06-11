"""Step 5 — generate a 1280x720 thumbnail per video: blurred frame + centered title text.

Input:  outputs/scripts_YYYY-MM-DD.json + outputs/videos/final_<slug>_*.mp4
Output: outputs/thumbnails/<slug>.jpg
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import (
    EXIT_FAILURE,
    OUTPUTS_DIR,
    PROJECT_ROOT,
    is_dry_run,
    load_dotenv,
    read_output,
    today,
)

SCRIPT = "thumbnail_gen"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"


def extract_frame(video: Path, dest: Path) -> None:
    """Grab a frame from 1s in as the thumbnail base."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(video),
         "-frames:v", "1", str(dest)],
        check=True,
    )


def generate_thumbnail(frame: Path, text: str, out: Path) -> None:
    """Blur the frame, draw the title centered with stroke + dark backing box."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    img = Image.open(frame).convert("RGB").resize((1280, 720))
    blurred = img.filter(ImageFilter.GaussianBlur(radius=15))

    ttf_files = sorted(FONTS_DIR.glob("*.ttf"))
    if ttf_files:
        font = ImageFont.truetype(str(ttf_files[0]), size=72)
    else:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=72)
        except OSError:
            font = ImageFont.load_default(size=72)

    draw = ImageDraw.Draw(blurred, "RGBA")

    # Semi-transparent dark rectangle behind the text for readability
    bbox = draw.textbbox((640, 360), text, font=font, anchor="mm",
                         stroke_width=3)
    pad = 24
    draw.rectangle(
        (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
        fill=(0, 0, 0, 150),
    )

    draw.text((640, 360), text, font=font, anchor="mm",
              fill="white", stroke_width=3, stroke_fill="black")

    blurred.save(str(out), "JPEG", quality=95)


def find_video(slug: str) -> Path | None:
    matches = sorted(VIDEOS_DIR.glob(f"final_{slug}_*.mp4"))
    return matches[-1] if matches else None


def main() -> None:
    load_dotenv()
    scripts = read_output(f"scripts_{today()}.json")

    if is_dry_run():
        print(f"[{SCRIPT}] DRY-RUN — no frame extraction, no PIL rendering")
        ttf = sorted(FONTS_DIR.glob("*.ttf"))
        print(f"[{SCRIPT}] font: {ttf[0].name if ttf else 'none in assets/fonts (would use default)'}")
        for s in scripts:
            print(f"  {s['slug']}: would render \"{s['title'][:50]}\" "
                  f"→ outputs/thumbnails/{s['slug']}.jpg (1280x720, blur r=15, "
                  f"text mm@(640,360), stroke 3, JPEG q95)")
        return

    if not shutil.which("ffmpeg"):
        print(f"[{SCRIPT}] ffmpeg not found on PATH", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    for s in scripts:
        video = find_video(s["slug"])
        if video is None:
            print(f"[{SCRIPT}] No video for slug {s['slug']} — run video_assembler first",
                  file=sys.stderr)
            sys.exit(EXIT_FAILURE)
        try:
            with tempfile.TemporaryDirectory() as td:
                frame = Path(td) / "frame.jpg"
                extract_frame(video, frame)
                out = THUMBS_DIR / f"{s['slug']}.jpg"
                generate_thumbnail(frame, s["title"], out)
                print(f"[{SCRIPT}] {s['slug']} → {out}")
        except Exception as exc:
            print(f"[{SCRIPT}] FAILED on {s['slug']}: {exc}", file=sys.stderr)
            sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
