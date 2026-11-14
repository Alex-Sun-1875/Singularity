# Male Astarion/Gale/Geralt Face Refresh

**Goal:** Replace the male facial identity with an original Astarion/Gale/Geralt blend while retaining the accepted side-profile direction, silver half-tied hair, full soft cheeks, wardrobe, body, weapon carry and game behavior.

User requested this after weapon-carry implementation was complete. Do not roll back carry work. Use built-in image_gen and preserve all original output bytes; no API/CLI fallback without explicit authorization.

- [x] Make a three-view face study from official Astarion/Gale references and current hairstyle/outfit reference. Check healthy cheek volume and rounded profile; retain the accepted profile while revising front/near-front with the later Geralt influence.
- [x] Produce a small in-game representative/portrait to check identity before multiplying the face edit across68 body atlases.
- [x] Clone and freeze current88-action manifest once. Replace each unique current image through explicit old→new path maps; preserve all action timing, existing run phase ground planes and body UPP.
- [x] Update independent HUD head and current-equipped inventory images consistently. Female/NPC/shield art and carry logic remain unchanged.
- [x] Measure only actual body/crop deviations; no rerun of older installers that drop exploration actions or recompute accepted run origins.
- [x] Rebuild and verify real input, carry/combat selection, portraits, source/runtime/compiled SHA and face consistency.

## Context

Current root manifest revision concept-image-2d-weapon-carry-v1,88 actions/68 PNG (35hero-v6,33carry-v1). HUD ChapterGame.ts uses flat2d/hero-head-soft-geralt-v3/texture and Rect(190,0,850,850). Carry feature is fully verified at17:00:40 build:95existingrules,28manualchecks,476nativebindings,desktop/mobile release. Latest carry audit:src/cocos/test-results/weapon-carry-v1/final-audit.json.

The two official faces are inspiration only. No vampire traits, beard, scars, new race or story changes. Keep existing female Shadowheart-inspired designs.

User feedback on first three-view study: prefer moreAstarion brows/eyes; mouth/chin unattractive; then clarified sideprofile is ACCEPTED and only FRONT is wrong. Lock the rightprofile fromface-study-v1.png. Improve front mouth/chin and eyebrows/eyes; nearfront3/4 may adapt for coherence without changing approved sideprojection. Do not propagate68atlases until current front identity is coherent; no bulk assets have been changed yet.

## Recovery 2026-11-06

Recovered the original thread's final user messages from its local rollout: front-v2 mouth/chin still need revision, then “再加上杰洛特的合体吧”, then “继续”. This supersedes the earlier two-reference-only direction. Make an original Astarion/Gale/Geralt blend: Astarion-led brow/eye elegance, Gale cheek fullness, restrained Geralt maturity and relaxed mouth/jaw character. The accepted right profile, silver half-tied hair, rounded healthy cheek volume, outfit and carry behavior remain locked. Do not treat front-v2 as approved.

The two prototype requests saved before interruption did not produce workspace files. Current runtime still matches the frozen carry baseline; no face migration is installed. Next: revised front/near-front master, review and save original bytes, then HUD/body pilot before the full 68-atlas migration. Built-in image_gen only; reuse current Cocos renderer and existing validation, no dependency or test additions.

Progress: face-front-v3.png and HUD/W01-dodge pilots are saved with original-byte provenance. Independent pilot-measurement-v3.json found all16 lower-body offsets zero (IoU0.966–0.983), every alpha>=16 body contained by the accepted crops, and the original HUD crop usable. Preserve existing body scale/origins; do not normalize the tiny boot AA changes. The previous 88-action/68-image frozen baseline remains immutable.

Ruling: proceed with v3 as the working three-reference identity under the user's repeated continuation; optional aesthetic feedback is pending, not recorded as approval. The accepted side profile remains locked. Bulk generation is source-only until geometry and native runtime review; no old art is deleted. `generation-jobs-v3.json` owns the exact68-image mapping; prototype W01 dodge accounts for one job, remaining32carry/35combat images are generated separately. Runtime changes are a HUD resource path and measured atlas metadata only, with no changes to FlatActors carry or core rules.

Verification so far: current existing95rules pass (src/cocos/test-results/face-v3-rules.log), TypeScript check passes (face-v3-types.log). These establish the rule baseline; they do not prove the new full image set has been imported or built.

## Completed delivery

Final build finished2026-11-06 19:05:20 Asia/Shanghai. All68atlases plus independentHUD are installed through `runtime-install-record.json`; manifestSHA256 `e1641ddd0083a8088284dceba297d6f2f14d987de31df8c746eae7922218fd9e`. Raw/source/runtime/actualUUID-mapped compiled PNGs all match. The original68inputPNGs, frozen baselineSHA `c1615afe98a69dbf450e2fce1ffdd8c5bce8c5389663d2d93719df252a2bc097`, source references and carry code remain intact.

Ruling: connected-alpha components are not semantic animation frames in the legacy hit/death atlas. Use independently audited explicit semantic rectangles where automatic detection fails; all old/new alpha>=16 pixels remain covered exactly once, and removed duplicate padding contains no alpha64 subject. No PNG edits or global cutoff changes. Stable64/80-window measurements supply boundary translations, including the hero idle's real[-33,+1]pixel move; transfer that move into its local origin to preserve world contact, never normalize stature.

Fresh review found and fixed partial-install and unknown-dirty overwrite risks: stage all images/manifest outside imported assets, verify bytes before atomic replacement, roll back failures, and require the frozen or an exactly known installed manifest SHA. Missing raw-output provenance blocks installation. No new test dependency or unit cases were introduced.

Same-build verification passed:95existingrules,TypeScript,88actions/1364nativepose samples,28realcarrychecks/476explorationbindings,desktop/mobile release with movement/attack/inventory/save reload,motion8programs,two-finger/cancel checks,and legal11-area/4-kill chapter completion (HP120→106,gold120,W02×1). Four advanced weapon identities are rendered fixtures, not acquisition claims.14actual screenshots independently visually reviewed; no browser/network errors.

Audit: `src/cocos/test-results/face-blend-v3/final-audit.json`. ZIP: `src/cocos/artifacts/first-chapter-playable-concept-2d-face-v3-2026-11-06.zip`, CRC verified, SHA256 `409e0425eab3d09da991b26e8219d35232ceb841b757664cc16222ea4e9b6c07`. The delivered v3 is a working artistic direction; no unanswered optional preference was called approval. Existing low-frame art, direct draw/restow pose swaps and physical-phone/TapTap validation limits remain documented.
