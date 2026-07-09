# Autopilot Video — Claude Project Instructions

Automated short-video content pipeline: trend research → niche selection → script
generation → video assembly → thumbnail → human approval → multi-platform upload.

## Project Root

- On Windows (Robert's machine): `C:\Users\ROBERT\.claude\projects\autopilot-video`
- In the Robert repo: `autopilot-video/`
- All scripts run from the project root: `python scripts/<name>.py`
- All relative paths (`./logs`, `./outputs`, `./config`, `./assets`) resolve from the project root.

## Model Routing Rules (3 models)

| Model | Exact ID | Used for | Why |
|---|---|---|---|
| Claude Fable 5 | `claude-fable-5` | Niche selection — the one high-stakes strategic decision per run (`niche_selector.py`) | Most capable model; this single decision drives the whole day's content. One call/day keeps cost bounded. |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Script generation — 3 video scripts per run (`script_generator.py`) | Best speed/intelligence balance for structured creative output at volume. |
| Claude Haiku 4.5 | `claude-haiku-4-5` | Cheap utility tasks — titles, tags, captions, classification | Fastest and cheapest; use for anything that doesn't need deep reasoning. |

Routing rule of thumb: **one Fable call per pipeline run, a handful of Sonnet calls,
Haiku for everything else.** Never use Fable for bulk generation.

## Pipeline Order (do not reorder)

1. `scripts/trend_researcher.py` — rising Google Trends (Vietnam + Worldwide) per whitelisted niche → `data/trends/trends_YYYY-MM-DD.json`
2. `scripts/niche_selector.py` — Haiku judges (virality + SEO) then Fable 5 final decision, prompt from `prompts/niche_selection.txt` → `data/selected_niches/niches_YYYY-MM-DD.json`
3. `scripts/script_generator.py` — Sonnet 4.6 writes 3 scripts concurrently, prompt from `prompts/script_generation.txt` → `data/scripts/script_<slug>_<NNN>.json`
4. `scripts/video_assembler.py` — Pexels clips + edge-tts voiceover + whisper subs + bgm, platform-aware resolution from `config/platform_config.json` → `outputs/videos/final_<slug>_001.mp4`
5. `scripts/thumbnail_gen.py` — cv2 frame at 2s + Haiku caption + PIL render → `outputs/thumbnails/thumb_<slug>_001.jpg`
6. `scripts/approval_gate.py` — Telegram preview with Approve/Reject buttons (60-min timeout) → `data/approved_YYYY-MM-DD.json`; rejected videos → `outputs/rejected/`
7. `scripts/multi_uploader.py` — YouTube + Facebook Reels + Instagram Reels, rate limit + retries from `config/upload_schedule.json` → `logs/uploads_YYYY-MM-DD.json`
8. `scripts/main_pipeline.py` — orchestrator + FastAPI server (`/health`, `POST /run`) + Telegram summary

## Platform Resolutions (config/platform_config.json)

- `youtube_long`: 1920×1080 landscape
- `youtube_shorts` / `facebook_reels` / `instagram_reels`: 1080×1920 portrait

## Trend Result Format

`fetch_google_trends()` must return a list of dicts in exactly this shape:

```json
{
  "keyword": "string — the rising query",
  "niche": "string — whitelist category it came from",
  "score": 0-100,
  "source": "google_trends",
  "fetched_at": "ISO-8601 timestamp"
}
```

## Hard Rules

- Read `.claude/rules/pipeline-rules.md` and `.claude/rules/cost-rules.md` before changing any script.
- Every script must support `--dry-run` (no network, no API keys, mock data, exit 0).
- Every Claude API call must log cost to `./logs/costs_YYYY-MM-DD.json` immediately after the call.
- If the daily cost limit (see cost-rules.md) is already exceeded, scripts must refuse to make new API calls and exit(2).
- Secrets come only from environment variables / `.env`. Never hardcode keys.
