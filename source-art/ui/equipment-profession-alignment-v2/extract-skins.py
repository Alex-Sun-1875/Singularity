"""Deterministic component extraction from the five approved UI proposals.
No full screenshot is used as an interactive screen; all changing text remains native.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import json, hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'source-art/ui/equipment-profession-points-v1'
OUT=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
screens={n:Image.open(SOURCE/f'{name}.png').convert('RGBA') for n,name in {
 1:'01-equipment-current',2:'02-equipment-all',3:'03-profession-preview',4:'04-attribute-points',5:'05-skill-points'}.items()}
records=[]
def save(name,image,screen,box,method):
 p=OUT/f'prep-{name}-v2.png';image.save(p)
 records.append({'file':p.name,'screen':screen,'source_box':box,'method':method,'size':image.size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 return image
def crop(name,screen,box,feather=0):
 im=screens[screen].crop(box)
 if feather:
  mask=Image.new('L',im.size,0);ImageDraw.Draw(mask).rounded_rectangle((feather,feather,im.width-feather-1,im.height-feather-1),radius=feather*2,fill=255)
  im.putalpha(mask.filter(ImageFilter.GaussianBlur(max(1,feather/2))))
 return save(name,im,screen,box,'crop; soft edge alpha' if feather else 'crop')
def blank(name,screen,box,margin=15,keep_middle=False,outline=False):
 im=screens[screen].crop(box);d=ImageDraw.Draw(im)
 # Interior texture is sampled from the same component's empty upper band.
 patch=im.crop((margin,margin//2,im.width-margin,max(margin//2+3,margin-2)))
 if outline:
  mask=Image.new('L',im.size,255);ImageDraw.Draw(mask).rounded_rectangle((margin,margin,im.width-margin-1,im.height-margin-1),radius=max(2,margin//2),fill=0)
  im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
 else:
  if name in ['plaque','skill-cost']:margin=30
  my=4 if im.height<80 or name=='skill-row' else margin
  base=Image.new('RGBA',(im.width-2*margin,im.height-2*my),(15,11,8,255))
  if name in ['button-dark','button-gold','step']:
   strip=im.crop((margin+7,my,margin+9,im.height-my))
   base=strip.resize(base.size,Image.Resampling.BICUBIC)
  if name in ['chip','badge-teal']:base=Image.new('RGBA',base.size,screens[1].getpixel((631,210)))
  if name=='badge-gold':
   fill=Image.new('RGBA',im.size,(28,21,12,255));mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([(11,5),(78,5),(86,18),(78,31),(11,31),(4,18)],fill=255);im.paste(fill,(0,0),mask)
  else:im.paste(base,(margin,my))
  if keep_middle:
   y=im.height//2;im.paste(screens[screen].crop((box[0]+margin,box[1]+y-2,box[2]-margin,box[1]+y+2)),(margin,y-2))
 return save(name,im,screen,box,'blank native-text interior; retain original metal perimeter'+('; transparent interior' if outline else ''))
def gold(name,screen,box):
 im=screens[screen].crop(box);mask=Image.new('L',im.size);px=im.load();a=mask.load()
 for y in range(im.height):
  for x in range(im.width):
   r,g,b,_=px[x,y];a[x,y]=round(max(0,min(1,(max(r,g,b)-38)/90))*255) if r>=b*.95 else 0
 im.putalpha(mask);return save(name,im,screen,box,'extract warm-metal motif alpha; retain source RGB')

im=screens[3].copy();mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask);d.rectangle((0,0,1843,852),outline=255,width=4)
for x,y in [(0,0),(1814,0),(0,823),(1814,823)]:d.rectangle((x,y,x+29,y+29),fill=255)
im.putalpha(mask)
# Compact nine-patch: keep the original 32 px corners without a full-screen texture.
compact=Image.new('RGBA',(96,96));edges=[(0,32,0,32),(32,64,32,1812),(64,96,1812,1844)]
vertical=[(0,32,0,32),(32,64,32,821),(64,96,821,853)]
for dx0,dx1,sx0,sx1 in edges:
 for dy0,dy1,sy0,sy1 in vertical:compact.paste(im.crop((sx0,sy0,sx1,sy1)).resize((dx1-dx0,dy1-dy0),Image.Resampling.BICUBIC),(dx0,dy0))
save('frame',compact,3,(0,0,1844,853),'original corners/perimeter compacted to 96px nine-patch; transparent interior')
crop('header',3,(1364,7,1498,55))
crop('surface',3,(1267,675,1827,733))
gold('logo',3,(78,11,232,53))
blank('button-dark',3,(951,760,1218,831),17)
blank('button-gold',3,(1238,760,1522,831),18)
blank('step',4,(1172,137,1266,232),13)
blank('card',3,(471,108,841,384),8)
blank('card-selected',3,(854,106,1229,385),8,outline=True)
blank('attribute-row',4,(417,116,1289,249),13)
blank('skill-row',5,(557,158,1220,261),14)
blank('skill-selected',5,(553,271,1223,375),5,outline=True)
blank('scope',1,(596,96,1217,160),11)
blank('categories',1,(594,182,1218,241),10)
blank('chip',1,(594,183,750,240),12)
blank('badge-gold',1,(944,395,1042,432),9)
blank('badge-teal',3,(725,119,819,161),10)
blank('plaque',3,(55,633,415,681),12)
blank('point-counter',4,(28,590,379,719),14,keep_middle=True)
blank('skill-cost',5,(1376,193,1718,245),11)
gold('rule',3,(1294,187,1808,203))
gold('active',3,(696,56,877,70))
gold('shell-rule',3,(6,739,1838,754))
gold('crest-sword',4,(154,326,258,438))
gold('stat-life',4,(1346,216,1393,256))
gold('stat-power',4,(1346,303,1394,351))
gold('stat-plan',4,(1347,407,1396,456))
gold('stat-target',5,(1292,267,1339,311))
gold('stat-radius',5,(1292,330,1341,376))
gold('info',3,(1307,625,1341,660))
crop('hero',3,(8,69,443,629))
crop('hero-narrow',5,(8,76,284,735))
for name,box in {'strength':(439,126,575,231),'dexterity':(438,280,575,385),'intellect':(437,430,578,536),'vitality':(440,583,576,684)}.items():crop('attribute-'+name,4,box,5)
for name,box in {'sword':(608,280,734,395),'head':(925,279,1057,394),'chest':(1082,280,1207,393),'hands':(606,469,734,582),'feet':(768,469,897,584),'necklace':(925,469,1055,581),'ring':(1082,469,1208,583)}.items():crop('item-'+name,1,box,4)
crop('item-bow',2,(912,249,1034,337),4)
crop('item-staff',2,(610,400,726,476),4)
gold('stat-level',1,(1286,419,1337,465))
gold('stat-weapon',1,(1287,472,1336,512))
gold('stat-upgrade',1,(1289,522,1337,568))
gold('stat-source',1,(1290,626,1339,662))
crop('inspect-sword',1,(1242,74,1824,282),5)
crop('inspect-staff',2,(1524,74,1836,336),5)
crop('smoke',3,(875,111,1090,141),6)

(HERE/'skin-exports.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
thumbs=Image.new('RGB',(1100,((len(records)+4)//5)*155),'#0c0907');d=ImageDraw.Draw(thumbs)
for i,row in enumerate(records):
 im=Image.open(OUT/row['file']);im.thumbnail((206,120));x=(i%5)*220;y=(i//5)*155;thumbs.paste(im,(x+(210-im.width)//2,y),im);d.text((x+4,y+125),row['file'].replace('prep-','').replace('-v2.png',''),fill='#EDE4CB')
thumbs.save(HERE/'02-extracted-skins.jpg',quality=95)
print(f'Exported {len(records)} original-design components; native text interiors cleared.')
