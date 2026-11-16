"""Deterministic review-sheet composition. No game resources or code are modified."""
from pathlib import Path
from shutil import copy2
import math
import json
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RAW = Path(r'C:\Users\Alexa\.codex\generated_images\01a1e07a-ae0c-79f3-83e9-6d9363988a5b')
FONT = r'C:\Windows\Fonts\msyh.ttc'
BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
RESAMPLE = Image.Resampling.LANCZOS
(OUT / 'derived').mkdir(exist_ok=True)
copy2(RAW / 'exec-72e45fa5-dc9c-4829-ae32-b65174ae12b1.png', OUT / '01-four-class-direction.png')

# Extract only the orange/ivory linework from the generated pattern study.
# This derivative is for static mockup composition, not an approved runtime texture.
sheet = Image.open(OUT / '02-patterns-and-states.png').convert('RGB')
crop = sheet.crop((81, 137, 501, 557))
pattern = Image.new('RGBA', crop.size)
pixels = []
for y in range(crop.height):
    for x in range(crop.width):
        r, g, b = crop.getpixel((x, y))
        dist = math.hypot(x - 209, y - 209)
        strength = max(0, r - .75 * g - .25 * b - 25)
        alpha = min(235, int(strength * 4.4)) if r > 110 and dist < 207 else 0
        pixels.append((min(255, r + 25), min(255, int(g * 1.10)), b, alpha))
pattern.putdata(pixels)
pattern.save(OUT / 'derived/fire-pattern-review-only.png')

base = Image.open(ROOT / 'src/cocos/test-results/enemy-no-ranges/real-enemy-field-844x390.png').convert('RGBA')
fire_hud = Image.open(ROOT / 'src/cocos/test-results/attack-skill-gap-48/FIR-844x390.png').convert('RGBA')
# Reuse existing fire-class HUD pixels at the same physical pixel coordinates.
stat_mask = Image.new('L', base.size)
ImageDraw.Draw(stat_mask).rounded_rectangle((19,20,550,207),radius=25,fill=255)
base.paste(fire_hud,(0,0),stat_mask)
layout = json.loads((ROOT/'src/cocos/test-results/attack-skill-gap-48/layout-validation.json').read_text(encoding='utf-8'))
fire_layout = next(v for v in layout['views'] if v['family']=='FIR' and v['width']==844)
controls = {c['action']:(round(c['x']*3),round(c['y']*3),round(c['face']*1.5)-2) for c in fire_layout['controls']}
centres = [(x,y) for x,y,r in controls.values()]
for x, y, radius in controls.values():
    box = (x-radius, y-radius, x+radius, y+radius)
    tile = fire_hud.crop(box)
    mask = Image.new('L', tile.size)
    ImageDraw.Draw(mask).ellipse((1, 1, tile.width-2, tile.height-2), fill=255)
    base.paste(tile, (box[0], box[1]), mask)

# Proposed visual slot swap: meteor to the existing rightmost ultimate, fire sea to ordinary slot 2.
# This only swaps screenshot icon interiors, not actual skill bindings.
def swap_icon(destination, source):
    radius = 60
    sx, sy = source
    dx, dy = destination
    tile = fire_hud.crop((sx-radius, sy-radius, sx+radius, sy+radius))
    mask = Image.new('L', tile.size)
    ImageDraw.Draw(mask).ellipse((0, 0, tile.width-1, tile.height-1), fill=255)
    base.paste(tile, (dx-radius, dy-radius), mask)

swap_icon(controls['ultimate'][:2], controls['combat1'][:2])
swap_icon(controls['combat1'][:2], controls['ultimate'][:2])

def place_pattern(canvas, opacity):
    ellipse = pattern.resize((720, 360), RESAMPLE)
    ellipse.putalpha(ellipse.getchannel('A').point(lambda a: int(a * opacity)))
    canvas.alpha_composite(ellipse, (1290, 155))
    # Keep the photographed enemy in front of the ground decal.
    protect = Image.new('L', canvas.size)
    ImageDraw.Draw(protect).polygon([(1645,32),(1705,23),(1724,80),(1710,104),(1741,135),(1745,187),(1773,223),(1749,242),(1706,216),(1679,225),(1634,219),(1632,204),(1658,180),(1639,135),(1628,119),(1645,89)], fill=255)
    canvas.paste(base, (0, 0), protect)

