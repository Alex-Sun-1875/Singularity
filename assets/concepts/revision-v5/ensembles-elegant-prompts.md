# Ensemble elegant revision — built-in image edit record

Date: 2026-11-03

Mode: built-in `image_gen.imagegen` edit, using exactly one local source per image through `referenced_image_paths`; both source images were inspected with `view_image` before editing. `transparent_background: false`. No CLI/API fallback. Generated output files are copied into the project; old sources are retained.

## Explorers

- Source: `F:\workspace\Singularity\assets\concepts\revision-v5\explorers-v5-refined.png`
- Output: `F:\workspace\Singularity\assets\concepts\revision-v5\explorers-v5-elegant.png`
- Generated source: `C:\Users\Alexa\.codex\generated_images\01a19d22-5e50-7410-8158-a65f78e7c012\exec-a383ddae-181b-43d2-b3ed-65686e5283c8.png`
- Verified dimensions: 1536 × 1024 pixels.
- Verified format: PNG, 24bpp RGB, opaque background.
- Visual check: exactly four distinct youthful adult figures, full bodies and separated silhouettes; labels AIDA / BRAN / LAESA / MOREN correctly spelled and ordered. AIDA has champagne-blonde neck-length broad waves; LAESA has honey-blonde voluminous long waves in a high ponytail with small braids. BRAN retains short black hair and broad-shouldered fitted navy armor; MOREN has medium-length dark-brown swept-back waves and an elegant young scholar's face. Signature weapons, shield, bow, optical staff and clothing colors remain. Natural warm-lit light skin, detailed materials and practical full coverage. Parent independently reviewed and accepted this output without further iteration.

### Actual complete prompt

```text
Use case: precise-object-edit.
Asset type: premium Western fantasy CRPG full-body character ensemble concept sheet.
Input image 1 is the sole EDIT TARGET: explorers-v5-refined.png. Edit this existing board, preserving its landscape 3:2 canvas, warm neutral opaque textured background, refined painterly realism, four original characters' professions, exact left-to-right arrangement, separated full-body silhouettes, grounded boots, original poses and signature props. Retain all four name labels with exact spelling beneath their corresponding feet: "AIDA", "BRAN", "LAESA", "MOREN". Do not crop heads, weapons, feet, or text.
Primary request: targeted beauty and hairstyle refinement with distinct original faces, all fair-skinned youthful-looking adults. Women have conspicuous blonde large waves. Keep the two men dark-haired and individual. Upgrade clean tailoring and believable fine cloth, leather and metal with restrained wear.

Left to right:
AIDA: woman age 36, visibly youthful adult face, beautiful and spirited with a slightly sly, confident expression. Make her thick hair CHAMPAGNE BLONDE, with luxurious broad sculpted soft waves in a short bob ending at jaw/neck, not tight tiny curls and not a pixie cut. Fair skin, distinct feminine original face, lively eyes. Preserve burgundy long waistcoat, practical fully covered cream blouse and fitted layers, double short blades and copper seal tokens, crossed arms, lean capable physique.
BRAN: man age 38, fair skin, short BLACK hair, handsome strong youthful adult face, broad shoulders and a fitted waist, athletic shield guardian. Preserve his existing original facial identity, massive shield, navy fitted quilted armor, pose and equipment. No gray beard, no gray hair, no heavy facial wrinkles, no old man appearance, no obesity. Natural subtle dark stubble is acceptable.
LAESA: woman age 27, fair skin, refined beautiful and heroic youthful adult face. Change hair to HONEY BLONDE, long voluminous BIG WAVES in a high ponytail; individual broad flowing wave locks must be visibly lush, with a few small braids gathering the hair away from the bow. Keep original gray-green cloak, bow and quiver, practical fitted leather layers, full coverage, poised athletic proportions. Hair must remain clear of bow string and weapon grip.
MOREN: man age 32, fair skin, a strikingly handsome youthful elegant scholar with intelligent expressive eyes, refined brow and graceful charm. The intended temperament recalls Gale's elegant scholarly charisma and Astarion's refined sly intelligence in Baldur's Gate 3, but this is an ORIGINAL face and original outfit, not a copy of either game character. Give him DARK BROWN medium-length natural broad wavy hair, swept back at the temples, optionally a restrained half-tie. Keep the hair visibly brown, never blond, white, or gray. Preserve ivory-gray and ink-blue fitted scholar clothing, bronze multi-lens optical staff, book satchel, pose and slim adult figure. Avoid an aged or gaunt face.

Composition and invariants: retain four characters and only these four, precise left-to-right names AIDA / BRAN / LAESA / MOREN, similar generous spacing and full-height proportions, no overlapping silhouettes, no duplicates. Improve faces and hairstyle without changing their professions or color identities. Maintain natural skin texture rather than plastic beauty retouching, clean deliberate seams, premium authentic materials. Practical fully covered female clothes, no added sexualization. No modern clothing, no anime, no logos, no BG3 costume copying, no white or gray hair, no elderly faces. Ordinary opaque background. Match original 1536 x 1024 landscape composition.
```

## Rivals

