"""Step 2 — multi-agent niche selection: 2 Haiku judges → Fable 5 final decision.

Input:  data/trends/trends_YYYY-MM-DD.json
Output: data/selected_niches/niches_YYYY-MM-DD.json
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime
from string import Template

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    NICHES_DIR,
    TRENDS_DIR,
    check_cost_limit,
    is_dry_run,
    load_dotenv,
    log_cost,
    read_data_json,
    read_prompt,
    require_env,
    today,
    write_data_json,
)

SCRIPT = "niche_selector"
HAIKU = "claude-haiku-4-5"
FABLE = "claude-fable-5"

DRY_RUN_MOCK = {
    "niche": "technology",
    "rationale": (
        "AI tools dominate both Vietnam and Worldwide trending with scores 88-95, "
        "signalling peak audience curiosity. Technology content matches our brand voice "
        "and delivers strong repeat-view potential."
    ),
    "angles": [
        {
            "title": "Top 5 AI Tools Replacing Jobs in 2026",
            "hook": "These AI tools will replace your job.",
            "keyword": "AI coding tools 2026",
        },
        {
            "title": "ChatGPT vs Claude: Which AI Actually Wins?",
            "hook": "Two AIs — only one comes out smarter.",
            "keyword": "ChatGPT vs Claude",
        },
        {
            "title": "Free AI Tools You Are Missing Right Now",
            "hook": "You are sleeping on these free AI tools.",
            "keyword": "AI coding tools 2026",
        },
    ],
    "judge_a_analysis": "[DRY-RUN] Technology: peak viral potential — AI anxiety drives shares.",
    "judge_b_analysis": "[DRY-RUN] Technology: score 95 with moderate SEO competition — ideal.",
    "selected_at": "2026-06-11T07:05:00",
}


async def run_judge(
    client,
    perspective: str,
    trends_json: str,
    whitelist_json: str,
) -> tuple[str, object]:
    import anthropic
    response = await client.messages.create(
        model=HAIKU,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": (
                f"You are a short-video content strategist analyzing from a "
                f"{perspective} perspective.\n\n"
                f"Trending topics today (JSON):\n{trends_json}\n\n"
                f"Available niches:\n{whitelist_json}\n\n"
                f"In 3-4 sentences, recommend the single best niche to target today "
                f"and explain why from your specialist angle."
            ),
        }],
    )
    return response.content[0].text.strip(), response


async def run_debate(trends: list[dict], whitelist: dict, business: dict) -> dict:
    import anthropic

    client = anthropic.AsyncAnthropic()
    trends_json = json.dumps(trends, indent=2)
    whitelist_json = json.dumps(whitelist, indent=2)
    business_json = json.dumps(business, indent=2)

    check_cost_limit(SCRIPT)
    # Haiku judges run concurrently
    (judge_a, resp_a), (judge_b, resp_b) = await asyncio.gather(
        run_judge(client, "virality and audience engagement potential", trends_json, whitelist_json),
        run_judge(client, "SEO and search discoverability", trends_json, whitelist_json),
    )
    log_cost(SCRIPT, HAIKU, resp_a.usage.input_tokens, resp_a.usage.output_tokens)
    log_cost(SCRIPT, HAIKU, resp_b.usage.input_tokens, resp_b.usage.output_tokens)
    print(f"[{SCRIPT}] Judge A (virality): {judge_a[:100]}…")
    print(f"[{SCRIPT}] Judge B (SEO):      {judge_b[:100]}…")

    # Fable 5 final decision
    check_cost_limit(SCRIPT)
    template_text = read_prompt("niche_selection.txt")
    prompt = Template(template_text).safe_substitute(
        TRENDS_JSON=trends_json,
        WHITELIST_JSON=whitelist_json,
        BUSINESS_JSON=business_json,
        JUDGE_A=judge_a,
        JUDGE_B=judge_b,
    )

    response = await client.messages.create(
        model=FABLE,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    if response.stop_reason == "refusal":
        print(f"[{SCRIPT}] Fable 5 refused the request", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    log_cost(SCRIPT, FABLE, response.usage.input_tokens, response.usage.output_tokens)

    raw = next((b.text for b in response.content if b.type == "text"), "")
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)

    try:
        selection = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[{SCRIPT}] Failed to parse Fable 5 JSON: {exc}\nRaw:\n{raw}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    selection["judge_a_analysis"] = judge_a
    selection["judge_b_analysis"] = judge_b
    selection["selected_at"] = datetime.now().isoformat(timespec="seconds")
    return selection


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    trends_path = TRENDS_DIR / f"trends_{today()}.json"
    out_path = NICHES_DIR / f"niches_{today()}.json"

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no API calls (Haiku×2 + Fable 5)")
        print(f"[{SCRIPT}] Would read: {trends_path}")
        print(f"[{SCRIPT}] Would load: prompts/niche_selection.txt")
        print(f"[{SCRIPT}] Would run: Judge A (virality) + Judge B (SEO) concurrently via {HAIKU}")
        print(f"[{SCRIPT}] Would run: {FABLE} final strategic decision")
        write_data_json(out_path, DRY_RUN_MOCK)
        print(f"[{SCRIPT}] DRY-RUN output → {out_path}")
        print(f"[{SCRIPT}] Selected niche: {DRY_RUN_MOCK['niche']}")
        for a in DRY_RUN_MOCK["angles"]:
            print(f"  • {a['title']}")
        return

    require_env(SCRIPT, "ANTHROPIC_API_KEY")
    trends = read_data_json(trends_path)
    whitelist = json.loads((CONFIG_DIR / "niche_whitelist.json").read_text())
    business = json.loads((CONFIG_DIR / "business_context.json").read_text())

    selection = asyncio.run(run_debate(trends, whitelist, business))

    if not (isinstance(selection.get("angles"), list) and len(selection["angles"]) == 3):
        print(f"[{SCRIPT}] Response must contain exactly 3 angles", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    write_data_json(out_path, selection)
    print(f"[{SCRIPT}] niche={selection['niche']} → {out_path}")
    for a in selection["angles"]:
        print(f"  • {a['title']}")


if __name__ == "__main__":
    main()
