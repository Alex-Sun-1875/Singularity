# Native Character Kit Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox syntax for tracking.

**Goal:** Stage ten coherent CC0 native65 characters for Cocos review without overwriting production before approval.

**Architecture:** Reuse the supplied Quaternius Peasant/Ranger complete outfits, matching Base head and supplied hair. Consume the animation agent's canonical native65 Action blend; retain native rest rigs, source UVs and skin weights. Export FBX 7.4 with the existing Blender axis/animation settings and explicit source/PBR/part manifests.

**Tech Stack:** Blender 4.5.15, built-in glTF importer/FBX exporter/image scaling/compositor; existing character roundtrip verifier and byte-level asset checks; no new dependencies or cases.

**Spec:** Root task A and `src/.tmp/native-kit-review/evaluation-summary.json`; v5 identity references in `docs/story/revision-v5/characters.md` and `art-direction.md`.

## Global Constraints

- Own `tools/model-pipeline/cocos_native_characters.py`, character assets/source and necessary existing verifier contract changes only.
- Do not edit Actors, SurfaceMaterials, ChapterGame, weapon props or animation conversion script.
- Stage actors under `src/.tmp/native-production/actors`, source under `src/.tmp/native-production/source`.
- No production install until root's actual Cocos visual review accepts the staged group.
- Original archives/images/licenses and source hashes remain preserved; only export adapters resize/recolor maps.
- Shared runtime garment/hair maps at 512px; principal heads may be 1024px.
- No paid assets, handmade body/clothes, bespoke animation solver or new tests/dependencies.
- Latest root art steering takes precedence over historical presets; no white-haired/aged women.
- Canonical animation interface is `src/.tmp/native-production/animation/native65-actions.blend` and `manifest.json` from animation agent; 65 skin joints may have explicitly described nondeform attachment helpers.

## Review Focus

- Base head/neck inverse bind must match the corresponding outfit; original hidden body triangles must be removed as the publisher instructs.
- Female hair must be supplied long hair with blonde adaptation, rather than white stock buns.
- Shared maps must preserve sRGB versus non-color data, alpha and original PBR channels.
- Character-specific root floor alignment must preserve jog flight and dodge/death body contact, plus final death hold.
- FBX actual bones, geometry, clip names, UV maps, resolved images and foot contact must survive a real Blender roundtrip.
- Original short sword segment must retain natural source timing; temporary missing bow must be explicit, never replaced by a fake clip.

## Task 1: Source mapping and exporter interface

**Files:** Create `tools/model-pipeline/cocos_native_characters.py`; stage manifests/source under the two temporary directories above.

**Consumes:** Quaternius Standard original glTFs and source variants; original current identity height/width profile; native65 Action blend/manifest when ready.

**Produces:** `<id>/<id>.fbx`, `<id>/manifest.json`, source `<id>.blend`, common texture/provenance records, explicit part groups and animation readiness.

- [x] Read and inspect actual original source files, bindings, variants, existing exporter and v5 art specification.
- [x] Report exact role mapping and output interface to root; coordinate canonical Action slots/Head/helper contract with animation agent.
- [x] Implement import/reuse, native source head extraction, source hair rest attachment, palette adapter and native image export.
- [x] Stage Raphael and Mira first with honest `pendingClips` if bow is not yet ready; notify root as soon as FBX and preview are available.
- [x] Stage remaining eight with the same exporter and preserved heights/main colors; do not call Ranger a heavy armor set.

## Task 2: Consume canonical animation output

**Files:** Same exporter only; do not modify the animation agent's script/output.

**Consumes:** Eleven canonical Actions `idle/walk/run/attack_sword/attack_bow/attack_staff/spell/dodge/hit/death/interact`, original pose slot, source reference rest and bow attachment contract.

**Produces:** Per-character native rest FBX action baking, measured stride metadata, world-up floor alignment and explicit attachment helper names/matrices.

- [x] Append canonical Actions and select their OBJECT slots explicitly.
- [x] Measure native sole/body contact and apply root-position export alignment only; keep jog flight and original action timing.
- [x] Preserve source final death pose with a documented final hold if not already supplied.
- [x] Rebuild staged first group when bow/helper output is ready; no production copy as an incidental side effect.

## Task 3: Existing checks and Cocos handoff

**Files:** Modify only necessary native contracts in `cocos_verify_characters.py` and `cocos_test_assets.py`.

**Consumes:** Actual staged FBX bytes and manifests, canonical clip metadata, shared runtime textures.

**Produces:** Fresh roundtrip inspection reports and existing check output; reviewable staged group for root's Cocos scene.

- [x] Replace historical fixed53, MPFB texture-name and mesh-count assumptions with manifest native contracts while preserving substantive weight/geometry/foot/texture budget checks.
- [x] Run actual Blender roundtrip for staged first pair and then all ten; run the existing three byte-level asset cases after all required assets are staged.
- [x] Render real reimported staged FBX review views and notify root with exact paths, limitations and pending runtime acceptance.

## Execution rulings

- Root assigned a shared workspace with exclusive file ownership and staging paths; do not create another checkout or move shared files.
- User explicitly prefers existing checks and no new test scaffolding; this plan adapts existing cases only, with no test-first extra cases or commits.
- Original free pack contains two Ranger palettes and two Peasant palettes, not all outfits shown in the marketing preview.
- Current free supplied hair cannot exactly reproduce every v5 curl/bob/ponytail; use the requested original long hair and record visual gaps, without sculpting new hair strands.

## Final staging ledger

2026-11-05: all ten staged FBX files frozen;67 hierarchy bones/65 original skin joints,11 canonical actions,0pending. All ten real FBX roundtrips and the3 existing asset cases passed. Root is installing and performing actual Cocos/mobile acceptance; source metrics do not replace that review.

Ruling: preserve original kit proportions and use uniform v5 height scale. Historical MPFB profile.width is archived as legacyProceduralWidth and is not applied.

Ruling: shared native PBR PNG budget16,000,000B, RGBA base64MiB and full mip chain86MiB replace the historical256px MPFB6.5MB budget. Actual56 PNGs total15,401,066B; base63,438,848B; full mip84,585,056B. No device-frame-rate acceptance is claimed.

Ruling: actual engine captures showed correct dark teal/wine colors. The proposed studio-driven darkening was reverted before execution; existing PNG contents/hashes remained unchanged.

## Root runtime acceptance

Root completed production installation/import and the final web-mobile build. The observed integration record `src/cocos/test-results/native-library-integration.json` records95 core checks,3 production resource cases and TypeScript passing,11-area complete chapter traversal with all10 native bundles instantiated, desktop/mobile touch and save restoration, and8 actual motion recording cases with0errors. Actual full-hold GPU string alignment residual is0.00028757m.

Delivered ZIP `src/cocos/artifacts/first-chapter-playable-web-mobile-2026-11-05.zip`:125,260,232B; SHA256 `6c8ec8ee9eddca069ca8a2a61fd9c174dd4d0bfab5973906a4399742293c10f9`; Root verified CRC. These are local web-mobile checks, not physical-phone FPS or TapTap deployment acceptance. Final original motions,FBX and PNGs remained frozen after delivery.
