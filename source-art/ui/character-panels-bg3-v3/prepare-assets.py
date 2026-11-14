"""Re-use approved pixels; only the archived small wall patch was generated."""
from pathlib import Path
import hashlib,json,uuid,shutil
from PIL import Image,ImageDraw,ImageFilter,ImageOps,ImageChops
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUT=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze'
REF=ROOT.parent/'character-panels-bg3-v1/screens'
character=Image.open(REF/'01-character.png').convert('RGBA')
equipment=Image.open(REF/'02-equipment.png').convert('RGBA')
skills=Image.open(REF/'03-skills.png').convert('RGBA')
forge=Image.open(ROOT.parent/'character-panels-bg3-v2/screens/01-preview.png').convert('RGBA')
records=[]
def save(im,name):
 p=OUT/(name+'.png');im.save(p)
 meta=Path(str(p)+'.meta')
 if not meta.exists():
  template=json.loads((OUT/'rpg-surface-v2.png.meta').read_text(encoding='utf8'))
  meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('rpg-surface-v2',name)+'\n',encoding='utf8')
 records.append({'file':p.relative_to(PROJECT).as_posix(),'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def edge(im,width=6,corner=24):
 im=im.copy();m=Image.new('L',im.size);d=ImageDraw.Draw(m);w,h=im.size
 d.rectangle((0,0,w-1,h-1),outline=255,width=width)
 for x,y in [(0,0),(w-corner,0),(0,h-corner),(w-corner,h-corner)]:d.rectangle((x,y,x+corner-1,y+corner-1),fill=255)
 im.putalpha(m);return im
def key(im):
 im=im.copy()
 im.putalpha(im.convert('RGB').point(lambda n:max(0,min(255,(n-55)*3))).convert('L'))
 return im
def button(rect,source=forge):
 im=source.crop(rect);w,h=im.size
 # Keep original metal bevels; smooth the letter-free median field to avoid stripes.
 field=im.copy()
 for y in range(7,h-7):
  values=[im.getpixel((x,y)) for x in range(12,w-12)]
  c=tuple(sorted(p[k] for p in values)[len(values)//2] for k in range(3))+(255,)
  ImageDraw.Draw(field).line((12,y,w-13,y),fill=c)
 field=field.filter(ImageFilter.GaussianBlur(2))
 im.paste(field.crop((14,9,w-14,h-9)),(14,9));return im
save(edge(character,10,30),'rpg-outer-frame-v3')
save(edge(character.crop((655,70,1267,713)),5,22),'rpg-inner-frame-v3')
save(character.crop((0,734,1844,752)),'rpg-section-divider-v3')
save(character.crop((453,57,677,69)),'rpg-active-rule-v3')
save(button((1158,758,1518,827)),'rpg-button-gold-v3')
save(button((1544,758,1818,827)),'rpg-button-dark-v3')
save(button((40,89,241,149),skills),'rpg-tab-selected-v3')
selection=edge(forge.crop((60,237,511,348)),14,20)
brightness=selection.convert('RGB').point(lambda n:max(0,min(255,(n-45)*4))).convert('L')
selection.putalpha(ImageChops.multiply(selection.getchannel('A'),brightness))
save(selection,'rpg-selection-frame-v3')
save(edge(skills.crop((80,375,231,509)),5,11),'rpg-icon-frame-v3')
tile=character.crop((674,645,1250,706));material=Image.new('RGBA',(576,576))
for n,y in enumerate(range(0,576,tile.height)):material.paste(ImageOps.flip(tile) if n%2 else tile,(0,y))
save(material,'rpg-material-v3')
cloth=character.crop((1772,76,1835,735));mask=Image.new('L',cloth.size)
for x in range(cloth.width):ImageDraw.Draw(mask).line((x,0,x,cloth.height),fill=int(255*x/(cloth.width-1)))
cloth.putalpha(mask);save(cloth,'rpg-drape-v3')
badge=skills.crop((212,195,294,227));empty=Image.new('RGBA',badge.size,'#20170e');empty.alpha_composite(edge(badge,3,4));save(empty,'rpg-type-badge-v3')
plate=Image.new('RGBA',(280,257));d=ImageDraw.Draw(plate)
for x in range(280):d.line((x,0,x,257),fill=(10,8,6,int(190*min(1,(280-x)/40))))
plate.alpha_composite(character.crop((0,394,280,419)),(0,0));save(plate,'rpg-nameplate-v3')
wall=ROOT/'sources/identity-wall-generated.png'
wall.parent.mkdir(exist_ok=True)
if not wall.exists():shutil.copy2('C:/Users/Alexa/.codex/generated_images/01a1c46b-eff4-7a71-a1ee-6621fccd0eb5/exec-fa471322-8572-4ae2-b805-6b5cc709813a.png',wall)
scene=character.crop((0,70,655,740));patch=Image.open(wall).convert('RGBA').resize((312,281),Image.Resampling.LANCZOS)
mask=Image.new('L',(312,281));ImageDraw.Draw(mask).polygon([(0,0),(280,0),(280,50),(312,50),(312,281),(0,281)],fill=255)
# Feather outside the former lettering/bars, protect the original hand at x>=299,y<430.
for y in range(281):
 for x in range(312):
  limit=280 if y<50 else 312
  alpha=int(255*min(1,y/12,(280-y)/12,max(0,(limit-1-x)/12)))
  mask.putpixel((x,y),max(0,alpha))
patch.putalpha(mask);scene.alpha_composite(patch,(0,310));save(scene,'rpg-approved-hero-scene-v3')
for name,rect in {'war':(80,100,122,138),'bow':(285,100,326,138),'fir':(481,100,515,139),'thu':(667,99,701,138),'com':(840,99,882,138)}.items():save(key(skills.crop(rect)),'rpg-family-'+name+'-v3')
for name,rect in {'power':(1314,175,1358,211),'armor':(1314,219,1357,256),'criticalChance':(1314,267,1357,307),'speed':(1314,313,1357,352)}.items():save(key(character.crop(rect)),'rpg-stat-'+name+'-v3')
save(key(forge.crop((1578,564,1617,600))),'rpg-iron-v3')
save(key(forge.crop((646,669,672,700))),'rpg-lock-v3')
save(key(forge.crop((1576,773,1624,812))),'rpg-return-arrow-v3')
# Exact approved sword silhouette, traced in a 3x review crop; no model regeneration.
points=[(231,20),(254,24),(273,40),(278,61),(274,81),(259,94),(253,115),(244,134),(241,151),(235,174),(232,193),(225,215),(221,235),(216,259),(211,274),(231,281),(251,287),(273,295),(296,304),(314,312),(337,323),(334,345),(319,339),(297,329),(277,324),(256,321),(239,324),(226,336),(217,357),(218,373),(208,398),(200,437),(193,476),(187,512),(175,566),(164,617),(154,667),(145,712),(134,760),(118,814),(106,851),(90,888),(77,918),(68,929),(56,927),(50,905),(47,877),(48,850),(51,816),(57,780),(65,734),(73,688),(83,638),(91,589),(99,544),(107,494),(112,461),(121,410),(125,382),(128,354),(124,332),(116,321),(107,314),(95,312),(75,313),(53,318),(38,325),(33,322),(31,304),(49,296),(75,288),(103,282),(132,278),(158,272),(160,255),(165,232),(171,208),(177,188),(180,168),(183,147),(191,125),(196,105),(197,90),(204,84),(192,78),(189,65),(190,48),(200,34),(216,24)]
sword=forge.crop((814,160,953,480));mask=Image.new('L',(556,1280));ImageDraw.Draw(mask).polygon([(round(x*4/3),round(y*4/3)) for x,y in points],fill=255);sword.putalpha(mask.resize(sword.size,Image.Resampling.LANCZOS));save(sword,'rpg-approved-sword-v3')
(ROOT/'runtime-assets.json').write_text(json.dumps({'method':'Original approved artwork crops and alpha masks; original hero and arch pixels preserved. One small generated text-removal wall patch composited at source [0,380,280,661]; dynamic text remains native.','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Exported',len(records),'alignment assets.')
