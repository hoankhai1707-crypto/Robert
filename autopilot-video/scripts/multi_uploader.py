"""Step 7 — upload approved videos to YouTube, Facebook Reels, Instagram Reels.

Input:  data/approved_YYYY-MM-DD.json, data/scripts/script_*.json,
        outputs/videos/final_<slug>_*.mp4, outputs/thumbnails/thumb_<slug>_*.jpg,
        config/upload_schedule.json
Output: logs/uploads_YYYY-MM-DD.json

Rate limit: max 5 uploads per platform per hour (config/upload_schedule.json).
Retries: 3 attempts with exponential backoff (2s, 4s, 8s).
Instagram requires the video at a public URL (PUBLIC_VIDEO_BASE_URL).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from common import (
    CONFIG_DIR,
    DATA_DIR,
    EXIT_FAILURE,
    LOGS_DIR,
    OUTPUTS_DIR,
    SCRIPTS_DATA_DIR,
    is_dry_run,
    load_dotenv,
    read_data_json,
    today,
)

SCRIPT = "multi_uploader"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
GRAPH = "https://graph.facebook.com/v19.0"


def load_schedule() -> dict:
    path = CONFIG_DIR / "upload_schedule.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"rate_limits": {"per_platform_per_hour": 5},
            "retry": {"max_attempts": 3, "backoff_seconds": [2, 4, 8]}}


def uploads_log_path() -> Path:
    return LOGS_DIR / f"uploads_{today()}.json"


def read_upload_log() -> list[dict]:
    path = uploads_log_path()
    return json.loads(path.read_text()) if path.exists() else []


def log_upload(entry: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    data = read_upload_log()
    data.append(entry)
    uploads_log_path().write_text(json.dumps(data, indent=2))


def uploads_last_hour(platform: str) -> int:
    """Count successful uploads to `platform` in the past hour from today's log."""
    cutoff = time.time() - 3600
    count = 0
    for entry in read_upload_log():
        if entry.get("platform") != platform or entry.get("error"):
            continue
        try:
            ts = datetime.fromisoformat(entry["ts"]).timestamp()
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            count += 1
    return count


def with_retries(fn, label: str, schedule: dict):
    """Run fn() with up to max_attempts tries, exponential backoff between."""
    retry_cfg = schedule.get("retry", {})
    max_attempts = retry_cfg.get("max_attempts", 3)
    backoffs = retry_cfg.get("backoff_seconds", [2, 4, 8])
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                wait = backoffs[min(attempt, len(backoffs) - 1)]
                print(f"[{SCRIPT}] {label} attempt {attempt+1}/{max_attempts} "
                      f"failed: {exc} — retrying in {wait}s")
                time.sleep(wait)
    raise last_exc


def find_video(slug: str) -> Path | None:
    matches = sorted(VIDEOS_DIR.glob(f"final_{slug}_*.mp4"))
    return matches[-1] if matches else None


def find_thumb(slug: str) -> Path | None:
    matches = sorted(THUMBS_DIR.glob(f"thumb_{slug}_*.jpg"))
    return matches[-1] if matches else None


