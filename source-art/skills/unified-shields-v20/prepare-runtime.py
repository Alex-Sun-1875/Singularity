"""Pack approved interior motifs for the shared native 3D shield material."""
from pathlib import Path
import json,uuid,hashlib
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'src/cocos/assets/resources/vfx/production'
layers=[]
for family in ['WAR','BOW','FIR','THU']:
 source=Image.open(HERE.parent/'reference-seals-v3/assets'/f'{family}.png').convert('RGBA')
 a=np.asarray(source,dtype=np.float32)[:,:,3]/255
 y,x=np.mgrid[:1024,:1024];sx=(x-512)/460;sy=(y-512)/460;r=np.sqrt(sx*sx+sy*sy)
 def smooth(v):
  t=np.clip(v,0,1);return t*t*(3-2*t)
 keep=smooth((r-.22)/.07)*(1-smooth((r-.79)/.035))*smooth((np.minimum(np.abs(sx),np.abs(sy))-.035)/.035)
 layer=Image.fromarray(np.uint8(a*keep*255)).filter(ImageFilter.MaxFilter(7)).resize((512,512),Image.Resampling.LANCZOS)
 layers.append(layer)
path=DEST/'shield-unified-motifs-v1.png'
Image.merge('RGBA',layers).save(path,optimize=True)
meta=path.with_suffix('.png.meta')
if not meta.exists():
 template=json.loads((DEST/'thunder-reference-strip-v1.png.meta').read_text(encoding='utf8'))
 previous=template['uuid'];identifier=str(uuid.uuid4())
 data=json.dumps(template,ensure_ascii=False,indent=2).replace(previous,identifier).replace('thunder-reference-strip-v1','shield-unified-motifs-v1')
 meta.write_text(data+'\n',encoding='utf8')
for relative,importer,version in [('src/cocos/assets/resources/vfx/production/shield-unified-v1.effect','effect','1.7.1'),('src/cocos/assets/scripts/features/combat/runtime/UnifiedShieldEffects.ts','typescript','4.0.24')]:
 metadata=ROOT/(relative+'.meta')
 if not metadata.exists():metadata.write_text(json.dumps(dict(ver=version,importer=importer,imported=True,uuid=str(uuid.uuid4()),files=['.json'] if importer=='effect' else [],subMetas={},userData={}),indent=2)+'\n',encoding='utf8')
print(json.dumps({'texture':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'channels':['WAR','BOW','FIR','THU']},ensure_ascii=False))
