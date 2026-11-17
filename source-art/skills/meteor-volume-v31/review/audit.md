# Meteor v31 read-only review

The user rejected the v30 meteor runtime ground-light look. The approved visual target is the v29 lower-right concept: one impact centre opens outward into bright, connected orange-gold combustion, with substantial curling volume. It is not seven isolated bonfires, a ring of upright jets, or narrow electric-like strands.

Reviewed source: `source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png`, necessary region `(930,735,1330,985)`. Runtime: `src/.tmp/fire-distinct-runtime-v30/meteor-final-empty-r1/FIR_02/075.jpg`, plus the final stage board. Local `v29-v30-comparison.jpg` contains only crops and layout, with no added effect.

## Why v30 reads as lines

1. The curling-fire sampler uses the lance atlas's U `.03..86`, excluding the concentrated tip. Across V, only **22.9%** of the typical sampled cross-section exceeds alpha `.2`. It is a thin-filament projectile texture mapped onto an already narrow ribbon.
2. At ribbon progress `s=.5`, a representative full geometric width is `.084 × radius`. The actual bright cross-section is approximately `.019 × radius`, only **7.3 cm for a 3.8m radius**. Seven such curls cannot read as a continuous burning volume.
3. The principal sheet is low: its peak coefficient is roughly `.07..09 × radius` before settling. The sheet supplies floor colour while almost all vertical volume is delegated to those seven fine ribbons. Their opacity also receives `.78 × .92` and the shader's `.90` absorption factor.
4. The field texture's whole-atlas mean alpha is `.312`, while the lance is `.127`. The shader further attenuates low-density samples. The field is already sufficient to tint a floor, but its low geometry and lack of a broad raised cross-section produce a soft surface wash. Multiplying brightness alone will brighten the wash and the thin strands without supplying missing fire body.

## Display comparison, not alpha inference

`metrics.json` reports RGB/luma of warm image pixels within individually selected effect ellipses. Neutral floor and dark rocks fail the thresholds. This is **not** the same camera, background, illumination or an opacity ground truth. Warm floor reflection can contribute to a concept's displayed appearance, so it must not be extracted or interpreted as fire alpha.

- Bright orange-gold coverage using R>.85, G>.55 and R-B>.20 is about **14.5%** in the concept ellipse and **0.43%** in the runtime ellipse.
- Warm-pixel P90 display luma is about **173/255** in the concept and **136/255** in the runtime.
- Warm-pixel P90 RGB is approximately **(251,160,65)** versus **(193,127,56)**.

These provide useful initial brightness/area checks for native iteration; they are not a request to brighten the neutral background or colour stone fragments.

## New texture contract

Use a **wide, continuous, curling fire wave on genuine transparent RGBA**, with enough orange-gold combustion body between the brighter folded filaments. It should be a broad flowing billow, connected along the lower portion and opening into several unequal rolling crests. No floor, baked orange floor light, rocks, character fragments, black smoke, white cloudy mass, separate pillar silhouettes, sparse line-art-only flames, or large transparent holes through its entire main body.

The lower/middle body should occupy most of the useful cross-section, with approximately 50–70% of that interior supported by alpha `.35..65`; stronger gold folds can reach `.7..9`, and outer fringes should feather smoothly to zero. These are **engineering targets for a new texture**, not alpha values inferred from the flattened v29 concept. A section at alpha `.2` should span at least about 60% of the intended burning width, rather than the lance's 22.9%.

Initial display colours can use orange body `(1,.47..65,.12..25)`, bright gold folds `(1,.72..82,.30..45)`, with a small brief centre peak up to warm ivory. Preserve per-pixel colour and optical density variation; do not replace it with a uniformly filled orange sheet.

Build native volume from connected radial curved surfaces with broad overlapping cross-sections. As initial native-review values, use a main height around `.35..60 × radius`, lower front rolls around `.15..25 × radius`, and broad rather than thread-like crests. Retain an irregular silhouette and limited openings; avoid a uniform vertical cylindrical wall. Two to three overlapping broad skins per observed ray are enough to test useful depth without a solid opaque slab. Prefer a few connected surfaces with texture detail over numerous detached bonfires.

Keep normal premultiplied source-over for the orange body. A small stronger emission in the bright folds and brief impact centre can provide the desired punch. Do not solve the density deficit with additive blending alone. Preserve the existing resolved centre/radius/hit timing and long fade; test the sustained main burn before the residual stage because that is where the current volume deficit is most visible.

Only files in this `review/` directory were written. No production source, texture, shader, gameplay, build, or approved v27 jet/shield was changed by this review.
