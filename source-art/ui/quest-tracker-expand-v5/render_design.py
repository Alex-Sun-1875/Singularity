"""Compose both quest states using the supplied screenshot and existing skin.

No generation or game-code changes: this is a deterministic UI concept board.
"""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
FONT = ASSETS / 'rpg-serif-v2.ttf'
SOURCE = Image.open(HERE / 'reference-original.png').convert('RGBA')
INK = (237, 228, 203, 255)
GOLD = (185, 148, 86, 255)
MUTED = (175, 157, 133, 255)
LEFT, TOP, WIDTH = 177, 250, 537
COLLAPSED_H, EXPANDED_H = 104, 168
original_material = SOURCE.crop((280, 299, 560, 310))


def label(draw, x, y, value, size, color=INK, anchor='lm'):
    draw.text((x, y), value, font=ImageFont.truetype(str(FONT), size),
              fill=color, anchor=anchor)


def slice_border(width, height):
    src = Image.open(ASSETS / 'double-gold-frame-v6.png').convert('RGBA')
    edge = 48
    native_scale = .75 * width / 328
    ex = min(round(edge * native_scale), width // 2)
    ey = min(round(edge * native_scale), height // 2)
    sx, sy = (0, edge, src.width-edge, src.width), (0, edge, src.height-edge, src.height)
    dx, dy = (0, ex, width-ex, width), (0, ey, height-ey, height)
    out = Image.new('RGBA', (width, height))
    for iy in range(3):
        for ix in range(3):
            w, h = dx[ix+1]-dx[ix], dy[iy+1]-dy[iy]
            if w <= 0 or h <= 0:
                continue
            tile = src.crop((sx[ix], sy[iy], sx[ix+1], sy[iy+1]))
            out.alpha_composite(tile.resize((w, h), Image.Resampling.LANCZOS), (dx[ix], dy[iy]))
    return out


def panel(width, height):
    # Both states share the exact same material sampled from the original panel.
    out = Image.new('RGBA', (width+24, height+24))
    shadow = Image.new('RGBA', out.size)
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((9, 12, width+15, height+18), radius=35, fill=(5, 5, 4, 115))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(4)))
    mat = original_material.resize((width, height), Image.Resampling.BICUBIC)
    mask = Image.new('L', (width, height))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width-1, height-1), radius=33, fill=255)
    mat.putalpha(mask)
    out.alpha_composite(mat, (12, 12))
    out.alpha_composite(slice_border(width, height), (12, 12))
    return out


def quest(image, expanded, action='出发'):
    h = EXPANDED_H if expanded else COLLAPSED_H
    image.alpha_composite(panel(WIDTH, h), (LEFT-12, TOP-12))
    d = ImageDraw.Draw(image)
    cy = TOP + h/2
    # The navigation hit can fit 48 logical pixels at x=382..526; the text hit
    # ends at x=358, retaining an 8-logical-pixel gap at this screenshot scale.
    d.line((LEFT+376, cy-37, LEFT+376, cy+37), fill=(185, 148, 86, 105), width=1)
    label(d, LEFT+454, cy, action, 38, INK, 'mm')
    if expanded:
        label(d, LEFT+28, TOP+38, '断轮磨坊', 28, (216, 195, 145, 255))
        label(d, LEFT+27, TOP+84, '→', 34)
        label(d, LEFT+65, TOP+84, '夺回断轮磨坊', 36)
        label(d, LEFT+28, TOP+130, '35m · 固定守军 1', 28, MUTED)
    else:
        label(d, LEFT+24, cy, '→', 30)
        label(d, LEFT+65, cy, '夺回断轮磨坊', 33)
        label(d, LEFT+311, cy, '35m', 29, MUTED, 'mm')


