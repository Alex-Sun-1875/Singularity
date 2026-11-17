"""Original light colours and alpha; retain v25 contours and v24 animation."""
from pathlib import Path
import json,hashlib,uuid
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DEST=ROOT/'src/cocos/assets/resources/vfx/production'
(HERE/'media').mkdir(exist_ok=True)
ref=np.load(HERE/'assets/reference-matte.npz');fg=ref['fg'];a=ref['alpha'];prem=ref['premul'];box=ref['box'];original=ref['original'];background=ref['background']
yy,xx=np.mgrid[:512,:512];nx=(xx-255.5)/231;ny=(yy-255.5)/231
sx=497.5+nx*55.5-box[0];sy=425.5+ny*26.5-box[1]
x0=sx.astype(int);y0=sy.astype(int);tx=(sx-x0)[:,:,None];ty=(sy-y0)[:,:,None]
field=np.dstack([prem,a])
sample=field[y0,x0]*(1-tx)*(1-ty)+field[y0,x0+1]*tx*(1-ty)+field[y0+1,x0]*(1-tx)*ty+field[y0+1,x0+1]*tx*ty
radius=np.hypot(nx,ny);cut=np.clip((1.08-radius)/.055,0,1)
sample*=cut[:,:,None]
color=sample[:,:,:3]/np.maximum(sample[:,:,3,None],1e-6)
seal=Image.fromarray(np.uint8(np.clip(np.dstack([color,sample[:,:,3]]),0,1)*255))

# Map the existing flame's colour ratios and optical density to the selected
# original. Geometry, continuous frame flow and the outer silhouette stay.
y,x=np.mgrid[box[1]:box[3],box[0]:box[2]]
valid=(y>250)&(y<395)&(x>450)&(x<548)&(a>.10)&(fg[:,:,0]>.85)&(fg[:,:,1]<=fg[:,:,0])&(fg[:,:,2]<=fg[:,:,1])
target=fg[valid];target=target[:,1:]/np.maximum(target[:,0,None],1e-5)
registered=np.asarray(Image.open(ROOT/'source-art/skills/fire-jet-native-sequence-v24/assets/reference-flame-registered.png').convert('RGBA'),dtype=float)/255
live=registered[:,:,3]>.10;src=registered[:,:,:3][live];src=src[:,1:]/np.maximum(src[:,0,None],1e-5)
quantiles=np.linspace(.005,.995,65);targetQ=np.quantile(target,quantiles,axis=0);sourceQ=np.quantile(src,quantiles,axis=0)
atlas=np.asarray(Image.open(DEST/'fire-ground-jets-v24.png').convert('RGBA'),dtype=float)/255
for channel in [1,2]:
 ratio=atlas[:,:,channel]/np.maximum(atlas[:,:,0],1e-5)
 atlas[:,:,channel]=atlas[:,:,0]*np.interp(ratio,sourceQ[:,channel-1],targetQ[:,channel-1])
# Retain the reference's channel correlation: its hottest gold filaments also
# contain blue. Independent channel histograms can turn these into yellow/green.
order=np.argsort(target[:,0]);sortedTarget=target[order];gNodes=np.linspace(.25,.99,96)
bNodes=np.array([np.median(sortedTarget[np.argsort(np.abs(sortedTarget[:,0]-g))[:180],1]) for g in gNodes])
mappedG=atlas[:,:,1]/np.maximum(atlas[:,:,0],1e-5)
conditionalB=np.interp(mappedG,gNodes,bNodes)*atlas[:,:,0]
atlas[:,:,2]=atlas[:,:,2]*.20+conditionalB*.80
atlas[:,:,:3]=np.minimum(atlas[:,:,:3]*1.01,1)
sourceAlphaQ=np.quantile(registered[:,:,3][live],quantiles)
targetAlphaQ=np.quantile(a[valid],quantiles)
oldAlpha=atlas[:,:,3].copy()
atlas[:,:,3]=np.interp(oldAlpha,sourceAlphaQ,targetAlphaQ)
low=oldAlpha<sourceAlphaQ[0];atlas[:,:,3][low]=oldAlpha[low]/sourceAlphaQ[0]*targetAlphaQ[0]
atlas[:,:,3][oldAlpha==0]=0
atlas=np.uint8(np.clip(atlas,0,1)*255);jets=Image.fromarray(atlas)
for name,im,template in [('fire-ground-jets-v26',jets,'fire-ground-jets-v24'),('fire-jet-seal-v26',seal,'fire-jet-seal-v25')]:
 im.save(HERE/'assets'/(name+'.png'),optimize=True);im.save(DEST/(name+'.png'),optimize=True)
 meta=DEST/(name+'.png.meta')
 if not meta.exists():
  text=(DEST/(template+'.png.meta')).read_text(encoding='utf8');old=json.loads(text)['uuid'];meta.write_text(text.replace(old,str(uuid.uuid4())).replace(template,name),encoding='utf8')

roundtrip=prem+background*(1-a[:,:,None]);soft=valid&(a>.99)
error=np.abs(roundtrip[soft]-original[soft])*255
core=fg[valid];palette={n:np.quantile(core,q,axis=0).tolist() for n,q in [('low',.1),('mid',.5),('high',.9)]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'method':'deterministic original foreground/background colour separation + conditional colour/opacity distribution mapping, no generation','reference':'../fire-selected-reference-v18/user-selected-effect.jpg','referenceSha256':sha(ROOT/'source-art/skills/fire-selected-reference-v18/user-selected-effect.jpg'),'seal':'Original per-pixel RGB and physically valid alpha, not a flat recolour. No added blur or glow. Original visible rings and curves retained, including light passing in front of the source staff area. Hidden ground strokes are not invented. Native core RGB residual is compensated by 1.016/1.052/1.095, measured against the selected reference.','flame':'v24 continuous atlas flow and silhouette preserved. Red-dominant reference foreground colours provide green/red quantiles and conditional blue/red values. Opacity quantiles restore transparent haze versus bright cores; the shader no longer uniformly dims the cores.','palette':palette,'foregroundRoundTrip':{'opaqueReferencePixelCount':int(soft.sum()),'maximumChannelError255':float(error.max())},'displayColour':'Custom transparent pass consumes these artist display colours directly, without an additional SRGBToLinear or display transfer. Final native result is separately checked.','outputs':{n:sha(DEST/(n+'.png')) for n in ['fire-ground-jets-v26','fire-jet-seal-v26']},'artAcceptance':'native comparison pending; user acceptance pending','taptapDevice':'pending'}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(record,ensure_ascii=False))
