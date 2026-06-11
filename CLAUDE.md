# Robert's Claude Workspace

This is the repository for Claude work on digital products.

---

## Skill Auto-Use Rules

Claude must proactively invoke the relevant skill below based on the task context — **no `/skill` command from the user is required**. Read the trigger conditions and apply them automatically.

### `deep-research`
**Auto-invoke when:**
- User asks about a topic that requires multi-source verification (market trends, technology comparisons, best practices, factual questions about products/tools/frameworks)
- The question is complex enough that a single answer would benefit from citing multiple sources
- User asks "what is the best...", "how does X compare to Y", "research X for me", "find out about X"

### `code-review`
**Auto-invoke when:**
- User asks to review, check, audit, or look over any code
- A PR or diff exists and the user wants feedback
- User says "is this good?", "what do you think of this code?", "any issues here?"
- After implementing a non-trivial feature, proactively offer a review pass

### `simplify`
**Auto-invoke when:**
- User asks to refactor, clean up, or simplify code
- Code has obvious duplication or abstraction opportunities
- After a bug fix that touched multiple similar sections

### `verify`
**Auto-invoke when:**
- User asks "does this work?", "test this", "confirm this fix works", "check if it works"
- After implementing a bug fix or feature — verify it actually works before reporting done
- User wants to validate a change before pushing

### `run`
**Auto-invoke when:**
- User asks to start, launch, demo, or screenshot the app
- User wants to see the result of a UI/frontend change in a real browser
- User says "show me", "run it", "start it up"

### `review` (PR Review)
**Auto-invoke when:**
- User asks to review a pull request
- User shares a PR URL or PR number and asks for feedback
- User says "what's in this PR?", "review this PR", "look at this PR"

### `security-review`
**Auto-invoke when:**
- User asks about security, vulnerabilities, or safe deployment
- Changes involve authentication, authorization, input handling, API keys, or credentials
- User asks "is this secure?", "any security issues?", "audit this for security"

### `update-config`
**Auto-invoke when:**
- User wants to change Claude Code behavior ("from now on...", "always do X", "whenever X happens")
- User wants to add permissions, set environment variables, or configure hooks
- User says "set up", "configure", "add permission for", "add a hook for"

### `fewer-permission-prompts`
**Auto-invoke when:**
- User is frustrated by too many permission prompts
- User says "stop asking me", "just do it", "reduce prompts", "too many confirmations"

### `session-start-hook`
**Auto-invoke when:**
- User wants to set up a new repository for Claude Code on the web
- User wants tests/linters to run automatically at session start

### `loop`
**Auto-invoke when:**
- User wants something to run repeatedly or on a schedule
- User says "every X minutes", "keep checking", "poll for", "recurring", "watch for"

### `claude-api`
**Auto-invoke when:**
- User asks about Claude models, pricing, API parameters, streaming, tool use, MCP, caching, token counting
- User is building an AI application and the provider is Claude/Anthropic
- Code uses `@anthropic-ai`, `anthropic`, `claude-*` identifiers

### `keybindings-help`
**Auto-invoke when:**
- User wants to customize keyboard shortcuts in Claude Code
- User mentions rebinding keys, chord bindings, or `/` keybindings

### `init`
**Auto-invoke when:**
- Starting work in a new project that has no CLAUDE.md
- User asks to document the project or set up Claude context for a codebase

---

## General Behavior

- Always check which skill is relevant **before** generating a plain-text answer
- If multiple skills apply, invoke the most specific one first
- Never require the user to type `/skill-name` — detect context and act
- After any code change: auto-run `verify` or `run` if there is a UI or behavior to confirm
- After implementing features: auto-run `code-review` at low effort before declaring done
- For research questions: always prefer `deep-research` over answering from memory alone

---

## Project Context

- Owner: Robert
- Purpose: Digital products workspace
- Stack: TBD per sub-project
