---
name: motion-animations
description: Use the Motion library (formerly Framer Motion) idiomatically for UI animation in React or vanilla JS. Use when adding animations, transitions, gestures, scroll effects, or micro-interactions to any frontend work, or when the user mentions motion/framer-motion/animations.
---

# Motion Animations

Idiomatic use of Motion (motiondivision/motion, studied at v12.42.2).
Details and verified sources: `docs/motion-learnings.md`.

## Setup & imports

- Install: `npm install motion` (React & vanilla), `motion-v` for Vue.
- React: `import { motion, AnimatePresence } from "motion/react"`
- Vanilla: `import { animate, scroll } from "motion"` — or `"motion/mini"`
  for the smallest `animate()` when you only tween styles.
- Bundle-size discipline (a Motion core value): for app-wide usage prefer
  `m` + `LazyMotion`: `import { LazyMotion, domAnimation, m } from "motion/react"`,
  wrap once with `<LazyMotion features={domAnimation}>`, use `m.div`
  everywhere. Use `domMax` only if you need drag/layout animations.

## Core idioms (React)

1. **Declarative first**: `<motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} transition={{duration: 0.3}} />`.
   Reach for `useAnimate()` only for imperative sequences.
2. **Exit animations require `<AnimatePresence>`** around the conditional —
   and the child needs a stable `key`. No AnimatePresence → element unmounts
   instantly, `exit` ignored.
3. **Variants for orchestration**: name states (`hidden`/`visible`), set
   `variants` on parent + children; parent `staggerChildren`/`delayChildren`
   in its transition. Children inherit the active variant name — don't
   duplicate `animate` props down the tree.
4. **Gestures**: `whileHover`, `whileTap`, `whileFocus`, `whileDrag`,
   `whileInView` (viewport-triggered; `viewport={{ once: true }}` for
   enter-once reveals).
5. **Layout animations**: `layout` prop for FLIP position/size changes;
   `layoutId` for shared-element transitions between mounted/unmounted
   elements; wrap related groups in `<LayoutGroup>`.
6. **Scroll**: `useScroll()` → progress MotionValues; derive with
   `useTransform(scrollYProgress, [0,1], [...])`; smooth with `useSpring`.
   Bind values via `style={{ x, opacity }}` — never via state re-renders.
7. **Springs**: `transition={{ type: "spring", stiffness, damping }}` for
   interactive/gesture-driven motion; tweens+easing for timed UI transitions.
8. **Skip mount animation**: `initial={false}` on the component (or
   AnimatePresence) when the first render must not animate.

## Performance rules (verified from Motion's own audit)

- **Fast path (compositor/WAAPI, off main thread)**: plain `opacity` and
  literal `transform`/`filter`/`clipPath` string animations.
- **JS main-thread path**: the shorthands `x`/`y`/`scale`/`rotate`
  (yes — NOT compositor-accelerated), colors, `width`/`height`/`top`/`left`,
  springs on those, drag, layout animations. Fine in moderation — but for
  always-running or hot-path animations, prefer the fast path
  (e.g. `transform: "translateX(100px)"` over `x: 100`).
- Adding `onUpdate` or `transformTemplate` forces ANY animation onto the JS
  path. Never attach them casually.
- Don't use `useWillChange` by default — the auto value latches and never
  resets.
- Animate transforms/opacity instead of layout properties (`width`, `top`,
  margins) whenever the design allows; use the `layout` prop rather than
  animating size by hand.

## Accessibility

- Respect OS settings: `useReducedMotion()` to branch, or set
  `<MotionConfig reducedMotion="user">` app-wide (disables transform/layout
  animation, keeps opacity/color).

## Gotchas

- `exit` without AnimatePresence silently does nothing (most common mistake).
- Missing/unstable `key`s inside AnimatePresence break exit tracking.
- MotionValues don't trigger React re-renders — that's the point; read them
  with `useMotionValueEvent(value, "change", cb)`, not in render.
- Keyword targets like `height: "auto"` work, but `onUpdate` reports the
  keyword, not pixels — read `getComputedStyle()` if you need numbers.
- Testing animated UI in JSDOM only exercises the JS fallback (no WAAPI);
  assert visual behavior in a real browser (Playwright).
