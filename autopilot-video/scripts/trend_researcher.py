"""Step 1 — fetch rising Google Trends from Vietnam + Worldwide.

Output: data/trends/trends_YYYY-MM-DD.json
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    TRENDS_DIR,
    is_dry_run,
    load_dotenv,
    today,
    write_data_json,
)

SCRIPT = "trend_researcher"
REGIONS = [
    {"geo": "VN", "hl": "vi", "tz": 420, "name": "Vietnam"},
    {"geo": "", "hl": "en-US", "tz": 0, "name": "Worldwide"},
]

DRY_RUN_MOCK = [
    {"keyword": "AI coding tools 2026", "niche": "technology", "score": 95,
     "source": "google_trends", "region": "Vietnam",
     "fetched_at": "2026-06-11T07:00:00"},
    {"keyword": "ChatGPT vs Claude", "niche": "technology", "score": 88,
     "source": "google_trends", "region": "Worldwide",
     "fetched_at": "2026-06-11T07:00:00"},
    {"keyword": "side hustle income 2026", "niche": "personal_finance_literacy", "score": 82,
     "source": "google_trends", "region": "Vietnam",
     "fetched_at": "2026-06-11T07:00:00"},
    {"keyword": "morning routine productivity", "niche": "productivity", "score": 77,
     "source": "google_trends", "region": "Worldwide",
     "fetched_at": "2026-06-11T07:00:00"},
    {"keyword": "space telescope discovery 2026", "niche": "science_curiosity", "score": 71,
     "source": "google_trends", "region": "Worldwide",
     "fetched_at": "2026-06-11T07:00:00"},
    {"keyword": "home workout no equipment", "niche": "health_fitness", "score": 68,
     "source": "google_trends", "region": "Vietnam",
     "fetched_at": "2026-06-11T07:00:00"},
]


def fetch_region_keyword(keyword: str, niche: str, region: dict) -> list[dict]:
    from pytrends.request import TrendReq
    try:
        from pytrends.exceptions import TooManyRequestsError
    except ImportError:
        TooManyRequestsError = Exception

    pytrends = TrendReq(hl=region["hl"], tz=region["tz"])

    def _fetch() -> list[dict]:
        pytrends.build_payload([keyword], timeframe="now 7-d", geo=region["geo"])
        related = pytrends.related_queries()
        rising = related.get(keyword, {}).get("rising")
        results = []
        if rising is not None and not rising.empty:
            for _, row in rising.head(3).iterrows():
                results.append({
                    "keyword": str(row["query"]),
                    "niche": niche,
                    "score": int(row.get("value", 50)),
                    "source": "google_trends",
                    "region": region["name"],
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                })
        return results

    try:
        return _fetch()
    except TooManyRequestsError:
        print(f"[{SCRIPT}] Rate-limited on '{keyword}' ({region['name']}), waiting 60s…")
        time.sleep(60)
        try:
            return _fetch()
        except Exception as exc:
            print(f"[{SCRIPT}] Retry failed for '{keyword}': {exc}", file=sys.stderr)
            return []
    except Exception as exc:
        print(f"[{SCRIPT}] Error on '{keyword}' ({region['name']}): {exc}", file=sys.stderr)
        return []


def fetch_all_trends() -> list[dict]:
    whitelist = json.loads((CONFIG_DIR / "niche_whitelist.json").read_text())
    seen: set[str] = set()
    results = []
    total_niches = len(whitelist["niches"])
    for region in REGIONS:
        print(f"[{SCRIPT}] Scanning region: {region['name']}")
        for niche_def in whitelist["niches"]:
            niche = niche_def["category"]
            for keyword in niche_def["seed_keywords"]:
                for item in fetch_region_keyword(keyword, niche, region):
                    if item["keyword"] not in seen:
                        seen.add(item["keyword"])
                        results.append(item)
    print(f"[{SCRIPT}] Fetched {len(results)} unique trends across "
          f"{len(REGIONS)} regions × {total_niches} niches")
    return results


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    out_path = TRENDS_DIR / f"trends_{today()}.json"

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no network calls")
        for region in REGIONS:
            print(f"  Region: {region['name']} "
                  f"(geo={region['geo']!r}, hl={region['hl']!r}, tz={region['tz']})")
        print(f"[{SCRIPT}] Would query niche_whitelist.json seed keywords per region")
        write_data_json(out_path, DRY_RUN_MOCK)
        print(f"[{SCRIPT}] DRY-RUN output → {out_path} ({len(DRY_RUN_MOCK)} trends)")
        return

    trends = fetch_all_trends()
    if not trends:
        print(f"[{SCRIPT}] No trends fetched — check pytrends connectivity", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    write_data_json(out_path, trends)
    print(f"[{SCRIPT}] Saved {len(trends)} trends → {out_path}")
    for t in trends[:5]:
        print(f"  {t['score']:>3}  {t['niche']:<26} {t['keyword']} ({t['region']})")


if __name__ == "__main__":
    main()
