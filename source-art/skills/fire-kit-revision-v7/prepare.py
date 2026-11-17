from pathlib import Path
from PIL import Image
import numpy as np
import hashlib,json

HERE=Path(__file__).resolve().parent
raw=Image.open(HERE/'raw/fire-jet.png').convert('RGBA')
cw,ch=raw.width//2,raw.height//2
strip=Image.new('RGBA',(2048,512))
for index in range(4):
 tile=raw.crop(((index%2)*cw,(index//2)*ch,(index%2+1)*cw,(index//2+1)*ch)).resize((512,512),Image.Resampling.LANCZOS)
 rgba=np.asarray(tile,dtype=np.float32).copy();alpha=rgba[:,:,3]/255
 rgba[:,:,3]*=np.clip(alpha/.09,0,1)
 strip.paste(Image.fromarray(np.uint8(np.clip(rgba,0,255))),(index*512,0))
strip.save(HERE/'assets/fire-bolt-v9.png')
data={'backend':'OpenAI image_gen built-in cloud tool','generated':'raw/fire-jet.png','prompt':'jet-prompt.txt','references':['../fire-spells-design-v5/raw/fire-lance.png','../../../src/.tmp/fire-meteor-burn-v6/final/design/FIR_02/055.jpg'],'processing':'Pillow/NumPy resize, alpha cleanup, repack 2x2 into 4x1. No local model.','generationStatus':'success','artAcceptance':'Pending user review','productIntegration':False,'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'raw/fire-jet.png',*sorted((HERE/'assets').glob('*.png'))]}}
(HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(raw.size,strip.size)
