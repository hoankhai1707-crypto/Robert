# Robert skills — routing map

Marketplace: `robert-skills` (this repo). Every entry points to its **upstream repo**, so updates
flow from the original authors and no third-party skill files are copied here.
Skills are namespaced `plugin:skill`, so same-named skills from different repos never collide.

## Install once

**Claude (Cowork / desktop / web):** Customize → Plugins → Add → *Add marketplace* → *Add from a repository* →
`hoankhai1707-crypto/Robert` → install the plugins below.
Installed plugins **sync to Claude Code automatically** (Claude Code ≥ 2.1.273, signed in with the same account).

**Claude Code only (fallback):** `claude plugin marketplace add hoankhai1707-crypto/Robert` then
`claude plugin install <name>@robert-skills`.

## Auto-use (no slash commands)

`robert-core` ships three always-on skills: **task-router** (picks the right skills per task),
**prompt-optimizer** (turns any request into a structured brief first) and **daily-video**
(the episode pipeline). Rules: never blend competing skills without Khai's OK;
HyperFrames = long-form, Remotion = captions/charts/Shorts; third-party footage = reference-only by default.

## Roles

| Role | Meaning |
|---|---|
| R0-core | router, prompt optimizer, daily-video |
| R1-generate | AI images/video/voice/characters |
| R2-full-video | finished long-form explainers |
| R3-cut-remix | cut long → Shorts, captions, b-roll, edits |
| R4-shorts-films | short animated films, loops, sims, sound, QA |
| R5-web-app | website & app motion |
| R6-promo | launches, ads, e-commerce, freelance delivery |
| R8-base-engine | HyperFrames, Remotion, GSAP foundations |
| R9-prompts | prompt libraries |

## Plugins

