"""Extract exact component perimeters from the accepted artwork, without new art."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SOURCE=ROOT/'source-art/ui/equipment-profession-points-v1'
OUT=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
rows=[]
def export(name,screen,box,margin=0,outline=False):
    im=Image.open(SOURCE/(screen+'.png')).convert('RGBA').crop(box)
    if outline:
        mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask)
        d.rounded_rectangle((1,1,im.width-2,im.height-2),radius=12,fill=255)
        d.rounded_rectangle((margin,margin,im.width-margin-1,im.height-margin-1),radius=6,fill=0)
        im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    elif margin:
        lo,hi=(22,im.height-20) if name=='side-tab-selected' else (10,im.height-10) if name=='side-tab' else (8,im.height-8)
        sample_x=im.width-44 if name=='side-tab' else margin
        strip=im.crop((sample_x,lo,sample_x+2,hi))
        im.paste(strip.resize((im.width-2*margin,hi-lo)),(margin,lo))
    p=OUT/('prep-'+name+'-v5.png');im.save(p)
    rows.append({'asset':str(p.relative_to(ROOT)).replace('\\','/'),'reference':screen+'.png','sourceBox':box,'method':'alpha-only perimeter extraction' if outline else 'reference texture crop; native text interior cleared','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
export('identity','01-equipment-current',(128,81,479,133),30)
export('socket','01-equipment-current',(55,209,154,309),8,True)
export('socket-selected','01-equipment-current',(95,571,215,688),12,True)
export('side-tab','04-attribute-points',(28,194,379,274),22)
export('side-tab-selected','04-attribute-points',(26,100,382,192),22)
export('scope-active','01-equipment-current',(596,96,908,160),28)
export('skill-selected','05-skill-points',(553,271,1223,375),12,True)
for name,screen,box in [
 ('item-steel-sword','01-equipment-current',(768,280,899,396)),
 ('item-blue-bow','02-equipment-all',(1071,248,1196,337)),
 ('item-lightning-staff','02-equipment-all',(766,393,891,477)),
 ('empty-offhand','01-equipment-current',(429,596,480,663))]:
 export(name,screen,box)
im=Image.open(SOURCE/'03-profession-preview.png').convert('RGBA').crop((1295,286,1339,332))
a=Image.new('L',im.size);px=im.load();mask=a.load()
for y in range(im.height):
 for x in range(im.width):
  r,g,b,_=px[x,y];mask[x,y]=round(max(0,min(1,(max(r,g,b)-38)/90))*255) if r>=b*.95 else 0
im.putalpha(a);p=OUT/'prep-weapon-bow-v5.png';im.save(p)
rows.append({'asset':str(p.relative_to(ROOT)).replace('\\','/'),'reference':'03-profession-preview.png','sourceBox':[1295,286,1339,332],'method':'warm-metal alpha extraction','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
# Replace the previous flat near-black text blanks with original empty material columns.
patches=[
 ('attribute-row','04-attribute-points',(417,116,1289,249),(1040,129,1042,236),13,13),
 ('skill-row','05-skill-points',(557,158,1220,261),(1035,162,1037,257),14,4),
 ('card','03-profession-preview',(471,108,841,384),(490,302,492,350),8,8),
 ('point-counter','04-attribute-points',(28,590,379,719),(350,604,352,705),14,14),
 ('skill-cost','05-skill-points',(1376,193,1718,245),(1410,199,1412,239),30,6),
]
for name,screen,box,sample,mx,my in patches:
 source=Image.open(SOURCE/(screen+'.png')).convert('RGBA');im=source.crop(box)
 im.paste(source.crop(sample).resize((im.width-2*mx,im.height-2*my)),(mx,my))
 p=OUT/('prep-'+name+'-v5.png');im.save(p)
 rows.append({'asset':str(p.relative_to(ROOT)).replace('\\','/'),'reference':screen+'.png','sourceBox':box,'emptyTextureSample':sample,'method':'retain original perimeter; refill native-text interior from original empty texture column','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
# Unmatte extracted gold instead of multiplying already blended source RGB twice.
legacy=json.loads((ROOT/'source-art/ui/equipment-profession-alignment-v2/skin-exports.json').read_text('utf-8'))
names={1:'01-equipment-current',2:'02-equipment-all',3:'03-profession-preview',4:'04-attribute-points',5:'05-skill-points'}
for old in legacy:
 if not old['method'].startswith('extract warm-metal'):continue
 screen=names[old['screen']];im=Image.open(SOURCE/(screen+'.png')).convert('RGBA').crop(old['source_box']);px=im.load();bg=(18,14,9)
 for y in range(im.height):
  for x in range(im.width):
   r,g,b,_=px[x,y];a=max(0,min(1,(r-bg[0])/(230-bg[0]))) if r>38 and r>=g and g>=b else 0
   px[x,y]=tuple(round(max(0,min(255,bg[i]+(c-bg[i])/a))) for i,c in enumerate((r,g,b)))+(round(a*255),) if a>.015 else (0,0,0,0)
 p=OUT/old['file'].replace('-v2.png','-v5.png');im.save(p)
 rows.append({'asset':str(p.relative_to(ROOT)).replace('\\','/'),'reference':screen+'.png','sourceBox':old['source_box'],'method':'warm gold unmatting over original18/14/9 matte; preserves source composite luminance','sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(HERE/'reference-parts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('Extracted',len(rows),'reference components')
