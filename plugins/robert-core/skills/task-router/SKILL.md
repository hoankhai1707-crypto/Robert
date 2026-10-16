---
name: task-router
description: Use at the START of any task Khai gives — a video, Short, animation, motion graphic, whiteboard/doodle explainer, edit or cut, website or app animation, prompt, or study/file work — to pick and load the right installed skills automatically, without him typing a slash command. Also use when he asks "which skill", "what should we use", or names a role (generate, create, cut, remix, Shorts, web motion, characters, tools).
---

# Task router (Khai / Robert)

Khai never wants to type `/skill-name`. On every task: classify it, then load the
matching skills yourself, in pipeline order. Say in one line which skills you are
using and why; then work.

## Hard rules

1. **Never combine skills without Khai's OK.** Running skills one after another
   for different pipeline stages is fine. *Blending* two competing skills for the
   same stage (e.g. two "motion-design" skills, or HyperFrames + Remotion on one
   video) needs his explicit permission. Ask in one line.
2. **Engine split (decided 2026-10-16):** HyperFrames = long-form explainers.
   Remotion = captions, data charts, Shorts. Do not port a video between engines
   unless asked (`hyperframes:remotion-to-hyperframes` only on explicit request).
3. **Footage rights gate.** Third-party footage (YouTube/TikTok/IG/Douyin/FB/Whop):
   default to *reference-only* (study motion/style with `watch`, rebuild in our own
   art). If he insists on reusing clips, require transformation before export:
   added commentary/narration over most of the runtime, clips short, visual
   reframing, credit in description. State the risk once; don't lecture.
4. If a needed skill is missing, say which plugin from the `robert-skills`
   marketplace to enable — don't improvise a replacement silently.

## Routing table

| Task signal | Role | Load (in order) |
|---|---|---|
| "video today", "video about <big topic>", daily episode | R2 | `robert-core:daily-video` (it chains the rest) |
| Long-form whiteboard / stick-figure explainer from a script | R2 | `hyperframes:hyperframes` → `hyperframes:faceless-explainer` → `hyperframes:motion-doctrine` → `hyperframes:hyperframes-audio` → `hyperframes:embedded-captions` |
| SRT subtitles → hand-drawn whiteboard animation | R2 | `srt-whiteboard:srt-whiteboard-animation` (its UI text is Chinese) or `explainer-video-skills:whiteboard-animation` — pick one, ask if unsure |
| Hand-made procedural style (sketchbook, crosshatch, cut paper) | R2 | `animate:animate` |
| Vox-style documentary explainer | R2 | `charlie-motion:vox-explainer` |
| Diagram / isometric / map / math visuals | R2 | `explainer-video-skills:diagram-animation`, `…:isometric-animation`, `map-animation-skills:map-animation`, `manim-skills:manim` |
| Data / chart animation | R2 | `remotion-skills` (render) + `data-animation-skills:chart-animation` or `charlie-motion:animated-chart` |
| Cut long video → Shorts, remove silences/mistakes | R3 | `herk-edit:cut-silences` → `herk-edit:cut-mistakes` → `herk-edit:short-form-edit` → `charlie-motion:reel-export` |
| Talking-head graphics / b-roll | R3 | `hyperframes:talking-head-recut` or `b-roll-skills:talking-head-b-roll`; `barty-motion:motion-broll` |
| Captions on Shorts | R3 | `remotion-skills:remotion-captions` or `tiktok-video-skills:caption-animation` |
| Study a reference video (any platform) | R3 | `watch` (frames + transcript) → describe moves → rebuild |
| Short animated film / loop / sim | R4 | `whaley-motion:web-sims`, `javascript-animation-skills:javascript-animation`, `charlie-motion:loop-cover` |
| Title sequence / showreel | R4 | `charlie-motion:title-sequence-3d`, `herk-edit:motion-showreel` |
| Polish / QA a render | R4 | `whaley-motion:review-loop`, `hyperframes:seam-craft` |
| Sound effects / music pass | R1/R4 | `barty-motion:sound-effects`, `whaley-motion:sound-design`, `hyperframes:hyperframes-audio` |
| Voice-over / narration | R1 | existing `tts-engine` / `video-production` skills (Kokoro) |
| Images / characters (AI generation) | R1/R7 | Higgsfield connector; character consistency: `higgsfield:higgsfield-soul-id`, thumbnails: `higgsfield:higgsfield-youtube-thumbnail`; cut-out subject: `barty-motion:object-separation` |
| Website / app animation | R5 | `gsap-skills:*` (default), `motion-dev-animations` for React/Motion.dev, `lottie-motion-design`, `web-animation-skills:*`, `webgl-animation-skills:*` for 3D |
| Product launch / promo / ad | R6 | `product-launch-motion` (URL → film) or `charlie-motion:launch-video`; ads: `ad-video-skills:*` |
| Prompt writing / improving | R9 | `robert-core:prompt-optimizer`, `prompts.chat:prompt-lookup`, `charlie-motion:motion-prompt-writer` |
| Engine/tool questions | R8 | `hyperframes:hyperframes-cli`, `remotion-skills:remotion-best-practices` |

## Where things live (Khai's PC)

`C:\Users\ROBERT\Robert\use\` —
`01_AI-Video-Production` (episodes, Shorts, `_Bible` with prompt bible, tone, voice and narrator notes),
`02_Skills-Plugins` (this marketplace clone + ROUTING.md),
`03_Automations`, `04_Prompt-Library` (local prompt repos), `05_Study-UEH`,
`06_Research-Tools`, `07_Business`, `08_Media-References`, `09_Dev` (kits: herk-edit-kit, claude-motion).
Kits whose skills call repo scripts (`whaley-motion:web-sims`, `herk-edit:edit-video`)
must run inside their clone under `09_Dev`.
