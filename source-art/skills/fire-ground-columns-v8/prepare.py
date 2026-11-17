"""Reuse the cloud-made flame atlas, retaining its thick body for ground eruptions."""
from pathlib import Path
from PIL import Image
import json,hashlib
HERE=Path(__file__).resolve().parent
source=HERE.parent/'fire-kit-revision-v7/assets/fire-bolt-v9.png'
image=Image.open(source).convert('RGBA')
out=Image.new('RGBA',image.size)
for i in range(4):
 tile=image.crop((i*512+118,0,(i+1)*512,512)).resize((512,512),Image.Resampling.LANCZOS)
 out.paste(tile,(i*512,0))
out.save(HERE/'assets/fire-bolt-v9.png')
data={'source':'../fire-kit-revision-v7/provenance.json','newGeneration':False,'method':'Deterministic crop removes the pointed nozzle; existing Cocos cards orient the thick fire body upward from the ground. Ground flames use v5/v6 atlas.','croppedSource':'../fire-kit-revision-v7/assets/fire-bolt-v9.png','productIntegration':False,'artAcceptance':'Pending user review','sha256':hashlib.sha256((HERE/'assets/fire-bolt-v9.png').read_bytes()).hexdigest()}
(HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out.size)
