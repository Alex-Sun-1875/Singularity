"""Evidence from native Cocos UI, with isolated fixture profiles only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
QA=ROOT/'src/cocos/test-results/rpg-floating-v3'
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-profession-v1/src/cocos')
font='C:/Windows/Fonts/msyh.ttc'
pages=[('人物','06-character'),('装备 · 当前职业','01-equipment-current'),('装备 · 全部装备','02-equipment-all'),('职业选择','03-profession-preview'),('属性加点','04-attribute-points'),('技能加点','05-skill-points'),('战斗技能与槽位','07-combat-skills'),('锻造与强化','08-forge')]
W,COL,GAP,PAD,ROW=1960,936,28,30,484
board=Image.new('RGB',(W,116+4*ROW+88),'#100c08');d=ImageDraw.Draw(board)
def text(x,y,value,size=22,color='#EDE4CB'):d.text((x,y),value,font=ImageFont.truetype(font,size),fill=color)
text(PAD,18,'圆角管理界面 · 实际运行预览',30,'#DAAE65')
text(PAD,66,'手机四周留白 · 可见 header 40px · 装备 4列×3行 · 844×390逻辑视口',20,'#B8AF9B')
for i,(title,name) in enumerate(pages):
 x=PAD+(i%2)*(COL+GAP);y=116+(i//2)*ROW
 text(x,y,title,22,'#DAAE65');im=Image.open(QA/(name+'.png')).convert('RGB').resize((COL,433),Image.Resampling.LANCZOS);board.paste(im,(x,y+36))
text(PAD,116+4*ROW+8,'画面来自独立验证存档；文字、选择、滚动、费用与保存均为实际 Cocos 界面。',19,'#B8AF9B')
text(PAD,116+4*ROW+40,'手机、安全区与桌面分别验证；TapTap 平台和真机验收仍需单独进行。',19,'#B8AF9B')
board.save(HERE/'runtime-overview.jpg',quality=94)
runtime=json.loads((QA/'runtime-review.json').read_text('utf-8'));regression=json.loads((QA/'regression/browser-review.json').read_text('utf-8'));profiles=json.loads((QA/'profiles/profiles.json').read_text('utf-8'));default=json.loads((QA/'default-preview.json').read_text('utf-8'));copied=json.loads((QA/'build-copy-review.json').read_text('utf-8'))
for report in [runtime,regression]:
 assert not report['errors'] and not report['failed']
 for page in report['reports']:assert not page['small'] and not page['overlap'] and not page.get('close',page.get('tooClose',[])),page['name']
assert not default['errors'] and not copied['mismatches']
files=['shared/ui/RpgPanel.ts','features/equipment/runtime/EquipmentPanels.ts','features/progression/runtime/PreparationPanels.ts','features/progression/runtime/SkillBook.ts','features/crafting/runtime/ForgeWorkshop.ts','features/crafting/runtime/ForgingPanel.ts','app/ChapterGame.ts']
hashes=[]
for name in files:
 p=ROOT/'src/cocos/assets/scripts'/name;sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==hashlib.sha256((MIRROR/'assets/scripts'/name).read_bytes()).hexdigest(),name;hashes.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha})
asset=ROOT/'src/cocos/assets/resources/ui/quiet-bronze/prep-skill-selected-v2.png';assert asset.read_bytes()==(MIRROR/'assets/resources/ui/quiet-bronze'/asset.name).read_bytes()
evidence={
 'date':'2026-11-12','status':'implemented_and_reviewed_in_native_Cocos_browser_output; user_acceptance_pending',
 'userReference':'user-rounded-reference.jpg','gallery':'runtime-overview.jpg',
 'decisions':{'shell':'Shared DoubleGoldFrame rounded panel for all six primary tabs; phone floats with visible outside world.','header':'Visible 40 logical pixels on phones, proportional on desktop; native targets remain 48px with 8px gaps.','equipment':'4 columns × 3 rows in both scopes; empty cells retained; one row of scope tabs and a category selector; overflow scrolls.','theme':'Existing approved deep-brown textures, native serif text, gold metal and teal selection.','otherPages':'Character stats, combat skill catalog/slots, enhancement, affix pool, recipe and inheritance pages all use the same preparation skin.'},
 'reused':['Cocos native Button / ScrollView / Mask','Shared RpgPanel / DoubleGoldFrame','Existing approved preparation and forge artwork; one selected outline cleaned deterministically'],
 'newDependencies':[], 'imageGeneration':'None; reused approved artwork and deterministic Pillow extraction.',
 'validation':{'typeScript':'npm run check passed','existingRules':'60 passed','runtimeScreens':len(runtime['reports']),'regressionStates':len(regression['reports']),'androidAndDesktopStates':len(profiles['reports']),'runtimeErrors':0,'networkFailures':0,'overlappingControls':0,'minimumTarget':'48 CSS px','minimumGap':'8 CSS px','functional':['category filtering','profession preview/confirm','attribute and skill drafts/application','respec and leaving guards','active-slot reassignment without duplicates','save/reload','native enhancement and recipe transactions with exact cost deduction'],'defaultEntry':'all seven pages checked at port 7469','buildFilesMatched':copied['filesVerified']},
 'fixtures':'Independent browser contexts. Canonical gear/experience fixtures; gold/iron/runes and one recipe supplied only in the isolated cost-preview profile. User save not cleared or replaced.',
 'preview':{'url':'http://127.0.0.1:7469/','output':'src/cocos/build/concept-2d','candidate':'src/cocos/build/concept-2d-rpg-floating-v3','backup':'src/cocos/temp/default-before-rpg-floating-v3-20261112','publicRelease':False},
 'remaining':['TapTap real AppID and physical-device acceptance; Web checks are not platform acceptance.'],
 'sourceHashes':hashes
}
(HERE/'implementation-result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8');(QA/'source-review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'source-art/ui/equipment-profession-points-v1/design-spec.json';spec=json.loads(p.read_text('utf-8'));spec['latestAlignmentReview']='../rpg-floating-v3/implementation-result.json';p.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(evidence['validation'],ensure_ascii=False))
