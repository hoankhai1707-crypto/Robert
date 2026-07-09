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

- `trend_researcher.py` → `data/trends/trends_YYYY-MM-DD.json`: list of trend dicts
  (format in CLAUDE.md, plus `"region": "Vietnam"|"Worldwide"`).
- `niche_selector.py` → `data/selected_niches/niches_YYYY-MM-DD.json`:
  `{"niche": str, "rationale": str, "angles": [{"title": str, "hook": str, "keyword": str} x3],
    "judge_a_analysis": str, "judge_b_analysis": str, "selected_at": str}`
- `script_generator.py` → `data/scripts/script_<slug>_<NNN>.json` (one file per script):
  `{"slug": str, "title": str, "hook": str, "platform": str, "description": str, "tags": [str],
    "segments": [{"voiceover": str, "broll_query": str} x4-6], "generated_at": str}`
- `video_assembler.py` → `outputs/videos/final_<slug>_001.mp4`
  (resolution per platform from `config/platform_config.json`)
- `thumbnail_gen.py` → `outputs/thumbnails/thumb_<slug>_001.jpg`
- `approval_gate.py` → `data/approved_YYYY-MM-DD.json`:
  `{"approved": [slug], "rejected": [slug], "decided_at": str}`;
  rejected videos move to `outputs/rejected/`
- `multi_uploader.py` → appends to `logs/uploads_YYYY-MM-DD.json`
  (rate limit + retry policy from `config/upload_schedule.json`)

## Retries & Rate Limits

- pytrends `TooManyRequestsError`: wait 60s, retry once, then give up on that keyword (not the whole run).
- Anthropic SDK already retries 429/5xx twice with backoff — do not add an outer retry loop around API calls.
- Pexels/Graph API: 3 retries with exponential backoff (2s, 4s, 8s) on 5xx only.

## Approval

- Telegram approval timeout = `APPROVAL_TIMEOUT_MINUTES` from `.env` (default 60).
- On timeout: log a warning "Timeout - auto-approving" and proceed (auto-approve).
- A rejected video is skipped, never uploaded, and moved to `outputs/rejected/` for review.

## Uploads

- Rate limit: max 5 uploads per platform per hour (`config/upload_schedule.json`).
- Upload retries: 3 attempts with exponential backoff (2s, 4s, 8s).
