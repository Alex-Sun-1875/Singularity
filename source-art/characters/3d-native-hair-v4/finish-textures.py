"""Keep native coarse UV shading; composite only cloud-created fine hair detail."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,json,hashlib
from scipy.ndimage import gaussian_filter,distance_transform_edt
BASE=Path(__file__).resolve().parent;TEX=BASE/'textures'
source=Image.open(TEX/'hair-base.png').convert('RGBA');original=np.asarray(source).copy()
cloud=Image.open(BASE/'hair-cloud.png').convert('RGBA').resize(source.size,Image.Resampling.LANCZOS)
gen=np.asarray(cloud,dtype=float);base=original[:,:,:3].astype(float)
alpha=original[:,:,3];mask=alpha>200;safe=(np.asarray(Image.fromarray(alpha).filter(ImageFilter.MinFilter(7)))>220)&(gen[:,:,3]>220)
lum=gen[:,:,:3]@np.array([.2126,.7152,.0722]);detail=lum-gaussian_filter(lum,2.3)
base_lum=base@np.array([.2126,.7152,.0722]);generated_lum=gaussian_filter(lum,2.3)
# Author lock flow and root shading dominate; only limited new broad shading.
shade=(generated_lum-base_lum)*.18+detail*1.05
rgb=(base+shade[:,:,None]*safe[:,:,None]).clip(0,255)
outside=~mask
_,indices=distance_transform_edt(outside,return_indices=True)
rgb[outside]=rgb[indices[0][outside],indices[1][outside]]
rgba=np.dstack([rgb.astype('uint8'),alpha]);Image.fromarray(rgba).save(TEX/'hair-detail-color.png')
normal=np.asarray(Image.open(TEX/'hair-normal-base.png').convert('RGB'),dtype=float)/127.5-1
dy,dx=np.gradient(gaussian_filter(detail/255,.4));normal[:,:,0]-=dx*1.15*safe;normal[:,:,1]+=dy*1.15*safe
normal/=np.linalg.norm(normal,axis=2,keepdims=True).clip(.0001)
normal[outside]=normal[indices[0][outside],indices[1][outside]]
Image.fromarray(((normal*.5+.5)*255).clip(0,255).astype('uint8')).save(TEX/'hair-detail-normal.png')
rough=(.76-detail/255*.35).clip(.66,.84);orm=np.zeros((*rough.shape,3),dtype='uint8');orm[:,:,0]=255;orm[:,:,1]=(rough*255).astype('uint8')
Image.fromarray(orm).resize((512,512),Image.Resampling.LANCZOS).save(TEX/'hair-detail-orm.png')
Image.fromarray(np.uint8(safe)*255).save(BASE/'fine-detail-mask.png')
assert np.array_equal(rgba[:,:,3],original[:,:,3])
report={'tool':'Built-in cloud OpenAI image_gen.imagegen, one UV texture edit',
 'rawGeneratedSize':Image.open(BASE/'hair-cloud.png').size,'runtimeColorSize':source.size,
 'inputs':['cloud-input-uv.png','hair-2d-reference.jpg'],'prompt':'generation-prompt.txt',
 'composite':'Native broad lock shading + masked fine generated strand detail; original UV alpha retained; nearest-color padding avoids mip seams',
 'normal':'Author tangent normal retained; low-amplitude fine-strand height gradients added and vectors normalized',
 'roughness':'Subtle strand variation, zero metallic','allFaceAndClothingTexturesUnchanged':True,
 'generationStatus':'Completed','artReview':'Pending actual Cocos character views',
 'files':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(TEX.glob('hair-detail-*.png'))]}
(BASE/'texture-provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Composited protected native hair texture detail')
