# Run-to-idle appearance alignment implementation plan

> For agentic workers: execute the bounded tasks below; existing checks and manual visual comparison take precedence over adding tests or dependencies (AGENTS.md).

**Goal:** Make the currently shown W01 character consistent across standing, slow walking and running. Body proportions/hip/leg line/outfit follow the accepted running body; following the user's latest correction, head shape and physical head size follow the standing character.

**Authority:** The four W01 run PNGs at initial manifest SHA `e1e1d5bdde78dff15892acecbd1c460551855a776cc60f7441a125eb1e772541` define body/stride. The user's later explicit instruction, “应该使用站姿的头型吧，跑起来的时候看起来很大”, makes installed `locomotion-v1/W01-explore-idle.png` / `W01-held-idle.png` the head-shape/volume authority. Do not enlarge standing heads or revert to the older global head master.

**Root cause:** Exploration idle samples column0 of a different dodge atlas. Slow walk and held idle also use different whole-body drawings. Measured world heights are mostly already1.55–1.60; changing global scale or matching bent-knee run bounding-box heights would preserve the wrong silhouette and introduce new scale errors.

**Architecture / reuse:** Keep existing Cocos3.8.8 cutout quad, per-action SpriteFrame rect/anchor/UPP data and existing alpha measurement helpers. Stage1 derives four W01 idle/walk sheets and removes idle's dodge dependency. Stage2 uses standing heads to reduce the four running and two walking heads, retaining body pose, stride, UPP and timing through measured per-phase body XY. New paths preserve old PNG files. Each stage changes six bounded action records, nine distinct actions total against the initial e1 baseline. Dodge/HUD/other weapons remain untouched. No new dependencies, test suites, commits or publishing.

**Alternatives considered:** Global scaling cannot change head/leg/clothes proportions. Existing curly-restore neutral/walk art is closer but lacks the installed gold-hilt back carry and is not identical to the user's chosen run. Reusing its pose organization as a reference is reasonable; final whole-body authority remains current run.

- [x] Reproduce and audit actual action routing, native art and world geometry; independent runtime and visual audits agree on source mismatch.
- [x] Freeze manifest/current run bytes and create native source/provenance records under `source-art/characters/2d-concepts/locomotion-alignment-v1/`.
- [x] Generate independent4-direction exploration idle and4-direction4-phase slow walk from current run; visually compare hair/head, neck, shoulders, hip, legs, garments and gold-hilt sword carry.
- [x] Derive matching held-sword idle/walk from those approved sheets; independently review geometry and silhouette. Native tool moved idle figures slightly; measured lower-body XY and actual shoe details calibrate anchors rather than claiming unchanged pixels. Both original PNGs remain unchanged bytes.
- [x] Adapt only selected action metadata using measured complete alpha crops, authored foot anchors and calibrated world scale. Use current run head/body landmarks as calibration, not alpha height of lifted feet. Idle UPP.003191794871794872; walk UPP.004376933895921238. Per-frame support soles and hip axes reviewed; held-body translation IoU>=.9371 with at most1px sole refinements.
- [x] Install all four PNGs and bounded manifest edits with native-byte verification/backups. Four run PNG hashes and all run action records unchanged; unrelated82 action records unchanged. `install-report.json` validated four native sheets with no missing/errors/issues; build running.
- [x] Rebuild, run existing checks and real-Cocos motion capture; record fixed-camera four-direction idle→slowwalk→run→idle transitions and held/exploration transitions. TypeScript/95 existing rules pass; final build exit0; original real-Cocos motion scenarios pass. The two final capture runs together cover four walk phases/eight run phases; camera fixed2.0/1280x720, zero runtime errors/material mismatches.
- [x] Open playable new build, save exact-source/build/HTTP verification and report what was actually reviewed. New landscape iframe preview remains playable in the portrait desktop side pane with viewport override reset.

## Latest head-authority correction

- [x] Capture stage1 at one camera and measure actual head dimensions. Stationary right head was about37px wide/36px high versus run44/41 and walk42/40. Whole-body calibration alone did not resolve head volume.
- [x] Apply user's correction: keep the standing head. Do not execute `idle-head-scale-v2.prompt.txt`; it was drafted before the correction and was never sent to ImageGen.
- [x] Native head-only edits of four run/two walk atlases to standing-head canon; review actual dimensions after applying each action's UPP. Preserve run body/stride and every contact/flight phase. Held walk required one bounded head correction; explore runB required one native alpha cleanup; provenance retains both attempts.
- [x] Install six new `locomotion-v2` PNGs against frozen stage1 manifest `e1682ed6f1b6000e4ff3e46f4871abcd018532979cca0d891308117003e64443`; preserve standing PNGs/root/HUD/82 other action records exactly. Final manifest `4065d59acbccb8c85642cf31cab840a8fce3577a87806ce2c558096098b41df8`; min body-registration IoU.924215, no install issues.
- [x] Rebuild and recapture final same-camera standing→walk→run→stop; independent review of24 screenshots across four directions in explore/held mode found no obvious large-head recurrence/body regression. Right screen head dimensions approximate idle37×36, walk38–39×36, run38×37; held run remains slightly larger5–8%, within phase/pose differences. Small generative redraw differences are not described as unchanged body pixels. Old/new stationary screenshots are identical at the same right-view camera.

**Visual acceptance:** Same head silhouette/part/curl volume and face in each direction; same shoulder/head relationship, long thigh/shin proportions and fitted clothing; no oversized standing head or pointed narrow new face, no inventory bottles appearing when stopping. Feet remain on one contact plane and the run's intentional flight/bob stays intact. A prompt's pixel target is not proof—inspect the actual rendered transitions.

**Delivery ruling:** The user's screenshot shows the in-app desktop preview stuck on a rotation prompt because its parent pane is portrait. Add a tiny16:9 iframe preview page through the existing web-mobile build-template mechanism. It keeps the embedded game's real viewport landscape without changing game orientation rules or retaining temporary browser viewport overrides. No added controls/dependencies or gameplay changes.