# Remove only the old quest/red annotation footprint before composing the states.
clean = SOURCE.copy()
terrain = SOURCE.crop((0, 460, 1000, 682)).resize((1000, 640), Image.Resampling.BICUBIC)
mask = Image.new('L', terrain.size)
ImageDraw.Draw(mask).rectangle((65, 125, 885, 530), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(30))
ImageDraw.Draw(mask).rectangle((145, 205, 805, 453), fill=255)
clean.paste(terrain, (0, 0), mask)
# Protect every original status-frame pixel above the annotation footprint.
clean.paste(SOURCE.crop((170, 12, 721, 205)), (170, 12))
collapsed, expanded = clean.copy(), clean.copy()
quest(collapsed, False)
quest(expanded, True)
collapsed.convert('RGB').save(HERE / 'collapsed-game-v8.png')
expanded.convert('RGB').save(HERE / 'expanded-game-v8.png')

board = Image.new('RGBA', (1600, 1030), (22, 22, 20, 255))
d = ImageDraw.Draw(board)
label(d, 72, 56, '任务追踪 · 收起与展开', 44)
label(d, 74, 113, '同一套双层金属框与原版底色，宽度始终与头像区对齐', 24, MUTED)
label(d, 85, 171, '收起 · 单行常驻', 30, (216, 195, 145, 255))
label(d, 946, 171, '展开 · 紧凑三行', 30, (216, 195, 145, 255))
crop = (151, 8, 744, 522)
board.alpha_composite(collapsed.crop(crop), (73, 205))
board.alpha_composite(expanded.crop(crop), (934, 205))
d = ImageDraw.Draw(board)
d.line((800, 204, 800, 784), fill=(185, 148, 86, 80), width=1)
label(d, 86, 758, '目标、距离与寻路操作，保留更多场景空间', 23, MUTED)
label(d, 946, 758, '地点与进度使用小字，中间任务目标突出', 23, MUTED)
d.line((75, 807, 1525, 807), fill=(185, 148, 86, 105), width=1)
label(d, 800, 860, '点击任务区展开  /  再次点击收起', 29, INK, 'mm')
label(d, 800, 914, '出发、停止、继续保持独立；切换显示不启动寻路', 24, MUTED, 'mm')
label(d, 800, 990, 'UI设计稿 · 展开高度约72px降至56px · 原版材质与双层框', 22, (216, 195, 145, 255), 'mm')
output = HERE / 'design-review-v8.png'
board.convert('RGB').save(output)

manifest = {
    'source': 'reference-original.png',
    'sourceOriginalName': 'codex-clipboard-ef85b7b2-2c6f-4be0-97af-3da7e7212e5d.png',
    'method': 'Pillow deterministic layout and pixel composition; no new image generation',
    'assets': ['src/cocos/assets/resources/ui/quiet-bronze/double-gold-frame-v6.png',
               'src/cocos/assets/resources/ui/quiet-bronze/rpg-serif-v2.ttf'],
    'originalBackgroundPatch': [280, 299, 560, 310],
    'originalBackgroundMedianRGB': [32, 29, 26],
    'frame': {'sliceInsets': [48, 48, 48, 48], 'sharedSkinPixelScale': .75},
    'comparison': {'heroFrameLeft': LEFT, 'heroFrameWidth': WIDTH,
                   'questFrameLeft': LEFT, 'questFrameWidthBothStates': WIDTH,
                   'collapsedHeightInScreenshotPixels': COLLAPSED_H,
                   'expandedHeightInScreenshotPixels': EXPANDED_H},
    'behaviorIntent': ['task text area toggles expanded/collapsed',
                       'navigation action is independent',
                       'toggling display does not start or resume navigation'],
    'disclosureArrowsVisible': False,
    'revision': 'Reduce expanded location/progress font sizes to 28/28 screenshot pixels; preserve central objective size, compact panel geometry and collapsed state.',
    'expandedLayout': {'previousHeightInScreenshotPixels': 216,
                       'currentHeightInScreenshotPixels': 168,
                       'rowCenters': [38, 84, 130],
                       'previousFontSizes': [34, 36, 29],
                       'fontSizes': [28, 36, 28],
                       'heightReductionPercent': round((216-168)/216*100, 2)},
    'outputs': ['design-review-v8.png', 'collapsed-game-v8.png', 'expanded-game-v8.png'],
    'artReview': {'status': 'pending visual review', 'userApproved': False},
    'implementedInGame': False,
    'platformValidated': False,
    'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
}
(HERE / 'provenance-v8.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(output)
