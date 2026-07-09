"""Step 3 — generate 3 video scripts concurrently with Sonnet 4.6.

Input:  data/selected_niches/niches_YYYY-MM-DD.json
Output: data/scripts/script_<slug>_<NNN>.json (one file per script)
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
    SCRIPTS_DATA_DIR,
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

SCRIPT = "script_generator"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500

DRY_RUN_SCRIPTS = [
    {
        "slug": "ai-tools-replacing-jobs-2026",
        "title": "Top 5 AI Tools Replacing Jobs in 2026",
        "hook": "These AI tools will replace your job.",
        "platform": "youtube_shorts",
        "description": (
            "Discover the 5 AI tools disrupting every industry in 2026. "
            "Are you ready for the future of work? "
            "#AItools #futureofwork #automation #tech2026 #artificialintelligence"
        ),
        "tags": ["AI tools", "future of work", "automation", "tech 2026", "AI 2026"],
        "segments": [
            {"voiceover": "These AI tools will replace your job — if you're not using them first.",
             "broll_query": "robot working office"},
            {"voiceover": "Number one: AI writing assistants handle 40% of all content now.",
             "broll_query": "typing laptop close up"},
            {"voiceover": "Number two: AI customer bots resolve 60% of tickets — no humans needed.",
             "broll_query": "customer support headset"},
            {"voiceover": "The future belongs to people who work WITH AI. Follow for daily tips.",
             "broll_query": "person smiling laptop"},
        ],
        "generated_at": "2026-06-11T07:10:00",
    },
    {
        "slug": "chatgpt-vs-claude-which-wins",
        "title": "ChatGPT vs Claude: Which AI Actually Wins?",
        "hook": "Two AIs — only one comes out smarter.",
        "platform": "youtube_shorts",
        "description": (
            "We tested ChatGPT and Claude on 10 real tasks. The results were shocking. "
            "Here's which one you should actually use. "
            "#ChatGPT #Claude #AIcomparison #tech #artificialintelligence"
        ),
        "tags": ["ChatGPT", "Claude", "AI comparison", "tech", "AI tools"],
        "segments": [
            {"voiceover": "Two AIs — only one comes out smarter.",
             "broll_query": "two computers comparison"},
            {"voiceover": "We tested both on coding, writing, and complex research tasks.",
             "broll_query": "coding screen developer"},
            {"voiceover": "Claude wins on accuracy and reasoning. ChatGPT wins on speed.",
             "broll_query": "speed test benchmark"},
            {"voiceover": "Comment your pick below — and follow for the full breakdown!",
             "broll_query": "person pointing phone"},
        ],
        "generated_at": "2026-06-11T07:10:00",
    },
    {
        "slug": "free-ai-tools-missing",
        "title": "Free AI Tools You Are Missing Right Now",
        "hook": "You are sleeping on these free AI tools.",
        "platform": "youtube_shorts",
        "description": (
            "These completely free AI tools will transform your workflow today. "
            "No subscription needed — just results. "
            "#freeAI #productivity #AItools #freesoftware #tech2026"
        ),
        "tags": ["free AI tools", "productivity", "no cost", "AI", "tools 2026"],
        "segments": [
            {"voiceover": "You are sleeping on these free AI tools.",
             "broll_query": "free sign technology"},
            {"voiceover": "Perplexity AI is Google but smarter — and completely free.",
             "broll_query": "search engine interface"},
            {"voiceover": "Claude free tier beats most paid tools for complex tasks.",
             "broll_query": "AI chat interface screen"},
            {"voiceover": "Follow for more free tools that actually boost your productivity!",
             "broll_query": "productive person desk"},
        ],
        "generated_at": "2026-06-11T07:10:00",
    },
]


async def generate_one(
    client,
    semaphore: asyncio.Semaphore,
    angle: dict,
    niche: str,
    business: dict,
    platform_cfg: dict,
    prompt_template: str,
    idx: int,
) -> tuple[dict, object]:
    platform = platform_cfg.get("default_platform", "youtube_shorts")
    specs = platform_cfg["platforms"][platform]
    duration = specs["preferred_duration_seconds"][0]

    prompt = Template(prompt_template).safe_substitute(
        PLATFORM=platform,
        WIDTH=specs["width"],
        HEIGHT=specs["height"],
        ORIENTATION=specs["orientation"],
        DURATION_SECONDS=duration,
        NICHE=niche,
        TITLE=angle["title"],
        HOOK=angle["hook"],
        KEYWORD=angle["keyword"],
        BRAND_VOICE=business.get("brand_voice", "Energetic, curious, fact-forward."),
    )

    async with semaphore:
        check_cost_limit(SCRIPT)
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

    raw = next((b.text for b in response.content if b.type == "text"), "")
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[{SCRIPT}] JSON parse failed for angle {idx+1}: {exc}\nRaw:\n{raw}",
              file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    script["generated_at"] = datetime.now().isoformat(timespec="seconds")
    return script, response


async def generate_all(niches: dict, business: dict, platform_cfg: dict,
                        prompt_template: str) -> list[dict]:
    import anthropic
    client = anthropic.AsyncAnthropic()
    semaphore = asyncio.Semaphore(3)
    tasks = [
        generate_one(client, semaphore, angle, niches["niche"],
                     business, platform_cfg, prompt_template, i)
        for i, angle in enumerate(niches["angles"])
    ]
    pairs = await asyncio.gather(*tasks)
    scripts = []
    for script, response in pairs:
        log_cost(SCRIPT, MODEL, response.usage.input_tokens, response.usage.output_tokens)
        scripts.append(script)
    return scripts


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    niches_path = NICHES_DIR / f"niches_{today()}.json"

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — no {MODEL} calls")
        print(f"[{SCRIPT}] Would read: {niches_path}")
        print(f"[{SCRIPT}] Would load: prompts/script_generation.txt")
        print(f"[{SCRIPT}] Would generate 3 scripts concurrently (asyncio.Semaphore(3))")
        for i, s in enumerate(DRY_RUN_SCRIPTS, 1):
            out_path = SCRIPTS_DATA_DIR / f"script_{s['slug']}_{i:03d}.json"
            write_data_json(out_path, s)
            print(f"  [{i}] {s['slug']} → {out_path}")
        return

    require_env(SCRIPT, "ANTHROPIC_API_KEY")
    niches = read_data_json(niches_path)
    business = json.loads((CONFIG_DIR / "business_context.json").read_text())
    platform_cfg = json.loads((CONFIG_DIR / "platform_config.json").read_text())
    prompt_template = read_prompt("script_generation.txt")

    scripts = asyncio.run(generate_all(niches, business, platform_cfg, prompt_template))

    failures = 0
    for i, s in enumerate(scripts, 1):
        slug = s.get("slug", f"script-{i:03d}")
        out_path = SCRIPTS_DATA_DIR / f"script_{slug}_{i:03d}.json"
        try:
            write_data_json(out_path, s)
            print(f"[{SCRIPT}] [{i}] {slug} → {out_path}")
        except Exception as exc:
            print(f"[{SCRIPT}] Failed to write script {i}: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
