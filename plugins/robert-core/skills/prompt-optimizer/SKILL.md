---
name: prompt-optimizer
description: Use automatically whenever Khai gives a non-trivial task or idea (video, script, design, website, app, research, study) — especially a long, mixed-language (Vietnamese/English) or loosely worded request — to turn it into a clear structured brief before doing the work. Also use when he asks to improve, rewrite or optimize a prompt.
---

# Prompt optimizer

Goal: understand Khai's idea exactly, then act. Do not make him re-explain.

## Step 1 — Rewrite the request as a brief (show it, max 8 lines)

```
GOAL:        the outcome in one sentence
FOR:         audience / platform (YouTube long-form, Shorts, TikTok, web, class…)
DELIVERABLE: format, length, resolution, file type
INPUTS:      files, links, references he gave (and what each is for)
CONSTRAINTS: budget ($120/mo ceiling for AIVPOS), engine rule, deadlines, language
STYLE:       tone, visual style, references
DONE WHEN:   2–3 checkable success criteria
UNKNOWN:     only the gaps that change the result → ask these (AskUserQuestion)
```

Keep his own words for names and terms. Translate Vietnamese intent faithfully;
never drop a requirement because it was phrased casually.

## Step 2 — Stress-test before executing

- Name any flawed premise first (he wants ruthless honesty), then the fix.
- If two readings are plausible and a wrong guess is expensive → ask.
- Otherwise state the reading you took and proceed.

## Step 3 — Pull patterns, don't invent them

Prompt-pattern sources (use, cite which one helped):

| Source | Use for | How to reach it |
|---|---|---|
| prompts.chat | ready prompts by role/task | `prompts.chat:prompt-lookup` (MCP) |
| OpenAI cookbook prompting guides (GPT-5 / GPT-4.1 guide, meta-prompting, Optimize_Prompts) | structure, agentic instructions, eval loops | PC: `Robert\use\04_Prompt-Library\repos\openai-cookbook` |
| system-prompts-and-models-of-ai-tools | how production agents (Cursor, Devin, Lovable, Manus…) structure system prompts and tool rules | PC: `…\repos\system-prompts-and-models-of-ai-tools` |
| ChatGPT-Shortcut prompt cards (en/vi/zh) | short task prompts by category | PC: `…\repos\ChatGPT-Shortcut\src\data\cards` |
| charlie-motion:motion-prompt-writer | 8-part motion prompts | skill |

LangChain is an app framework, not a prompt library — use its docs only when
building an LLM app, not for prompt wording.

When a local repo is unavailable (cloud session), rely on the brief format above
and prompts.chat; never claim a template exists without having read it.
