"""Pack the new airy source and derive pale opaque-core pressure-wave materials."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter
BASE=Path(__file__).resolve().parent
PALETTES={
 'A':{'name':'银白剑气','detail':'浅银白亮芯 / 灰蓝柔边','colours':[(63,81,104),(123,148,169),(183,205,219),(218,234,243),(244,250,253),(255,255,255)]},
 'B':{'name':'淡赤金剑气','detail':'浅珊瑚亮芯 / 暖红柔边','colours':[(109,52,61),(174,111,119),(225,168,174),(247,212,211),(255,238,227),(255,253,245)]},
 'C':{'name':'香槟金剑气','detail':'浅香槟亮芯 / 暖金柔边','colours':[(102,80,46),(165,140,96),(220,200,157),(244,232,203),(254,248,228),(255,255,250)]},
 'D':{'name':'浅银紫剑气','detail':'浅银紫亮芯 / 淡紫柔边','colours':[(77,58,113),(142,120,174),(194,176,221),(228,215,244),(247,240,255),(255,252,255)]},
}
STOPS=[0,80,140,195,230,255]
source=Image.open(BASE/'aura-original.png').convert('RGBA');w,h=source.size
row_bounds=[(0,.25),(.25,.55),(.55,.75),(.75,1)]
def clean(tile,flow=False):
 p=np.asarray(tile).copy();rgb=p[:,:,:3].astype(float);a=p[:,:,3].astype(float)
 bad=((rgb[:,:,0]>rgb[:,:,1]*1.45)&(rgb[:,:,0]>rgb[:,:,2]*1.8))|((rgb[:,:,1]>rgb[:,:,0]*1.15)&(rgb[:,:,1]>rgb[:,:,2]*1.5))
 a[bad&(a<170)]=0
 alpha=np.asarray(Image.fromarray(a.astype('uint8')).filter(ImageFilter.MedianFilter(3))).astype(float)/255
 lum=np.clip(rgb[:,:,0]*.2126+rgb[:,:,1]*.7152+rgb[:,:,2]*.0722,0,255)
 if flow:
  lum=np.asarray(Image.fromarray(lum.astype('uint8')).filter(ImageFilter.GaussianBlur(3))).astype(float)
  lum=130+125*(alpha*(lum/255)+(1-alpha)*.25)
  alpha=np.ones(alpha.shape)
 else:
  alpha=np.where(alpha>.56,1,np.minimum(1,alpha/.56))
  lum=150+105*(lum/255)
 return lum,alpha
tiles=[]
for row,(top,bottom) in enumerate(row_bounds):
 cells=[]
 for col in range(4):
  tile=source.crop((round(w*col/4),round(h*top),round(w*(col+1)/4),round(h*bottom)))
  if row<2:tile=tile.crop((round(tile.width*.18),round(tile.height*.25),round(tile.width*.82),round(tile.height*.77)))
  tile=tile.resize((512,512),Image.Resampling.LANCZOS);cells.append(clean(tile,row<2))
 tiles.append(cells)
for key,palette in PALETTES.items():
 target=BASE/'variants'/key;target.mkdir(parents=True,exist_ok=True)
 blade=Image.new('RGBA',(2048,1536));guard=Image.new('RGBA',(1024,1024))
 for row in range(4):
  for col in range(4):
   lum,a=tiles[row][col];p=np.zeros((*lum.shape,4),dtype='uint8')
   for c in range(3):p[:,:,c]=np.interp(lum,STOPS,[rgb[c] for rgb in palette['colours']]).astype('uint8')
   p[:,:,3]=(a*255).astype('uint8');tile=Image.fromarray(p)
   if row<3:blade.paste(tile,(col*512,row*512))
   else:guard.paste(tile,((col%2)*512,(col//2)*512))

 blade.save(target/'blade.png');guard.save(target/'guard.png')
 if key=='A':blade.save(BASE/'blade.png');guard.save(BASE/'guard.png')
(BASE/'palette-candidates.json').write_text(json.dumps({'status':'Pale sword-qi shockwave candidates, user choice pending','opaqueCore':True,'coloursAppliedTo':'3D curled pressure-wave surface and soft outer wake; no metal facets','palettes':PALETTES},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(BASE/'processing.json').write_text(json.dumps({'source':'aura-original.png','sourceSize':[w,h],'rowBounds':row_bounds,'operation':'Crop flow detail, soften broad energy stream, use full-opacity flow texture with geometry-controlled core/feathering. Preserve opaque painted impact/barrier cores. Deterministic pale colour mapping.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared four pale pressure-wave treatments')
