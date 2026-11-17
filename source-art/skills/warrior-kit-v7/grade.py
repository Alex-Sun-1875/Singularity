"""Deterministic colour grading into the user's chosen cyan steel palette."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter
BASE=Path(__file__).resolve().parent
STOPS=[0,70,125,185,225,255]
COLOURS=[(6,18,42),(10,38,78),(20,103,152),(48,178,216),(161,238,255),(232,253,255)]
def grade(image,colours=COLOURS,edge_rgb=(6,24,57),halo_rgb=(27,145,206)):
 px=np.asarray(image.convert('RGBA')).copy();rgb=px[:,:,:3].astype(float);a=px[:,:,3].astype(float)
 bad=((rgb[:,:,0]>rgb[:,:,1]*1.45)&(rgb[:,:,0]>rgb[:,:,2]*1.8))|((rgb[:,:,1]>rgb[:,:,0]*1.15)&(rgb[:,:,1]>rgb[:,:,2]*1.5))
 a[bad&(a<160)]=0
 a=np.asarray(Image.fromarray(a.astype('uint8')).filter(ImageFilter.MedianFilter(3)))
 lum=rgb[:,:,0]*.2126+rgb[:,:,1]*.7152+rgb[:,:,2]*.0722
 for c in range(3):px[:,:,c]=np.interp(lum,STOPS,[v[c] for v in colours]).astype('uint8')
 px[:,:,3]=(a*.97).astype('uint8')
 face=Image.fromarray(px)
 mask=face.getchannel('A')
 edge=Image.new('RGBA',face.size,(*edge_rgb,0));edge.putalpha(mask.filter(ImageFilter.MaxFilter(5)).point(lambda p:round(p*.72)))
 halo=Image.new('RGBA',face.size,(*halo_rgb,0));halo.putalpha(mask.filter(ImageFilter.GaussianBlur(5)).point(lambda p:round(p*.12)))
 return Image.alpha_composite(Image.alpha_composite(halo,edge),face)
if __name__=='__main__':
 for name,grid in [('blade',(4,3)),('guard',(2,2))]:
  im=Image.open(BASE/(name+'-warm.png')).convert('RGBA');cols,rows=grid
  out=Image.new('RGBA',(cols*512,rows*512))
  for row in range(rows):
   for col in range(cols):
    tile=im.crop((round(im.width*col/cols),round(im.height*row/rows),round(im.width*(col+1)/cols),round(im.height*(row+1)/rows))).resize((512,512),Image.Resampling.LANCZOS)
    out.paste(grade(tile),(col*512,row*512))
  out.save(BASE/(name+'.png'))
 (BASE/'palette.json').write_text(json.dumps({'userChoice':'青蓝钢刃，冷色且清晰','stops':STOPS,'colours':COLOURS,'method':'Luminance-map colour grade; low-alpha red/green fringe cleanup; narrow deep-blue under-edge and restrained cyan halo.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Cyan steel blade and guard atlases prepared')
