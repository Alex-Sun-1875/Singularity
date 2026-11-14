# Original design face and hair alignment

**Goal:** Make the player's complete88-action set and HUD follow the original silver-curly-haired narrow oval face and rounded chin, rather than mixed fused-face/half-tied hair derivatives. Preserve the newly installed W01 long-legged running poses.

**Authority:** `appearance-v5/male-direction.png`, original full-body front/right heads and large portrait. A four-direction head master is a once-only derived reference; it does not replace the original as identity authority.

**Architecture:** Reuse matching original short-curly combat PNGs where independently acceptable; perform native ImageGen head/hair-only edits on remaining current atlases, using one fixed head reference. Reuse Cocos SpriteFrame/quad rendering and existing read-only alpha/crop/body-registration helpers. HUD directly samples the original design portrait via native SpriteFrame UV rect, with no new generated portrait identity. One full68-image installation against current5f baseline prevents mixed identities.

**Reuse decision:** AutoSprite Ninja's officialCC0 PNG/JSON can serve as animation reference, not this custom face. UniversalLPC provides pixel-art layered assembly/phase organization; do not replace the realistic character with its stock pixel heads. Summer is not uniformlyCC0 and CraftPix's stock werewolves do not match this human identity. Existing Cocos rendering/dependencies already support PNG atlases; no new runtime package is needed.

## Constraints

- Current88-action/68-PNG manifest SHA5f438265f874fc45785f0a596c1ba328f889bfc369c28f3480ab6af2e2f9240c is the only baseline. No old60-action or rejected-run rollback.
- Preserve all action keys, phase/direction lookup, FPS, timing, world UPP, game rules, inventory, saves and carry routing. Transfer crops/anchors only by measured original-body translation, never head/weapon-height normalization.
- The4newW01run images retain their long-leg proportions and cycle. Head/hair edits must not redraw, squash, re-pose, resize or crop bodies/weapons.
- Face: restrained temple/cheek width, natural oval jaw, rounded/softly squared chin end, no V/needle chin. Hair: original side part and soft short silver curls, modest skull-following side/back volume, no tie/pony/shoulder tails. Head size follows original adult shoulder/head proportions.
- Only built-in image_gen changes raster pixels. Native originals/output bytes and provenance retained. Pillow/NumPy/SciPy measure only. No new tests/dependencies; reuse existing checks/build/manual verification. No commit/push/publish.

## Tasks

- [x] Audit all runtime image/HUD identity sources and verify proposed libraries using official sources.
- [x] Generate and independently review a fixed four-direction head identity master. Reviewer confirmed no necessary face/chin/hair correction remains in this reference.
- [x] Freeze5f baseline and68image inventory; select26matching native original combat PNGs, preserving source SHA/provenance. Four additional low-body-IoU reuse candidates were rejected and regenerated from current bodies.
- [x] Validate head-only pilots on current W01 running and exploration idle/dodge; generate42fixed-identity source PNGs. Complete-set crop/registration review remains the installation gate.
- [x] Reuse mature crop/registration/atomic installation logic with a thin5f profile; update root identity provenance and direct-original HUD resource/crop. Independent review added a final all-destination SHA recheck to the transaction.
- [x] Verify complete coverage, unchanged timing/UPP/run geometry intent, all frame ownership and body registration; install all68native outputs and HUD together. Full68/88 report passed with no errors/issues; original native HUD copied without pixel editing.
- [x] Run current type/rule checks, rebuild concept-2d and inspect actual HUD/idle/run/attack and weapon readiness transitions; open the updated local preview. TypeScript exit0,95existing tests passed, Creator build exit0; existing real-Cocos motion capture passed sword/bow/staff/spell/dodge/run, no page errors or mismatched materials. Walk phase/crop/identity coverage was statically reviewed; not every weapon's walking direction was individually played in the browser. All69PNG native resources and compiled manifest matched installed sources over actual HTTP.

## Review findings and bounded adaptations

- Short curls extend differently from old pulled-back hair. Several densely packed atlases cannot provide complete rectangular crops without a neighbour's shoe/hair. Clearing AA alone did not resolve bow hit/death. A native packing edit may translate complete figures and minimally reduce their uniform pixel scale while preserving body proportions, phases and equipment. These exceptions are recorded per PNG with actual measured bounds; they are not described as unchanged body pixels or exact scale. The four corrected W01 run PNGs do not use this packing exception.
- Body-registration search radius96 is allowed for reviewed original-art reuse and generated figures relocated in their cells. A large translation alone does not justify an acceptance flag. Low-IoU scale/pose changes require actual review or a targeted native correction.
- The head-height number in a generation prompt is a target, not a precise measurement or proof of1/7.5. Face/hairstyle and head-to-shoulder relationship require visual review at sprite scale.
- Existing checks passed during source preparation: TypeScript exit0, existing95rule tests passed. Build and actual served-runtime validation follow full installation.
- W07walk was finally restored to the first head-only raw. Read-only semantic crops preserve complete unique new/old alpha16 and complete alpha64 bodies/equipment, avoiding the rejected packing shrink. Correct carry W02walk was likewise solved without pixel changes. Remaining native packing exceptions are bow hit/death, W02 attack and L02 exploration walk, with per-image evidence retained.
- Final manifest SHA: `e1e1d5bdde78dff15892acecbd1c460551855a776cc60f7441a125eb1e772541`. Served preview: `http://127.0.0.1:7469/?view=2d&identity=reference-v1`. The original HUD was visually checked in the normal playable inn screen.
