# Pipeline Rules

## Execution

1. Steps run strictly in the order defined in CLAUDE.md. A step may only start if the
   previous step exited 0 and produced its expected output file.
2. Every script accepts `--dry-run`: no network calls, no API keys required, mock data,
   prints what it WOULD do, exits 0. Dry-run must never write to `outputs/videos` or upload anywhere.
3. Every script exits non-zero on failure and prints the reason to stderr.
   Exit codes: 1 = runtime/parse failure, 2 = cost limit exceeded, 3 = missing config/env.
4. `main_pipeline.py` stops the chain at the first failing step and sends a Telegram
   failure alert with the step name. On full success it sends a success message pointing
   at `./logs/uploads_YYYY-MM-DD.json`.

## Data Contracts

- `trend_researcher.py` → `outputs/trends_YYYY-MM-DD.json`: list of trend dicts (format in CLAUDE.md).
- `niche_selector.py` → `outputs/selection_YYYY-MM-DD.json`:
  `{"niche": str, "rationale": str, "angles": [{"title": str, "hook": str, "keyword": str} x3]}`
- `script_generator.py` → `outputs/scripts_YYYY-MM-DD.json`: list of 3 script objects:
  `{"slug": str, "title": str, "hook": str, "platform": str, "description": str, "tags": [str],
    "segments": [{"voiceover": str, "broll_query": str} x4-6]}`
- `video_assembler.py` → `outputs/videos/final_<slug>_<NNN>.mp4`
- `thumbnail_gen.py` → `outputs/thumbnails/<slug>.jpg`
- `multi_uploader.py` → appends to `logs/uploads_YYYY-MM-DD.json`

## Retries & Rate Limits

- pytrends `TooManyRequestsError`: wait 60s, retry once, then give up on that keyword (not the whole run).
- Anthropic SDK already retries 429/5xx twice with backoff — do not add an outer retry loop around API calls.
- Pexels/Graph API: 3 retries with exponential backoff (2s, 4s, 8s) on 5xx only.

## Approval

- Telegram approval timeout = `APPROVAL_TIMEOUT_MINUTES` from `.env` (default 30).
- On timeout: log a warning "Timeout - auto-approving" and proceed (auto-approve).
- A rejected video is skipped, never uploaded, and left in `outputs/videos/` for review.
