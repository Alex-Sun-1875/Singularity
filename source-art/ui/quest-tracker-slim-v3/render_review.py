"""Lay out the review mock with the existing public frame art and RPG font.

This deterministic composition is a concept board, not a Cocos implementation.
"""
from pathlib import Path
import json
import hashlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
FONT = ASSETS / 'rpg-serif-v2.ttf'
IVORY = (229, 219, 191, 255)
GOLD = (218, 174, 101, 255)
MUTED = (194, 163, 122, 255)


def nine_slice(name, width, height, pixel_scale):
    source = Image.open(ASSETS / name).convert('RGBA')
    edge = 48
    out_edge = round(edge * pixel_scale)
    result = Image.new('RGBA', (width, height))
    sx = (0, edge, source.width - edge, source.width)
    sy = (0, edge, source.height - edge, source.height)
    dx = (0, out_edge, width - out_edge, width)
    dy = (0, out_edge, height - out_edge, height)
    for iy in range(3):
        for ix in range(3):
            size = (dx[ix + 1] - dx[ix], dy[iy + 1] - dy[iy])
            if min(size) <= 0:
                continue
            tile = source.crop((sx[ix], sy[iy], sx[ix + 1], sy[iy + 1]))
            result.alpha_composite(tile.resize(size, Image.Resampling.LANCZOS), (dx[ix], dy[iy]))
    return result


def frame(width, height):
    # Mirrors DoubleGoldFrame's panel assets, native 48px slices, .75 skin scale,
    # rounded base and layered shadow. 328 design units match the hero HUD width.
    ratio = width / 328
    skin_scale = .75 * ratio
    result = Image.new('RGBA', (width + 20, height + 20))
    draw = ImageDraw.Draw(result)
    radius = 26 * skin_scale
    for spread, alpha in ((6, 14), (4, 22), (2, 36)):
        spread *= skin_scale
        draw.rounded_rectangle((10-spread, 10-spread+2*skin_scale,
                                width+10+spread, height+10+spread+2*skin_scale),
                               radius=radius+spread, fill=(12, 9, 7, alpha))
    draw.rounded_rectangle((10, 10, width+10, height+10), radius=radius,
                           fill=(18, 18, 16, 248))
    for asset in ('double-gold-inset-v6.png', 'double-gold-frame-v6.png'):
        result.alpha_composite(nine_slice(asset, width, height, skin_scale), (10, 10))
    return result


def text(draw, pos, value, size, fill=IVORY, anchor='lm'):
    draw.text(pos, value, font=ImageFont.truetype(str(FONT), size), fill=fill,
              anchor=anchor, stroke_width=0)


def quest(board, x, y, action='出发', expanded=False):
    width, row_h = 333, 78
    height = 158 if expanded else row_h
    board.alpha_composite(frame(width, height), (x-10, y-10))
    draw = ImageDraw.Draw(board)
    cy = y + row_h / 2
    text(draw, (x+16, cy), '夺回断轮磨坊', 23)
    text(draw, (x+192, cy), '35m', 20, MUTED, 'mm')
    divider_x = x + 233
    draw.line((divider_x, cy-15, divider_x, cy+15), fill=(185, 148, 86, 110), width=1)
    text(draw, (x+283, cy), action, 23, GOLD, 'mm')
    if expanded:
        draw.line((x+16, y+row_h, x+width-16, y+row_h), fill=(185, 148, 86, 75), width=1)
        text(draw, (x+17, y+99), '断轮磨坊 · 第1/2阵', 20, MUTED)
        text(draw, (x+17, y+125), '固定守军 1', 20, IVORY)


source = Image.open(HERE / 'design-draft-02.png').convert('RGBA')
board = Image.new('RGBA', (1586, 1120), (32, 29, 25, 255))
board.alpha_composite(source.crop((0, 0, 1586, 774)))

# Replace only the obsolete task-strip patch with nearby empty terrain. The
# public skin and type below are composed directly; no new generated art here.
box = (102, 205, 515, 304)
terrain = source.crop((102, 300, 515, 399))
mask = Image.new('L', terrain.size)
ImageDraw.Draw(mask).rectangle((4, 4, terrain.width-5, terrain.height-5), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))
board.paste(terrain, box[:2], mask)
quest(board, 112, 218)

# Rebuild the explanatory footer with the same exact frame assets and no arrows.
draw = ImageDraw.Draw(board)
draw.rectangle((0, 774, 1585, 1119), fill=(32, 29, 25, 255))
draw.line((4, 774, 1581, 774), fill=(159, 132, 83, 200), width=1)
for x in (532, 1051):
    draw.line((x, 805, x, 1024), fill=(159, 132, 83, 120), width=1)
for x, title in ((100, '常驻状态'), (607, '点击任务名展开'), (1122, '寻路暂停')):
    text(draw, (x, 803), title, 25, (233, 210, 163, 255))
quest(board, 100, 839)
quest(board, 607, 839, expanded=True)
quest(board, 1122, 839, action='继续')
draw = ImageDraw.Draw(board)
text(draw, (111, 947), '只留目标、距离与操作', 20)
text(draw, (619, 1025), '点击空白收起', 20)
text(draw, (1133, 947), '出发 / 停止 / 继续，位置固定', 20)
draw.line((42, 1062, 1544, 1062), fill=(159, 132, 83, 150), width=1)
text(draw, (793, 1090), '公共双层框 · 与头像框等宽 · 可见高度42px / 点击48px · UI概念稿',
     20, (233, 210, 163, 255), 'mm')

output = HERE / 'design-review-v3.png'
board.convert('RGB').save(output)
manifest = {
    'generation': {
        'tool': 'OpenAI image_gen (cloud)',
        'drafts': ['design-draft-01.png', 'design-draft-02.png'],
        'sourceReference': 'codex-clipboard-df525d46-7ef8-4d10-8b7a-9cc38786159e.png',
        'promptRecord': 'prompt-notes.md',
        'result': 'generated successfully',
    },
    'composition': {
        'tool': 'Pillow, deterministic layout and pixel composition',
        'output': output.name,
        'sharedComponent': 'src/cocos/assets/scripts/shared/ui/DoubleGoldFrame.ts',
        'sharedAssets': ['double-gold-frame-v6.png', 'double-gold-inset-v6.png', 'rpg-serif-v2.ttf'],
        'skinScale': .75,
        'sliceInsetsNativePixels': [48, 48, 48, 48],
        'heroAndQuestFrameWidthInBoardPixels': 333,
        'questFrameHeightInBoardPixels': 78,
        'intendedLogicalHeight': 42,
        'intendedTouchSize': 48,
        'arrowRemoved': True,
    },
    'artReview': {
        'status': 'visual layout reviewed; user review pending',
        'checks': ['quest frame aligns with hero frame at x=112, width=333',
                   'main task strip and footer variants have no leading arrow',
                   'exact shared frame/inset textures and RPG font reused',
                   'single-line target, distance and action fit without overlap',
                   'expanded progress has bottom padding'],
        'userApproved': False,
        'implementedInGame': False,
        'platformValidated': False,
    },
    'outputSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
}
(HERE / 'provenance.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(output)
