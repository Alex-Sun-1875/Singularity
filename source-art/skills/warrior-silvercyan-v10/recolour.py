"""Deterministic silver-cyan treatment of the existing source texture."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image

BASE=Path(__file__).resolve().parent
SOURCE=BASE.parent/'warrior-aura-v9'
stops=[0,70,125,185,225,255]
colours=[[24,63,77],[50,103,124],[73,143,165],[100,178,194],[162,217,229],[241,253,255]]
inputs={}
for kind in ['blade','guard']:
 path=SOURCE/(kind+'.png');inputs[kind]=hashlib.sha256(path.read_bytes()).hexdigest()
 rgba=np.asarray(Image.open(path).convert('RGBA')).copy()
 rgb=rgba[:,:,:3].astype(float)
 luminance=rgb[:,:,0]*.2126+rgb[:,:,1]*.7152+rgb[:,:,2]*.0722
 mapped=np.stack([np.interp(luminance,stops,[c[i] for c in colours]) for i in range(3)],axis=-1)
 rgba[:,:,:3]=np.clip(np.round(mapped),0,255).astype(np.uint8)
 Image.fromarray(rgba).save(BASE/(kind+'.png'))
data={'source':'../warrior-aura-v9/{blade,guard}.png','sourceSha256':inputs,'method':'Deterministic luminance-to-silver-cyan mapping; alpha preserved byte-for-byte. No generative edit.',
 'stops':stops,'colours':colours,'rendering':{'waveLayerPeakOpacity':.55,'thicknessScale':1.65,'depthScale':1.22,'crossAcuteAngleDegrees':40,'densityProfile':'Broader rolled wave body; unchanged maximum alpha; feathered rear.'},
 'artReview':'Pending user review','productionIntegration':False}
(BASE/'processing.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(data['rendering']))
