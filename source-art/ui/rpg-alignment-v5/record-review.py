"""Review native output against the marked reference, including measured colors."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageStat
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
QA=ROOT/'src/cocos/test-results/rpg-alignment-v5';REF=ROOT/'source-art/ui/equipment-profession-points-v1'
OLD=ROOT/'src/cocos/test-results/rpg-alignment-v4/desktop'
FONT='C:/Windows/Fonts/msyh.ttc'
def read(path):return json.loads(path.read_text('utf-8'))
mobile=read(QA/'runtime-review.json');desktop=read(QA/'desktop/runtime-review.json')
regression=read(QA/'regression/browser-review.json');profiles=read(QA/'profiles/profiles.json')
default=read(QA/'default-preview.json');copied=read(QA/'build-copy-review.json')
for report in [mobile,desktop,regression]:
 assert not report['errors'] and not report['failed']
 for r in report['reports']:
  assert not r['small'] and not r['overlap'] and not r.get('missingSprites',[]),r['name']
  if report is not desktop:assert not r.get('close',r.get('tooClose',[])),r['name']
  else:
   for a,b,gap in r['close']:
    assert gap>=3.5 and (a.startswith('inventory:scope:') and b.startswith('inventory-category:') or a.startswith('AllocationTab:') and b.startswith('AllocationTab:')),(r['name'],a,b,gap)
assert not default['errors'] and not copied['mismatches']
assert all(r['borderFront'] and r['rounded'] for r in default['panels'])
def caption(d,xy,s,size=21,color='#E8D0A3'):d.text(xy,s,font=ImageFont.truetype(FONT,size),fill=color)
def native(name,where='desktop'):
 if where=='reference':return Image.open(REF/(name+'.png')).convert('RGB').resize((844,390),Image.Resampling.LANCZOS)
 folder=OLD if where=='old' else QA/'before-tone' if where=='before-tone' else QA/'desktop'
 data=read(folder/'runtime-review.json');r=next(r for r in data['reports'] if r['name']==name)['shell']
 im=Image.open(folder/(name+'.png')).convert('RGB');return im.crop(tuple(round(v*1.5) for v in [r['left'],r['top'],r['left']+r['width'],r['top']+r['height']])).resize((844,390),Image.Resampling.LANCZOS)
pages=[('装备 · 当前职业','01-equipment-current'),('装备 · 全部装备','02-equipment-all'),('职业选择','03-profession-preview'),('属性加点','04-attribute-points'),('技能加点','05-skill-points')]
board=Image.new('RGB',(1940,170+5*490+85),'#100c08');d=ImageDraw.Draw(board)
caption(d,(32,20),'按标记逐项校正 · 原稿与最新实际运行',30)
caption(d,(32,69),'原稿控件、材质与亮度 · 圆角浮层 · 当前技能与装备数据保留',20)
caption(d,(32,112),'原设计稿',21);caption(d,(988,112),'最新 Cocos 实际运行',21)
for i,(title,name) in enumerate(pages):
 y=170+i*490;caption(d,(32,y),title)
 for x,where in [(32,'reference'),(988,'desktop')]:board.paste(native(name,where).resize((920,425),Image.Resampling.LANCZOS),(x,y+35))
caption(d,(32,170+5*490+5),'技能已按用户确认保留当前方案；名称、技能数量和数值来自实际规则。',18)
caption(d,(32,170+5*490+36),'仅裁切和等比缩放真实 Cocos 截图；Web 验证不替代 TapTap 真机验收。',18)
board.save(HERE/'design-runtime-comparison.jpg',quality=95)

regions=[('姓名牌','01-equipment-current',(40,34,235,85)),('主副手槽及槽下标签','01-equipment-current',(25,256,242,333)),('当前职业装备','01-equipment-current',(267,110,562,327)),('全部装备 · 三行','02-equipment-all',(267,101,562,336)),('职业详情与当前技能图标','03-profession-preview',(581,42,837,315)),('加点侧栏','04-attribute-points',(6,36,180,337)),('属性行与加减控件','04-attribute-points',(188,43,596,330)),('技能列表与升级预览','05-skill-points',(249,40,838,329))]
board=Image.new('RGB',(1860,130+len(regions)*290+65),'#100c08');d=ImageDraw.Draw(board)
caption(d,(24,16),'圈出区域 · 控件与材质逐项对照',30)
for x,title in [(24,'原稿'),(642,'上一版 v4'),(1260,'本次 v5')]:caption(d,(x,73),title,21)
for i,(title,name,box) in enumerate(regions):
 y=130+i*290;caption(d,(24,y),title)
 for x,where in [(24,'reference'),(642,'old'),(1260,'desktop')]:
  im=native(name,where).crop(box);im.thumbnail((570,235),Image.Resampling.LANCZOS);board.paste(im,(x+(570-im.width)//2,y+35))
caption(d,(24,130+len(regions)*290+10),'旧技能图仅作视觉参考；本次保留当前玩法，并将线框占位图补为同风格绘制图标。',18)
board.save(HERE/'marked-regions-comparison.jpg',quality=95)

tone=Image.new('RGB',(1860,800),'#100c08');d=ImageDraw.Draw(tone)
caption(d,(24,15),'颜色校正 · 恢复原稿暖棕底材、暖白正文与金线亮度',29)
for x,title in [(24,'原稿'),(642,'本轮调整亮度前'),(1260,'本轮调整亮度后')]:caption(d,(x,75),title,21)
for row,name in enumerate(['04-attribute-points','05-skill-points']):
 for x,where in [(24,'reference'),(642,'before-tone'),(1260,'desktop')]:tone.paste(native(name,where).resize((575,266),Image.Resampling.LANCZOS),(x,120+row*310))
caption(d,(24,742),'对照保持相同尺度与色彩处理，截图未额外调亮。',20)
tone.save(HERE/'tone-before-after.jpg',quality=95)

ref=native('04-attribute-points','reference');before=native('04-attribute-points','before-tone');after=native('04-attribute-points')
regions={'attributeMaterial':(200,61,575,67),'detailMaterial':(610,310,830,333)}
colors={name:{'referenceMedianRGB':ImageStat.Stat(ref.crop(b)).median,'beforeMedianRGB':ImageStat.Stat(before.crop(b)).median,'afterMedianRGB':ImageStat.Stat(after.crop(b)).median} for name,b in regions.items()}
def white(im,box):
 pixels=[c for c in im.crop(box).get_flattened_data() if c[0]>150 and c[1]>140 and c[2]>115 and c[0]<c[1]*1.13 and c[1]<c[2]*1.25]
 pixels.sort(key=sum);pixels=pixels[-max(1,len(pixels)//4):]
 return [round(sum(c[i] for c in pixels)/len(pixels),1) for i in range(3)]
colors['warmWhiteText']={'referenceUpperQuartileRGB':white(ref,(270,66,320,99)),'beforeUpperQuartileRGB':white(before,(260,66,310,99)),'afterUpperQuartileRGB':white(after,(270,66,320,99))}
(HERE/'color-review.json').write_text(json.dumps(colors,indent=2),encoding='utf-8')
files=['shared/ui/RpgPanel.ts','shared/ui/DoubleGoldFrame.ts','shared/ui/UiSkin.ts','shared/ui/PreparationSkin.ts','shared/ui/FeedbackPalette.ts','features/equipment/runtime/EquipmentPanels.ts','features/progression/runtime/PreparationPanels.ts','features/progression/locales/index.ts','features/combat/runtime/CombatSkillIcons.ts','app/ChapterGame.ts']
mirror=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-profession-v1/src/cocos');hashes=[]
for f in files:
 p=ROOT/'src/cocos/assets/scripts'/f;assert p.read_bytes()==(mirror/'assets/scripts'/f).read_bytes(),f
 hashes.append({'file':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for r in read(HERE/'reference-parts.json'):
 p=ROOT/r['asset'];assert p.read_bytes()==(mirror/'assets/resources/ui/quiet-bronze'/p.name).read_bytes(),p.name
result={'date':'2026-11-12','status':'native_browser_review_complete; user_acceptance_pending','userDecision':'Keep current skills; precisely restore the approved appearance. Match brighter reference colors.','comparison':'design-runtime-comparison.jpg','markedRegions':'marked-regions-comparison.jpg','tone':'tone-before-after.jpg','colors':colors,'changes':['Exact reference identity plaque, sidebar tabs, original gold equipment sockets and selected frames','Two large hand sockets with captions below; shared ring socket opens left/right choice without changing equipment','Distinct steel sword, blue bow and lightning staff art; all-scope equipped weapon first; reference badge tone and order','Scope selection material restored; current8items form2rows, all12items3rows without a forced empty row','Attribute labels, steps, sidebar and skill rows aligned to reference; native text remains live','Two painted replacement skill icons from built-in image_gen; current mechanics and progression preserved','Reference empty material strips replace near-black fills; gold unmatting removes double darkening; shared semantic warm-white and gold text roles'],
 'validation':{'typeScript':'passed','CocosCreator':'3.8.8 web-mobile completed','mobileScreens':len(mobile['reports']),'desktopScreens':len(desktop['reports']),'functionalStates':len(regression['reports']),'additionalProfileStates':len(profiles['reports']),'defaultPages':len(default['panels']),'runtimeErrors':0,'missingSprites':0,'overlappingControls':0,'phoneTargets':'48 logical px with8px gaps','wideMouseTargets':'reference header/filter/sidebar hitboxes cover their visible controls; at least24 CSS px, separate from mobile sizing','wideClosePairs':[{ 'page':r['name'],'pairs':r['close']} for r in desktop['reports'] if r['close']],'filesCopiedAndVerified':copied['filesVerified'],'functionalPassTiming':'functional plan/transaction regression reused from this implementation before final material and readonly caption pass; final screenshots and default smoke use final build'},
 'sourceHashes':hashes,'art':'Original design parts extracted with Pillow; two new icons generated with built-in OpenAI image_gen. Generation and art-review statuses recorded separately in painted-icons.json; prompts in painted-icon-prompts.json.','preview':{'url':'http://127.0.0.1:7469/','default':'src/cocos/build/concept-2d','candidate':'src/cocos/build/concept-2d-rpg-alignment-v5','backup':copied['backup'],'published':False},'fixtures':'Independent browser contexts, user save untouched. Canonical progression/gear fixtures; isolated resources for transaction tests.','remaining':['TapTap physical-device and platform acceptance.']}
(HERE/'implementation-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(QA/'source-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
p=REF/'design-spec.json';s=read(p);s['latestAlignmentReview']='../rpg-alignment-v5/implementation-result.json';p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'validation':result['validation'],'colors':colors},ensure_ascii=False))
