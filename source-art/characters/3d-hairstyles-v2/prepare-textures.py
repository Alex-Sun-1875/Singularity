from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage as nd
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
KIT=ROOT/'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)'
OUT=BASE/'textures';OUT.mkdir(exist_ok=True)
raw=Image.open(BASE/'hair-card-atlas-raw.png').convert('RGBA');atlas=Image.new('RGBA',(2048,2048),(150,145,140,0))
for i,box in enumerate([(40,0,340,1254),(365,0,600,1254),(625,0,860,1254),(880,0,1254,1254)]):
 strip=raw.crop(box).resize((512,1536),Image.Resampling.LANCZOS);atlas.paste(strip,(i*512,0))
for i,style in enumerate(['curly','dante','nero','vergil']):
 reference=ROOT/'source-art/characters'/('3d-2d-hair-v6'if style=='curly'else '3d-hairstyles-v1/'+style)/'back-extended.png'
 roots=np.array(Image.open(reference).convert('RGB').resize((512,512),Image.Resampling.LANCZOS),dtype=float)
 roots=np.clip(roots*.84,0,255).astype(np.uint8);patch=Image.fromarray(roots).convert('RGBA');atlas.paste(patch,(i*512,1536))
a=np.array(atlas);valid=a[:,:,3]>100;index=nd.distance_transform_edt(~valid,return_distances=False,return_indices=True);a[:,:,:3]=a[index[0],index[1],:3]
Image.fromarray(a).save(OUT/'hair-strands-color.png')
light=a[:,:,:3]@[.2126,.7152,.0722]/255.;light=nd.gaussian_filter(light,.7);dy,dx=np.gradient(light);nx=np.clip(-dx*2.0,-.23,.23);ny=np.clip(dy*.55,-.13,.13);nz=np.sqrt(np.maximum(.01,1-nx*nx-ny*ny));normal=np.stack([(nx+1)*127.5,(ny+1)*127.5,(nz+1)*127.5],axis=2).astype(np.uint8)
Image.fromarray(normal).save(OUT/'hair-strands-normal.png')
print('Prepared alpha strand atlas and native scalp patch',flush=True)