aim = base.copy()
place_pattern(aim, .86)
aim.convert('RGB').save(OUT / '03a-player-meteor-aim.png')

descent = base.copy()
place_pattern(descent, 1.0)
comet = Image.open(ROOT / 'source-art/skills/fire-comet-v10/generated-comet.png').convert('RGBA').resize((540, 180), RESAMPLE)
angle = -49
rotated = comet.rotate(angle, Image.Resampling.BICUBIC, expand=True)
theta = math.radians(-angle)
# Anchor the rounded head to the same ground point as the targeting pattern.
headx = rotated.width / 2 + .40 * comet.width * math.cos(theta)
heady = rotated.height / 2 + .40 * comet.width * math.sin(theta)
descent.alpha_composite(rotated, (round(1650-headx), round(335-heady)))
# Preserve existing screen-edge HUD exactly even when world effects pass behind it.
protect_hud = Image.new('L', descent.size)
hud_draw = ImageDraw.Draw(protect_hud)
hud_draw.rectangle((0, 0, 560, 340), fill=255)
hud_draw.rounded_rectangle((1045, 45, 1485, 132), radius=45, fill=255)
hud_draw.rectangle((2000, 0, 2531, 485), fill=255)
for x,y in centres:
    radius = 118 if (x,y)==controls['attack'][:2] else 87
    hud_draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
descent.paste(base, (0, 0), protect_hud)
descent.convert('RGB').save(OUT / '03b-player-meteor-descent.png')

board = Image.new('RGB', (1600, 1848), '#211a15')
d = ImageDraw.Draw(board)
gold = '#e7c68a'
cream = '#d8cbb7'
def text(x, y, value, size, fill=cream, bold=False):
    d.text((x,y), value, font=ImageFont.truetype(BOLD if bold else FONT,size), fill=fill)
text(42,24,'陨石终极 · 横屏实景合成稿',40,gold,True)
text(42,88,'844×390 逻辑视口｜保留现有七按钮布局｜静态示意，尚未接入',21)
text(42,137,'A  施放前：全盘火纹标示落点',27,gold,True)
text(42,952,'B  终极释放：锁定落点，陨火沿目标坠下',27,gold,True)
for im,y in [(aim,183),(descent,998)]:
    display = im.convert('RGB').resize((1516,700),RESAMPLE)
    board.paste(display,(42,y))
    d.rectangle((41,y-1,1558,y+700),outline='#947a4d',width=2)
text(42,895,'外圈保持清晰；火纹贯穿圈内，纹路之间仍可观察地面与目标。',22)
text(42,1712,'陨石拟移至右上终极位；原火海拟移至普通进阶槽。数值与玩法未改。',22)
d.line((42,1771,1558,1771),fill='#745c38',width=1)
text(42,1790,'实景底图 + 云端纹样 + 既有陨火素材的本地合成；不是游戏运行截图或动画验收。',20)
board.save(OUT / '03-mobile-ui-proposal.png')

# Compact contact sheet for the delivery index.
overview = Image.new('RGB',(1600,740),'#211a15')
od = ImageDraw.Draw(overview)
od.text((28,18),'剑与火｜四职业特效与技能范围圈 · 首版提案',font=ImageFont.truetype(BOLD,30),fill=gold)
for name,box in [('01-four-class-direction.png',(24,83,796,598)),('02-patterns-and-states.png',(804,83,1576,598))]:
    im=Image.open(OUT/name).convert('RGB').resize((772,515),RESAMPLE)
    overview.paste(im,(box[0],box[1]))
od.text((28,626),'01 四职业特效方向    02 范围圈纹样与状态    03 现有HUD内的陨石终极合成稿',font=ImageFont.truetype(FONT,25),fill=cream)
od.text((28,678),'2026-11-16 · 静态设计候选 · 待用户审阅 · 未改游戏代码或资源',font=ImageFont.truetype(FONT,21),fill=cream)
overview.save(OUT/'00-review-index.jpg',quality=94)
print('Saved design boards and two 2532x1170 static UI composites.')
