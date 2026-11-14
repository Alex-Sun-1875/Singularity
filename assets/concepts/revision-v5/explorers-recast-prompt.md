# Explorers three-face recast

Date: 2026-11-03

## Request and mode

The user rejected the previous face-width correction and requested a new casting pass influenced by Gale and Astarion: preserve the second character BRAN in the earlier elegant version; genuinely change the first, third and fourth faces. AIDA and LAESA remain women with their blonde wave hairstyles. MOREN should reflect Gale's actual facial construction rather than only a vague scholarly mood.

Mode: built-in `image_gen.imagegen`, image EDIT with three `referenced_image_paths`, `transparent_background: false`. One completed call. No CLI, no Python editing, no post-processing. All three inputs were viewed with `view_image` before the call. The earlier balanced output was inspected for comparison but was not submitted as an edit source.

## Inputs and reference roles

1. Sole edit target: `F:\workspace\Singularity\assets\concepts\revision-v5\explorers-v5-elegant.png`.
2. Gale official face/structure reference: `F:\workspace\Singularity\tmp\art-reference\bg3-gale-official.png`. Official Larian source: [Gale character render](https://baldursgate3.game/heros/hero-gale.png). Local reference dimensions: 1710 × 1380.
3. Astarion official face/expression reference: `F:\workspace\Singularity\tmp\art-reference\bg3-astarion-official.png`. Official Larian source: [Astarion character render](https://baldursgate3.game/heros/hero-astarion.png). Local reference dimensions: 1710 × 1380.

Gale is used as MOREN's explicit brow/eye, forehead, midface, nose/mouth, chin and expression reference. Astarion is used for articulate expression, charm and individual character acting, particularly AIDA's knowing expression. Reference costumes, magic effects, vampire features and white hair are not transferred.

## Output

- Project file: `F:\workspace\Singularity\assets\concepts\revision-v5\explorers-v5-recast.png`
- Original generated file: `C:\Users\Alexa\.codex\generated_images\01a19d05-6cf0-7d40-82b1-31ad3253a5ce\exec-0d8bbb67-8ec8-4ea5-8449-21df6f25a223.png`
- Dimensions: 1536 × 1024 pixels.
- Format: PNG, opaque 24-bit RGB.
- Bytes: 2,482,607.
- SHA256: `CC7996511AD80332E68DB4A6BEA7CA180AAD5861411B4C2F99BAE56AC209924B`.
- Original elegant, balanced and official reference files remain unchanged.

## Visual inspection

The generated image was displayed through `generatedImage`, copied into the project, then viewed again from the final project path.

- BRAN: the approved elegant-version face, short dark hair, subtle stubble, steady expression, broad-shouldered body, pose, indigo-gray armor, shield and boots are visually retained. The prior balanced-version heavier jaw is not used as the base.
- AIDA: visibly recast eyebrow/eye shape, narrower knowing gaze, different nose/lip relationship and asymmetric amused smile. Her champagne-blonde neck-length large waves, wine-red clothing, crossed arms, twin blades and copper seals remain.
- LAESA: recast straighter stronger brow/eye structure, nose and mouth, with a clearer composed heroic gaze and a different facial appearance from AIDA. Her honey-blonde long wave ponytail, fine braids, gray-green cloak, bow, body and stance remain.
- MOREN: substantial change from the former elongated angular face to a Gale-referenced adult scholar's facial structure: fuller natural midface, substantial brow/eye relation, dimensional nose, short dark facial stubble, warm visible smile and swept-back dark-brown hair. His ivory-gray/ink-blue costume, copper lens staff, body and gesture remain his original design.
- The original four-person order, exact AIDA / BRAN / LAESA / MOREN labels, full-body framing, complete heads and boots, original palette, opaque neutral background and grounded stance remain intact. No vampire fangs, white hair, pointed ears, reference robes or blue spell effects appear.

Limitations: selective generative editing preserves BRAN and the composition visually but does not guarantee pixel-identical preservation of every fabric thread, shadow or painted edge. This sheet is a concept-art casting result, not a production facial topology specification. All three redesigned faces should be judged against the user's casting preference, not only against an objective width metric.

## Exact submitted prompt

```text
Use case: precise-object-edit.
Asset type: selective character-face RECAST on an existing four-person fantasy CRPG concept board.

INPUT ROLES:
Image 1 is the sole EDIT TARGET: the four-person AIDA / BRAN / LAESA / MOREN lineup. Preserve this board.
Image 2 is the official Gale face REFERENCE: use the actual visible face structure, brow/eye relationship, nose and mouth proportions, hair grooming and mature confident charm to redesign MOREN's face.
Image 3 is the official Astarion face/expression REFERENCE: use its exceptionally readable acting, intelligent amused gaze, eyebrow expressiveness, and captivating refined presence to guide character performance. It is not a costume or hair-color reference.

CRITICAL GOAL:
The first, third and fourth people need THREE CLEARLY NEW FACIAL IDENTITIES. Do NOT keep their existing faces with wider cheeks, shorter chins, more fat, cosmetic retouching or tiny adjustments. Replace their actual facial casting: new eyes, brows, nose, mouth, facial proportions and acting. The prior result failed because it merely widened the same faces. This is a fresh casting pass of exactly those THREE faces, while preserving the original board and character designs.
The SECOND person, BRAN, must remain EXACTLY as he appears in Image 1. He is approved and must not be recast, retouched or beautified.

SELECTIVE EDITS:
1. AIDA, far left: retain her feminine identity, fair warm skin, age approximately 36 and EXACT champagne-blonde neck-length large waves. Give her a NEW distinctive sophisticated adult female face: expressive slightly arched eyebrows, perceptive almond-shaped eyes, a gracefully proportioned nose with a softly rounded tip, an articulate curved mouth with a defined cupid's bow, and a subtle asymmetric knowing half-smile. Her expression has the clever social confidence and slight teasing amusement visible in Image 3, adapted convincingly to a beautiful adult WOMAN. Naturally balanced oval proportions, living cheek volume and elegance without skeletal hollows, a pointed V chin or overfilled round cheeks. She must look like a different woman from Image 1, not a stretched version of the same face.
2. BRAN, second from left: LOCK THIS WHOLE PERSON TO IMAGE 1. Keep the exact face and expression, short black hair, dark stubble, head shape, skin, broad-shouldered body, pose, hands, indigo-gray armor, shield, clothing details and footwear unchanged. Do not apply Gale/Astarion references to him. Do not widen or shorten his face. Preserve his original approved appearance.
3. LAESA, third from left: retain feminine identity, fair skin, age approximately 27 and EXACT honey-blonde long large waves in a high ponytail with fine braids. Give her a NEW beautiful adult female face that is immediately distinct from both old LAESA and new AIDA: straighter defined eyebrows, more openly spaced clear eyes, a refined straight nose, a softly articulated wider mouth with a natural fuller lower lip, and a composed courageous expression with a trace of warmth. Balanced adult proportions with soft but structured cheek transitions, a graceful natural oval jaw and a proportionate chin. This is clear-eyed heroic beauty and confident presence, not a thin fashion-model face, doll face or a gender-swapped male reference. Her facial identity must visibly differ from AIDA in eyes, brows, nose, mouth and expression.
4. MOREN, far right: REPLACE the existing narrow long angular youthful face with a distinctly Gale-inspired handsome adult scholar's face, using Image 2 as an actual facial-structure reference, not just a vague mood. Closely follow Image 2's broad forehead and softly squared oval facial outline; substantial brows that run relatively level inside and rise slightly toward the outer ends; horizontal almond eyes with weight in the upper lids; naturally full midface; longer straight nose bridge with a rounded dimensional nose tip; a relatively broad mouth with a thinner upper lip and fuller lower lip; mouth corners and cheeks lifting together in a natural warm smile; and a broad rounded-square chin supported by short dark stubble. Use a proportionate strong jaw and natural chin rather than a pinched long V-shaped lower face. Short neatly trimmed dark facial stubble may echo the reference; no gray hair or elderly appearance. Keep approximately age 32-35. Shift the dark-brown medium-length hair into a Gale-like swept-back/half-tied arrangement around the temples with natural waves, maintaining dark brown color. This face must strongly and visibly reflect Image 2's handsome scholarly facial construction and be completely different from the old MOREN, while keeping MOREN's own ivory-gray/ink-blue outfit, copper lens staff, body and gesture.

LOCKED BOARD DETAILS:
Keep Image 1's exact four characters, order, full-body framing, positions, approximate head scale, bodies, limbs, poses, hands, feet, clothing, colors, equipment, materials, neutral opaque warm-beige canvas background, ground shadows and lighting. Only AIDA's face, LAESA's face, and MOREN's face plus allowed temple/half-tied hair arrangement may change. Never alter BRAN. Preserve all female blonde hairstyles and female practical fully covered costumes. All heads and boots remain fully visible and grounded. Keep the exact names "AIDA", "BRAN", "LAESA", "MOREN" with existing typography and placement.

RENDERING:
Keep the detailed premium realistic fantasy art and naturally textured skin of the board, with the convincing adult character acting seen in the references. Do not introduce the reference backgrounds, blue spell light, robes, weapons, vampire fangs, red eyes, white hair or pointed ears. All four remain human. No anime, dolls, plastic skin, exaggerated wide jaws, swollen cheeks, elderly features, extra people, extra labels or watermarks.
Output one opaque edited board. The success criteria are: BRAN visibly unchanged; three clearly recast and individually compelling faces; MOREN visibly anchored to the supplied Gale face; original character silhouettes and wardrobe preserved.
```

