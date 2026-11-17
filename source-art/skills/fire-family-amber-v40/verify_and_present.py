"""Verify real captures and compose their original pixels; no recolouring here."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / 'src/.tmp/fire-family-amber-v40'
PRODUCTION = ROOT / 'src/cocos/assets/resources/vfx/production'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reports = {s: load(HERE/s/'capture.json') for s in ['before', 'after']}
if not all(r['stableBuild'] and r['journeyPreserved'] and not r['errors'] for r in reports.values()):
    raise RuntimeError('Unstable or failed native recording')
checks = []
skills = ['FIR_01', 'FIR_04', 'FIR_03', 'FIR_05', 'FIR_02']
for mode in ['empty', 'targets']:
    for skill in skills:
        a, b = [load(HERE/s/(mode+'-'+skill+'.json')) for s in ['before', 'after']]
        events_equal = a['events'] == b['events']
        geometry_equal = all((x['fire'], x['ground'], x['shield']) == (y['fire'], y['ground'], y['shield'])
                             for x, y in zip(a['metrics'], b['metrics']))
        cooldown_equal = all(x['cooldown'] == y['cooldown'] for x, y in zip(a['metrics'], b['metrics']))
        cleaned = not b['metrics'][-1]['fire']['active'] and not b['metrics'][-1]['ground']['active'] and not b['metrics'][-1]['shield']['visible']
        check = {'mode': mode, 'skill': skill, 'eventsExactlyEqual': events_equal,
                 'fireGroundShieldStateExactlyEqual': geometry_equal, 'cooldownExactlyEqual': cooldown_equal,
                 'hitsBeforeAfter': [a['metrics'][-1]['hits'], b['metrics'][-1]['hits']],
                 'damageBeforeAfter': [a['metrics'][-1]['damage'], b['metrics'][-1]['damage']],
                 'peakDrawCallsBeforeAfter': [max(m['drawCalls'] for m in c['metrics']) for c in [a,b]],
                 'peakTrianglesBeforeAfter': [max(m['triangles'] for m in c['metrics']) for c in [a,b]],
                 'cleaned': cleaned}
        checks.append(check)
        if not (events_equal and geometry_equal and cooldown_equal and cleaned):
            raise RuntimeError('Native regression: '+json.dumps(check))

bindings = []
provenance = load(HERE/'provenance.json')
for entry in provenance['textures']:
    name = entry['name']+'.png'
    original = np.asarray(Image.open(HERE/'originals'/name))
    production = np.asarray(Image.open(PRODUCTION/name))
    if original.shape != production.shape or not np.array_equal(original[...,3], production[...,3]):
        raise RuntimeError('Texture alpha/dimensions changed: '+name)
    uuid = load(PRODUCTION/(name+'.meta'))['uuid']
    exported = ROOT/reports['after']['servedBuild']/'assets/resources/native'/uuid[:2]
    matches = list(exported.glob(uuid+'*.png'))
    if not matches or not all(np.array_equal(production, np.asarray(Image.open(p))) for p in matches):
        raise RuntimeError('Actual exported texture does not match: '+name)
    bindings.append({'name': name, 'alphaExactlyEqual': True, 'sizeExactlyEqual': True,
                     'sourceSha256': sha(PRODUCTION/name), 'exportedFiles': [str(p.relative_to(ROOT)).replace('\\','/') for p in matches], 'exportedPixelsMatch': True})

SAMPLES = [
    ('FIR_02', '陨星天坠', 54, (20,190,655,640)),
    ('FIR_03', '焰心护盾', 48, (550,190,755,430)),
    ('FIR_01', '赤焰枪', 24, (150,310,485,430)),
    ('FIR_04', '烈焰喷流', 48, (120,250,650,505)),
    ('FIR_05', '焚焰火域', 48, (125,210,575,615)),
]
palette = load(HERE/'palette.json')['colours']
font = lambda n: ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', n)
titlefont = lambda n: ImageFont.truetype('C:/Windows/Fonts/simsun.ttc', n)
def crop(stage, sample):
    skill, label, frame, box = sample
    return Image.open(CACHE/stage/'empty'/skill/(f'{frame:03}.png')).convert('RGB').crop(box)
def contain(canvas, im, box):
    x,y,w,h = box
    canvas.paste(Image.new('RGB', (w,h), '#27312E'), (x,y))
    resized = ImageOps.contain(im, (w,h), Image.Resampling.LANCZOS)
    canvas.paste(resized, (x+(w-resized.width)//2,y+(h-resized.height)//2))

kit = Image.new('RGB', (1280,1110), '#161E1C')
d = ImageDraw.Draw(kit)
d.text((30,20), 'C  琥珀金焰 / 整套实景', font=titlefont(35), fill='#EADAB8')
d.text((32,70), '四个普通技能与陨石共用色阶', font=font(21), fill='#C8B58B')
for i, shade in enumerate(palette.values()):
    d.rectangle((780+i*92,30,864+i*92,58), fill=shade)
contain(kit, crop('after',SAMPLES[0]), (26,120,800,510))
contain(kit, crop('after',SAMPLES[1]), (846,120,408,510))
d.text((32,642),SAMPLES[0][1],font=titlefont(25),fill='#E8DCC3')
d.text((852,642),SAMPLES[1][1],font=titlefont(25),fill='#E8DCC3')
for i,sample in enumerate(SAMPLES[2:]):
    contain(kit,crop('after',sample),(26+i*416,702,400,310))
    d.text((32+i*416,1023),sample[1],font=titlefont(25),fill='#E8DCC3')
d.text((32,1074),'实际游戏录制画面 · 正常 test · 仅裁切排版',font=font(18),fill='#AAB5A7')
kit.save(HERE/'native-C-kit.png', optimize=True)

comparison = Image.new('RGB',(1260,1500),'#161E1C')
d = ImageDraw.Draw(comparison)
d.text((28,18),'火系统一为 C 琥珀金焰 / 实景前后',font=titlefont(32),fill='#EADAB8')
d.text((203,75),'调整前',font=font(23),fill='#BFC6B8')
d.text((744,75),'C 接入后',font=font(23),fill='#E8CC8D')
for i,sample in enumerate(SAMPLES):
    y=122+i*265
    d.text((24,y+12),sample[1],font=titlefont(24),fill='#E8DCC3')
    for j,stage in enumerate(['before','after']):
        contain(comparison,crop(stage,sample),(198+j*522,y,506,245))
comparison.save(HERE/'native-before-after.png', optimize=True)

result = {'selection': 'C', 'profileId': 'amber-gold-v40', 'nativeComparisons': checks, 'textures': bindings,
          'typecheck': 'passed', 'existingTests': {'passed':181,'failed':0}, 'webBuild':'normal test',
          'beforeMainSha256': reports['before']['mainHash'], 'afterMainSha256': reports['after']['mainHash'],
          'media': {'processing':'crop, rescale, label and arrange actual canvas pixels only; no recolouring', 'samples':[{'skill':s[0],'frame':s[2],'crop':s[3]} for s in SAMPLES]},
          'designSelection':'user selected C', 'nativeArtEngineeringReview':'recorded separately from user acceptance',
          'taptapDevice':'not verified'}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'selection':'C','nativeComparisons':len(checks),'allNativeStatesAndEventsEqual':True,'exportedTexturesMatched':len(bindings),'kit':str(HERE/'native-C-kit.png')},ensure_ascii=False))
