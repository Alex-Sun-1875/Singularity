from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
from scipy.ndimage import gaussian_filter
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];TEX=BASE/'textures';TEX.mkdir(parents=True,exist_ok=True)
cloud=Image.open(BASE.parent/'3d-native-hair-v4/hair-cloud.png').convert('RGB')
detail=np.asarray(cloud.crop((120,130,350,420)).resize((256,512),Image.Resampling.LANCZOS),dtype=float).mean(2)
detail-=gaussian_filter(detail,2)
along=1-np.arange(512)[:,None]/511
roots=np.array([104,108,114]);tips=np.array([220,220,217]);factor=np.clip(along/.6,0,1)**.5
rgb=roots+(tips-roots)*factor[:,:,None]+detail[:,:,None]*.65
rgb=np.broadcast_to(rgb,(512,256,3)).clip(0,255).astype('uint8');Image.fromarray(rgb).save(TEX/'curl-fibres.png')
Image.fromarray((rgb.astype(float)*.64).clip(0,255).astype('uint8')).save(TEX/'curl-roots.png')
orm=np.empty((128,64,3),dtype='uint8');orm[:,:,0]=255;orm[:,:,1]=np.linspace(165,205,128).astype('uint8')[:,None];orm[:,:,2]=0;Image.fromarray(orm).save(TEX/'curl-orm.png')
(BASE/'texture-provenance.json').write_text(json.dumps({'method':'Reused cloud fine silver strand texture from v4; deterministic crop, tint and length gradient for new 3D curl fibres','newImageGeneration':False,'source':'../3d-native-hair-v4/hair-cloud.png','prompt':'../3d-native-hair-v4/generation-prompt.txt','sourceUVNotReusedAsModelGeometry':True},indent=2)+'\n',encoding='utf-8')
print('Prepared silver curl fibre materials')
