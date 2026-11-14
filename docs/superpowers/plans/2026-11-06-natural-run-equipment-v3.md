# Natural Run and Equipment v3 Implementation Plan

> **For agentic workers:** Use subagent-driven-development/executing-plans within the user-authorized continuation. Existing checks and runtime review take precedence over adding tests.

**Goal:** Natural running and map colors, plus a complete low-to-high equipment design visible in the playable Cocos2D project.

**Architecture:** Reuse existing native quad/unlit/SpriteFrame rendering and equipment/save rules. Separate authored artwork and metadata from runtime selection. Add a read-only equipment gallery, preserving existing gameplay and HUD.

**Tech Stack:** Cocos Creator3.8.8, TypeScript, native imagegen; existing Pillow for measurement only.

**Spec:** `docs/superpowers/specs/2026-11-06-natural-colors-equipment-design.md`

## Constraints and review focus

No new test dependencies/framework/cases; no original concept identity substitution; no source3D character rendering. Keep map geometry, saves, merchant/drop receipts, original19 item IDs and gameplay balance. Future design items never enter valid inventory. PNG bytes stay unchanged after generation; all slicing is metadata/native UV. Never release borrowed SurfaceMaterials textures. Preserve transparent map-before-actor ordering.

## Tasks

- [x] Natural map assets: `FlatWorldPresentation.ts`, `FlatWorldLayers.ts`, natural-v3 resources and provenance. Gray stone, cold weathered inn wood, natural foliage and local firelight verified in native scenes and all32 area lifecycle checks.
- [x] Natural run assets: two4×4 sheets per held-weapon category,8 phases/four directions. Native frameImages/directional origins validated; real keyboard W01/W07/W11 four-direction review confirms A/B continuity at3.6m/s with consistent body/materials.
- [x] Equipment design/art: `resources/equipment/v3/manifest.json`, seven source boards,15 weapons/15 armor looks/five jewelry grades; `docs/design/equipment-progression-v3.md`. Higher grades visibly add structure/gems/magic. Existing19 items retain their rules. Oath v3b fourth/fifth-grade native review passed.
- [x] Native equipment art/gallery: `EquipmentArt.ts`, `EquipmentGallery.ts`, `CharacterPanel.ts`, `Menus.ts`; new fourth character tab, family/grade selection and enlarged artwork, independent future/owned status. Verified35cards and all seven zoom flows in the09:24 candidate; original equip/craft controls retained.
- [x] Longsword runtime: ordinary/rare/legendary exact item poses and portraits verified in engine, alongside all seven weapon routes. New bow pose phases align with core emission; pending cancellable shots retain draw rather than showing release early.
- [x] Aggregate review/build: typecheck and95 existing rules passed; real input/save, touch/cancel, legal full chapter,32 area lifecycle and native visual audits passed. Final35 native PNGs match source bytes, runtime JS matches the fully checked code, new natural-v4 ZIP has CRC/SHA verification. Prior package retained. Evidence: `src/cocos/test-results/natural-v4-final-audit.json`.

## User steering: character quality/proportion gate

- [x] Replaced the unacceptedv3 character art. Adult anatomy/materials now derive from the user-approved master; the source diagnosis and rejected assets remain preserved.
- [x] Produce and inspect a high-detail master using the previously approved identity: standing front/side and natural run contact/passing, adult long-legged proportions and distinct leather/cloth/steel materials. `source-art/characters/2d-concepts/hero-v4-proportion/hero-v4-proportion-master-v1.png` is the candidate source, not a claim of finished in-game quality.
- [x] Diagnose source anatomy versus engine scaling at normal camera scale. Default915×412 idle/walk/run silhouettes are107.94/107.51/106.86CSS pixels high; runtime scales remain1. The old run's world-space head width grows approximately25% versus idle, with broader shoulders. Correct authored proportions rather than stretching the renderer. Evidence: `test-results/player-proportion-diagnostic-2026-11-06/`.
- [x] Propagated the corrected body/materials across seven weapon states and short reactions:35 selected PNGs/60 action keys, no old-body path. Restored the original~1.556 image-height scale after the rejected1.8 preview; standing beltline reference~38:62. Native normal/close views,112 weapon samples,28 inventory views and bow accessory continuity increments passed. Distant faces remain~15–20CSS pixels; low-frame artwork and physical-phone performance limits are documented.
