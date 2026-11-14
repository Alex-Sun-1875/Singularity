from pathlib import Path
from PIL import Image
import json,numpy as np
from scipy.ndimage import gaussian_filter
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));rows=[r for r in manifest['materials']if r['parts']==['body']and'appearance-v3'in r['maps'].get('albedo','')];record=rows[0]
rgb=np.array(Image.open(BASE/'textures/cloth-burgundy.png').convert('RGB')).astype(float)/255;mask=np.array(Image.open(BASE/'fabric-composite-mask.png')).astype(float)/255;r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2];gold=(r>.30)&(g/r.clip(.01)>.60)&(g/r.clip(.01)<.93)&(b/g.clip(.01)<.82)&(mask>.6);h=gaussian_filter(gold.astype(float),.7);dy,dx=np.gradient(h);anchor=ROOT/'src/cocos/assets/resources/actors/raphael'
n=np.array(Image.open((anchor/record['maps']['normal']).resolve()).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)).astype(float)/255*2-1;n[:,:,0]-=dx*.45;n[:,:,1]+=dy*.45;n/=np.linalg.norm(n,axis=2,keepdims=True).clip(.001);Image.fromarray(np.uint8((n*.5+.5).clip(0,1)*255)).save(BASE/'textures/brocade-normal.png')
orm=np.array(Image.open((anchor/record['maps']['orm']).resolve()).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)).copy();orm[:,:,1]=np.uint8(orm[:,:,1]*(1-h*.18));orm[:,:,2]=np.maximum(orm[:,:,2],np.uint8(h*28));Image.fromarray(orm).save(BASE/'textures/brocade-orm.png')
for record in rows:record['maps'].update(normal='../appearance-v3/textures/brocade-normal.png',orm='../appearance-v3/textures/brocade-orm.png')
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Prepared fine thread relief on original native UV')
