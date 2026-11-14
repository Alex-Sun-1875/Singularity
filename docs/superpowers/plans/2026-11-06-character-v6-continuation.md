# Character v6 Continuation Implementation Plan

> **For agentic workers:** Use executing-plans with parallel asset adapters. Track the existing authorized continuation below.

**Goal:** Finish the interrupted v5 appearance adaptation for ten first-chapter actors and deliver an updated playable Cocos Web build.

**Architecture:** Keep the current Native65 rig, 11 actions, gameplay, warm gold UI and geography. Reuse the staged MakeHuman/Quaternius head, hair and garments and KayKit props, using Blender bake/export and Cocos native PBR materials. Separate editable source, staged FBX and production assets; back up before installation.

**Tech Stack:** Existing Cocos Creator 3.8.8, Blender 4.5.15, native Cycles/FBX, Playwright and existing project checks. No new dependencies.

**Spec:** Previous chat 01a1a6e1-32f5-7d23-bd0c-d2991c446678; docs/story/revision-v5/characters.md; docs/story/revision-v5/art-direction.md.

## Global Constraints

- Continue the user's already authorized appearance work in the current dirty codex/cocos-chapter-one workspace. Do not move or commit unrelated work.
- Preserve actions, bind pose, equipment behavior, source licenses, warm honey gold mobile UI and save compatibility.
- Reuse current libraries and engine tools. New geometry is limited to missing concept-specific adaptations; do not rebuild the body/animation system.
- Reuse existing checks and actual runtime inspection; no additional test cases, scaffolding or dependencies.
- Physical phone performance and TapTap deployment require their own evidence and are not claimed from browser emulation.

## Review Focus

- Head/neck joins and hair alpha must remain clean in rendered views and animated poses.
- Hidden hood/hair parts and equipped weapons must match inventory selections.
- Actual FBX contains 67 hierarchy joints, 65 skin joints, all 11 clips and valid texture paths.
- Bow Draw and arrow alignment, captain hammer and shield/map-tube attachment remain intact.
- Actual release build can complete the chapter, accept phone touch and restore saves without runtime errors.

## Tasks

- [ ] Repair and inspect staged face/hair and wardrobe adapters; export all ten actors with rig/action hashes preserved.
- [ ] Finish staged props and runtime bindings; retain authored bow morph and grips.
- [ ] Roundtrip real exported FBX, inspect first pair and full cast, back up and import production assets.
- [ ] Run existing TypeScript, rule and resource checks, build Web mobile and inspect actual appearance/motions.
- [ ] Reuse full chapter, touch, inventory/save and motion verification; package dated build and update progress/source notices.

## Execution ledger

- Initial state: previous chat failed during compaction. v6 Raphael staged, other nine not exported; weapon work partly imported by earlier parallel worker. Current production build is the warm gold version with old actor appearance.
- Ruling: resume in place because the requested work and editable assets are already uncommitted here; a fresh worktree would omit them.
- Ruling: existing Blender bake and current licensed artwork replace the prior blocked image generation attempt. Source geometry/UV adapters are the remaining work.
- User steering: first build a playable 2D comparison scene, using hand-painted overhead scenery and pre-rendered detailed characters. Stop expanding the 3D export batch and preserve its partial work. The isolated implementation is `src/prototype-2d/`; this is a route comparison milestone and does not establish full first-chapter completion.
- 3D handoff: face/hair adapter v3 and wardrobe fixes saved; full-cast appearance not accepted. Props have a fresh isolated `props-review` build and runtime report. See wardrobe `resume-status.json` and `test-results/v6-props-review-runtime.json` before resuming.
