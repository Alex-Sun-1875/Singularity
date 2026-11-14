# Weapon Carry Implementation Plan

**Goal:** Exploration uses natural empty-hand locomotion with actual equipped sword/bow/staff visibly secured to the back; combat remains immediately responsive and uses existing held-weapon poses.

**Architecture:** Reuse existing Cocos FlatActors native atlas rendering and measured metadata. Add exploration-specific pose keys and presentation-only combat readiness with a2s grace. Preserve existing60 combat routes, core rules and save schema. No new library or test dependency.

**Spec:** docs/superpowers/specs/2026-11-06-weapon-carry-design.md

## Global constraints

- User explicitly confirmed long swords go diagonally on the BACK in sheaths, not waist.
- Preserve silver half-tied hair, soft full face, burgundy/navy/gold clothes and accepted body scale. Source pixels may only be edited through built-in image_gen; measurement is read-only.
- Existing shields stay held. No invented player shield item or paper-doll capability.
- User AGENTS overrides test-workflow defaults: reuse existing checks/build/manual review, no new test cases/framework/dependencies unless necessary.
- Stay on existing codex/cocos-chapter-one user workspace; preserve dirty work and old source art. No publish, commit or merge requested.

## Tasks

- [x] Produce W01 back-carry idle/walk/run pilot from latest hero-v6 and measure complete crops/support anchors.
- [x] Implement presentation readiness and exploration routing, preserving cancellation, pause, first-attack timing and all combat animation phases.
- [x] Expand full back-carry locomotion to seven actual weapon identities; add corresponding exploration dodge/interaction continuity where routed. Record exact scope for any not-yet-authored transitions.
- [x] Merge manifest through native fields; retain old combat art and original bytes; validate selected image bounds, phase semantics and raw/source/runtime SHA.
- [x] Build and reuse existing type/rule/input/motion checks. Manually verify exploration empty hands/back carry, combat movement/first attack,2s restow, weapon changes, pauses and existing shields.
- [x] Independent review and final actual-scene screenshots; document result and remaining material limits honestly.

## Ledger

2026-11-06: User said continue after confirming back-carried long sword. Design is approved by this explicit continuation; proceed without another approval gate. Prior design-board imagegen attempts were output-moderation blocked; retry only normal allowed asset editing through built-in image_gen, do not switch CLI/API without explicit user authorization. Runtime changes should not pretend held source art is stowed if images remain unavailable.

Completed at17:00:40 build:33 newPNG/28explorekeys, original60combatkeys/35combatPNG unchanged;95rules pass,28manualbehaviour checks pass,476nativebindings match,desktop/mobile release passes. W01/W02 idle use reviewed neutraldodgefirstframe after independentidle output moderation blocks. No authoreddraw/sheathtransitions; directpose switching documented. Evidence:src/cocos/test-results/weapon-carry-v1/final-audit.json. User subsequently changed male face direction to Astarion/Gale blend; preserve this completed carry logic/poses during face refresh.
