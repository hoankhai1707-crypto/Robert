"""Step 4 — assemble final videos: Pexels b-roll + edge-tts voiceover + whisper subs + bgm.

Input:  outputs/scripts_YYYY-MM-DD.json
Output: outputs/videos/final_<slug>_<NNN>.mp4

Requires ffmpeg on PATH for real runs (not needed in --dry-run).
"""
from __future__ import annotations

import asyncio
import os
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
    require_env,
    today,
)

SCRIPT = "video_assembler"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
BGM_DIR = PROJECT_ROOT / "assets" / "bgm"
VOICE = "en-US-AriaNeural"
TARGET_W, TARGET_H = 1280, 720


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd)}\n{result.stderr}")


def fetch_pexels_clip(query: str, dest: Path) -> None:
    """Download the first Pexels video file with width >= 1280 for `query`."""
    import requests

    resp = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": os.getenv("PEXELS_API_KEY")},
        params={"query": query, "per_page": 3, "orientation": "landscape"},
        timeout=30,
    )
    resp.raise_for_status()
    for video in resp.json().get("videos", []):
        for vf in video.get("video_files", []):
            if (vf.get("width") or 0) >= 1280:
                with requests.get(vf["link"], stream=True, timeout=120) as dl:
                    dl.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in dl.iter_content(chunk_size=1 << 16):
                            f.write(chunk)
                return
    raise RuntimeError(f"No Pexels clip >=1280px wide for query '{query}'")


async def generate_tts(text: str, dest: Path) -> None:
    """Synthesize voiceover with edge-tts (en-US-AriaNeural)."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=VOICE)
    await communicate.save(str(dest))


def assemble_segment(clip: Path, voiceover: Path, out: Path) -> None:
    """Trim the clip to the voiceover length, scale to 1280x720, mux the audio."""
    run_ffmpeg([
        "-i", str(clip), "-i", str(voiceover),
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
               f"crop={TARGET_W}:{TARGET_H}",
        "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
        "-shortest", str(out),
    ])


def concat_segments(segments: list[Path], out: Path) -> None:
    """Losslessly concatenate same-codec segment files."""
    list_file = out.parent / "concat.txt"
    list_file.write_text("".join(f"file '{p}'\n" for p in segments))
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_file),
                "-c", "copy", str(out)])


def extract_audio(video: Path, out: Path) -> None:
    run_ffmpeg(["-i", str(video), "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", str(out)])


def write_srt(video: Path, srt_path: Path, tmp_dir: Path) -> None:
    """Transcribe the assembled audio with faster-whisper and write an .srt file."""
    from faster_whisper import WhisperModel

    audio_path = tmp_dir / "assembled_audio.wav"
    extract_audio(video, audio_path)

    model = WhisperModel("base", device="cpu")
    segments, _ = model.transcribe(str(audio_path))

    def ts(seconds: float) -> str:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{seg.text.strip()}\n")
    srt_path.write_text("\n".join(lines))


def burn_subtitles(video: Path, srt: Path, out: Path) -> None:
    # ffmpeg subtitles filter needs escaped path on some platforms; keep paths simple
    run_ffmpeg(["-i", str(video),
                "-vf", f"subtitles={srt}",
                "-c:a", "copy", str(out)])


def add_bgm(video: Path, bgm: Path, out: Path) -> None:
    """Mix background music under the voiceover at low volume, looped to fit."""
    run_ffmpeg([
        "-i", str(video), "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        "[1:a]volume=0.12[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(out),
    ])


def next_output_path(slug: str) -> Path:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    n = 1
    while (VIDEOS_DIR / f"final_{slug}_{n:03}.mp4").exists():
        n += 1
    return VIDEOS_DIR / f"final_{slug}_{n:03}.mp4"


def assemble_video(script: dict) -> Path:
    slug = script["slug"]
    tmp_dir = Path(tempfile.gettempdir()) / f"autopilot_{slug}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        # 1-2. Per segment: b-roll + voiceover -> segment_N.mp4
        segment_files = []
        for i, seg in enumerate(script["segments"]):
            clip = tmp_dir / f"clip_{i}.mp4"
            voice = tmp_dir / f"voice_{i}.mp3"
            seg_out = tmp_dir / f"segment_{i}.mp4"
            fetch_pexels_clip(seg["broll_query"], clip)
            asyncio.run(generate_tts(seg["voiceover"], voice))
            assemble_segment(clip, voice, seg_out)
            segment_files.append(seg_out)

        # 3. Concatenate
        assembled = tmp_dir / "assembled.mp4"
        concat_segments(segment_files, assembled)

        # 4. Subtitles via faster-whisper
        srt = tmp_dir / "subtitles.srt"
        write_srt(assembled, srt, tmp_dir)

        # 5. Burn subtitles
        with_subs = tmp_dir / "with_subs.mp4"
        burn_subtitles(assembled, srt, with_subs)

        # 6. Background music — first .mp3 in assets/bgm (skip mixing if none)
        bgm_files = sorted(BGM_DIR.glob("*.mp3"))
        final_tmp = tmp_dir / "final.mp4"
        if bgm_files:
            add_bgm(with_subs, bgm_files[0], final_tmp)
        else:
            print(f"[{SCRIPT}] No .mp3 in {BGM_DIR} — skipping bgm")
            final_tmp = with_subs

        # 7. Copy to outputs
        out_path = next_output_path(slug)
        shutil.copy2(final_tmp, out_path)
        return out_path
    finally:
        # 8. Clean up temp folder
        shutil.rmtree(tmp_dir, ignore_errors=True)


def dry_run_report(scripts: list[dict]) -> None:
    print(f"[{SCRIPT}] DRY-RUN — no downloads, no tts, no ffmpeg")
    bgm_files = sorted(BGM_DIR.glob("*.mp3"))
    print(f"[{SCRIPT}] bgm available: {bgm_files[0].name if bgm_files else 'none (would skip mixing)'}")
    for script in scripts:
        slug = script["slug"]
        print(f"  {slug}: would build {len(script['segments'])} segments in "
              f"/tmp/autopilot_{slug}/ → outputs/videos/final_{slug}_001.mp4")
        for i, seg in enumerate(script["segments"]):
            print(f"    seg{i}: pexels '{seg['broll_query']}' + tts({VOICE}) "
                  f"\"{seg['voiceover'][:40]}...\"")


def main() -> None:
    load_dotenv()
    scripts = read_output(f"scripts_{today()}.json")

    if is_dry_run():
        dry_run_report(scripts)
        return

    require_env(SCRIPT, "PEXELS_API_KEY")
    if not shutil.which("ffmpeg"):
        print(f"[{SCRIPT}] ffmpeg not found on PATH", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    for script in scripts:
        try:
            out = assemble_video(script)
            print(f"[{SCRIPT}] {script['slug']} → {out}")
        except Exception as exc:
            print(f"[{SCRIPT}] FAILED on {script['slug']}: {exc}", file=sys.stderr)
            sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
