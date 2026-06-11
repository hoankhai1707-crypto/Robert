"""Step 2 — Claude Fable 5 picks the best niche + 3 video angles from today's trends.

Input:  outputs/trends_YYYY-MM-DD.json
Output: outputs/selection_YYYY-MM-DD.json
"""
from __future__ import annotations

import json
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

SCRIPT = "niche_selector"
MODEL = "claude-fable-5"
MAX_TOKENS = 2000

PROMPT_TEMPLATE = """You are the content strategist for an automated short-video channel.

Business context:
{business_context}

Today's rising Google Trends results (scored 0-100 by trend velocity):
{trends}

Pick the single best niche to publish in today and exactly 3 video angles within it.
Optimize for: trend velocity, fit with the business context, and watchability as a
30-60 second faceless video with stock footage.

Respond with ONLY a JSON object, no markdown fences, in exactly this shape:
{{"niche": "<whitelist category>", "rationale": "<2 sentences>",
  "angles": [{{"title": "<video title>", "hook": "<first-2-seconds hook line>",
               "keyword": "<the trend keyword this targets>"}}, ...3 items...]}}"""


def call_fable5(trends: list[dict]) -> dict:
    """One strategic call to claude-fable-5. Logs cost, parses JSON, exit(1) on bad JSON."""
    import anthropic

    business_context = (CONFIG_DIR / "business_context.json").read_text()
    prompt = PROMPT_TEMPLATE.format(
        business_context=business_context,
        trends=json.dumps(trends[:20], indent=2),
    )

    client = anthropic.Anthropic()
    # Fable 5: thinking is always on — do NOT pass a `thinking` parameter at all.
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    # Cost: fable-5 is $0.0100/1K input, $0.0500/1K output (cost-rules.md)
    log_cost(SCRIPT, MODEL, response.usage.input_tokens, response.usage.output_tokens)

    # Fable 5 can return stop_reason "refusal" with empty content — check first.
    if response.stop_reason == "refusal":
        print(f"[{SCRIPT}] Fable 5 refused the request "
              f"(category={getattr(response.stop_details, 'category', None)})", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"[{SCRIPT}] Failed to parse Fable 5 response as JSON: {exc}", file=sys.stderr)
        print(f"[{SCRIPT}] Raw response:\n{text}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)


def mock_selection(trends: list[dict]) -> dict:
    top = trends[0]
    return {
        "niche": top["niche"],
        "rationale": f"Mock selection: '{top['keyword']}' has today's highest velocity "
                     f"({top['score']}) and fits the brand. (dry-run)",
        "angles": [
            {"title": "This Free AI Tool Edits Photos Better Than Photoshop",
             "hook": "Stop paying for photo editing.", "keyword": top["keyword"]},
            {"title": "3 AI Photo Tricks Nobody Shows You",
             "hook": "Your camera roll is about to change.", "keyword": top["keyword"]},
            {"title": "I Tested 5 Free AI Editors — One Shocked Me",
             "hook": "Number 4 should be illegal.", "keyword": top["keyword"]},
        ],
    }


def main() -> None:
    load_dotenv()
    dry = is_dry_run()
    trends = read_output(f"trends_{today()}.json")

    if dry:
        print(f"[{SCRIPT}] DRY-RUN — skipping {MODEL} call, no cost incurred")
        print(f"[{SCRIPT}] Would send top {min(len(trends), 20)} trends, "
              f"max_tokens={MAX_TOKENS}, model={MODEL}")
        selection = mock_selection(trends)
    else:
        require_env(SCRIPT, "ANTHROPIC_API_KEY")
        check_cost_limit(SCRIPT)
        selection = call_fable5(trends)

    if not (isinstance(selection.get("angles"), list) and len(selection["angles"]) == 3):
        print(f"[{SCRIPT}] Selection must contain exactly 3 angles", file=sys.stderr)
        sys.exit(EXIT_FAILURE)

    path = write_output(f"selection_{today()}.json", selection)
    print(f"[{SCRIPT}] niche={selection['niche']} → {path}")
    for a in selection["angles"]:
        print(f"  • {a['title']}")


if __name__ == "__main__":
    main()
