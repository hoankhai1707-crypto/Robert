---
name: skill-extractor
description: Extract reusable skills from any codebase, repo, or finished task. Use when the user says "learn from this repo", "extract skills/patterns from X", "study how X does Y", or after solving a hard problem whose method is worth keeping.
---

# Skill Extractor

Turn someone else's working system — or your own finished task — into composed,
reusable skills in `.claude/skills/`. Method learned from the jcode harness
(see `docs/jcode-harness-learnings.md`).

## Procedure

1. **Locate the knowledge, not the code.** In order of yield:
   - Root docs: `README.md`, `AGENTS.md`, `CLAUDE.md`, `PLAN_*.md`, `CONTRIBUTING.md`
   - `docs/` — architecture and design docs (`*_ARCHITECTURE.md`, `*_PLAN.md`, `HOOKS.md`…)
   - The implementation of the subsystem you care about (find with `Glob`/`Grep`,
     read the module header comments and public API first, bodies second)
2. **Extract patterns, not snippets.** For each subsystem answer:
   - What problem does it solve? What are the moving parts?
   - What are the *rules* it enforces (invariants, fail-open vs fail-closed,
     blocking vs async)?
   - What would transfer to a different stack, and what is incidental?
3. **Write a learnings doc** at `docs/<source>-learnings.md`: one section per
   subsystem, each ending with a **Transfer:** line stating how it applies here.
4. **Compose skills** from the transferable patterns:
   - One skill per distinct *procedure* (not per source repo)
   - File: `.claude/skills/<name>/SKILL.md` with frontmatter `name`,
     `description` (description must say WHEN to use it — that's what triggers
     auto-invocation)
   - Body: a numbered procedure an agent can follow without the source repo,
     plus hard rules and failure modes
5. **Register triggers** in the workspace `CLAUDE.md` auto-use table so the
   skill fires without a `/command`.
6. **Commit** the learnings doc + skills together, referencing the source
   commit hash of the studied repo.

## Rules

- Skills must be self-contained: reading the source repo again must not be
  required to apply them.
- Prefer 1 page per skill. Details go to the learnings doc, not the skill.
- Never copy licensed code into a skill — extract the *method*.
- If a candidate skill overlaps an existing one, update the existing one
  (see `skill-updater`) instead of creating a near-duplicate.
