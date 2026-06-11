"""Step 3 — Claude Sonnet 4.6 writes 3 video scripts concurrently (max 3 at once).

Input:  outputs/selection_YYYY-MM-DD.json
Output: outputs/scripts_YYYY-MM-DD.json
"""
from __future__ import annotations

import asyncio
import json
import re
import sys

from common import (
    CONFIG_DIR,
    EXIT_FAILURE,
    check_cost_limit,
    is_dry_run,
    load_dotenv,
    log_cost,
    read_output,
    require_env,
    today,
    write_output,
)

SCRIPT = "script_generator"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500
MAX_CONCURRENT = 3

PROMPT_TEMPLATE = """You are a short-video scriptwriter for a faceless channel.

Business context:
{business_context}

Write one 30-60 second video script for this angle:
Title: {title}
Hook: {hook}
Target keyword: {keyword}
Niche: {niche}

Respond with ONLY a JSON object, no markdown fences, in exactly this shape:
{{"slug": "<kebab-case-slug>", "title": "{title}", "hook": "{hook}",
  "platform": "all", "description": "<upload description, 2-3 sentences + keyword>",
  "tags": ["<5-8 tags>"],
  "segments": [{{"voiceover": "<1-2 spoken sentences>",
                 "broll_query": "<2-4 word stock footage search>"}}, ...4 to 6 items...]}}

The first segment's voiceover must be the hook verbatim."""


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]


async def generate_script(client, semaphore: asyncio.Semaphore, angle: dict, niche: str,
                          business_context: str) -> dict:
    """One Sonnet 4.6 call per angle, gated by the semaphore (max 3 concurrent)."""
    prompt = PROMPT_TEMPLATE.format(
        business_context=business_context,
        title=angle["title"], hook=angle["hook"],
        keyword=angle["keyword"], niche=niche,
    )
    async with semaphore:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

    # Sonnet 4.6 pricing from cost-rules.md: $0.0030/1K in, $0.0150/1K out
    log_cost(SCRIPT, MODEL, response.usage.input_tokens, response.usage.output_tokens)

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[{SCRIPT}] JSON parse failed for '{angle['title']}': {exc}", file=sys.stderr)
        print(f"[{SCRIPT}] Raw response:\n{text}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)


async def generate_all(selection: dict) -> list[dict]:
    import anthropic

    client = anthropic.AsyncAnthropic()
    business_context = (CONFIG_DIR / "business_context.json").read_text()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [
        generate_script(client, semaphore, angle, selection["niche"], business_context)
        for angle in selection["angles"]
    ]
    return list(await asyncio.gather(*tasks))


def mock_scripts(selection: dict) -> list[dict]:
    scripts = []
    for angle in selection["angles"]:
        scripts.append({
            "slug": slugify(angle["title"]),
            "title": angle["title"],
            "hook": angle["hook"],
            "platform": "all",
            "description": f"{angle['title']} — {angle['keyword']}. (dry-run mock)",
            "tags": [angle["keyword"], selection["niche"], "shorts", "trending"],
            "segments": [
                {"voiceover": angle["hook"], "broll_query": "person using laptop"},
                {"voiceover": "Here's the part nobody tells you.", "broll_query": "close up screen"},
                {"voiceover": "It takes less than a minute to try.", "broll_query": "happy person phone"},
                {"voiceover": "Follow for more — tomorrow gets better.", "broll_query": "sunset city"},
            ],
        })
    return scripts


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    selection = read_output(f"selection_{today()}.json")

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — skipping {MODEL} calls, no cost incurred")
        print(f"[{SCRIPT}] Would run 3 async calls (max {MAX_CONCURRENT} concurrent), "
              f"max_tokens={MAX_TOKENS} each, model={MODEL}")
        scripts = mock_scripts(selection)
    else:
        require_env(SCRIPT, "ANTHROPIC_API_KEY")
        check_cost_limit(SCRIPT)
        scripts = asyncio.run(generate_all(selection))

    path = write_output(f"scripts_{today()}.json", scripts)
    print(f"[{SCRIPT}] {len(scripts)} scripts → {path}")
    for s in scripts:
        print(f"  • {s['slug']} ({len(s['segments'])} segments)")


if __name__ == "__main__":
    main()
