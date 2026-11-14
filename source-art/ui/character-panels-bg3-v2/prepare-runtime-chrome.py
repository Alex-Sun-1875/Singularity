"""Extract the approved mockup's empty chrome; preserve editable native UI text."""
from pathlib import Path
import hashlib
import json
import uuid
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT.parents[2]/'src/cocos/assets/resources/ui/quiet-bronze'
src=Image.open(ROOT/'screens/01-preview.png').convert('RGBA')

def save(image,name):
    target=ASSETS/(name+'.png')
    image.save(target)
    meta=Path(str(target)+'.meta')
    if not meta.exists():
        template=json.loads((ASSETS/'leather-inset-v8.png.meta').read_text(encoding='utf8'))
        text=json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace('leather-inset-v8',name).replace('repeat','clamp-to-edge')
        meta.write_text(text,encoding='utf8')
    return {'file':target.relative_to(ROOT.parents[2]).as_posix(),'size':list(image.size),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}

def frame(rect):
    im=src.crop(rect)
    mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask);w,h=im.size
    d.rectangle((0,0,w-1,h-1),outline=255,width=4)
    for x,y in [(0,0),(w-26,0),(0,h-26),(w-26,h-26)]:d.rectangle((x,y,x+25,y+25),fill=255)
    im.putalpha(mask);return im

def empty_button(rect):
    im=src.crop(rect);w,h=im.size
    for y in range(8,h-8):
        values=[im.getpixel((x,y)) for x in range(14,w-14)]
        color=tuple(sorted(p[c] for p in values)[len(values)//2] for c in range(3))+(255,)
        for x in range(12,w-12):im.putpixel((x,y),color)
    return im

records=[]
records.append(save(frame((1,1,1843,852)),'rpg-outer-frame-v2'))
records.append(save(frame((40,159,522,720)),'rpg-inner-frame-v2'))
records.append(save(empty_button((1158,758,1518,827)),'rpg-button-gold-v2'))
records.append(save(empty_button((1544,758,1818,827)),'rpg-button-dark-v2'))
texture=src.crop((1490,78,1790,146)).resize((512,256),Image.Resampling.LANCZOS)
texture=ImageOps.colorize(ImageOps.grayscale(texture),'#15100b','#66503a').convert('RGBA')
records.append(save(texture,'rpg-surface-v2'))
for name,rect in [('rpg-logo-v2',(68,7,220,58)),('rpg-anvil-v2',(68,90,148,139))]:
    icon=src.crop(rect)
    for y in range(icon.height):
        for x in range(icon.width):
            r,g,b,_=icon.getpixel((x,y));icon.putpixel((x,y),(r,g,b,max(0,min(255,(max(r,g,b)-45)*5))))
    records.append(save(icon,name))
equipment=Image.open(ROOT.parent/'character-panels-bg3-v1/screens/02-equipment.png').convert('RGBA')
for name,rect in {'sword':(710,218,824,329),'bow':(850,220,960,330),'staff':(989,221,1096,329),'head':(108,168,200,255),'hands':(108,291,198,382),'feet':(530,623,617,707),'chest':(1127,222,1233,329),'ring':(109,547,196,632),'necklace':(531,163,618,251),'offhand':(530,420,618,505)}.items():
    records.append(save((src.crop((84,251,170,335)) if name=='sword' else equipment.crop(rect)).resize((192,192),Image.Resampling.LANCZOS),'rpg-equipment-'+name))

room=Image.open(ROOT/'sources/room-empty-generated.png').convert('RGBA')
records.append(save(room.resize((1024,544),Image.Resampling.LANCZOS),'forge-room-v2'))
records.append(save(room.crop((70,0,700,740)).resize((640,752),Image.Resampling.LANCZOS),'character-room-v2'))
for name,rect in [('rpg-coin-v2',(1440,14,1484,55)),('rpg-campfire-v2',(48,758,129,827))]:
    icon=src.crop(rect)
    for y in range(icon.height):
        for x in range(icon.width):
            r,g,b,_=icon.getpixel((x,y));icon.putpixel((x,y),(r,g,b,max(0,min(255,(max(r,g,b)-45)*5))))
    records.append(save(icon,name))
character=Image.open(ROOT.parent/'character-panels-bg3-v1/screens/01-character.png').convert('RGBA')
for key,rect in {'strength':(696,202,785,280),'dexterity':(697,316,785,395),'intellect':(697,443,785,512),'vitality':(696,545,785,628)}.items():
    icon=character.crop(rect)
    for y in range(icon.height):
        for x in range(icon.width):
            r,g,b,_=icon.getpixel((x,y));icon.putpixel((x,y),(r,g,b,max(0,min(255,(max(r,g,b)-48)*5))))
    records.append(save(icon,'rpg-attribute-'+key))
(ROOT/'runtime-chrome.json').write_text(json.dumps({'source':'screens/01-preview.png; ../character-panels-bg3-v1/screens/01-character.png; ../character-panels-bg3-v1/screens/02-equipment.png','method':'Pillow crop, per-row median to remove button lettering, border alpha extraction and alpha-keyed static icons. Empty room generated separately; see room-background-provenance.json. Dynamic values remain native labels.','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
preview=Image.new('RGBA',(1200,430),'#100C08');preview.alpha_composite(room.resize((680,360)),(0,0));preview.alpha_composite(Image.open(ASSETS/'rpg-button-gold-v2.png'),(700,10));preview.alpha_composite(Image.open(ASSETS/'rpg-button-dark-v2.png'),(700,100));preview.convert('RGB').save(ROOT/'review/runtime-chrome.jpg',quality=94)
print('Extracted approved chrome and room background without baking gameplay values.')
