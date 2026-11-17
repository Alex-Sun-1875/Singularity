"""Deterministic colour proposals from existing native captures; no runtime edits."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'examples'
OUT.mkdir(exist_ok=True)
REFERENCE = Path('C:/Users/Alexa/AppData/Local/Temp/codex-clipboard-5aa1e4e2-af3b-4222-9b80-1daf1ddec3b4.png')
PROFILES = [
    {'id': 'A', 'name': '熔金炽橙', 'note': '浓橙火身 · 明黄亮芯', 'recommend': True,
     'stops': ['#A72808', '#E84B06', '#FF7A0B', '#FFBB29', '#FFF18C'], 'gain': 1.18, 'gamma': 1.02},
    {'id': 'B', 'name': '赤焰熔芯', 'note': '赤红外焰 · 明暗反差更强', 'recommend': False,
     'stops': ['#721707', '#C93207', '#F45507', '#FF9F1A', '#FFE778'], 'gain': 1.18, 'gamma': 1.06},
    {'id': 'C', 'name': '琥珀金焰', 'note': '琥珀橙底 · 金黄亮纹', 'recommend': False,
     'stops': ['#9B3D07', '#D95C06', '#F98A0B', '#FFC544', '#FFF7A1'], 'gain': 1.14, 'gamma': .99},
]
SAMPLES = [
    {'id': 'FIR_02', 'name': '陨星天坠', 'detail': '地火与法阵',
     'path': 'source-art/skills/meteor-translucent-fill-v37/final-empty-r1/media/impact-0250ms.jpg', 'crop': [0, 390, 1140, 1190]},
    {'id': 'FIR_05', 'name': '焚焰火域', 'detail': '连续火面',
     'path': 'src/.tmp/fire-field-density-v38/after-stable/empty/045.png', 'crop': [133, 222, 575, 613]},
    {'id': 'FIR_01', 'name': '赤焰枪', 'detail': '集中亮芯与细焰',
     'path': 'source-art/skills/fire-reference-alignment-v32/regression-r1/media/FIR_01-projectile-native.jpg', 'crop': [895, 645, 1090, 728]},
    {'id': 'FIR_04', 'name': '烈焰喷流', 'detail': '喷焰与符纹',
     'path': 'src/.tmp/fire-distinct-runtime-v30/final-r1/FIR_04/045.jpg', 'crop': [985, 570, 1185, 790],
     'protect': [[1097,570],[1185,570],[1185,760],[1143,767],[1124,725],[1115,688],[1118,650],[1100,620]]},
    {'id': 'FIR_03', 'name': '焰心护盾', 'detail': '护罩边缘与纹样',
     'path': 'src/.tmp/fire-distinct-runtime-v30/final-r1/FIR_03/045.jpg', 'crop': [980, 390, 1325, 865],
     'protect': [[1138, 490], [1172, 495], [1201, 534], [1216, 580], [1200, 650], [1195, 719], [1191, 799], [1159, 822], [1117, 802], [1114, 757], [1138, 681], [1126, 623], [1100, 595], [1054, 566], [1040, 470], [1054, 468], [1085, 533], [1095, 535], [1126, 540]]},
]
rgb = lambda h: np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], dtype=float)
def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def grade(im, profile, sample):
    source = np.asarray(im.convert('RGB'), dtype=float)
    r, g, b = np.moveaxis(source, -1, 0)
    value = np.max(source, axis=2) / 255
    saturation = (np.max(source, axis=2) - np.min(source, axis=2)) / np.maximum(np.max(source, axis=2), 1)
    warm = (r >= g-2) * smooth((g - b - 2) / 26)
    warm *= smooth((saturation - .19) / .25) * smooth((value - .12) / .18)
    # Mask only warm effects. Keep the cool floor/grid unchanged; protect the
    # character inside the shield using a source-coordinate polygon.
    if sample.get('protect'):
        protected = Image.new('L', im.size)
        x, y = sample['crop'][:2]
        ImageDraw.Draw(protected).polygon([(px-x, py-y) for px, py in sample['protect']], fill=255)
        # The polygon also overlaps transparent fire in front of the boots.
        # Preserve the dark character pixels, while grading those bright flames.
        warm *= 1 - np.asarray(protected, dtype=float) / 255 * (value < .68)
    floor = np.median(source[(r < g) & (g > b)], axis=0)
    signal = np.maximum(source-floor, 0)
    # All skills use the same colour ramp. Source hue is deliberately discarded:
    # a formerly yellow jet and a formerly brown shield must both become orange.
    # A weighted luminance rank reserves yellow for the brightest fine filaments,
    # instead of preserving each old material's yellow/red distribution.
    luminance = signal @ np.array([.2126, .7152, .0722])
    bins = np.clip(np.round(luminance*4), 0, 1023).astype(int)
    weights = warm*smooth(np.max(signal, axis=2)/40)
    histogram = np.bincount(bins.ravel(), weights=weights.ravel(), minlength=1024)
    cdf = (np.cumsum(histogram)-histogram*.5)/max(histogram.sum(), 1)
    heat = cdf[bins]
    palette = np.array([rgb(h) for h in profile['stops']])
    knots = [0, .20, .90, .985, 1]
    target = np.stack([np.interp(heat, knots, palette[:, c]) for c in range(3)], axis=-1)
    signal_range = max(1, 255-floor[0])
    strength = np.clip(np.max(signal, axis=2)/signal_range, 0, 1)
    body_level = float(np.percentile(np.max(signal, axis=2)[weights > .5], 80))
    normalization = np.clip(195/max(body_level, 1), .85, 2)
    amplitude = signal_range*np.power(strength, profile['gamma'])*profile['gain']*normalization
    # Re-composite the shared saturated ramp over the sampled dark floor.
    # Simply adding the floor's blue to a hot pixel would wash orange into beige.
    coverage = np.clip(amplitude/signal_range, 0, 1)[..., None]
    target = floor*(1-coverage) + target*coverage
    target = np.clip(target, 0, 255)
    result = np.round(source * (1-warm[..., None]) + target * warm[..., None]).astype(np.uint8)
    unchanged = bool(np.array_equal(result[warm == 0], source.astype(np.uint8)[warm == 0]))
    return Image.fromarray(result), {'zeroMaskPixelsUnchanged': unchanged, 'maskedPixels': int(np.sum(warm > .01)), 'emissionNormalization': float(normalization), 'sourceHueDiscarded': True, 'sharedRampKnots': knots}

FONT = 'C:/Windows/Fonts/msyh.ttc'
SERIF = 'C:/Windows/Fonts/simsun.ttc'
def font(size, serif=False):
    return ImageFont.truetype(SERIF if serif else FONT, size)
def put(draw, xy, value, size=24, fill='#E8DEC9', serif=False):
    draw.text(xy, value, font=font(size, serif), fill=fill, stroke_width=0)
def contain(canvas, im, box, background='#27312E'):
    x, y, w, h = box
    canvas.paste(Image.new('RGB', (w, h), background), (x, y))
    resized = ImageOps.contain(im, (w, h), Image.Resampling.LANCZOS)
    canvas.paste(resized, (x+(w-resized.width)//2, y+(h-resized.height)//2))

sources, results, evidence = {}, {}, []
for sample in SAMPLES:
    file = ROOT / sample['path']
    sources[sample['id']] = Image.open(file).convert('RGB').crop(sample['crop'])
    sources[sample['id']].save(OUT / (sample['id']+'-original.png'))
    for profile in PROFILES:
        image, record = grade(sources[sample['id']], profile, sample)
        results[(profile['id'], sample['id'])] = image
        image.save(OUT / (profile['id']+'-'+sample['id']+'.png'))
        evidence.append({'option': profile['id'], 'skill': sample['id'], **record})

# Comparison board: same source, crop, proportions and flame density in every column.
W, LEFT, COL, GAP = 1664, 200, 456, 16
row_heights = [280, 248, 150, 230, 280]
HEADER, PALETTES, FOOTER = 160, 190, 74
H = HEADER+PALETTES+sum(row_heights)+FOOTER
board = Image.new('RGB', (W, H), '#161E1C')
d = ImageDraw.Draw(board)
put(d, (34, 20), '火系技能 / 统一配色候选', 35, serif=True)
put(d, (36, 75), '四技能共用同一色阶  ·  深橙外焰 → 亮橙火身 → 明黄亮芯', 23, '#CEB888')
put(d, (36, 113), '同一实景画面校色比较 · 选定后统一接入', 19, '#A6B0A7')
reference = Image.open(REFERENCE).convert('RGB').crop((430, 1410, 940, 1760))
reference.save(HERE / 'reference-crop.png')
contain(board, reference, (W-290, 18, 244, 108))
put(d, (W-280, 129), '你标出的参考火色', 16, '#CBB88E')
d.line((32, HEADER-1, W-32, HEADER-1), fill='#675338', width=1)
for column, profile in enumerate(PROFILES):
    x = LEFT+column*(COL+GAP)
    put(d, (x+8, HEADER+14), profile['id']+'  '+profile['name'], 31, serif=True)
    if profile['recommend']:
        d.rounded_rectangle((x+COL-76, HEADER+15, x+COL-8, HEADER+45), 5, fill='#51442C', outline='#A28A55')
        put(d, (x+COL-64, HEADER+18), '推荐', 19, '#F3D99E')
    put(d, (x+8, HEADER+62), profile['note'], 19, '#BAAA8F')
    sw = (COL-16)//5
    for i, shade in enumerate(profile['stops']):
        d.rectangle((x+8+i*sw, HEADER+103, x+8+(i+1)*sw-3, HEADER+130), fill=shade)
    put(d, (x+8, HEADER+139), '外焰', 16, '#9FA99F')
    put(d, (x+COL//2-20, HEADER+139), '火身', 16, '#9FA99F')
    put(d, (x+COL-46, HEADER+139), '亮芯', 16, '#9FA99F')

y = HEADER+PALETTES
for sample, row_h in zip(SAMPLES, row_heights):
    d.line((32, y, W-32, y), fill='#36423B', width=1)
    put(d, (36, y+22), sample['name'], 24, serif=True)
    put(d, (36, y+61), sample['detail'], 16, '#A9B19F')
    icon_name = 'rpg-fir-'+sample['id'][-2:]
    icon = ROOT / 'src/cocos/assets/resources/ui/combat-relief/hud-circular' / (icon_name+'.png')
    if icon.exists():
        im = Image.open(icon).convert('RGBA')
        im.thumbnail((66, 66), Image.Resampling.LANCZOS)
        board.paste(im, (38, y+100), im)
    for column, profile in enumerate(PROFILES):
        x = LEFT+column*(COL+GAP)
        contain(board, results[(profile['id'], sample['id'])], (x, y+12, COL, row_h-24))
    y += row_h
put(d, (36, y+20), '同一截图局部校色 · 图标沿用现有原色 · 配色仍为候选，尚未修改游戏资源', 19, '#AEB5A7')
board.save(HERE / 'fire-colour-options-A-B-C.png', optimize=True)

# Larger individual sheets make each option easy to inspect without shrinking the grid.
for profile in PROFILES:
    page = Image.new('RGB', (1180, 1130), '#161E1C')
    draw = ImageDraw.Draw(page)
    put(draw, (32, 22), profile['id']+'  '+profile['name'], 34, serif=True)
    put(draw, (33, 73), profile['note']+' · 配色候选示意', 22, '#C7B58B')
    for i, shade in enumerate(profile['stops']):
        draw.rectangle((34+i*124, 116, 151+i*124, 144), fill=shade)
    contain(page, results[(profile['id'], 'FIR_02')], (28, 179, 740, 520))
    contain(page, results[(profile['id'], 'FIR_03')], (788, 179, 364, 520))
    put(draw, (34, 706), '陨星天坠', 23, serif=True)
    put(draw, (796, 706), '焰心护盾', 23, serif=True)
    for i, skill in enumerate(['FIR_01', 'FIR_04', 'FIR_05']):
        sample = next(s for s in SAMPLES if s['id'] == skill)
        contain(page, results[(profile['id'], skill)], (28+i*382, 764, 360, 282))
        put(draw, (36+i*382, 1057), sample['name'], 23, serif=True)
    page.save(HERE / ('option-'+profile['id']+'.png'), optimize=True)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
record = {
    'status': 'design-options-awaiting-user-choice', 'runtimeModified': False,
    'method': 'deterministic masked RGB colour grading of existing native captures',
    'newGenerativeImages': False, 'referenceSha256': sha(REFERENCE), 'referenceCrop': [430, 1410, 940, 1760],
    'profiles': PROFILES,
    'sources': [{**s, 'sha256': sha(ROOT/s['path'])} for s in SAMPLES],
    'processing': {'shapeDensityTiming': 'same source frame and crop in each option', 'sharedColourContract': 'discard old skill hues; use one luminance-ranked ramp and normalized emission across all five effects', 'floorGrid': 'warm-colour mask excludes the cool floor/grid', 'shieldPlayer': 'dark character pixels protected inside source-coordinate polygons; bright foreground flame still graded', 'hudIcons': 'existing originals, not recoloured', 'runtimeValidation': 'not performed: candidates only'},
    'pixelChecks': evidence,
}
(HERE / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'board': str(HERE/'fire-colour-options-A-B-C.png'), 'pixels': board.size, 'profiles': [p['id'] for p in PROFILES], 'protectedPixelChecksPassed': all(r['zeroMaskPixelsUnchanged'] for r in evidence)}, ensure_ascii=False))
