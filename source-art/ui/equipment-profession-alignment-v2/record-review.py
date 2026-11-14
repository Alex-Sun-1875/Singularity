"""Publish comparison evidence from actual native Cocos browser captures."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'source-art/ui/equipment-profession-points-v1'
QA=ROOT/'src/cocos/test-results/equipment-profession-alignment-v2'
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-profession-v1/src/cocos')
FONT='C:/Windows/Fonts/msyh.ttc'
rows=[
 ('01-equipment-current','装备 · 当前职业','恢复人物纸娃娃、两级筛选、绘制装备图、大图详情与标签。'),
 ('02-equipment-all','装备 · 全部装备','恢复三行装备、其他职业标签、斜置法杖与职业切换提示。'),
 ('03-profession-preview','职业 · 预览','恢复 2×2 职业绘画卡、人物栏、金色选中边与右侧职业详情。'),
 ('04-attribute-points','加点 · 属性','恢复四行底板、属性图标、数值分隔、方形加减与收益分区。'),
 ('05-skill-points','加点 · 技能','恢复窄人物栏、侧栏、五行技能、升级消耗牌与效果对比。'),
]
W,COL,PAD,GAP,ROW=1920,928,24,16,510
board=Image.new('RGB',(W,92+len(rows)*ROW+92),'#100c08');d=ImageDraw.Draw(board)
def write(draw,xy,value,size=20,color='#EDE4CB'):
 draw.text(xy,value,font=ImageFont.truetype(FONT,size),fill=color)
write(d,(PAD,16),'五页逐项对照 · 已确认设计稿 / 实际 Cocos 运行',29,'#DAAE65')
write(d,(PAD,58),'844 × 390 逻辑视口 · 2532 × 1170 原始运行截图 · 独立验证存档',18,'#B8AF9B')
for i,(name,title,note) in enumerate(rows):
 y=92+i*ROW
 write(d,(PAD,y),title,23,'#DAAE65')
 for j,(folder,label) in enumerate([(SOURCE,'设计稿'),(QA,'实际运行')]):
  x=PAD+j*(COL+GAP)
  write(d,(x,y+36),label,17,'#B8AF9B')
  im=Image.open(folder/(name+'.png')).convert('RGB').resize((COL,429),Image.Resampling.LANCZOS)
  board.paste(im,(x,y+66))
 pair=board.crop((0,y-4,W,y+ROW))
 pair.save(HERE/(name+'-compare.jpg'),quality=95)
write(d,(PAD,92+len(rows)*ROW+8),'布局保留 48px 触控区和 8px 间距；筛选条与列表纵向间距据此调整。',19,'#B8AF9B')
write(d,(PAD,92+len(rows)*ROW+43),'名称、品质、点数与装备槽来自真实规则；TapTap 真机仍待验收。',19,'#B8AF9B')
board.save(HERE/'03-after-comparison.jpg',quality=94)

browser=json.loads((QA/'regression/browser-review.json').read_text('utf-8'))
five=json.loads((QA/'five-page-review.json').read_text('utf-8'))
default=json.loads((QA/'default-preview.json').read_text('utf-8'))
copy=json.loads((QA/'build-copy-review.json').read_text('utf-8'))
assert not browser['errors'] and not browser['failed']
assert not five['errors'] and not five['failed']
assert not default['errors'] and not default['failed'] and not copy['mismatches']
assert not [issue for r in browser['reports'] for key in ['small','overlap','tooClose'] for issue in r[key]]
assert not [issue for r in five['reports'] for key in ['small','overlap','close'] for issue in r[key]]
files=[ROOT/'src/cocos/assets/scripts'/p for p in [
 'shared/ui/RpgPanel.ts','shared/ui/UiSkin.ts','shared/ui/PreparationSkin.ts','shared/ui/FeedbackPalette.ts',
 'features/equipment/runtime/EquipmentPanels.ts','features/progression/runtime/PreparationPanels.ts','features/progression/locales/index.ts']]
files+=list((ROOT/'src/cocos/assets/resources/ui/quiet-bronze').glob('prep-*-v2.png'))
files+=list((ROOT/'src/cocos/assets/resources/ui/quiet-bronze').glob('prep-*-v2.png.meta'))
files.append(ROOT/'src/cocos/assets/scripts/shared/ui/PreparationSkin.ts.meta')
hashes=[]
for path in files:
 relative=path.relative_to(ROOT/'src/cocos')
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 assert sha==hashlib.sha256((MIRROR/relative).read_bytes()).hexdigest(),relative
 hashes.append({'file':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha})
evidence={
 'status':'corrected_and_reviewed_in_actual_Cocos_output; user_acceptance_pending',
 'date':'2026-11-11','approvedDesign':'source-art/ui/equipment-profession-points-v1',
 'before':'01-before-comparison.jpg','after':'03-after-comparison.jpg',
 'pages':[{'page':title,'changes':note,'comparison':name+'-compare.jpg','runtime':str((QA/(name+'.png')).relative_to(ROOT)).replace('\\','/')} for name,title,note in rows],
 'sourceArt':{'generation':'No new generative images; deterministic extraction of 52 components from the approved mockups.','sourceBoxes':'skin-exports.json','changingText':'All changing text, buttons, preview values, selection and scrolling remain native Cocos.','frame':'Original corners retained in a compact 96×96 nine-patch instead of a full-screen texture.'},
 'intentionalDifferences':[
  'Management pages follow the mockups inside the actual safe area. Independent buttons retain >=48 logical CSS pixels and >=8 pixels gap, increasing filter/list spacing compared with the compact drawing.',
  'Keep all nine existing equipment slots, including both rings; the drawing only illustrated eight. Real item names, quality, learned skills and derived stats are not replaced with example labels.',
  'Long lists/descriptions scroll, and narrow safe-area skill sidebars shorten the current-profession label rather than wrapping over adjacent content.'
 ],
 'validation':{'typeScript':'npm run check passed','existingRules':'60 passed; no new test dependencies or cases','cocosBuild':'Creator 3.8.8 web-mobile completed; exit 36','fivePageStates':len(five['reports']),'regressionStates':len(browser['reports']),'touchTargets':'>=48 CSS px','independentGaps':'>=8 CSS px','overlappingControls':0,'runtimeErrors':0,'networkFailures':0,'saveReload':'profession, weapon, attributes and skill points restored','defaultPreview':'all four panels loaded the corrected frame; no errors; bare URL still defaults to 2D scene / 3D player','buildFilesMatched':copy['filesVerified']},
 'screens':'src/cocos/test-results/equipment-profession-alignment-v2',
 'preview':{'url':'http://127.0.0.1:7469/?view=2d&player=3d&progression=natural','defaultOutput':'src/cocos/build/concept-2d','previousOutputBackup':'src/cocos/temp/default-before-profession-align-v2-20261111','userSaveCleared':False,'publicRelease':False},
 'limits':['Web runtime verified. Real TapTap AppID and physical-device acceptance are not claimed.'],
 'sourceHashes':hashes
}
(HERE/'alignment-review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'source-review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
spec=json.loads((SOURCE/'design-spec.json').read_text('utf-8'))
spec['latestAlignmentReview']='../equipment-profession-alignment-v2/alignment-review.json'
(SOURCE/'design-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'comparedPages':5,'regressionStates':len(browser['reports']),'sourceFilesMatched':len(hashes),'comparison':str(HERE/'03-after-comparison.jpg')},ensure_ascii=False))
