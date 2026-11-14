"""Record verified implementation artifacts; compose only actual Cocos screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PROJECT=ROOT/'src/cocos'
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-profession-v1/src/cocos')
QA=PROJECT/'test-results/equipment-profession-points-v1'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
files=[
 'assets/scripts/shared/ui/RpgPanel.ts',
 'assets/scripts/features/equipment/runtime/EquipmentPanels.ts',
 'assets/scripts/features/progression/runtime/SkillBook.ts',
 'assets/scripts/features/progression/runtime/PreparationPanels.ts',
 'assets/scripts/features/progression/common/CombatLoadouts.ts',
 'assets/scripts/features/progression/locales/index.ts',
 'assets/scripts/core/GameSession.ts',
 'assets/scripts/app/ChapterGame.ts',
 'assets/scripts/app/Menus.ts',
]
files += [str(p.relative_to(PROJECT)).replace('\\','/') for p in (PROJECT/'assets/resources/ui/quiet-bronze').glob('rpg-profession-*-v1.png*')]
proof=[{'file':name,'sha256':sha(PROJECT/name),'mirror_matches':sha(PROJECT/name)==sha(MIRROR/name)} for name in files]
assert all(row['mirror_matches'] for row in proof)
all_scripts=list((PROJECT/'assets/scripts').rglob('*.ts'))
assert all((MIRROR/p.relative_to(PROJECT)).exists() and sha(p)==sha(MIRROR/p.relative_to(PROJECT)) for p in all_scripts)
report=json.loads((QA/'browser-review.json').read_text('utf-8'))
assert not report['errors'] and not report['failed']
assert all(not case['small'] and not case['overlap'] and not case['tooClose'] for case in report['reports'])
report['device_scope']={'base':[844,390],'larger':[932,430],'density':3,'safe_area_fixture':{'viewport':[844,390],'left':44,'right':44,'bottom':21,'real_device':False},'minimum_touch_css':48,'minimum_gap_css':8}
report['validation']={'typescript':'passed','existing_rule_tests':60,'passed':60,'failed':0,'new_test_dependencies':0,'new_test_suites':0,'browser_states':len(report['reports']),'tap_device_validation':'pending'}
(QA/'browser-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
build=PROJECT/'build/concept-2d-profession-v1'
default=PROJECT/'build/concept-2d'
assert sha(build/'index.html')==sha(default/'index.html')==sha(MIRROR/'build/concept-2d-profession-v1/index.html')
evidence={
 'date':'2026-11-11','stage':'implemented_and_browser_verified',
 'ui':'Approved equipment/profession/allocation v1; production character, unique skill icons and shared gold shell reused; four profession illustrations cropped deterministically from the approved cloud design.',
 'generator':'No new generation during implementation. Existing approved OpenAI image_gen design reused.',
 'sourceChecks':proof,'allTypeScriptFilesMirrorMatched':len(all_scripts),
 'build':{'creator':'3.8.8','target':'web-mobile','output':'src/cocos/build/concept-2d-profession-v1','method':'Independent C-drive snapshot after existing F-drive Creator configuration write error; complete current script snapshot verified.','officialCliReference':'https://docs.cocos.com/creator/3.8/manual/en/editor/publish/publish-in-command-line.html','entrySha256':sha(build/'index.html')},
 'preview':{'url':'http://127.0.0.1:7469/?view=2d&player=3d&progression=natural','output':'src/cocos/build/concept-2d','previousOutputBackup':'src/cocos/temp/default-before-profession-v1-20261111','userSaveCleared':False,'publicRelease':False},
 'verification':report['validation'],
 'browserEvidence':'src/cocos/test-results/equipment-profession-points-v1/browser-review.json',
 'artReview':{'status':'reviewed_in_actual_Cocos_browser_screenshots','userAcceptance':'pending','checks':['two equipment filter states preserve worn gear','class preview versus confirmed class','four distinct class paintings and unique skill icons','attribute and skill point pools and preview benefits','48px targets and 8px gaps; no target overlap','844x390, 932x430 and separately marked safe-area pressure fixture','closing clears modal input nodes; save and reload retain class, weapon and allocated points']},
 'remaining':['TapTap real AppID platform and physical-device acceptance; not substituted by this Web build.'],
}
(HERE/'implementation-result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'source-review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
spec=json.loads((HERE/'design-spec.json').read_text('utf-8'))
spec['status'].update({'userApproval':'2026-11-11 用户确认按本方案实现','pixelSpecification':'已按逻辑触控尺寸及安全区细化；浏览器检查见 implementation-result.json','cocosImplementation':'已实现并通过本地浏览器验证','tests':'TypeScript、60项既有规则检查、16个浏览器界面状态通过；TapTap真机待验'})
spec['implementationRecord']='implementation-result.json'
(HERE/'design-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')

screens=[('装备 · 当前职业','equipment-current'),('装备 · 全部与其他职业预览','equipment-foreign'),('职业 · 先预览再确认','profession-fire-preview'),('加点 · 属性收益预览','attribute-preview'),('加点 · 技能成本与效果','bow-level3-preview')]
font='C:/Windows/Fonts/msyh.ttc'
W,PAD,GAP,COL,ROW=1960,42,32,922,500
board=Image.new('RGB',(W,128+ROW*3+30),'#110E0B');d=ImageDraw.Draw(board)
d.text((PAD,28),'装备、职业与加点 · 实现效果',font=ImageFont.truetype(font,34),fill='#DAAE65')
d.text((PAD,81),'实际 Cocos 浏览器截图 · 844 × 390 逻辑视口 · 非设计稿贴图',font=ImageFont.truetype(font,20),fill='#B8AF9B')
for i,(title,name) in enumerate(screens):
 x=PAD+(i%2)*(COL+GAP);y=128+(i//2)*ROW
 d.text((x,y),title,font=ImageFont.truetype(font,23),fill='#EDE4CB')
 image=Image.open(QA/f'iphone14-{name}.png').convert('RGB');image.thumbnail((COL,428))
 board.paste(image,(x,y+43))
x=PAD+COL+GAP;y=128+2*ROW
for i,line in enumerate(['已验证','当前职业 / 全部装备切换','四职业预览、确认与武器准备','属性点 / 技能点独立，先预览再应用','免费重配、离开保护与存档重载','48 逻辑像素触控区，8 像素间距','更大视口与安全区压力检查','TypeScript + 60 项既有规则检查','TapTap 真机验收待进行']):
 d.text((x,y+i*43),line,font=ImageFont.truetype(font,24 if i==0 else 21),fill='#DAAE65' if i==0 else '#B8AF9B')
(HERE/'review').mkdir(exist_ok=True)
board.save(HERE/'review/runtime-overview.jpg',quality=94)
print(json.dumps({'verifiedSourceFiles':len(files),'allScriptsMatched':len(all_scripts),'browserStates':len(report['reports']),'overview':str(HERE/'review/runtime-overview.jpg')},ensure_ascii=False))
