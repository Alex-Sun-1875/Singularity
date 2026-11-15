"""Deterministic skin extraction and alpha compositing from the accepted v2 art."""
from pathlib import Path
import json
import math
import uuid
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
ASSETS=REPO/'src/cocos/assets'
UI=ASSETS/'resources/ui/quiet-bronze'

source=Image.open(ROOT/'legendary-generated-v2.png').convert('RGBA')
panel=source.crop((598,14,1246,169))
# Replace the illustrated icon and baked words with the same panel's clean grain.
tile=source.crop((1152,39,1211,142))
tile=tile.resize((tile.width,panel.height-38),Image.Resampling.LANCZOS)
inset=Image.new('RGBA',panel.size)
for x in range(20,panel.width-20,tile.width):
    inset.paste(tile if (x//tile.width)%2 else ImageOps.mirror(tile),(x,19))
mask=Image.new('L',panel.size)
ImageDraw.Draw(mask).rounded_rectangle((30,20,panel.width-31,panel.height-22),5,fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(2))
panel=Image.composite(inset,panel,mask)
silhouette=Image.new('L',panel.size)
ImageDraw.Draw(silhouette).polygon([(30,0),(618,0),(647,25),(647,129),(620,154),(28,154),(0,127),(0,27)],fill=255)
panel.putalpha(silhouette)
panel.save(UI/'loot-drop-panel-v1.png')

# White alpha is tinted by FeedbackPalette in Cocos. Layered soft lobes have no
# rigid beam/ring geometry; the one mesh contains the entire plume and its motes.
w,h=256,320
alpha=Image.new('L',(w,h))
pixels=[]
for y in range(h):
    t=y/(h-1)
    for x in range(w):
        u=(x-w/2)/(w/2)
        v=0.0
        for cx,cy,sx,sy,strength in [(-.02,.84,.35,.14,150),(.05,.65,.24,.19,85),(-.07,.43,.14,.17,45),(.04,.28,.09,.12,22)]:
            v+=strength*math.exp(-.5*((u-cx)/sx)**2-.5*((t-cy)/sy)**2)
        edge=min(1,max(0,t/.12))*min(1,max(0,(1-t)/.07))
        # Smooth low-frequency modulation keeps the aura's fade irregular.
        modulation=.88+.08*math.sin(x*.047+y*.028)+.04*math.sin(y*.083-x*.034)
        pixels.append(round(min(220,v)*edge*modulation))
alpha.putdata(pixels)
for x,y,r,opacity in [(144,117,2,145),(108,176,2,130),(151,209,2,160),(124,71,1,110)]:
    mote=Image.new('L',(w,h));ImageDraw.Draw(mote).ellipse((x-r,y-r,x+r,y+r),fill=opacity)
    mote=mote.filter(ImageFilter.GaussianBlur(.7))
    from PIL import ImageChops
    alpha=ImageChops.lighter(alpha,mote)
aura=Image.new('RGBA',(w,h),(255,255,255,0));aura.putalpha(alpha);aura.save(UI/'loot-drop-aura-v1.png')

ground_alpha=Image.new('L',(256,256))
ground_alpha.putdata([round(150*math.exp(-(((x-126)/65)**2+((y-131)/61)**2)*1.5)) for y in range(256) for x in range(256)])
arcs=Image.new('L',(256,256));ad=ImageDraw.Draw(arcs)
ad.arc((37,37,219,219),18,76,fill=55,width=2);ad.arc((44,44,212,212),189,231,fill=45,width=2)
from PIL import ImageChops
ground_alpha=ImageChops.lighter(ground_alpha,arcs.filter(ImageFilter.GaussianBlur(1.6)))
ground=Image.new('RGBA',(256,256),(255,255,255,0));ground.putalpha(ground_alpha);ground.save(UI/'loot-drop-ground-v1.png')

template=json.loads((UI/'skill-soft-halo-v17.png.meta').read_text(encoding='utf-8'))
for name in ['loot-drop-panel-v1','loot-drop-aura-v1','loot-drop-ground-v1']:
    file=UI/(name+'.png.meta')
    if file.exists(): continue
    meta=json.loads(json.dumps(template));uid=str(uuid.uuid4());meta['uuid']=uid
    meta['userData'].update(redirect=uid+'@6c48a',genMipmaps=False)
    tex=meta['subMetas']['6c48a'];tex['uuid']=uid+'@6c48a';tex['displayName']=name
    tex['userData'].update(imageUuidOrDatabaseUri=uid,wrapModeS='clamp-to-edge',wrapModeT='clamp-to-edge',mipfilter='none')
    file.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
file=ASSETS/'scripts/features/equipment/common/LootFeedback.ts.meta'
if not file.exists():
    meta=json.loads((ASSETS/'scripts/features/equipment/runtime/GroundLootPresentation.ts.meta').read_text(encoding='utf-8'))
    meta['uuid']=str(uuid.uuid4());file.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
review=Image.new('RGBA',(800,480),'#28221b');review.alpha_composite(panel,(76,30))
warm=Image.new('RGBA',aura.size,'#F5A45D');warm.putalpha(alpha);review.alpha_composite(warm,(272,170))
review.convert('RGB').save(ROOT/'runtime-skins-review.jpg',quality=94)
print('Prepared accepted-panel skin and soft-aura alpha; existing metadata is preserved.')
