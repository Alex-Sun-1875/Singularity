"""Compose reference comparisons from unaltered native Cocos screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
QA=ROOT/'src/cocos/test-results/rpg-alignment-v4'
REF=ROOT/'source-art/ui/equipment-profession-points-v1'
FONT='C:/Windows/Fonts/msyh.ttc'
pages=[('装备 · 当前职业','01-equipment-current'),('装备 · 全部装备','02-equipment-all'),('职业选择','03-profession-preview'),('属性加点','04-attribute-points'),('技能加点','05-skill-points')]
mobile=json.loads((QA/'runtime-review.json').read_text('utf-8'))
desktop=json.loads((QA/'desktop/runtime-review.json').read_text('utf-8'))
regression=json.loads((QA/'regression/browser-review.json').read_text('utf-8'))
profiles=json.loads((QA/'profiles/profiles.json').read_text('utf-8'))
default=json.loads((QA/'default-preview.json').read_text('utf-8'))
copied=json.loads((QA/'build-copy-review.json').read_text('utf-8'))
for report in [mobile,desktop,regression]:
    assert not report['errors'] and not report['failed']
    for page in report['reports']:
        assert not page['small'] and not page['overlap'] and not page.get('close',page.get('tooClose',[])),page['name']
assert not default['errors'] and not copied['mismatches']
assert all(p['rounded'] and p['borderFront'] and abs(p['visibleHeader']-40)<.3 for p in default['panels'])
assert all(p['rounded'] and not p['small'] for p in profiles['reports'])

def caption(draw,xy,value,size=22,color='#DAB16D'):
    draw.text(xy,value,font=ImageFont.truetype(FONT,size),fill=color)

def dialog(name,desktop_mode=True):
    report=desktop if desktop_mode else mobile
    folder=QA/'desktop' if desktop_mode else QA
    record=next(p for p in report['reports'] if p['name']==name)
    im=Image.open(folder/(name+'.png')).convert('RGB')
    density=1.5 if desktop_mode else 3
    s=record['shell']
    return im.crop(tuple(round(v*density) for v in [s['left'],s['top'],s['left']+s['width'],s['top']+s['height']]))

W,COL,PAD,GAP,ROW=1940,920,32,36,490
board=Image.new('RGB',(W,160+len(pages)*ROW+90),'#100c08');d=ImageDraw.Draw(board)
caption(d,(PAD,18),'管理界面 · 原设计稿与最新运行逐页对照',30)
caption(d,(PAD,66),'桌面浮层缩至 1040 逻辑像素 · 四角完整金边 · 顶栏 40px · 点击区域独立保留',20,'#BDB29C')
caption(d,(PAD,110),'原设计稿',21);caption(d,(PAD+COL+GAP,110),'最新 Cocos 实际运行',21)
for i,(title,name) in enumerate(pages):
    y=160+i*ROW;caption(d,(PAD,y),title)
    original=Image.open(REF/(name+'.png')).convert('RGB').resize((COL,426),Image.Resampling.LANCZOS)
    current=dialog(name).resize((COL,426),Image.Resampling.LANCZOS)
    board.paste(original,(PAD,y+36));board.paste(current,(PAD+COL+GAP,y+36))
caption(d,(PAD,160+len(pages)*ROW+4),'仅裁切与等比缩放真实运行截图；技能名称、技能数量和数值来自当前规则。',19,'#BDB29C')
caption(d,(PAD,160+len(pages)*ROW+36),'旧稿中的连穿箭现已调整为当前技能配置；本次对齐布局，不回退玩法数据。TapTap 真机另行验收。',19,'#BDB29C')
board.save(HERE/'design-runtime-comparison.jpg',quality=94)

overview_pages=[('人物','06-character'),*pages,('技能配置','07-combat-skills'),('锻造','08-forge')]
overview=Image.new('RGB',(1940,112+4*480+70),'#100c08');d=ImageDraw.Draw(overview)
caption(d,(32,18),'手机横屏 · 最新实际运行',30)
caption(d,(32,65),'844×390 逻辑视口 / 3倍密度 · 浮层四周留白 · 装备4列3行 · 安全区与触控检查通过',20,'#BDB29C')
for i,(title,name) in enumerate(overview_pages):
    x=32+i%2*956;y=112+i//2*480;caption(d,(x,y),title)
    im=Image.open(QA/(name+'.png')).convert('RGB').resize((920,425),Image.Resampling.LANCZOS)
    overview.paste(im,(x,y+35))
caption(d,(32,112+4*480+8),'独立验证存档；用户存档未清除。Web 检查不代替 TapTap 平台与真机验收。',19,'#BDB29C')
overview.save(HERE/'mobile-runtime-overview.jpg',quality=94)

corners=Image.new('RGB',(1050,500),'#100c08');d=ImageDraw.Draw(corners)
caption(d,(24,14),'圆角检查 · 四角边框位于内容层上方',25)
for row,(label,desktop_mode) in enumerate([('手机',False),('桌面',True)]):
    im=dialog('07-combat-skills',desktop_mode);w,h=im.size;size=75 if desktop_mode else 115
    caption(d,(24,75+row*200),label,21)
    for i,box in enumerate([(0,0,size,size),(w-size,0,w,size),(0,h-size,size,h),(w-size,h-size,w,h)]):
        corner=im.crop(box).resize((160,160),Image.Resampling.NEAREST)
        corners.paste(corner,(160+i*215,75+row*200))
corners.save(HERE/'rounded-corners.jpg',quality=96)

evidence={
    'date':'2026-11-12','status':'implemented_and_reviewed_in_native_Cocos_output; user_acceptance_pending',
    'reference':'../equipment-profession-points-v1/','comparison':'design-runtime-comparison.jpg','mobileOverview':'mobile-runtime-overview.jpg','corners':'rounded-corners.jpg',
    'changes':{'frame':'Shared DoubleGoldFrame foreground border, interior alpha cleaned deterministically, clip follows inner radius; screen-based border width is stable across density and tall browser windows.','size':'Desktop max1040 logical px (previous1120); phone remains floating with outside gutters.','header':'40 logical px visible on all profiles; targets48px and gaps8px.','alignment':'Wide layout uses original column and vertical anchors for profession, attribute rows, skill rows, equipment portrait/filter/grid/detail. Compact phone/narrow layout preserves usable targets.','equipment':'4x3 cells fully visible in both scopes; wide layout two filter strips, compact layout one strip with category chooser.','numbers':'Attribute deltas separated; benefit values cannot wrap.'},
    'validation':{'typescript':'npm run check passed','build':'Cocos Creator3.8.8 web-mobile completed','mobileScreens':len(mobile['reports']),'tallDesktopScreens':len(desktop['reports']),'regressionStates':len(regression['reports']),'additionalProfileStates':len(profiles['reports']),'defaultPages':len(default['panels']),'runtimeErrors':0,'networkFailures':0,'smallTargets':0,'overlappingControls':0,'gapsBelow8px':0,'copiedFilesVerified':copied['filesVerified'],'functional':['scope/category filters','profession confirmation','attribute/skill drafts and apply','discard guards','respec','active-slot swap','save/reload','enhancement and recipe transactions with exact costs']},
    'sourceHashes':json.loads((QA/'source-hashes.json').read_text('utf-8')),
    'fixtures':'Independent browser contexts using real progression/gear APIs; isolated currencies/recipe for transaction previews. User save not replaced.',
    'art':'No generation or new dependencies; approved material retained, Pillow alpha cleanup only.',
    'preview':{'url':'http://127.0.0.1:7469/','default':'src/cocos/build/concept-2d','candidate':'src/cocos/build/concept-2d-rpg-alignment-v4','backup':copied['backup'],'published':False},
    'limitations':['TapTap real AppID/device/safe-area acceptance remains separate.','Current skill definitions differ from old concept; kept the current gameplay data.']
}
(HERE/'implementation-result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'source-review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
p=REF/'design-spec.json';spec=json.loads(p.read_text('utf-8'));spec['latestAlignmentReview']='../rpg-alignment-v4/implementation-result.json';p.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(evidence['validation'],ensure_ascii=False))
