# Fire-family asset audit

This is a read-only asset/material review. `texture-compositing-review.jpg` is a deterministic local swatch sheet, **not** a game capture or visual acceptance of the new skills. No production files, shaders, build output, gameplay, shields, or accepted FIR04 presentation were changed by this audit.

The latest user accepts the v27 filled-centre wisps and asks to apply that style to the other fire skills. The accepted source atlas is `fire-ground-jets-v27.png` (SHA256 `37a8319026bf39a4862f1f9bedbfceb98a6a3119c16f3265f300756dd4c2e4c6`). It contains 32 192×288 frames arranged in 8 columns and 4 rows. Its anchor is (95.5, 264), rather than the cell bottom. Keep the last 24 pixels below the ground anchor outside the visible flame footprint. The RGBA upload cost is 7,077,888 bytes (6.75 MiB), already loaded for FIR04; sharing the same Texture2D does not need a new atlas allocation.

## Causes in the existing renderer

- `drawRibbon` oscillates around only about frames 6.4–8.6 for the deep field, and `drawPlume` traverses 4–8 back and forth. Dense v7 rolling-cloud shapes cannot produce the selected upward-flowing thin flame look merely by reducing opacity.
- The existing `phase` retains the outgoing card until late in the transition while introducing the incoming card early. At blend=.5 the two opacity weights are 1 and about .778, so overlapping opaque areas become thicker and brighter. More field rows or ignition cores compound this effect.
- The representative v7 pyro/roll/bolt frames have mean occupied alpha .68–.70 and about 60–62% of occupied pixels above alpha .75. The v27 representative frame has mean occupied alpha .389 and 10.7% above .75. Exact inputs and selected frames are in `metrics.json`.
- The ground blast switches to five residual patches after progress=.60 and, from .73 on, has no main volume. The late v7 residual clocks approach the same terminal frame rather than continuously flowing upward. Fade must not stop the new 32-frame clock.
- The current `Effects.ts` constructs SkillFireSprites with flatCamera while the accepted ground jets use battleCamera. Use the camera actually rendering the player/scene when orienting new wisps, and validate both projection and depth against ordinary training-range footage.

## Reuse and material recommendations

Reuse the v27 atlas directly for FIR01 trails, FIR05 fire-field tongues, and FIR02 residual fire. No new large atlas is necessary. Preserve its authored colour and central translucent fill; do not add a white axial line, erase a central stripe, or introduce serpentine UV motion. Use continuous ascending phases, not reversed playback.

Use one card draw with two adjacent frame samples interpolated in premultiplied space. Share the accepted v27 compositing: RGB colour × alpha × 1.10; output alpha × .90; blend ONE / ONE_MINUS_SRC_ALPHA; depth test on, depth writes off, culling off. `mainColor.rgb` should stay neutral (1,1,1). Begin at 24fps with per-emitter phase offsets; the existing 12fps low-motion clock is suitable. Start with one primary sheet per flame and keep any back/side sheet low enough that overlapping wisps remain visibly separate.

Suggested initial tuning for native visual review, not a final art verdict:

| Skill | Reuse / hierarchy | Initial opacity and layers |
| --- | --- | --- |
| FIR01 | Rotate the v27 long axis into flight; root toward the projectile head and tips toward the tail. Keep the projectile and its wake anchored to the resolved flight position. | Main tongue .80–.95; at most two side wisps .20–.35; remove the round white ignition overlay or constrain it to <=.12 and a brief release/contact beat. |
| FIR05 | Three staggered ground rows of upward tongues, distinct from the five sealed FIR04 jets. Make the full authoritative depth visible, rather than one wide flat curtain. | Single front layer .65–.85 per patch; any rear layer <=.12; varied height .8–1.2m. Continue texture motion during the existing 1.8s cooldown, fading alpha smoothly and shrinking height to about 35%. |
| FIR02 | A distinct short impact beat, then 5–7 spatially separated v27 plumes that settle into the long residual burn. Preserve its ultimate radius and existing timing. | Prefer the same v27 flame material. If the existing pyro atlas remains for impact, one layer only, alpha .35–.55 and <=.16–.30s; no repeated smoke clouds. Main plume peak around 2–3m as an initial review value, residual alpha .65–.90 then smooth fade. |

Do not add the small FIR04 sigil under the other ground flames; only meteor retains the large cast/range circle. Keep the unified shield and existing accepted FIR04 unchanged. There is no required derived core or blast sheet; if a compact ignition accent remains necessary, reuse `fire-core-v7` at very low opacity for a very short beat before considering another texture.

Final validation must come from ordinary Cocos training-range footage with the current player, scene camera, normal animation timing and current shader. Swatches establish source/material differences only. Mobile TapTap/device verification remains separate.