def upload_to_youtube(video: Path, thumbnail: Path | None, script: dict) -> dict:
    """Resumable upload via YouTube Data API, then set the custom thumbnail."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    credentials = Credentials(
        token=None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    youtube = build("youtube", "v3", credentials=credentials)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": script["title"],
                "description": script["description"],
                "tags": script["tags"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        },
        media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    video_id = response["id"]

    if thumbnail and thumbnail.exists():
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail)),
        ).execute()

    return {"platform": "youtube", "video_id": video_id,
            "url": f"https://youtube.com/watch?v={video_id}"}


def upload_to_facebook_reels(video: Path, script: dict) -> dict:
    """Three-phase Reels upload: initialize → upload binary → publish."""
    import requests

    page_id = os.getenv("FB_PAGE_ID")
    token = os.getenv("META_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}

    init = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        headers=headers,
        json={"upload_phase": "start"},
        timeout=30,
    )
    init.raise_for_status()
    video_id = init.json()["video_id"]
    upload_url = init.json()["upload_url"]

    size = video.stat().st_size
    with open(video, "rb") as f:
        up = requests.post(
            upload_url,
            headers={"Authorization": f"OAuth {token}",
                     "offset": "0", "file_size": str(size)},
            data=f,
            timeout=600,
        )
    up.raise_for_status()

    fin = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        headers=headers,
        json={"upload_phase": "finish", "video_id": video_id,
              "video_state": "PUBLISHED", "description": script["description"]},
        timeout=60,
    )
    fin.raise_for_status()

    return {"platform": "facebook", "post_id": video_id,
            "url": f"https://www.facebook.com/reel/{video_id}"}


def upload_to_instagram_reels(public_url: str, script: dict) -> dict:
    """REELS container from public URL → poll status_code → publish."""
    import requests

    ig_id = os.getenv("IG_ACCOUNT_ID")
    token = os.getenv("META_ACCESS_TOKEN")
    params = {"access_token": token}

    create = requests.post(
        f"{GRAPH}/{ig_id}/media",
        params=params,
        json={"media_type": "REELS", "video_url": public_url,
              "caption": script["description"]},
        timeout=60,
    )
    create.raise_for_status()
    creation_id = create.json()["id"]

    deadline = time.monotonic() + 300
    while True:
        status = requests.get(
            f"{GRAPH}/{creation_id}",
            params={**params, "fields": "status_code"},
            timeout=30,
        )
        status.raise_for_status()
        code = status.json().get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR" or time.monotonic() > deadline:
            raise RuntimeError(f"IG media container status: {code}")
        time.sleep(10)

    publish = requests.post(
        f"{GRAPH}/{ig_id}/media_publish",
        params=params,
        json={"creation_id": creation_id},
        timeout=60,
    )
    publish.raise_for_status()
    media_id = publish.json()["id"]

    return {"platform": "instagram", "media_id": media_id,
            "url": f"https://www.instagram.com/reel/{media_id}"}


def load_approved_scripts() -> list[dict]:
    approved_doc = read_data_json(DATA_DIR / f"approved_{today()}.json")
    approved_slugs = set(approved_doc.get("approved", []))
    scripts = []
    for sf in sorted(SCRIPTS_DATA_DIR.glob("script_*.json")):
        s = json.loads(sf.read_text())
        if s["slug"] in approved_slugs:
            scripts.append(s)
    return scripts


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    schedule = load_schedule()
    rate_limit = schedule.get("rate_limits", {}).get("per_platform_per_hour", 5)

    approved = load_approved_scripts()

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no uploads")
        print(f"[{SCRIPT}] Rate limit: {rate_limit}/platform/hour "
              f"(config/upload_schedule.json)")
        print(f"[{SCRIPT}] Retry policy: "
              f"{schedule['retry']['max_attempts']} attempts, "
              f"backoff {schedule['retry']['backoff_seconds']}s")
        for s in approved:
            print(f"  {s['slug']}: would upload → youtube (resumable + thumbnail), "
                  f"facebook reels (3-phase), instagram reels (public URL + poll)")
        print(f"[{SCRIPT}] Would append results to {uploads_log_path()}")
        return

    if not approved:
        print(f"[{SCRIPT}] Nothing approved to upload", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    failures = 0
    for s in approved:
        slug = s["slug"]
        video = find_video(slug)
        if video is None:
            print(f"[{SCRIPT}] No video file for {slug}", file=sys.stderr)
            failures += 1
            continue
        thumbnail = find_thumb(slug)

        targets = []
        if os.getenv("YOUTUBE_REFRESH_TOKEN"):
            targets.append(("youtube",
                            lambda v=video, t=thumbnail, sc=s: upload_to_youtube(v, t, sc)))
        if os.getenv("META_ACCESS_TOKEN") and os.getenv("FB_PAGE_ID"):
            targets.append(("facebook",
                            lambda v=video, sc=s: upload_to_facebook_reels(v, sc)))
        public_base = os.getenv("PUBLIC_VIDEO_BASE_URL")
        if os.getenv("META_ACCESS_TOKEN") and os.getenv("IG_ACCOUNT_ID") and public_base:
            url = f"{public_base.rstrip('/')}/{video.name}"
            targets.append(("instagram",
                            lambda u=url, sc=s: upload_to_instagram_reels(u, sc)))

        if not targets:
            print(f"[{SCRIPT}] No platform credentials configured", file=sys.stderr)
            sys.exit(EXIT_FAILURE)

        for name, fn in targets:
            if uploads_last_hour(name) >= rate_limit:
                print(f"[{SCRIPT}] {slug} → {name}: SKIPPED "
                      f"(rate limit {rate_limit}/hour reached)")
                log_upload({"slug": slug, "platform": name,
                            "error": f"rate_limited ({rate_limit}/hour)",
                            "ts": datetime.now().isoformat(timespec="seconds")})
                continue
            try:
                result = with_retries(fn, f"{slug}→{name}", schedule)
                result.update({"slug": slug,
                               "ts": datetime.now().isoformat(timespec="seconds")})
                log_upload(result)
                print(f"[{SCRIPT}] {slug} → {name}: {result['url']}")
            except Exception as exc:
                print(f"[{SCRIPT}] {slug} → {name} FAILED after retries: {exc}",
                      file=sys.stderr)
                log_upload({"slug": slug, "platform": name, "error": str(exc),
                            "ts": datetime.now().isoformat(timespec="seconds")})
                failures += 1

    if failures:
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
