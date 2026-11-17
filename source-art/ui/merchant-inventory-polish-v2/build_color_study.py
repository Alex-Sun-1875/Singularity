from pathlib import Path
import json, uuid
import numpy as np
from PIL import Image, ImageOps

here = Path(__file__).resolve().parent
root = here.parents[2]
target = root / 'src/cocos/assets/resources/equipment/gems-polished-v1'
target.mkdir(parents=True, exist_ok=True)
source = Image.open(here / 'gem-original.png').convert('RGBA')
box = source.getchannel('A').point(lambda v: 255 if v > 12 else 0).getbbox()
source = ImageOps.contain(source.crop(box), (226, 226), Image.Resampling.LANCZOS)
base = Image.new('RGBA', (256, 256)); base.alpha_composite(source, ((256-source.width)//2, (256-source.height)//2))
pixels = np.asarray(base).astype(np.float32)/255
light = pixels[:,:,:3].mean(axis=2, keepdims=True)
palette = {'power':(.80,.14,.16),'maxHp':(.08,.64,.38),'armor':(.13,.42,.82),'criticalChance':(.88,.56,.13),'criticalDamage':(.59,.25,.84)}
template = json.loads((root / 'src/cocos/assets/resources/equipment/supplies-v2/health-bottle.png.meta').read_text(encoding='utf-8'))
for name, color in palette.items():
    tint = np.array(color, dtype=np.float32).reshape(1,1,3)
    low = tint * np.clip(light/.70, 0, 1)**.85
    highlight = np.clip((light-.70)/.30, 0, 1)**1.35
    rgb = np.clip(low*(1-highlight)+np.array([1,.97,.92])*highlight,0,1)
    out = np.concatenate((rgb, pixels[:,:,3:4]), axis=2)
    Image.fromarray(np.round(out*255).astype(np.uint8), 'RGBA').save(target/(name+'.png'), optimize=True)
    meta = json.loads(json.dumps(template)); identity = str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gems-polished-v1/'+name))
    meta['uuid']=identity; meta['userData']['redirect']=identity+'@6c48a'
    texture=meta['subMetas']['6c48a']; texture['uuid']=identity+'@6c48a'; texture['displayName']=name;texture['userData']['imageUuidOrDatabaseUri']=identity
    (target/(name+'.png.meta')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
folder={'ver':'1.2.0','importer':'directory','imported':True,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gems-polished-v1')),'files':[],'subMetas':{},'userData':{}}
target.with_name(target.name+'.meta').write_text(json.dumps(folder,indent=2)+'\n',encoding='utf-8')
preview=Image.new('RGB',(640,128),(18,15,12))
for i,name in enumerate(palette):
    icon=Image.open(target/(name+'.png')).resize((110,110),Image.Resampling.LANCZOS);preview.paste(icon,(128*i+9,9),icon)
preview.save(here/'gem-icons-preview.jpg',quality=94)
print(json.dumps({'icons':5,'sourceAlphaExtrema':base.getchannel('A').getextrema(),'runtimeBytes':sum(p.stat().st_size for p in target.glob('*.png'))}))
