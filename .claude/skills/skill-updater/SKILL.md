---
name: skill-updater
description: Keep .claude/skills/ current automatically. Use at the end of any task that taught something new, after a fix that contradicts an existing skill, when the same problem was solved twice, or when the user says "remember this", "update your skills", "from now on".
---

# Skill Updater

Self-maintenance loop for the workspace's skills, using the knowledge-lifecycle
semantics from jcode's memory graph (Supersedes / Contradicts / DerivedFrom —
see `docs/jcode-harness-learnings.md` §2).

## When to run (auto-triggers)

- A task just finished and the method was non-obvious → candidate **DerivedFrom**
- Something in an existing skill turned out wrong or outdated → **Contradicts**
- A better version of a known procedure emerged → **Supersedes**
- The same ad-hoc fix happened for the 2nd time → promote it to a skill
- Never mid-task: learning is async — finish the work first, update skills at
  the natural pause (jcode rule: results from turn N surface at turn N+1).

## Procedure

1. **Collect candidates** from the just-finished work: what was learned that a
   future session would otherwise rediscover the hard way?
2. **Diff against existing skills** (`ls .claude/skills/`, read the relevant
   `SKILL.md`s):
   - *New procedure, no overlap* → create `.claude/skills/<name>/SKILL.md`
   - *Improves existing* (Supersedes) → edit the skill in place; add a line to
     its `## Changelog` (`YYYY-MM-DD: <what changed and why>`). Never fork a
     `-v2` copy.
   - *Conflicts with existing* (Contradicts) → resolve in the text: state the
     new rule AND the condition under which the old behavior still applies.
     A skill must never contain two contradictory instructions.
3. **Quality gate before writing** (jcode "regression budget" idea — learning
   must not degrade the agent):
   - Is it true beyond the one case it came from?
   - Does the `description` say WHEN to trigger, not just what it does?
   - Would applying it blindly break anything? If yes, encode the guard.
4. **Register/refresh the trigger row** in workspace `CLAUDE.md` if the
   trigger conditions changed.
5. **Commit** skill changes in their own small commit
   (`skills: <verb> <name> — <reason>`), and push at end of session.

## Rules

- Project-local skills are live on next read — no restart, no reload; just
  write the file (jcode issue #457 pattern).
- Keep lineage: when superseding, the changelog line replaces jcode's
  `Supersedes` edge. Never silently rewrite history.
- One skill = one procedure. If an update makes a skill do two jobs, split it.
- Deleting a skill requires the user's confirmation; deprecate first by noting
  it in the changelog and removing its CLAUDE.md trigger.
