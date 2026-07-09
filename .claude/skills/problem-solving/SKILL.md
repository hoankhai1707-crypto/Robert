---
name: problem-solving
description: Default working method for non-trivial tasks — planning, iteration speed, delegation, checks, and commit discipline. Use at the start of any multi-step implementation, refactor, debugging session, or when unsure how to structure an approach.
---

# Problem Solving — harness working method

Operating rules distilled from the jcode harness (`docs/jcode-harness-learnings.md`).

## Iteration

1. **Fast loop by default, full validation when done.** Use the cheapest check
   that can catch the current class of error (syntax check, one targeted test,
   `--dry-run`) while iterating; run the full build/suite once at the end —
   not after every edit.
2. **Every pipeline/tool gets a `--dry-run`** that needs no keys/network and
   exits 0. Prove the wiring before paying for the real run.
3. **Commit as you go** — small, focused commits per completed step; push when
   the task or session ends.

## Blocking vs non-blocking (the observer/gate rule)

Before adding any automation, check, or side process, classify it:

- **Observer** (notifications, logging, learning, metrics): fire-and-forget,
  detached, may NEVER block or slow the main work. Failures are logged, not
  raised.
- **Gate** (policy checks, approvals, cost limits): synchronous and blocking,
  but must (a) **fail open** on its own errors/timeouts, and (b) on rejection
  return a machine-actionable reason so the caller can adapt — not just "no".
  (Pattern: exit 0 = allow, exit 2 = block with reason on stderr.)

Cost guards are gates (check budget BEFORE the call, hard-stop when exceeded).
Skill updates and Telegram notifications are observers.

## Delegation (subtree ownership)

- Delegate a subtask with an explicit report-back edge: what to return, to whom.
- **One owner per shared artifact** — plan, file, PR, config. Parallel writers
  to one artifact = incoherence; split the artifact or serialize the writes.
- You may manage (and stop) only work you spawned; escalate for anything else.
- Isolate into worktrees/copies only when parallel workers would mutate the
  same files — isolation has a real cost, don't default to it.
- If a delegated chain loses its parent, re-attach the orphan explicitly —
  never leave background work unowned.

## Knowledge lifecycle

- New learning at task end → run `skill-updater`.
- Facts that keep getting re-derived → write them down once
  (CLAUDE.md, docs/, or a skill) instead of rediscovering.
- When new info contradicts recorded knowledge, resolve it in the record —
  don't keep both versions in circulation.

## Failure handling

- Non-zero exit + reason on stderr; distinct exit codes per failure class
  (runtime vs budget vs missing-config) so callers can branch.
- Stop a chain at the first failed step; report WHICH step and why.
- Retries only where the failure is transient by nature (network, 429), with
  bounded backoff — never around logic errors.

## Debugging

- **Get to a test fast.** ~5 minutes of code tracing to form a theory, then
  experiment through tests. Extended static reading is the recorded #1
  time-waster (Motion's session logs).
- Check `git log --grep="<keyword>" -- <file>` early — the bug may already be
  fixed, or a prior commit explains the root cause.
- **The reproduction is the basis of the test.** If you can't obtain the
  reporter's repro, stop and ask — a guessed test proves nothing.
- **Pivot after 2-3 inconclusive rounds.** The bug is often one level removed
  from the suspected path: a utility, type guard, or environment check.
- **Think defensively, not forensically.** If a function can receive invalid
  input and forward it somewhere dangerous, guard it — you don't need to
  trace which upstream path produced the bad value.
- **Pick the test layer where the buggy code path actually runs** (e.g. JSDOM
  has no WAAPI/real layout — visual/browser bugs need a real browser test).
  A passing test on the wrong layer is worse than no test. For
  environment-specific bugs, after 2-3 failed repro attempts: research the
  environment difference, land the clearly-correct defensive fix with a
  validating test, and say so in the PR.
- Capture full output on the first failing run (`tail -60`) instead of
  re-running to re-collect it. Document known dead-ends (broken tooling,
  expected failures) in CLAUDE.md so future sessions don't re-investigate.

## Changelog

- 2026-07-09: Added Debugging section — merged from motiondivision/motion
  CLAUDE.md (studied at 6183324); supersedes nothing, extends the skill.
