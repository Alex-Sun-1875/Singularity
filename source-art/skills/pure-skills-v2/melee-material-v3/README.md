# Close-range silver/gold sword material v3

`generated-strip.png` is the unmodified transparent strip produced by the
built-in OpenAI cloud image_gen tool on 2026-11-08. `steel-reference.png` is a
necessary material crop from the existing near-sword evolution reference.
The exact prompt is recorded separately by the root task in `prompt.txt`.

`tools/make-melee-material-v3.py` derives the runtime texture with an explicit
crop, brightness-driven alpha suppression of the broad grey smoke, a small RGB
exposure lift and Lanczos reduction. It preserves the generated silver/gold
striations; it does not generate replacement art. The runtime texture lives in
`src/cocos/assets/resources/vfx/production/melee-material-v3/steel-ribbon.png`.

The runtime uses the existing Cocos 3.8.8 transparent builtin-unlit technique
and a cached native annular sector. UV wrapping keeps every vertex inside the
authoritative close-range radius and never creates a projectile, target or hit.
No new dependencies or custom shaders were added.

Generation succeeded. The first runtime pass in package `main6e061` failed the
actual same-camera review: the silver sweep was too faint and ground-parallel
foreshortening reduced it to a thin low arc. The second pass retains more
translucent striations, uses a separate narrow additive cutting edge, and tilts
the native cutting plane forward by about 20 degrees. Its XZ projection remains
inside the real melee fan. Alpha levels and both mesh layers are pooled/cached.

Material cleanup and TypeScript checks passed. Acceptance of the second pass
remains pending actual in-game same-camera and motion review; a generated
texture alone is not evidence of combat visual acceptance.

Final representative review: `index.b5871.js` was rebuilt and observed in the
actual Cocos renderer. Sword basics, WAR01/05 sweeps, WAR02 crossing strokes and
WAR04 falling edge are readable in same-camera captures and original-speed
sequences. The final pass boosts silver/gold RGB while preserving alpha and
uses the same texture for camera-facing resolved short strokes. No projectile,
damage geometry or character artwork was added. See
[runtime record](../../../../docs/assets/combat-vfx-v3.md) and
[same-camera comparison](../../../../src/cocos/test-results/vfx-art-redesign-v3/before-after.jpg).
Representative material/readability review passed; fine gold filament density
still differs from the reference. This is not a claim of user acceptance or
pixel-identical reproduction of every rank.
The final review is stored separately from generation provenance in
[runtime-review.json](runtime-review.json).
