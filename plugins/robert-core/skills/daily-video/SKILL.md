---
name: daily-video
description: Use when Khai asks for "a video today", "today's video", "make a video about <big topic>", a new episode or a daily Short for his Techno Animation / Hypo channel. Proposes the day's main idea inside the big topic, then runs the production pipeline stage by stage with the right skills, stopping for his OK at the key gates.
---

# Daily video flow

Channel thesis: ancient human capabilities that modern life quietly eroded —
stress-tested as a net-loss analysis, not nostalgia. Stick-figure / whiteboard
doodle style, English narration (Kokoro), 8–12 min long-form + Shorts cut-downs.
Read the Project docs (video-0X files, packaging teardown, channel analytics) for
what has already shipped and what failed — never repeat a shipped topic.

## Stages (stop at ✋ for Khai's OK)

1. **Idea** — offer 3 day-ideas inside his big topic, each with: hook, the
   ancient-vs-modern trade-off, why it beats the last episode's packaging. Recommend one. ✋
2. **Packaging first** — title options + thumbnail concept (`higgsfield:higgsfield-youtube-thumbnail`) + first-90-seconds hook
   (packaging is the known bottleneck: Days 5–6 under 145 views). ✋
3. **Script** — `robert-core:prompt-optimizer` brief → script with beat markers;
   apply the `_Bible` tone/voice/narrator notes in `Robert\use\01_AI-Video-Production\_Bible`. ✋
4. **Image prompts** — per beat, from `IMAGE_PROMPT_BIBLE.md` (consistent character, no text in images unless needed).
5. **Voice** — Kokoro narration (`tts-engine` / `video-production`).
6. **Build** — HyperFrames long-form: `hyperframes:faceless-explainer` +
   `hyperframes:motion-doctrine` (or `animate:animate` / `srt-whiteboard` when Khai picks that look — don't mix engines in one video).
7. **QA** — `whaley-motion:review-loop` contact sheets, `hyperframes:seam-craft`; fix before showing.
8. **Shorts** — 2–3 cut-downs: `herk-edit:short-form-edit` → captions (`remotion-skills:remotion-captions`) → `charlie-motion:reel-export` (1080×1920). ✋
9. **Log** — save the episode doc to the Project (`video-0N-<slug>.md`).

Output files go to `Robert\use\01_AI-Video-Production\Episodes\Day-NN-<slug>\`.
