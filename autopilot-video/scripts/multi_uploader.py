"""Step 7 — upload approved videos to YouTube, Facebook Reels, and Instagram Reels.

Input:  outputs/scripts_YYYY-MM-DD.json, outputs/approvals_YYYY-MM-DD.json,
        outputs/videos/final_<slug>_*.mp4, outputs/thumbnails/<slug>.jpg
Output: logs/uploads_YYYY-MM-DD.json (appended per upload)

Note: Instagram Reels requires the video at a public URL (PUBLIC_VIDEO_BASE_URL/.env) —
the Graph API fetches it server-side; local file upload is not supported for IG.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from common import (
    EXIT_FAILURE,
    LOGS_DIR,
    OUTPUTS_DIR,
    is_dry_run,
    load_dotenv,
    read_output,
    today,
)

SCRIPT = "multi_uploader"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
THUMBS_DIR = OUTPUTS_DIR / "thumbnails"
GRAPH = "https://graph.facebook.com/v19.0"


def uploads_log_path() -> Path:
    return LOGS_DIR / f"uploads_{today()}.json"


def log_upload(entry: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = uploads_log_path()
    data = json.loads(path.read_text()) if path.exists() else []
    data.append(entry)
    path.write_text(json.dumps(data, indent=2))


def find_video(slug: str) -> Path | None:
    matches = sorted(VIDEOS_DIR.glob(f"final_{slug}_*.mp4"))
    return matches[-1] if matches else None


def upload_to_youtube(video: Path, thumbnail: Path, script: dict) -> dict:
    """Resumable upload via the YouTube Data API, then set the custom thumbnail."""
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

    if thumbnail.exists():
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

    # Phase 1: initialize
    init = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        headers=headers,
        json={"upload_phase": "start"},
        timeout=30,
    )
    init.raise_for_status()
    video_id = init.json()["video_id"]
    upload_url = init.json()["upload_url"]

    # Phase 2: upload the binary
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

    # Phase 3: publish with caption
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
    """Create a REELS media container from a public URL, poll until FINISHED, publish."""
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

    # Poll status every 10s until FINISHED (or fail on ERROR / 5min cap)
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


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    scripts = read_output(f"scripts_{today()}.json")
    approvals = read_output(f"approvals_{today()}.json")
    approved = [s for s in scripts if approvals.get(s["slug"])]

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no uploads")
        for s in approved:
            print(f"  {s['slug']}: would upload to youtube (resumable + thumbnail), "
                  f"facebook reels (3-phase), instagram reels (public URL + poll 10s)")
        for s in scripts:
            if not approvals.get(s["slug"]):
                print(f"  {s['slug']}: REJECTED — skipped")
        print(f"[{SCRIPT}] Would append results to {uploads_log_path()}")
        return

    failures = 0
    for s in approved:
        slug = s["slug"]
        video = find_video(slug)
        if video is None:
            print(f"[{SCRIPT}] No video file for {slug}", file=sys.stderr)
            failures += 1
            continue
        thumbnail = THUMBS_DIR / f"{slug}.jpg"

        targets = []
        if os.getenv("YOUTUBE_REFRESH_TOKEN"):
            targets.append(("youtube", lambda: upload_to_youtube(video, thumbnail, s)))
        if os.getenv("META_ACCESS_TOKEN") and os.getenv("FB_PAGE_ID"):
            targets.append(("facebook", lambda: upload_to_facebook_reels(video, s)))
        public_base = os.getenv("PUBLIC_VIDEO_BASE_URL")
        if os.getenv("META_ACCESS_TOKEN") and os.getenv("IG_ACCOUNT_ID") and public_base:
            url = f"{public_base.rstrip('/')}/{video.name}"
            targets.append(("instagram", lambda: upload_to_instagram_reels(url, s)))

        if not targets:
            print(f"[{SCRIPT}] No platform credentials configured — nothing to do",
                  file=sys.stderr)
            sys.exit(EXIT_FAILURE)

        for name, fn in targets:
            try:
                result = fn()
                result.update({"slug": slug, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
                log_upload(result)
                print(f"[{SCRIPT}] {slug} → {name}: {result['url']}")
            except Exception as exc:
                print(f"[{SCRIPT}] {slug} → {name} FAILED: {exc}", file=sys.stderr)
                log_upload({"slug": slug, "platform": name, "error": str(exc),
                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
                failures += 1

    if failures:
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