- Source: `F:\workspace\Singularity\assets\concepts\revision-v5\rivals-v5.png`
- Output: `F:\workspace\Singularity\assets\concepts\revision-v5\rivals-v5-elegant.png`
- Generated source: `C:\Users\Alexa\.codex\generated_images\01a19d22-5e50-7410-8158-a65f78e7c012\exec-c04812d2-3485-41fd-b580-1deefcedb0ca.png`
- Status: the original built-in edit request completed successfully; no retry or CLI fallback was used.
- Verified dimensions: 1536 × 1024 pixels.
- Verified format: PNG, 24bpp RGB, opaque background.
- Visual check: exact left-to-right labels ILO / ELIN / NAVI / RODERICK, four youthful-looking light-skinned adults, separated full-body silhouettes. ILO has chestnut-brown hair; ELIN has light-blonde large waves and a fitted deep-blue guard outfit with deliberate white repair patches and furnace lantern; NAVI has long golden waves over one shoulder, bronze-green coat, magnifying lens and ceramic cup; RODERICK has dark-golden-brown hair, dark stubble, fitted bronze-steel armor and red-brown cloak. No gray hair or elderly faces remain. Original colors, professions and props are recognizable, and cloth is tidier.
- Follow-up: the user's later feedback requested fuller cheeks and shorter rounder chins for all characters. A separate non-destructive revision is saved as `rivals-v5-balanced.png`; see `rivals-balanced-prompt.md`. The elegant image remains as an intermediate version.

### Actual complete prompt

```text
Use case: precise-object-edit.
Asset type: premium Western fantasy CRPG full-body character ensemble concept sheet.
Input image 1 is the sole EDIT TARGET: rivals-v5.png. This source depicts older weathered characters. Transform all FOUR into handsome or beautiful FAIR-SKINNED YOUNG-LOOKING ADULTS while preserving their distinct original professions, clothing colors, signature props, original left-to-right order, neutral warm opaque textured studio background, separated head-to-toe standing composition, lighting, and all four readable exact labels: "ILO", "ELIN", "NAVI", "RODERICK". Do not preserve the elderly faces, gray hair or ragged appearance. Do not crop any heads, boots, props or labels. Keep the source canvas 3:2 landscape.

Left to right:
ILO: man age 23, fair skin, short CHESTNUT BROWN hair, fresh handsome pretty young-adult face with alert intelligent eyes, clean-shaven. Keep his lean build, ochre-yellow short jacket, modest fully covered light shirt, map tube and measuring cord line/rope tools. Give the jacket cleaner crisp tailoring and authentic leather details, trousers in good repair, preserving the surveyor identity.
ELIN: woman age 37 with a visibly YOUNG ADULT, beautiful determined feminine face, fair skin and a fit athletic body, not an elderly or masculine face. Replace all gray hair with LIGHT GOLDEN BLONDE luxuriant medium-to-long hair in BIG SOFT WAVES, half-tied back, flowing wave locks clearly visible around shoulders. Keep deep-blue fitted protective guard armor and the furnace lantern in her hand. Retain only a few deliberate WHITE CLOTH repair panels as her signature, clean and thoughtfully sewn; replace extensive ragged torn fabric with a crisp tailored well-maintained silhouette. Athletic, capable, graceful. No wrinkles, no aged neck, no gray braid.
NAVI: woman age 38, visibly YOUNG ADULT with a radiant beautiful elegant face and warm FAIR skin; self-assured, lively expression. Change hair to lustrous GOLDEN BLONDE, LONG, FULL, LARGE WAVES swept over one shoulder; NOT an updo, NOT a bun, NOT gray. Keep refined fitted bronze-green long coat with premium tidy seams and brass buttons, single magnifying lens in one hand and ceramic cup in the other. Well-proportioned elegant adult body and clean tailored garments, not matronly or elderly. Preserve her original role and props.
RODERICK: man age 38, fair skin, short DARK GOLDEN BROWN hair, a very handsome strong youthful military officer's face, upright athletic build and broad shoulders with a defined waist. Small amount of DARK stubble is acceptable, no gray or white beard. Preserve red-brown cloak, sword and finely crafted bronze-and-steel plate armor. Upgrade neat fit, crisp trim and subtle material detail, keeping restrained authentic patina. No skulls, no horns, no elderly features.

Style: sophisticated Western fantasy CRPG concept art, refined semi-realistic painterly rendering with believable skin pores, fine fabrics, leather and metal. Separate individual facial features for each adult; do not give everyone the same face. Women's golden large waves are a key requirement. All four faces and exposed skin must be light/fair and youthful-looking, no gray or white hair, no heavy wrinkles or old-person posture. Hands anatomically plausible, props retained, natural adult proportions. Reduce dirt, torn cloth and ragged hems while preserving the specific repaired white fabric accents on ELIN. Women remain naturally and practically fully clothed; no added sexualization. No anime, no plastic airbrushed skin, no modern clothes, no new symbols, no extra characters, no overlaps.
Text and framing invariants: exact labels ILO / ELIN / NAVI / RODERICK, each below its corresponding character, elegant dark serif lettering. Preserve original whole-body board composition and opaque neutral background, 1536 x 1024 landscape.
```

