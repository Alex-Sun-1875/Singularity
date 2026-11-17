from pathlib import Path
import json, uuid
from PIL import Image, ImageOps, ImageFilter

here = Path(__file__).resolve().parent
root = here.parents[2]
target = root / 'src/cocos/assets/resources/equipment/gems-classic-v3'
target.mkdir(parents=True, exist_ok=True)
names = ['power','maxHp','armor','criticalChance','criticalDamage']
template = json.loads((root / 'src/cocos/assets/resources/equipment/supplies-v2/health-bottle.png.meta').read_text(encoding='utf-8'))
for name in names:
    source = Image.open(here / ('gem-'+name+'-original.png')).convert('RGBA')
    alpha = source.getchannel('A')
    source.putalpha(alpha.point(lambda v: 0 if v < 28 else v))
    box = source.getchannel('A').point(lambda v: 255 if v > 12 else 0).getbbox()
    source = ImageOps.contain(source.crop(box), (226, 226), Image.Resampling.LANCZOS)
    base = Image.new('RGBA', (256, 256)); base.alpha_composite(source, ((256-source.width)//2, (256-source.height)//2))
    base.save(target/(name+'.png'), optimize=True)
    meta = json.loads(json.dumps(template)); identity = str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gems-classic-v3/'+name))
    meta['uuid']=identity; meta['userData']['redirect']=identity+'@6c48a'
    texture=meta['subMetas']['6c48a']; texture['uuid']=identity+'@6c48a'; texture['displayName']=name;texture['userData']['imageUuidOrDatabaseUri']=identity
    (target/(name+'.png.meta')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
folder={'ver':'1.2.0','importer':'directory','imported':True,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gems-classic-v3')),'files':[],'subMetas':{},'userData':{}}
target.with_name(target.name+'.meta').write_text(json.dumps(folder,indent=2)+'\n',encoding='utf-8')
preview=Image.new('RGB',(640,128),(18,15,12))
for i,name in enumerate(names):
    icon=Image.open(target/(name+'.png')).resize((110,110),Image.Resampling.LANCZOS);preview.paste(icon,(128*i+9,9),icon)
preview.save(here/'gem-icons-preview.jpg',quality=94)
print(json.dumps({'icons':5,'sourceAlphaExtrema':base.getchannel('A').getextrema(),'runtimeBytes':sum(p.stat().st_size for p in target.glob('*.png'))}))
