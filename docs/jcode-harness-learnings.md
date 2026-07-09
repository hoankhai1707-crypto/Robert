# Harness Learnings — extracted from jcode (1jehuang/jcode)

Reference notes distilled from the jcode coding-agent harness (Rust). These patterns
back the three composed skills in `.claude/skills/`: `skill-extractor`,
`skill-updater`, and `problem-solving`.

Source: cloned at `f0e5127f` (2026-07). Key files: `crates/jcode-base/src/skill.rs`,
`crates/jcode-app-core/src/tool/skill.rs`, `docs/MEMORY_ARCHITECTURE.md`,
`docs/HOOKS.md`, `docs/SWARM_ARCHITECTURE.md`, `AGENTS.md`, `PLAN_MCP_SKILLS.md`.

---

## 1. Skills system

- **Format**: `SKILL.md` with YAML frontmatter (`name`, `description`,
  optional `allowed-tools`) + markdown body. Same format Claude Code uses —
  jcode imports `~/.claude/skills/` and `~/.codex/skills/` on first run
  (skills are portable across harnesses).
- **Two scopes with different freshness rules**:
  - *Global* skills (`~/.jcode/skills/`, plugins): cached in a shared registry,
    explicit `reload` / `reload_all` needed.
  - *Project-local* skills (`./.claude/skills/`): a **session-scoped overlay
    re-read from disk on every access** — edits are live immediately, no
    reload, and never leak into other sessions (jcode issue #457).
- **`skill_manage` tool** (`load`, `list`, `reload`, `reload_all`, `read`):
  the agent manages its own skill set at runtime. Creating/updating a skill is
  just writing a `SKILL.md` file — the registry picks it up.
- **Endorsement**: a skill can be "endorsed but not installed" — a curated
  recommendation with install instructions surfaced when the agent tries to
  load it. Separates *knowing about* a skill from *having* it.

**Transfer**: project skills in `.claude/skills/<name>/SKILL.md` are the
right unit of self-improvement — the agent can write and refine them itself,
and they version with the repo (PR-reviewable learning).

## 2. Memory architecture (the learning loop)

- Memory entries are typed: **fact**, **preference**, **procedure**.
  Procedures are skills-in-waiting.
- Memories form a **graph** with edges that encode knowledge lifecycle:
  - `Supersedes` — newer memory replaces older (never silently overwrite;
    keep the lineage)
  - `Contradicts` — conflicting knowledge is linked, not ignored
  - `DerivedFrom` — procedural knowledge derived from facts (experience →
    reusable procedure)
  - `HasTag` / `InCluster` / `RelatesTo` — retrieval organization
- **Fully async, never blocking**: the main agent never waits for memory;
  learning from turn N surfaces at turn N+1. A cheap sidecar model verifies
  candidate memories before they're committed.
- **Cascade retrieval**: an embedding hit triggers BFS traversal to pull in
  related memories — context arrives as a connected neighborhood, not isolated
  hits.
- **Regression budget** (`MEMORY_BUDGET.md`): memory-driven behavior changes
  have measurable guardrails and review expectations — learning must not
  degrade the agent.

**Transfer**: skill updates should follow the same semantics — new learning
*supersedes* (with a changelog line), *contradictions* get resolved explicitly
in the skill text, and repeated ad-hoc fixes get *derived* into a procedure.
Learning happens at natural pause points (end of task), never mid-task.

## 3. Hooks (lifecycle discipline)

- **Observers** (`turn_end`, `session_start/end`, `post_tool`): detached,
  fire-and-forget, can never block or slow the agent; failures only logged.
- **Gates** (`pre_tool`): synchronous, can block a tool call — exit 0 allows,
  exit 2 blocks *and feeds stderr back to the model so it can adapt*.
  Everything else (timeout, missing binary, crash) **fails open** with a
  logged warning.
- Recursion guard: hooks set an env var so nested agent calls don't re-fire
  hooks.

**Transfer**: when automating anything around the agent (checks, notifications,
skill-update triggers), decide first: observer or gate? Observers must never
block; gates must fail open and return machine-readable reasons the model can
act on.

## 4. Swarm (delegation discipline)

- Recursive spawn tree; each agent owns and may stop only its own subtree.
- Exactly **one coordinator slot per swarm**, used *only* for the single
  shared plan — everything else is coordinated subtree-locally via spawn
  prompts and messages. Multiple writers to one plan = incoherence.
- Orphaned children are **reparented** (grandparent → coordinator → root),
  never dropped; ownership edges are rewritten on rename/resume.
- **Worktrees only when they make sense** (parallel file mutation), and
  integration is done by worktree managers, not the coordinator.

**Transfer**: delegate subtasks with clear report-back edges; keep exactly one
owner per shared artifact (plan, file, PR); isolate (worktree) only when
agents would collide.

## 5. Working agreements (jcode AGENTS.md)

- Commit as you go — small, focused commits per feature/fix.
- Push when done — end of task or session.
- Fast iteration by default (`cargo check`, targeted tests, dev builds);
  full rebuild when done.
- Version bumps decided by reviewing all changes since the last release.

**Transfer**: mirrored in `problem-solving` skill.
