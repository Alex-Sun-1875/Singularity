# Rivals balanced facial proportions — built-in image edit record

Date: 2026-11-03

- User feedback addressed: all faces were too thin; add healthy cheek volume, soften cheekbones and shorten/round the chin while retaining adult proportions and distinctive features.
- Mode: built-in `image_gen.imagegen`, precise-object-edit, exactly one local source in `referenced_image_paths`.
- Source was inspected with `view_image` before editing.
- Source: `F:\workspace\Singularity\assets\concepts\revision-v5\rivals-v5-elegant.png`
- Output: `F:\workspace\Singularity\assets\concepts\revision-v5\rivals-v5-balanced.png`
- Generated source: `C:\Users\Alexa\.codex\generated_images\01a19d22-5e50-7410-8158-a65f78e7c012\exec-8d1bcd83-b83a-4752-a0ac-5186d3da526a.png`
- `transparent_background: false`
- Output checked: PNG, 1536 × 1024 pixels, 24bpp RGB, opaque background, 2,338,548 bytes.
- One targeted built-in edit completed successfully in approximately 119.7 seconds. No retry, CLI or API fallback.
- All prior image files are retained.

## Visual verification

- All four faces show fuller cheek volume and softened cheekbone planes; lower faces and chins are shorter/rounder, with no hollow cheeks.
- ILO and RODERICK retain clear masculine jawlines, adult proportions, distinct eyebrows and individual expressions.
- ELIN and NAVI have healthy soft oval adult faces rather than childlike proportions.
- The four identities remain differentiated; bodies and overall weight remain essentially unchanged.
- Women retain light/golden blonde large waves; men retain chestnut/dark-golden-brown hair.
- Four full figures remain separate and uncropped. Exact left-to-right labels ILO / ELIN / NAVI / RODERICK remain correct.
- Clothing colors, fitted tailoring, white repair accents on ELIN, map tube, measuring cord, lantern, magnifying lens, ceramic cup, sword and armor remain present.
- Warm neutral opaque backdrop and realistic painterly material treatment remain.
- The parent independently reviewed the output and accepted it as the current candidate for this round.

## Actual complete prompt

```text
Use case: precise-object-edit.
Input image 1 is the sole EDIT TARGET: rivals-v5-elegant.png, a four-character full-body fantasy concept board.
Make ONE targeted revision to all four faces: they currently look too long and thin. Give ILO, ELIN, NAVI and RODERICK noticeably healthier fuller cheek volume, softer less projecting cheekbones, and slightly SHORTER, more rounded chins and lower faces. Remove hollow cheek planes and gaunt temples. The correction must be visibly clear at the full-board scale, while preserving each character's distinctive beautiful or handsome identity, expression and young-adult age. Keep adult facial proportions: no baby faces, no chubby cheeks, no obesity, no oversized heads.
ILO (23): fresh handsome youthful man, fuller healthy cheeks and a balanced shorter lower face, retaining a clear masculine jaw.
ELIN (37): beautiful determined young-looking adult woman, healthy soft OVAL facial shape, fuller cheeks and a gently rounded shorter chin. Keep capable mature adult poise.
NAVI (38): radiant elegant young-looking adult woman, healthy soft OVAL face with fuller cheeks and a shorter rounded chin, retaining confident warmth.
RODERICK (38): striking handsome youthful officer; fuller non-hollow cheeks, broader clearly defined masculine jaw and a shorter firm chin, not a soft or childlike face.
Keep the men's clear BROAD MASCULINE JAWLINES. Keep women's naturally soft healthy adult oval faces. Skin stays fair/light with realistic texture and youthful appearance. Keep all bodies and body weight unchanged.

STRICT INVARIANTS: change facial geometry and facial shading only. Preserve every existing hairstyle and hair color exactly: ILO short chestnut-brown, ELIN light-blonde large waves half-tied back, NAVI long golden large waves over one shoulder, RODERICK short dark-golden-brown. Preserve the luxurious blonde wave volume on both women. Preserve all four outfits, neat tailoring, exposed skin tones, body proportions, poses, hands, weapons, props, lantern, map tube, measuring cord, magnifying lens and ceramic cup. Preserve refined Western fantasy CRPG painterly realism, material detail and lighting. Preserve the neutral warm OPAQUE background, original 1536 x 1024 landscape framing, four separated FULL BODIES and exact left-to-right names "ILO", "ELIN", "NAVI", "RODERICK" beneath the corresponding feet. No cropping, no overlaps, no new text or characters, no gray hair, no aged faces, no anime or plastic skin.
```

