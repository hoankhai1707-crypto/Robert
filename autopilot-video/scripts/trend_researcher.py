"""Step 1 — pull rising Google Trends queries for each whitelisted niche.

Output: outputs/trends_YYYY-MM-DD.json (list of trend dicts, format in CLAUDE.md).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    is_dry_run,
    load_dotenv,
    today,
    write_output,
)

SCRIPT = "trend_researcher"


def load_niches() -> list[dict]:
    return json.loads((CONFIG_DIR / "niche_whitelist.json").read_text())["niches"]


def fetch_google_trends() -> list[dict]:
    """Fetch rising related queries for every niche seed keyword via pytrends.

    Scores come from the pytrends 'value' field (0-100 trend velocity; values
    >100 mean 'breakout' and are clamped to 100). Deduplicated by keyword.
    On TooManyRequestsError: wait 60s and retry once, then skip that keyword.
    """
    from pytrends.exceptions import TooManyRequestsError
    from pytrends.request import TrendReq

    pytrends = TrendReq(hl="en-US", tz=420)
    fetched_at = datetime.now().isoformat(timespec="seconds")
    results: dict[str, dict] = {}

    for niche in load_niches():
        for keyword in niche["seed_keywords"]:
            for attempt in (1, 2):
                try:
                    pytrends.build_payload([keyword], timeframe="now 1-d", geo="")
                    related = pytrends.related_queries()
                    rising = related.get(keyword, {}).get("rising")
                    break
                except TooManyRequestsError:
                    if attempt == 1:
                        print(f"[{SCRIPT}] 429 on '{keyword}' — waiting 60s, retrying once")
                        time.sleep(60)
                    else:
                        print(f"[{SCRIPT}] 429 again on '{keyword}' — skipping", file=sys.stderr)
                        rising = None
            if rising is None or rising.empty:
                continue
            for _, row in rising.iterrows():
                query = str(row["query"]).strip().lower()
                score = min(int(row["value"]), 100)
                # Dedupe: keep the highest-scoring occurrence of each query
                if query not in results or results[query]["score"] < score:
                    results[query] = {
                        "keyword": query,
                        "niche": niche["category"],
                        "score": score,
                        "source": "google_trends",
                        "fetched_at": fetched_at,
                    }

    return sorted(results.values(), key=lambda r: r["score"], reverse=True)


def mock_trends() -> list[dict]:
    fetched_at = datetime.now().isoformat(timespec="seconds")
    samples = [
        ("ai photo editor free", "technology", 94),
        ("how to save money fast 2026", "personal_finance_literacy", 88),
        ("5 minute desk workout", "health_fitness", 81),
        ("cheap flights europe summer", "travel", 77),
        ("3 ingredient dinner ideas", "food", 73),
        ("james webb new discovery", "science_curiosity", 69),
        ("notion alternative 2026", "productivity", 64),
    ]
    return [
        {"keyword": k, "niche": n, "score": s, "source": "google_trends", "fetched_at": fetched_at}
        for k, n, s in samples
    ]


def main() -> None:
    load_dotenv()
    dry = is_dry_run()

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — using mock trend data, no network calls")
        trends = mock_trends()
    else:
        try:
            trends = fetch_google_trends()
        except Exception as exc:  # surface the real error, fail the step
            print(f"[{SCRIPT}] FAILED: {exc}", file=sys.stderr)
            sys.exit(EXIT_FAILURE)

    if not trends:
        print(f"[{SCRIPT}] No rising trends found for any niche", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    path = write_output(f"trends_{today()}.json", trends)
    print(f"[{SCRIPT}] {len(trends)} trends → {path}")
    for t in trends[:5]:
        print(f"  {t['score']:>3}  {t['niche']:<26} {t['keyword']}")


if __name__ == "__main__":
    main()
