# First Chapter 2D Completion Plan

> Continue the user-authorized work; use existing native Cocos capabilities, existing checks and parallel independent asset work. No new testing framework, dependencies or unrelated refactoring.

**Goal:** Deliver the playable first chapter with concept-derived 2D characters and 2D map presentation, retaining the original warm-gold Cocos HUD, gameplay, equipment and saves.

**Authority:** Latest user steering overrides earlier 3D production work: use the earlier approved design images directly for 2D character assets; only map and character presentation change. References: `docs/story/revision-v5/art-direction.md`, `characters.md`, `docs/assets/concept-2d-preview.md`.

## Required outcome

- All 32 existing areas use readable 2D map artwork at normal phone camera scale, with original geography, roads, bridges, ramps, collisions and interaction coordinates.
- Raphael and the five placed NPC identities remain distinct and faithful to their own approved designs. Four enemy types have their own readable equipment and combat appearances; no character identity is silently substituted by another.
- Player idle/walk/run/sword/bow/staff/spell/dodge/hit/death/interact states are represented by actual 2D poses. Sword/bow/staff equipped, walking and attacking displays agree with the rules. Enemy windup/active/recovery/death is readable.
- Original HUD, map/inventory/skills/dice panels, controls, saves, quest branches, equipment, merchants and chapter completion remain functional. Full chapter command playthrough and phone-size actual touch inputs must pass on the final 2D build.
- Deliver an updated local build and dated playable package. State physical-phone and TapTap acceptance boundaries honestly.

## Work ownership

- Root: player assets and runtime actor state contracts, ChapterGame integration, aggregate verification, packaging and progress ledger.
- World worker: FlatWorldPresentation/necessary SceneBuilder presentation records, all-area map layers and assets. Large areas use tiled ground and layered artwork so camera-scale detail remains clear.
- NPC worker: Lorn/Nightqi/Kael/Evelyn source-concept directions and provenance, no unused NPC animation expansion.
- Enemy worker: raider/archer/shield/captain dedicated movement/attack/reaction images and source records.

## Verification

Reuse existing `npm test`, `npm run check`, release/touch/character-panel/motion/full-chapter checks. Adapt existing rig-only asset assertions to explicit 2D coverage where necessary, preserving actual game state and completion assertions. Inspect actual engine renders for UVs, alpha, scale, foot anchors, direction, equipment, hit timing and map/physical agreement. No success claims from source manifests alone.

## Ledger

- Previous turn: progress. Working source-derived 2D inn scene, original HUD, walking/sword and inventory portrait; 95 existing rules, original control geometry, release inputs/save/character panels and actual dialogue route verified. The standalone Phaser/3D-rendered character experiment was superseded.
- Remaining at start: only inn map converted, NPC identity reuse, missing player/enemy poses, complete 2D chapter verification and package.
- [x] Player pose/equipment coverage
- [x] Distinct placed NPCs
- [x] Four enemy archetypes
- [x] All 32 area map presentation
- [x] Full chapter/phone-size input/save/UI/motion verification
- [x] Dated playable package and final audit


## Result (2026-11-06)

Completed the playable 2D chapter and dated package. Final audit: `src/cocos/test-results/flat2d-final-audit.json`. The 03:00 build completed the unchanged legal-command chapter route (11 areas, 4 defeats, HP106), all32 isolated area loads retained valid ground textures and disposed old worlds, and desktop/mobile-size actual inputs and save reload passed. Existing95 rules and TypeScript pass; no new testing framework/dependencies/cases.

Actual rendering exposed and fixed missing sprite effect (native unlit reuse), shared surface texture lifetime, transparent road ordering, player/enemy foot anchors, bow phase selection and table/cart projection. Failed diagnostic/fixture records remain separate from completion proof. The 10 concept-based identities,11 player states and4 enemy archetypes have their own actual images. UI, rules, map, skill checks and saves remain the original implementation.

This delivers a local playable version. Low-frame pose transitions, repeated world art families, small prop/hand-effect alignment and physical-phone/TapTap performance remain explicit refinement/acceptance boundaries, not claims of final production art.
