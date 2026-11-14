# Thunder residual ground presentation v1

The original `combat-thu.png` is the colour/material reference. It has an icy
filament within a loose blue-violet corona and local blue-violet ground bounce.
The rejected `index.561e9.js` version used a bright cyan-like uniform body and
ended after one short edge cue. This revision changes the material hierarchy,
allows separately seeded repeated discharges of the same resolved edge, and
adds a residual ground cloud.

No new generated image, model, dependency, or external download was used.
`src/cocos/tools/make-thunder-ground-v1.py` uses the existing Pillow workflow to
derive original analytic masks: one irregular overlapping Gaussian haze and
four deterministic, broken short-discharge alpha masks. Runtime files and
SHA256/source descriptions are in
`src/cocos/assets/resources/vfx/production/thunder-ground-v1/`.

`ThunderGroundAura` uses two transparent built-in unlit quads per
resolved patch, one shared quad mesh, and a bounded reusable 32-patch pool.
It has no Line budget, targets, collisions, status effects, damage or lighting
changes. Ground height is sampled from the existing scene callback. The patch
has a soft irregular perimeter and no outlined ring or selection marker.
The mist uses ordinary alpha blending with deep blue-violet colour; the smaller
broken discharge uses lower-weight blue-violet additive light.

`SkillEnergyStrokes` exposes `THUNDER_COLORS`, `isThunderColor`, and an optional
last `pulse` argument on `drawLightning`. Frozen endpoints are preserved while
each pulse gets a different fractal seed and short bright fracture. Network
edges use four native Lines each; the whole path is thinner and less uniformly
bright than the rejected cyan version. The existing 100-point Line ceiling is
retained.

Mask generation and TypeScript checks succeeded. Runtime material, depth,
readability, pulse cadence and residual duration still require the integrated
same-camera/continuous capture. This is not an assertion of user acceptance.

First integrated `index.26d91.js` time-sequence verified three separate discharge
windows, two empty gaps, ground residual after the chest-height graph ended,
and eventual cleanup; all eight victim HP values stayed unchanged after the
one actual hit. The first fully additive ground treatment failed art review:
it read as white ground cracks and almost invisible pale haze. A same-scene
native renderer candidate changed the mist to ordinary alpha and coloured
the residual filaments blue-violet. See
`src/cocos/test-results/thunder-ground-candidate-v5/{before.png,candidate-alpha-cloud.png,candidate-review.json}`.
The successful candidate parameters were encoded into the renderer, but the
final integrated package must still be checked; the browser-only candidate is
not a claim that the final build already passed.

Palette correction before final integration: targeted samples of the original
reference gave blue-light median RGB `[117,135,220]` and bright-filament median
`[177,198,252]`, both with G greater than R. The first runtime corona had G less
than R and read too pink-purple. The electrical body/corona/filament therefore
shift back toward electric blue while preserving the thin irregular geometry
and the deep blue-violet ground cloud. See
[palette-sampling.json](palette-sampling.json) for the unmodified reference
hash, selected-sample medians and exact runtime palette. The selected colours
are material guidance, not a claim of pixel-identical reproduction.

Final representative review passed in `index.44f3a.js`: the ice/electric blue
is less pink than the first build, the soft local ground cloud is visibly
blue-violet, and no circle or hard rectangular patch is present. The three
separated discharge windows contain 70 / 64 / 64 active Lines, with zero Lines
in the two intervening gaps. The ground cloud remains after the last discharge
and fully clears by release+2.10 seconds. Victim HP stays `[336,415,415,415,415,
415,415,415]` after the first true hit; all visual echoes together still produce
only eight actual hit events. The independent real ChapterGame recording has
227 source frames over about four seconds and no browser or failed-request
errors. This is representative implementation/art review, not user acceptance
or approval of all skill ranks.

Evidence: [runtime report](../../../../src/cocos/test-results/thunder-resonance-v5/actual-resonance.json),
[eight timing frames](../../../../src/cocos/test-results/thunder-resonance-v5/three-pulse-ground-contact.jpg),
[compact original-speed GIF](../../../../src/cocos/test-results/thunder-resonance-v5/three-pulse-ground-live-compact.gif),
and [retained frame indices / timing](../../../../src/cocos/test-results/thunder-resonance-v5/compact-animation-artifacts.json).
The initial fully additive white-crack result is preserved under
`thunder-resonance-v5/iteration-26d91` and is not the final accepted direction.
