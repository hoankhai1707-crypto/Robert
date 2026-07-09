# Motion Library Learnings — extracted from motiondivision/motion

Source: cloned at `6183324` (v12.42.2, 2026-07). Key files: `CLAUDE.md`, `AGENTS.md`,
`packages/framer-motion/src/index.ts`, `plans/PERFORMANCE_AUDIT.md`.
Backs the composed skill `.claude/skills/motion-animations/` and the debugging
additions to `.claude/skills/problem-solving/`.

---

## 1. Package architecture

Dependency flow: `motion-utils` (pure fns, easing) → `motion-dom` (framework-agnostic
DOM animation engine: animate, scroll, gestures) → `framer-motion` (React integration)
→ `motion` (public package, cleaner entry points).

- `npm install motion`; import from **`motion/react`** for React, `motion` for
  vanilla JS, **`motion/mini`** for the smallest vanilla `animate()`.
- The React-specific layer is deliberately thin; logic keeps migrating down to
  `motion-dom`. Vue gets `motion-v`.
- Library value: **small file size is a stated top priority** — they enforce
  bundle-size budgets in CI (plans/035) and audit per-byte (plans/038).

**Transfer**: prefer the smallest entry point that does the job; treat bundle
size as a feature when picking imports.

## 2. Public API map (from framer-motion/src/index.ts)

- Components: `motion.<el>`, `m.<el>` (featureless, pair with `LazyMotion` +
  `domAnimation`/`domMax`), `AnimatePresence`, `LayoutGroup`, `MotionConfig`,
  `Reorder`, `LazyMotion`.
- Hooks (values): `useMotionValue`, `useTransform`, `useSpring`, `useScroll`,
  `useVelocity`, `useTime`, `useMotionTemplate`, `useMotionValueEvent`,
  `useWillChange`, `useFollowValue`.
- Hooks (animation): `useAnimate` (scoped `animate()` + selectors),
  `useAnimateMini`, `useReducedMotion`, `useReducedMotionConfig`.
- Imperative: `animate()`, `scroll()`, gestures from `motion-dom`.

## 3. Performance model (verified in their PERFORMANCE_AUDIT.md)

The single most useful mental model: **two animation paths**.

- **WAAPI/compositor path** (off main thread, dormant JS): plain `opacity`
  and *literal string* `transform` / `filter` / `clipPath` animations on a
  default `<motion.el>`.
- **JS/main-thread path** (per-frame rebuild + rewrite of the element's
  styles): transform *shorthands* `x`/`y`/`scale`/`rotate` (verified NOT
  compositor-accelerated as of 12.42), colors/`background-color`,
  `width`/`height`/`top`/`left`, springs on non-accelerated props, drag,
  layout/projection animations, SVG — and *anything* once you add `onUpdate`
  or `transformTemplate`.
- Style *writes* are cheap (batched to ≤1 recalc/frame; the browser defers);
  the JS-path cost is the per-frame JS work. Layout *reads* mid-frame are the
  real recalc trigger.
- `will-change` auto-injection latches `"transform"` and never resets (known
  issue) — don't reach for `useWillChange` by default.

**Transfer**: prefer opacity/transform-string animations for hot paths; treat
`x`/`scale` shorthands, color, and size animations as main-thread work to be
used deliberately; never attach `onUpdate` to a hot animation casually.

## 4. Testing knowledge (their CLAUDE.md, hard-won)

- **JSDOM has no WAAPI** — unit tests only exercise the JS fallback path. Any
  bug involving opacity/transform/scroll/layout/visual behavior needs a real
  browser test (Cypress/Playwright), often *skipping* the unit test entirely.
- If a reported bug's unit test passes, that proves nothing — go to E2E.
- **Mid-animation measurement pattern**: long duration + linear easing, wait
  to ~50%, assert computed style at a point in time (`.then()` not retrying
  `.should()`, which waits until the animation finishes and masks wrong
  targets).
- `getAnimations()` only reports WAAPI animations for compositor props.
- For keyword targets (`"auto"`), `onUpdate` reports the keyword — use
  `getComputedStyle()` for resolved pixels.

**Transfer**: pick the test layer by which code path actually runs in it;
a passing test on the wrong layer is worse than no test.

## 5. Debugging strategy (their CLAUDE.md — merged into problem-solving skill)

- **Get to a test fast**: ~5 minutes of code tracing to form a theory, then
  experiment via tests. Static reading past that point is their #1 recorded
  time-waster.
- Check `git log --grep` early — the bug may already be fixed or explained.
- **Pivot after 2-3 inconclusive rounds** — the bug is often one level removed
  (utility, type guard, environment check), not in the suspected pipeline.
- **Think defensively, not forensically**: if a function can receive invalid
  input and pass it to a browser API, guard it — you don't need to trace which
  upstream path produced it.
- Environment-specific bugs (JSDOM/Electron vs Chrome): after 2-3 failed
  repro attempts, web-search the environment difference; a clearly-correct
  defensive fix with a validating (non-failing) test is acceptable — note it
  in the PR.
- The reporter's reproduction is the basis of the test; without it, stop and
  ask — don't guess.
- Capture full output on the first test run (`tail -60`); don't re-run to
  re-capture what you already had.

## 6. Repo hygiene patterns

- `skills-lock.json`: skills imported from other repos are **pinned by source
  + content hash** (`shadcn/improve` @ sha256) — reproducible skill supply
  chain.
- Known-broken tooling is documented as known (`gh pr edit` fails on this
  repo: "expected — do not investigate, retry, or work around"). Writing down
  what NOT to debug saves sessions.
- Plans live as numbered docs in `plans/` (`NNN-slug.md`) — small, reviewable
  design docs per change, plus `issues/` for investigations.

**Transfer**: pin external skills by hash when importing; document known
dead-ends in CLAUDE.md so future sessions don't re-investigate them.
