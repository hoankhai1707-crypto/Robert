"""Step 4 — assemble videos with platform-aware resolution (landscape vs portrait).

Input:  data/scripts/script_*.json, config/platform_config.json
Output: outputs/videos/final_<slug>_001.mp4

Requires ffmpeg on PATH for real runs (not needed in --dry-run).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    EXIT_MISSING_CONFIG,
    OUTPUTS_DIR,
    PROJECT_ROOT,
    SCRIPTS_DATA_DIR,
    is_dry_run,
    load_dotenv,
    require_env,
)

SCRIPT = "video_assembler"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
BGM_DIR = PROJECT_ROOT / "assets" / "bgm"
DEFAULT_VOICE = "en-US-AriaNeural"


def load_platform_config() -> dict:
    return json.loads((CONFIG_DIR / "platform_config.json").read_text())


def get_specs(platform: str, cfg: dict) -> dict:
    return cfg["platforms"].get(platform, cfg["platforms"]["youtube_shorts"])


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{r.stderr}")


def fetch_pexels_clip(query: str, dest: Path, orientation: str, token: str) -> None:
    import requests
    resp = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": token},
        params={"query": query, "per_page": 5, "orientation": orientation},
        timeout=30,
    )
    resp.raise_for_status()
    for video in resp.json().get("videos", []):
        for vf in video.get("video_files", []):
            if vf.get("quality") in ("hd", "sd"):
                with requests.get(vf["link"], stream=True, timeout=120) as dl:
                    dl.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in dl.iter_content(chunk_size=1 << 16):
                            f.write(chunk)
                return
    raise RuntimeError(f"No Pexels clip for '{query}'")


async def generate_tts(text: str, dest: Path, voice: str) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(dest))


def assemble_segment(clip: Path, voiceover: Path, out: Path,
                     width: int, height: int) -> None:
    scale = (f"scale={width}:{height}:force_original_aspect_ratio=fill,"
             f"crop={width}:{height}")
    run_ffmpeg([
        "-stream_loop", "-1", "-i", str(clip), "-i", str(voiceover),
        "-vf", scale,
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", str(out),
    ])


def concat_segments(segments: list[Path], out: Path) -> None:
    lst = out.parent / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segments))
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])


def write_srt(video: Path, srt: Path, tmp_dir: Path) -> None:
    from faster_whisper import WhisperModel
    wav = tmp_dir / "audio.wav"
    run_ffmpeg(["-i", str(video), "-vn", "-ar", "16000", "-ac", "1", str(wav)])
    model = WhisperModel("base", device="cpu")
    segs, _ = model.transcribe(str(wav))

    def ts(s: float) -> str:
        h, r = divmod(s, 3600); m, s = divmod(r, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1)*1000):03}"

    lines = []
    for i, seg in enumerate(segs, 1):
        lines.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{seg.text.strip()}\n")
    srt.write_text("\n".join(lines))


def burn_subtitles(video: Path, srt: Path, out: Path) -> None:
    run_ffmpeg(["-i", str(video), "-vf", f"subtitles={srt}", "-c:a", "copy", str(out)])


def add_bgm(video: Path, bgm: Path, out: Path) -> None:
    run_ffmpeg([
        "-i", str(video), "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        "[1:a]volume=0.12[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out),
    ])


def assemble_video(script: dict, specs: dict, token: str) -> Path:
    slug = script["slug"]
    width = specs["width"]
    height = specs["height"]
    orientation = specs.get("pexels_orientation", "portrait")
    voice = specs.get("voice", DEFAULT_VOICE)

    tmp_dir = Path(tempfile.gettempdir()) / f"autopilot_{slug}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        segs = []
        for i, seg in enumerate(script["segments"]):
            clip = tmp_dir / f"clip_{i}.mp4"
            vo = tmp_dir / f"voice_{i}.mp3"
            seg_out = tmp_dir / f"seg_{i}.mp4"
            fetch_pexels_clip(seg["broll_query"], clip, orientation, token)
            asyncio.run(generate_tts(seg["voiceover"], vo, voice))
            assemble_segment(clip, vo, seg_out, width, height)
            segs.append(seg_out)

        assembled = tmp_dir / "assembled.mp4"
        concat_segments(segs, assembled)

        srt = tmp_dir / "subs.srt"
        write_srt(assembled, srt, tmp_dir)

        with_subs = tmp_dir / "with_subs.mp4"
        burn_subtitles(assembled, srt, with_subs)

        bgm_files = sorted(BGM_DIR.glob("*.mp3"))
        final_tmp = tmp_dir / "final.mp4"
        if bgm_files:
            add_bgm(with_subs, bgm_files[0], final_tmp)
        else:
            print(f"[{SCRIPT}] No BGM in {BGM_DIR} — skipping mix")
            final_tmp = with_subs

        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        out = VIDEOS_DIR / f"final_{slug}_001.mp4"
        shutil.copy2(final_tmp, out)
        return out
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> None:
    load_dotenv()
    dry = is_dry_run()

    script_files = sorted(SCRIPTS_DATA_DIR.glob("script_*.json"))

    if dry:
        platform_cfg = load_platform_config()
        print(f"[{SCRIPT}] DRY-RUN — no Pexels, no TTS, no ffmpeg")
        if script_files:
            for sf in script_files:
                s = json.loads(sf.read_text())
                platform = s.get("platform", platform_cfg.get("default_platform", "youtube_shorts"))
                specs = get_specs(platform, platform_cfg)
                print(f"  {s['slug']}: platform={platform} "
                      f"({specs['width']}×{specs['height']} {specs['orientation']}) "
                      f"— {len(s['segments'])} segments")
                for i, seg in enumerate(s["segments"]):
                    print(f"    [{i}] pexels={seg['broll_query']!r}  "
                          f"tts={seg['voiceover'][:40]!r}…")
        else:
            print(f"  (no script files in {SCRIPTS_DATA_DIR})")
        return

    require_env(SCRIPT, "PEXELS_API_KEY")
    if not shutil.which("ffmpeg"):
        print(f"[{SCRIPT}] ffmpeg not found on PATH", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    if not script_files:
        print(f"[{SCRIPT}] No script files in {SCRIPTS_DATA_DIR}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    platform_cfg = load_platform_config()
    token = os.environ["PEXELS_API_KEY"]
    default_voice = platform_cfg.get("default_voice", DEFAULT_VOICE)

    for sf in script_files:
        script = json.loads(sf.read_text())
        platform = script.get("platform", platform_cfg.get("default_platform", "youtube_shorts"))
        specs = get_specs(platform, platform_cfg)
        specs["voice"] = default_voice
        try:
            out = assemble_video(script, specs, token)
            print(f"[{SCRIPT}] {script['slug']} → {out}")
        except Exception as exc:
            print(f"[{SCRIPT}] FAILED on {script['slug']}: {exc}", file=sys.stderr)
            sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
