"""Reuse native CC0 UV textures; deterministic silver/burgundy colour adapter."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'src/cocos/assets/resources/actors/native-shared/textures'
OUT=ROOT/'src/cocos/assets/resources/actors/player-aim-v1'
OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cloth=SOURCE/'eb115041165b2ae8-T_Ranger_BaseColor.png'
hair=SOURCE/'9c7058c66b88300b-T_Hair_1_BaseColor.png'
base=Image.open(cloth).convert('RGBA');hsv=np.asarray(base.convert('RGB').convert('HSV')).copy();alpha=base.getchannel('A')
fabric=(hsv[...,0]>55)&(hsv[...,0]<150)&(hsv[...,1]>25)&(np.asarray(alpha)>0)
for name,hue,saturation,gain,lift,maximum in [('cloth-burgundy.png',246,155,1.08,4,170),('cloth-charcoal.png',160,58,.64,3,94)]:
    a=hsv.copy();a[fabric,0]=hue;a[fabric,1]=saturation;a[fabric,2]=np.clip(hsv[...,2][fabric].astype(float)*gain+lift,18,maximum).astype('uint8')
    image=Image.fromarray(a,'HSV').convert('RGB').convert('RGBA');image.putalpha(alpha);image.save(OUT/name)
image=Image.open(hair).convert('RGBA');a=np.asarray(image).copy();v=a[...,:3].max(-1).astype(float);gray=np.clip(75+145*(v/32)**.8,78,235)
a[...,:3]=np.stack([gray*.97,gray,gray*1.025],-1).clip(0,255).astype('uint8');Image.fromarray(a).save(OUT/'hair-silver.png')
report=dict(method='Pillow/NumPy UV-preserving colour adapter, no model or texture generation',sourceLicense='Existing Quaternius CC0 native kit; see docs/assets/native-library-runtime.md',sources={str(p.relative_to(ROOT)):sha(p) for p in [cloth,hair]},outputs={p.name:sha(p) for p in OUT.glob('*.png')},recolouredFabricPixels=int(fabric.sum()),meshRigAndUVChanged=False)
(Path(__file__).resolve().parent/'texture-provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('Prepared 3 reused UV albedos; original normal/ORM maps and meshes retained.')