| Role | Plugin | Upstream | What it does |
|---|---|---|---|
| R0-core | `robert-core` | ./plugins/robert-core | Khai's router: auto-picks the right skill per task (no slash commands), optimizes prompts into briefs, and runs the daily-video flow. |
| R1-generate | `higgsfield` | higgsfield-ai/skills | Higgsfield (official): images/video generation, Soul ID characters, brand kit, video explainer, YouTube thumbnails, product photoshoot (pairs with the Higgsfield connector). |
| R2-full-video | `animate` | cth9191/animate/plugins/animate | Procedural canvas animation in any style (sketchbook, crosshatch, riso, cut paper) with synthesized score. |
| R2-full-video | `barty-motion` | Barty-Bart/motion-graphics | Explainers (default/engaging/high-energy), motion b-roll, SAM2 object separation, sound-effects pass. |
| R2-full-video | `charlie-motion` | charlie947/motion-graphics-skills | 15 code-only motion skills: vox-explainer, animated-chart, milestone-reveal, reel-export, motion-prompt-writer, brand-intake... |
| R2-full-video | `data-animation-skills` | iart-ai/data-animation-skills | iart: chart animation, animated infographics, presentation video. |
| R2-full-video | `explainer-video-skills` | iart-ai/explainer-video-skills | iart: explainer, whiteboard, diagram, isometric, wrapped videos. |
| R2-full-video | `kinetic-typography-skills` | iart-ai/kinetic-typography-skills | iart: kinetic typography. |
| R2-full-video | `manim-skills` | iart-ai/manim-skills | iart: Manim math/diagram animation. |
| R2-full-video | `map-animation-skills` | iart-ai/map-animation-skills | iart: Vox-style map animation. |
| R2-full-video | `srt-whiteboard` | geeklee/srt-whiteboard-animation | SRT subtitles -> hand-drawn whiteboard animation MP4 (stream pen strokes). Note: skill UI text is Chinese. |
| R3-cut-remix | `b-roll-skills` | iart-ai/b-roll-skills | iart: b-roll for talking-head videos, drawn from what is said. |
| R3-cut-remix | `herk-edit` | nateherkai/herk-edit-kit | Talking-head editing pipeline: cut silences/mistakes, story edit, beats, short-form edit. (Its old hyperframes/gsap copies excluded; uses hyperframes + gsap-skills plugins.) |
| R3-cut-remix | `lower-thirds-skills` | iart-ai/lower-thirds-skills | iart: transparent lower thirds for OBS/Premiere/Resolve. |
| R3-cut-remix | `text-message-video-skills` | iart-ai/text-message-video-skills | iart: text-message story videos. |
| R3-cut-remix | `tiktok-video-skills` | iart-ai/tiktok-video-skills | iart: short-form video, caption animation, countdown, lower thirds. |
| R3-cut-remix | `youtube-video-skills` | iart-ai/youtube-video-skills | iart: audiogram, YouTube intro/outro. |
| R4-shorts-films | `generative-illustration-skills` | iart-ai/generative-illustration-skills | iart: generative illustration. |
| R4-shorts-films | `javascript-animation-skills` | iart-ai/javascript-animation-skills | iart: zero-asset canvas films + code-made soundtrack. |
| R4-shorts-films | `motion-design-skills` | iart-ai/motion-design-skills | iart: animation principles, art direction, beat-sync editing, logo animation, shot composition... |
| R4-shorts-films | `remotion-motion-graphics` | haidrrrry/claude-remotion-skill | Remotion motion graphics: intros, outros, logo animation, reels, promos. |
| R4-shorts-films | `whaley-motion` | whaleyxbt/claude-motion | Remotion taste rules, render review-loop, procedural sound design, web-sims (needs repo clone for sims/ scripts). |
| R5-web-app | `lottie-motion-design` | LottieFiles/motion-design-skill | LottieFiles motion-design principles for UI/Lottie animation. |
| R5-web-app | `motion-dev-animations` | 199-biotechnologies/motion-dev-animations-skill | Motion.dev (Framer Motion successor) 120fps animations for React/Next/Svelte/Astro. |
| R5-web-app | `web-animation-skills` | iart-ai/web-animation-skills | iart: 60fps, accessible, SVG, Lottie, GSAP web, page transitions, micro-interactions. |
| R5-web-app | `webgl-animation-skills` | iart-ai/webgl-animation-skills | iart: three.js, shaders/GLSL, particle systems. |
| R6-promo | `ad-video-skills` | iart-ai/ad-video-skills | iart: ad creative, launch, testimonial videos. |
| R6-promo | `ecommerce-video-skills` | iart-ai/ecommerce-video-skills | iart: product demo, promo, photo slideshow. |
| R6-promo | `freelance-motion-skills` | iart-ai/freelance-motion-skills | iart: creative brief, brand motion guidelines, client revisions, pricing, delivery specs. |
| R6-promo | `howseen-motion-design` | howseen-ai/claude-motion-design | Code-only motion design pipeline: launch films, showreels, promos, 'remake this video'. |
| R6-promo | `product-launch-motion` | AbubakrChan/product-launch-motion | URL -> 60fps product launch film (HTML springs, beat-synced music, SFX). |
| R8-base-engine | `gsap-skills` | greensock/gsap-skills | Official GSAP skills (core, timeline, ScrollTrigger, plugins, React). |
| R8-base-engine | `hyperframes` | heygen-com/hyperframes | HyperFrames (HeyGen): HTML->MP4 engine. MAIN engine for long-form explainers. Includes house-style doctrine skills. |
| R8-base-engine | `remotion-skills` | remotion-dev/skills | Official Remotion skills. Engine for captions, data charts and Shorts. |
| R9-prompts | `prompts.chat` | f/prompts.chat/plugins/claude/prompts.chat | prompts.chat: search/improve thousands of prompts and skills (remote MCP). |

## Reference-only (not installed as skills)

| Repo | Why |
|---|---|
| remotion-dev/remotion | Library monorepo; its skills serve Remotion maintainers. `npm i remotion` per project. |
| motiondivision/motion | Library; `npm i motion` per web project. |
| iart-ai/motion-skills | Index of the 18 iart packs (all 18 listed above). |
| openai/openai-cookbook, x1xhlol/system-prompts-and-models-of-ai-tools, rockbenben/ChatGPT-Shortcut | Prompt references, cloned locally to `Robert\use\04_Prompt-Library\repos` and used by `robert-core:prompt-optimizer`. |
| langchain-ai/langchain | LLM app framework, not a prompt library — use when building an LLM app. |

## Kits that need a working clone

`whaley-motion:web-sims` (needs `sims/`) and `herk-edit:edit-video` (needs `style-library/`, docs) call files in
their own repos → clones live in `Robert\use\09_Dev\kits\`. Open Claude Code inside that folder for full pipelines.
