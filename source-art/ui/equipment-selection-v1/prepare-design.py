"""Deterministic candidate UI artwork; does not change runtime assets."""
from pathlib import Path
import json
import base64
import shutil
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ASSETS = OUT / 'assets'
ASSETS.mkdir(exist_ok=True)
SKIN = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
THREAD = Path('C:/Users/Alexa/.codex/visualizations/2026/11/17/01a1e853-dfaa-7992-913a-6822bff2eef8')

def neutralize(source, destination):
    im = Image.open(source).convert('RGBA')
    pixels = np.array(im).astype(float)
    rgb = pixels[:, :, :3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    # Preserve the warm metal and leather; steel is already close to neutral.
    # Non-metal colored smoke is muted to charcoal with unchanged geometry/alpha.
    lum = r * .299 + g * .587 + b * .114
    warm_metal = (r > g * 1.15) & (g > b * 1.25) & (lum > 55)
    strength = (~warm_metal) * .97
    bronze = np.stack([lum * 1.03, lum * .98, lum * .90], axis=-1)
    pixels[:, :, :3] = rgb * (1 - strength[:, :, None]) + bronze * strength[:, :, None]
    result = Image.fromarray(np.clip(pixels, 0, 255).astype('uint8'))
    result.save(destination, optimize=True)
    return result

common = neutralize(SKIN / 'prep-item-sword-v2.png', ASSETS / 'common-sword-neutral.png')
steel = neutralize(SKIN / 'prep-item-steel-sword-v5.png', ASSETS / 'steel-sword-neutral.png')
inspect = neutralize(SKIN / 'prep-inspect-sword-v2.png', ASSETS / 'inspect-sword-neutral.png')
shutil.copy2(SKIN / 'prep-socket-v5.png', ASSETS / 'socket-base.png')

IVORY = '#EDE4CB'
QUALITY = {'普通': '#AF9D85', '稀有': '#83CDE6', '史诗': '#C4A5ED', '传奇': '#F5A45D'}
FONT = 'C:/Windows/Fonts/simsun.ttc'
UIFONT = 'C:/Windows/Fonts/msyh.ttc'

def font(size, sans=False):
    return ImageFont.truetype(UIFONT if sans else FONT, size)

def tile(size=220, selected=False, equipped=False, quality='普通', art=common, mode='corners'):
    im = Image.new('RGBA', (size, size), (0,0,0,0))
    d = ImageDraw.Draw(im)
    margin = max(3, round(size * .035))
    d.rounded_rectangle((margin, margin, size-margin-1, size-margin-1), radius=size*.09,
                        fill='#17120F', outline=QUALITY[quality], width=max(1, size//130))
    factor = min(size*.89/art.width,size*.89/art.height)
    image = art.resize((round(art.width*factor),round(art.height*factor)),Image.Resampling.LANCZOS)
    im.alpha_composite(image, ((size-image.width)//2, (size-image.height)//2))
    d = ImageDraw.Draw(im)
    if selected:
        if mode == 'corners':
            a, b, length = margin+1, size-margin-2, int(size*.15)
            corners = Image.new('RGBA',im.size)
            cd = ImageDraw.Draw(corners)
            cd.rounded_rectangle((a,a,b,b),radius=size*.075,outline=IVORY,width=max(2,size//100))
            corner_mask = Image.new('L',im.size)
            md = ImageDraw.Draw(corner_mask)
            for box in [(0,0,a+length,a+length),(b-length,0,size,a+length),
                        (0,b-length,a+length,size),(b-length,b-length,size,size)]:
                md.rectangle(box,fill=255)
            im.paste(corners,(0,0),Image.fromarray(np.minimum(np.array(corners.getchannel('A')),np.array(corner_mask))))
            d = ImageDraw.Draw(im)
        else:
            d.rounded_rectangle((margin,margin,size-margin-1,size-margin-1), radius=size*.09,
                                outline=IVORY, width=max(2,size//100))
            cx, cy, r = size/2, margin+2, size*.025
            d.polygon([(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)], fill=IVORY)
    if equipped:
        x0, x1, y0, y1 = size*.23, size*.77, size*.80, size*.96
        d.rounded_rectangle((x0,y0,x1,y1), radius=3, fill='#18302B', outline='#507D70', width=1)
        d.text((size/2,(y0+y1)/2), '已穿戴', font=font(round(size*.095)), fill='#A4C2B0', anchor='mm')
    return im

# State matrix is intentionally a component study, not a running-game screenshot.
board = Image.new('RGB', (1600, 960), '#15100D')
d = ImageDraw.Draw(board)
d.text((70, 50), '装备选中态 · 象牙白角标', font=font(46), fill=IVORY)
d.text((70, 113), '候选设计  /  选中、品质、穿戴分别表达', font=font(24, True), fill='#B6A58E')
d.line((70,168,1530,168), fill='#665037', width=1)
labels = [('默认',False,False),('选中',True,False),('已穿戴',False,True),('选中 + 已穿戴',True,True)]
for index,(label,selected,equipped) in enumerate(labels):
    x = 138 + index * 355
    board.paste(tile(260,selected,equipped), (x,215), tile(260,selected,equipped))
    d.text((x+130,512),label,font=font(29),fill=IVORY,anchor='mm')
d.line((70,566,1530,566),fill='#443225',width=1)
d.text((70,600),'品质叠加示意',font=font(28),fill=IVORY)
for index,quality in enumerate(QUALITY):
    x = 170 + index * 355
    t = tile(190,True,False,quality)
    board.paste(t, (x,655), t)
    d.text((x+95,875),quality,font=font(25),fill=QUALITY[quality],anchor='mm')
d.text((1530,925),'设计稿 · 未接入游戏',font=font(19,True),fill='#AF9D85',anchor='rm')
board.save(OUT / 'selection-state-board.png', optimize=True)

spec = {
    'status': 'candidate_pending_user_review',
    'date': '2026-11-17',
    'scope': 'Equipment selection state only; no runtime or game-rule changes.',
    'recommended': 'ivory-corner-brackets',
    'colors': {'selectionCandidate': IVORY, 'equippedText': '#A4C2B0',
               'equippedSurface': '#18302B', 'qualityExisting': QUALITY},
    'geometryLogical': {'selectionStroke': 1.5, 'cornerLength': 10,
                        'inset': 1.5, 'qualityStroke': 0.75},
    'rules': [
        'Selection adds four ivory corner brackets and a very subtle neutral inset.',
        'Selection never adds a gold skin, changes quality color, scales art, or loops a glow.',
        'Worn sockets show quiet base frames; selection in the bag does not light the worn socket.',
        'An explicit socket filter uses the same selection geometry only while that socket is active.',
        'Equipped remains a compact text badge independent of selection.',
        'Common weapon art uses deterministic smoke neutralization; weapon silhouette is preserved.',
        'Rarity previews are labeled demonstrations, not new item definitions.',
        'Default UI touch requirements remain 48 logical pixels and 8-pixel separation.',
        'On implementation, centralize semantics in FeedbackPalette and EquipmentIconFrame; do not redefine the global selected token.'
    ],
    'sourceAssets': [str((SKIN/n).relative_to(ROOT)) for n in [
        'prep-item-sword-v2.png','prep-item-steel-sword-v5.png',
        'prep-inspect-sword-v2.png','prep-socket-v5.png']],
    'method': 'Pillow/NumPy deterministic composition. No generative edits or new model assets.',
    'validation': {'generation': 'complete', 'artReview': 'pending_user',
                   'runtimeIntegration': 'not_started', 'tapTapDevice': 'not_started'}
}
(OUT / 'design-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def data(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')

template = (OUT / 'selection-preview.template.html').read_text(encoding='utf-8')
for key, path in {'COMMON':ASSETS/'common-sword-neutral.png', 'STEEL':ASSETS/'steel-sword-neutral.png',
                  'INSPECT':ASSETS/'inspect-sword-neutral.png', 'SOCKET':ASSETS/'socket-base.png'}.items():
    template = template.replace('{{'+key+'}}',data(path))
(THREAD/'equipment-selection.html').write_text(template,encoding='utf-8')
print(json.dumps({'board':str(OUT/'selection-state-board.png'),'preview':str(THREAD/'equipment-selection.html'),
                  'previewBytes':len(template.encode('utf-8'))},ensure_ascii=False))
