"""Original UV-preserving complexion, textile and silver strand adaptation."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'textures';OUT.mkdir(exist_ok=True)
SOURCE=ROOT/'src/cocos/assets/resources/actors/native-shared/textures';records=[]
for name,filename,target,gain in [('skin-head','b837904994a02372-T_Superhero_Male_Ligh.png',(204,169,151),1.03),('skin-hands','917f81f829d903ac-T_Regular_Male_Dark_BaseColor.png',(200,160,139),1.00)]:
    source=SOURCE/filename;im=Image.open(source).convert('RGBA');a=np.array(im).copy();rgb=a[:,:,:3].astype(float);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2];mask=(r>35)&(g>48)&(b>30)&(r>g*.99)&(r<g*1.75)&(g>b*.97)&(a[:,:,3]>0)
    median=np.median(rgb[mask],axis=0);scale=np.array(target)/median
    rgb[mask]=np.clip((rgb[mask]-median)+np.array(target)*gain,0,255);a[:,:,:3]=rgb.astype('uint8');Image.fromarray(a).save(OUT/(name+'.png'));records.append({'source':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':name+'.png','sourceMedian':median.tolist(),'targetMedian':target,'changedSkinTexels':int(mask.sum()),'geometryUVAndFaceFeaturesUnchanged':True})
for name,source_name in [('cloth-burgundy','cloth-burgundy.png'),('cloth-charcoal','cloth-charcoal.png')]:
    source=ROOT/'src/cocos/assets/resources/actors/player-aim-v1'/source_name;im=Image.open(source).convert('RGBA');im.save(OUT/(name+'.png'))
cloth=Image.open(SOURCE/'eb115041165b2ae8-T_Ranger_BaseColor.png').convert('RGBA');hsv=np.array(cloth.convert('RGB').convert('HSV'));mask=((hsv[:,:,0]>55)&(hsv[:,:,0]<150)&(hsv[:,:,1]>25)).astype('uint8')*255;Image.fromarray(mask).save(OUT/'fabric-mask.png')
source=ROOT/'src/.tools/makehuman-assets/hair/short02/short02_diffuse.png';im=Image.open(source).convert('RGBA');a=np.array(im).copy();gray=np.array(im.convert('L')).astype(float);valid=a[:,:,3]>100;mid=np.median(gray[valid]);value=np.clip((gray-mid)*.70+185,75,239);a[:,:,:3]=np.stack([value*.97,value,value*1.025],-1).clip(0,255).astype('uint8');Image.fromarray(a).save(OUT/'silver-wavy-hair.png');records.append({'source':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':'silver-wavy-hair.png','license':'MakeHuman system assets CC0','alphaPreserved':True})
(BASE/'texture-provenance.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8');print('Prepared original UV material refinement')
