"""Deterministic typography correction; no new generated scene pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'source-art/ui/cinematic-dialogue-v3/generation-raw.png'
FONT = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze/rpg-serif-v2.ttf'
SCALE = 3
WIDTH, HEIGHT = 2532, 1170
IVORY = '#EDE4CB'
GOLD = '#D1AA63'
CAPTION = '矛尖上是王冠，下面却压着一片龙翼。新爪痕全都背向群山。'

base = Image.open(SOURCE).convert('RGB')
assert base.size == (1844, 853), 'Patch coordinates require the recorded v3 native image.'

# Reuse clean ground at the same vertical position, preserving the existing gradient.
# Feather only the patch borders; all old lettering lies inside the opaque interior.
patches = [
    ((1605, 710, 1790, 793), (1400, 710)),  # clear continue before sampling this column
    ((1605, 55, 1790, 124), (1380, 55)),  # skip story
    ((260, 580, 1050, 807), (1040, 580)),  # complete old speaker/two-line block
]
for (left, top, right, bottom), (sx, sy) in patches:
    patch = base.crop((sx, sy, sx + right - left, sy + bottom - top))
    mask = Image.new('L', patch.size)
    ImageDraw.Draw(mask).rectangle((5, 5, patch.width - 6, patch.height - 6), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    base.paste(patch, (left, top), mask)

canvas = ImageOps.fit(base, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS).convert('RGBA')
measurements = {}


def glyph_mask(text, logical_size):
    font = ImageFont.truetype(str(FONT), round(logical_size * SCALE))
    box = font.getbbox(text)
    mask = Image.new('L', (box[2] - box[0] + 8, box[3] - box[1] + 8))
    ImageDraw.Draw(mask).text((4 - box[0], 4 - box[1]), text, font=font, fill=255)
    return mask.crop(mask.getbbox())


def paint_mask(mask, x, y, color, shadow=True):
    if shadow:
        alpha = Image.new('L', canvas.size)
        alpha.paste(mask, (x, y + 2))
        alpha = alpha.filter(ImageFilter.GaussianBlur(2))
        shade = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        shade.putalpha(alpha.point(lambda a: round(a * .88)))
        canvas.alpha_composite(shade)
    canvas.paste(color, (x, y), mask)
    return [x, y, x + mask.width, y + mask.height]


def text_at(name, text, size, cx, cy, color):
    mask = glyph_mask(text, size)
    x, y = round(cx * SCALE - (mask.width - 1) / 2), round(cy * SCALE - (mask.height - 1) / 2)
    measurements[name] = {'text': text, 'logicalFontSize': size, 'inkBoundsPx': paint_mask(mask, x, y, color)}


# Original centered typography: same project serif, 14px speaker and 18px single-line caption.
text_at('speaker', '拉斐尔', 14, 422, 274, GOLD)
text_at('caption', CAPTION, 18, 422, 323, IVORY)
text_at('skip', '跳过剧情', 13, 779, 38, IVORY)

# The arrow is geometry rather than a font glyph. Match parity for exact pixel centers.
text_mask = glyph_mask('继续', 13)
arrow_height = round(text_mask.height * .78)
if arrow_height % 2 != text_mask.height % 2:
    arrow_height += 1
arrow_width, stroke, aa = round(6 * SCALE), round(SCALE), 4
arrow = Image.new('L', ((arrow_width + 8) * aa, (arrow_height + 8) * aa))
draw = ImageDraw.Draw(arrow)
draw.line([(4 * aa, 4 * aa), ((arrow_width + 4) * aa, (arrow_height / 2 + 4) * aa), (4 * aa, (arrow_height + 4) * aa)], fill=255, width=stroke * aa, joint='curve')
arrow = arrow.resize((arrow_width + 8, arrow_height + 8), Image.Resampling.LANCZOS)
arrow = arrow.crop(arrow.getbbox()).resize((arrow_width, arrow_height), Image.Resampling.LANCZOS)
gap = 8 * SCALE
group_width = text_mask.width + gap + arrow.width
left = round(779 * SCALE - (group_width - 1) / 2)
text_y = round(342 * SCALE - (text_mask.height - 1) / 2)
center_y = text_y + (text_mask.height - 1) / 2
arrow_y = round(center_y - (arrow.height - 1) / 2)
text_box = paint_mask(text_mask, left, text_y, GOLD)
arrow_box = paint_mask(arrow, left + text_mask.width + gap, arrow_y, GOLD)
delta = abs((text_box[1] + text_box[3] - 1) / 2 - (arrow_box[1] + arrow_box[3] - 1) / 2)
assert delta == 0, delta
measurements['continue'] = {'text': '继续', 'logicalFontSize': 13, 'inkBoundsPx': text_box}
measurements['arrow'] = {'inkBoundsPx': arrow_box, 'drawnGeometry': True, 'centerDeltaPx': delta, 'gapLogicalPx': gap / SCALE}

final = HERE / 'cinematic-dialogue-proposal-v4.png'
canvas.convert('RGB').save(final)
preview = HERE / 'preview.jpg'
canvas.convert('RGB').resize((1266, 585), Image.Resampling.LANCZOS).save(preview, quality=92)
detail_box = (left - 36, text_y - 35, arrow_box[2] + 36, text_box[3] + 35)
detail = canvas.convert('RGB').crop(detail_box).resize(((detail_box[2] - detail_box[0]) * 3, (detail_box[3] - detail_box[1]) * 3), Image.Resampling.NEAREST)
detail.save(HERE / 'continue-detail.png')

report = {
    'date': '2026-11-15',
    'status': 'revised_design_proposal_not_integrated',
    'userCorrection': 'Restore original font sizes and centered layout; correct continue/arrow alignment.',
    'method': 'Local deterministic Pillow pixel patches and bundled-font typography; no new cloud generation.',
    'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
    'font': str(FONT.relative_to(ROOT)).replace('\\', '/'),
    'layoutReference': 'src/cocos/assets/scripts/features/cinematics/common/CinematicLayout.ts',
    'size': [WIDTH, HEIGHT],
    'logicalReference': [844, 390],
    'measurements': measurements,
    'checks': {'continueArrowInkCenterDeltaPx': delta, 'captionOneLine': True, 'speakerAndCaptionCentered': True, 'noCrownOrSpeakerStroke': True},
    'sha256': hashlib.sha256(final.read_bytes()).hexdigest(),
    'userAcceptance': 'pending',
    'engineIntegration': False,
    'runtimeVerification': False,
    'limitations': ['Reused generated scene remains a design backdrop.', 'Actual runtime baseline and touch/safe-area validation require implementation.']
}
(HERE / 'provenance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'saved': str(final), 'fontSizesLogical': [14, 18, 13], 'continueArrowCenterDeltaPx': delta, 'measurements': measurements}, ensure_ascii=False))
