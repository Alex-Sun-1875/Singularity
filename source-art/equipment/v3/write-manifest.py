"""Read-only PNG inspection; emits JSON metadata only. Never alters source pixels."""
from pathlib import Path
from PIL import Image
import hashlib, json

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
RUNTIME = ROOT / 'src/cocos/assets/resources/equipment/v3'
names = json.loads((SOURCE / 'catalog-names.json').read_text(encoding='utf-8'))
bounds = {
 'sword': [0,330,644,968,1260,1620],
 'bow': [0,350,700,1040,1360,1774],
 'staff': [0,370,710,1020,1360,1774],
 'oath': [0,370,686,1000,1308,1774],
 'wind': [0,370,710,1040,1360,1774],
 'seeker': [0,395,714,1020,1340,1774],
 'jewelry': [0,355,710,1064,1419,1774],
}
existing = {'sword': {1:['W01'],3:['W02'],5:['L01']}, 'bow':{1:['W07'],3:['W08'],5:['L02']}, 'staff':{1:['W11']},'oath':{2:['A01','A13'],3:['A09']},'wind':{2:['A06'],3:['A02','A10','A14']},'jewelry':{2:['J03','J08']}}
materials = {
 'sword': [['锻钢','棕皮革','铁'],['精锻钢','银饰','深棕皮革'],['银钢','红宝石','绛红皮革'],['月纹钢','紫晶','银制镂空护手'],['海蓝钢','蓝宝石','分段银制雷翼']],
 'bow':[['白蜡木','皮革','角'],['层压紫杉木','钢帽','皮革'],['银木','雕银','绿晶'],['黑木','紫晶','悬浮银撑'],['深蓝木','星蓝宝石','轨道银架']],
 'staff':[['灰木','石英','皮革'],['胡桃木','银制笼架','石英'],['染蓝灰木','蓝晶','螺旋银架'],['黑木','紫晶','双层星环'],['星纹蓝钢','星钻','三轨银环']],
 'oath':[['铁','灰布','旧皮'],['精钢','灰麻','皮革'],['银钢','锁子甲','红宝石'],['夜钢','紫晶','银镂空','蓝布'],['蓝钢','蓝宝石','银制雷翼','夜蓝布']],
 'wind':[['棕皮革','苔绿旧布','亚麻'],['栗色层皮','灰羊毛','银扣'],['银叶护片','绿晶','棕绿皮革'],['蓝绿皮革','紫晶','镂空银羽'],['夜绿皮革','翡翠','银鹿角结构','蓝绿织物']],
 'seeker':[['粗灰羊毛','皮带','石英'],['蓝布','灰麻','银线'],['夜蓝织物','蓝宝石','星图刺绣'],['紫蓝丝绸','紫晶','镂空银架'],['星蓝丝绸','星钻','银轨道冠','蓝宝石']],
 'jewelry':[['旧铁','木','皮绳'],['银','木嵌片'],['银叶托','绿晶'],['黑银','紫晶','开环托架'],['银','星蓝宝石','星钻','轨道结构']],
}
features = [ ['可信基础形制','无魔法结构'], ['精确工艺','结构与层次改进'], ['独立宝石','主题雕刻或符纹'], ['镂空结构','多段符文与悬浮构件'], ['完整魔法结构','大切面主宝石','华丽且主轮廓可读'] ]
grips = {'sword':[(183,802),(490,803),(810,802),(1121,804),(1437,805)],'bow':[(133,453),(486,454),(828,453),(1154,456),(1494,474)],'staff':[(207,465),(535,467),(866,471),(1210,468),(1562,470)]}
# All slotRects are absolute image pixel coordinates, top-left origin.
slot_boxes={
 'oath': [
  {'head':[190,145,100,115],'chest':[145,265,200,315],'hands':[302,480,52,85],'feet':[164,631,155,155],'offhand':[57,458,115,122]},
  {'head':[490,148,125,90],'chest':[470,260,182,355],'hands':[614,480,45,87],'feet':[490,630,153,157],'offhand':[380,448,88,145]},
  {'head':[820,152,122,86],'chest':[793,258,182,357],'hands':[944,480,43,86],'feet':[806,631,155,157],'offhand':[695,448,90,146]},
  {'head':[1135,130,111,117],'chest':[1107,260,182,360],'hands':[1262,480,43,87],'feet':[1119,630,155,157],'offhand':[1003,444,91,152]},
  {'head':[1414,91,216,154],'chest':[1415,252,231,373],'hands':[1615,476,42,86],'feet':[1449,628,168,162],'offhand':[1315,432,108,182]}],
 'wind':[
  {'head':[160,136,121,126],'chest':[117,262,213,375],'hands':[290,455,44,85],'feet':[143,637,149,154]},
  {'head':[485,139,119,124],'chest':[443,265,211,370],'hands':[620,452,41,92],'feet':[469,636,143,156]},
  {'head':[812,137,126,129],'chest':[764,265,224,370],'hands':[954,452,44,96],'feet':[798,635,149,157]},
  {'head':[1135,134,126,133],'chest':[1090,267,223,370],'hands':[1278,454,42,94],'feet':[1127,635,151,158]},
  {'head':[1429,77,240,197],'chest':[1428,273,247,363],'hands':[1640,449,48,97],'feet':[1483,635,137,157]}],
 'seeker':[
  {'head':[192,141,117,122],'chest':[144,268,208,415],'hands':[324,440,45,93],'feet':[183,696,126,111],'offhand':[115,534,46,84]},
  {'head':[502,153,120,104],'chest':[461,259,217,420],'hands':[643,444,42,90],'feet':[504,697,121,111],'offhand':[414,533,68,87]},
  {'head':[817,141,136,126],'chest':[783,265,220,415],'hands':[965,444,43,88],'feet':[829,697,120,111],'offhand':[727,532,67,86]},
  {'head':[1144,132,111,107],'chest':[1085,259,229,452],'hands':[1280,444,43,91],'feet':[1141,699,116,111],'offhand':[1031,530,88,93]},
  {'head':[1444,80,178,163],'chest':[1421,264,226,447],'hands':[1627,443,42,94],'feet':[1483,698,111,112],'offhand':[1351,531,99,101]}],
}
manifest={'version':3,'coordinateSystem':'top-left image pixels; rect/slotRects absolute; grip relative to item rect','generator':'built-in image_gen','pixelPolicy':'Generated PNG bytes copied without pixel modification. PIL reads alpha only to measure metadata.','grades':[{'grade':i+1,'name':v} for i,v in enumerate(['普通','精良','稀有','史诗','传奇'])],'images':{},'items':{}}
provenance={}
for family in names:
 path=SOURCE / f'{family}-progression.png'
 im=Image.open(path); alpha=im.getchannel('A'); solid=alpha.point(lambda v:255 if v>=128 else 0)
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 manifest['images'][family]={'resource':f'equipment/v3/{family}-progression','width':im.width,'height':im.height,'sha256':sha}
 provenance[family]={'source':path.name,'runtime':str((RUNTIME/path.name).relative_to(ROOT)).replace('\\','/'),'sha256':sha,'mode':im.mode,'size':[im.width,im.height],'alphaExtrema':list(alpha.getextrema()),'materialBoundsAlpha128':list(solid.getbbox()),'sourcePixelsPreserved':True}
 for idx,name in enumerate(names[family]):
  left,right=bounds[family][idx:idx+2]; bb=solid.crop((left,0,right,im.height)).getbbox()
  x0=max(left,left+bb[0]-8); y0=max(0,bb[1]-8); x1=min(right,left+bb[2]+8); y1=min(im.height,bb[3]+8)
  art={'image':family,'rect':[x0,y0,x1-x0,y1-y0],'family':family,'grade':idx+1,'name':name,'materials':materials[family][idx],'features':features[idx],'existingIds':existing.get(family,{}).get(idx+1,[]),'availability':'existing-art' if existing.get(family,{}).get(idx+1) else 'future-design-only'}
  if family in grips:
   gx,gy=grips[family][idx]; art['grip']=[gx-x0,gy-y0]; art['normalizedGrip']=[round((gx-x0)/(x1-x0),5),round((gy-y0)/(y1-y0),5)]
  if family in slot_boxes: art['slotRects']=slot_boxes[family][idx]
  if family=='jewelry':
   colx=max(left,x0); colr=min(right,x1)
   art['slotRects']={'ringLeft':[colx,45,colr-colx,280],'ringRight':[colx,45,colr-colx,280],'necklace':[colx,365,colr-colx,465]}
  manifest['items'][f'ART_{family.upper()}_{idx+1}']=art
for dest in [SOURCE/'manifest.json',RUNTIME/'manifest.json']:
 dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(SOURCE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'items':len(manifest['items']),'images':len(manifest['images']),'existingIds':[e for v in manifest['items'].values() for e in v['existingIds']],'shaMatch':all(hashlib.sha256((RUNTIME/f'{f}-progression.png').read_bytes()).hexdigest()==provenance[f]['sha256'] for f in names)},ensure_ascii=False))
