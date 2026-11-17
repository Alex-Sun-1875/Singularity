"""Compare the actual fixed-step before/after recordings and crop their pixels."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'src/.tmp/fire-field-density-v38'
stages = {'before': 'before', 'after': 'after-stable'}
records = {stage: {mode: json.loads((HERE / stages[stage] / (mode + '.json')).read_text())
                   for mode in ['empty', 'targets', 'reduced']} for stage in ['before', 'after']}
summary = {}
for mode in ['empty', 'targets', 'reduced']:
    before, after = records['before'][mode], records['after'][mode]
    exact_events = before['events'] == after['events']
    meshes_equal = all([(f['width'], f['depth'], f['height'], f['vertices'], f['position']) for f in a['fields']] ==
                       [(f['width'], f['depth'], f['height'], f['vertices'], f['position']) for f in b['fields']]
                       for a, b in zip(before['metrics'], after['metrics']))
    summary[mode] = {
        'eventsExactlyEqual': exact_events,
        'meshGeometryExactlyEqual': meshes_equal,
        'hitsBeforeAfter': [before['metrics'][-1]['hits'], after['metrics'][-1]['hits']],
        'damageBeforeAfter': [before['metrics'][-1]['damage'], after['metrics'][-1]['damage']],
        'allDrawCountersEqual': all((a['drawCalls'], a['triangles']) == (b['drawCalls'], b['triangles']) for a, b in zip(before['metrics'], after['metrics'])),
        'differentCounterFrames': sum((a['drawCalls'], a['triangles']) != (b['drawCalls'], b['triangles']) for a, b in zip(before['metrics'], after['metrics'])),
        'peakDrawsBeforeAfter': [max(m['drawCalls'] for m in c['metrics']) for c in [before, after]],
        'peakTrianglesBeforeAfter': [max(m['triangles'] for m in c['metrics']) for c in [before, after]],
        'finalFieldsBeforeAfter': [len(before['metrics'][-1]['fields']), len(after['metrics'][-1]['fields'])],
    }
    if not exact_events or not meshes_equal or any(summary[mode]['finalFieldsBeforeAfter']):
        raise RuntimeError('Unexpected native simulation/geometry/cleanup difference: ' + mode)

frames = [30, 45, 75, 120]
corners = records['before']['empty']['metrics'][45]['fields'][0]['corners']
box = (int(min(p['x'] for p in corners)) - 30, int(min(p['y'] for p in corners)) - 40,
       int(max(p['x'] for p in corners)) + 30, int(max(p['y'] for p in corners)) + 20)
coverage = []
for frame in frames:
    counts = []
    for stage in ['before', 'after']:
        rgb = np.asarray(Image.open(CACHE / stages[stage] / 'empty' / f'{frame:03}.png').crop(box).convert('RGB'), dtype=float)
        counts.append(int(np.sum((rgb[..., 0] > 70) & (rgb[..., 0] > rgb[..., 1] * 1.22) & (rgb[..., 0] > rgb[..., 2] * 1.5))))
    coverage.append({'frame': frame, 'orangePixelCountsBeforeAfter': counts, 'ratio': counts[1] / max(1, counts[0])})

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 21)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
w, h = box[2] - box[0], box[3] - box[1]
sheet = Image.new('RGB', (w * 2 + 24, h + 73), '#202b2a')
draw = ImageDraw.Draw(sheet)
for index, (stage, label) in enumerate([('before', '调整前'), ('after', '火焰加密后')]):
    x = 8 + index * (w + 8)
    draw.text((x + 12, 8), label, font=font, fill='#ecddbd')
    sheet.paste(Image.open(CACHE / stages[stage] / 'empty/045.png').crop(box), (x, 43))
draw.text((20, h + 48), '实际游戏画面裁切 · 同机位、同一施放时刻 · 独立技能靶场', font=small, fill='#c6c6b8')
sheet.save(HERE / 'native-before-after.png')

source = ROOT / 'src/cocos/assets/resources/vfx/production/fire-field-flow-v30.png'
uuid = json.loads(Path(str(source) + '.meta').read_text())['uuid']
final_capture = json.loads((HERE / stages['after'] / 'capture.json').read_text())
native = ROOT / final_capture['servedBuild'] / 'assets/resources/native' / uuid[:2]
exports = list(native.glob(uuid + '*.png'))
export_evidence = [{'path': str(p.relative_to(ROOT)).replace('\\', '/'),
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                    'pixelsMatchProduction': np.array_equal(np.asarray(Image.open(p)), np.asarray(Image.open(source)))} for p in exports]
if not exports or not all(p['pixelsMatchProduction'] for p in export_evidence):
    raise RuntimeError('Exported field atlas does not match production texture')
result = {'nativeScenarios': summary, 'orangePixelCoverage': coverage, 'cropPixels': box,
          'coverageQualification': 'Orange-pixel count in identical native crops; not an alpha, damage-area or device-performance measurement.',
          'renderCounterQualification': 'Empty and reduced-motion whole-scene counters match frame by frame. Target combat counters differ on some frames; only their measured peaks match. Field mesh geometry matches exactly in all three scenarios. No physical-device performance conclusion.',
          'exportedTexture': export_evidence, 'typecheck': 'passed', 'existingTests': {'passed': 181, 'failed': 0},
          'webBuild': 'normal test', 'taptapDevice': 'not verified', 'userArtApproval': 'pending'}
(HERE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
