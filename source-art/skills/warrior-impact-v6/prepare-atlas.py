"""Deterministic packing and low-alpha fringe cleanup of the new generated artwork."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter

base=Path(__file__).resolve().parent
im=Image.open(base/'atlas-original.png').convert('RGBA')
pixels=np.asarray(im).copy();rgb=pixels[:,:,:3].astype(float);a=pixels[:,:,3].astype(float)
bad=((rgb[:,:,0]>rgb[:,:,1]*1.45)&(rgb[:,:,0]>rgb[:,:,2]*1.8))|((rgb[:,:,1]>rgb[:,:,0]*1.15)&(rgb[:,:,1]>rgb[:,:,2]*1.5))
a[bad&(a<128)]=0
warm=rgb.max(axis=2)
for channel,gain in enumerate([1,.87,.65]):pixels[:,:,channel][bad]=np.clip(warm[bad]*gain,0,255).astype('uint8')
pixels[:,:,3]=np.asarray(Image.fromarray(a.astype('uint8')).filter(ImageFilter.MedianFilter(3)))
im=Image.fromarray(pixels)
w,h=im.size
rows=[(.04,.28),(.28,.68),(.68,.96)]
out=Image.new('RGBA',(2048,1536))
for row,(top,bottom) in enumerate(rows):
 for col in range(4):
  tile=im.crop((round(w*col/4),round(h*top),round(w*(col+1)/4),round(h*bottom)))
  tile=tile.resize((512,512),Image.Resampling.LANCZOS)
  out.paste(tile,(col*512,row*512))
out.save(base/'atlas.png')
(base/'atlas-processing.json').write_text(json.dumps({'sourceSize':[w,h],'outputSize':list(out.size),'grid':[4,3],'rowBoundsFraction':rows,'processing':'Remove low-alpha red/green fringe, recolor remaining fringe only, median-filter alpha 3px, pack into twelve equal cells. Original artwork retained.'},indent=2)+'\n',encoding='utf8')
print('Packed new atlas',out.size)
