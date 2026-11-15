"""Export the user-approved draft pixels to Cocos; no model call or new dependency."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json, shutil, uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'src/cocos/assets/resources/ui/boss-awareness'
OUT.mkdir(exist_ok=True)
for name in ['tool-face','row','row-selected','captain','overseer','warden','huntmaster','beast','oath','golem']:
    shutil.copy2(HERE/f'assets/{name}.png',OUT/f'{name}.png')
tool_face=Image.open(OUT/'tool-face.png').convert('RGBA')
tool_mask=Image.new('L',tool_face.size);ImageDraw.Draw(tool_mask).ellipse((0,0,tool_face.width-1,tool_face.height-1),fill=255)
tool_face.putalpha(tool_mask);tool_face.save(OUT/'tool-face.png')

# Bake the final CSS filter into the small runtime sprite, without changing alpha.
record=json.loads((HERE/'provenance.json').read_text())['entryIdentity']['displayTreatment']
bright,sat,sepia=(record[k] for k in ['brightness','saturation','sepia'])
im=Image.open(HERE/'assets/boss-entry-beast-v1.png').convert('RGBA')
pixels=[]
for r,g,b,a in im.getdata():
    r,g,b=(min(255,c*bright) for c in (r,g,b))
    lum=.213*r+.715*g+.072*b
    r,g,b=(lum+(c-lum)*sat for c in (r,g,b))
    sr=.393*r+.769*g+.189*b;sg=.349*r+.686*g+.168*b;sb=.272*r+.534*g+.131*b
    pixels.append(tuple(round(max(0,min(255,v))) for v in (r+(sr-r)*sepia,g+(sg-g)*sepia,b+(sb-b)*sepia))+(a,))
im.putdata(pixels);im.save(OUT/'boss-entry.png')

# Wild alphas use their actual hound identity, not the optional ridgebreaker boss.
src=ROOT/'src/cocos/assets/resources/flat2d/characters/thorn-hound'
m=json.loads((src/'manifest.json').read_text())
head=Image.open(src/'atlas.png').convert('RGBA').crop((0,0,m['frameWidth'],m['frameHeight'])).crop((73,107,155,189)).resize((132,132),Image.Resampling.LANCZOS)
face=Image.open(HERE/'assets/tool-face.png').convert('RGBA').resize((132,132));face.alpha_composite(head)
mask=Image.new('L',(132,132));ImageDraw.Draw(mask).ellipse((0,0,131,131),fill=255)
face.putalpha(ImageChops.multiply(face.getchannel('A'),mask))
portrait=Image.new('RGBA',(144,144));portrait.alpha_composite(face,(6,6))
portrait.alpha_composite(Image.open(ROOT/'src/cocos/assets/resources/ui/quiet-bronze/unified-gold-ring-v16.png').convert('RGBA').resize((144,144),Image.Resampling.LANCZOS))
portrait.save(OUT/'alpha.png')

def uid(path):return str(uuid.uuid5(uuid.NAMESPACE_URL,str(path.relative_to(ROOT))))
folder=OUT.with_suffix('.meta')
if not folder.exists():folder.write_text(json.dumps({'ver':'1.2.0','importer':'directory','imported':True,'uuid':uid(OUT),'files':[],'subMetas':{},'userData':{}},indent=2)+'\n')
template=json.loads((ROOT/'src/cocos/assets/resources/ui/quiet-bronze/automation-battle-v5.png.meta').read_text())
for image in OUT.glob('*.png'):
    meta=image.with_suffix('.png.meta')
    if meta.exists():continue
    spec=json.loads(json.dumps(template));u=uid(image);spec['uuid']=u;spec['subMetas']['6c48a']['uuid']=u+'@6c48a';spec['subMetas']['6c48a']['displayName']=image.stem
    user=spec['subMetas']['6c48a']['userData'];user['imageUuidOrDatabaseUri']=u;user['wrapModeS']=user['wrapModeT']='clamp-to-edge'
    spec['userData']['redirect']=u+'@6c48a';meta.write_text(json.dumps(spec,indent=2)+'\n')
(HERE/'runtime-export.json').write_text(json.dumps({'date':'2026-11-15','approvedDesign':'fixed-entry-tone-v3.png','output':str(OUT.relative_to(ROOT)),'entryFilterBaked':record,'portraitSource':'Existing per-character approved draft crops; alpha from runtime thorn-hound','userApprovedDesign':True,'platformValidated':False},ensure_ascii=False,indent=2)+'\n')
print('Exported approved runtime icons, portraits and row skins')
