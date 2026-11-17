from pathlib import Path
import json, uuid
import numpy as np
from PIL import Image, ImageOps

here=Path(__file__).resolve().parent
root=here.parents[2]
target=root/'src/cocos/assets/resources/equipment/gem-orbs-v5'
target.mkdir(parents=True,exist_ok=True)
source=Image.open(here/'ruby-original.png').convert('RGBA')
source.putalpha(source.getchannel('A').point(lambda a:0 if a<20 else a))
source=ImageOps.contain(source.crop(source.getchannel('A').getbbox()),(226,226),Image.Resampling.LANCZOS)
base=Image.new('RGBA',(256,256));base.alpha_composite(source,((256-source.width)//2,(256-source.height)//2))
rgb=np.asarray(base)[:,:,:3].astype(np.float32)
hsv=np.asarray(base.convert('RGB').convert('HSV')).astype(np.float32)/255
yy,xx=np.mgrid[:256,:256];radius=np.sqrt((xx-127.5)**2+(yy-127.5)**2)
distance=np.minimum(hsv[:,:,0],1-hsv[:,:,0])
mask=np.clip((106-radius)/3,0,1)*np.clip((.075-distance)/.02,0,1)*np.clip((hsv[:,:,1]-.18)/.18,0,1)
mask=np.where(np.asarray(base.getchannel('A'))>0,mask,0)[:,:,None]
colors={'power':None,'maxHp':.38,'armor':.60,'criticalChance':'gold','criticalDamage':.79}
template=json.loads((root/'src/cocos/assets/resources/equipment/supplies-v2/health-bottle.png.meta').read_text(encoding='utf-8'))
report=[]
for name,hue in colors.items():
    if hue is None:result=base.copy()
    else:
        color=hsv.copy()
        if hue=='gold':color[:,:,0]=.125;color[:,:,1]*=.92;color[:,:,2]=.10+.90*color[:,:,2]**.85
        else:color[:,:,0]=hue;color[:,:,1]*=.94
        changed=np.asarray(Image.fromarray(np.round(np.clip(color,0,1)*255).astype('uint8'),'HSV').convert('RGB')).astype(np.float32)
        mixed=np.round(rgb*(1-mask)+changed*mask).astype('uint8')
        result=Image.fromarray(mixed,'RGB').convert('RGBA');result.putalpha(base.getchannel('A'))
        assert np.array_equal(np.asarray(result)[:,:,:3][mask[:,:,0]==0],rgb.astype('uint8')[mask[:,:,0]==0])
    result.save(target/(name+'.png'),optimize=True)
    identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gem-orbs-v5/'+name))
    meta=json.loads(json.dumps(template));meta['uuid']=identity;meta['userData']['redirect']=identity+'@6c48a'
    texture=meta['subMetas']['6c48a'];texture['uuid']=identity+'@6c48a';texture['displayName']=name;texture['userData']['imageUuidOrDatabaseUri']=identity
    (target/(name+'.png.meta')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    report.append({'id':name,'bytes':(target/(name+'.png')).stat().st_size})
folder={'ver':'1.2.0','importer':'directory','imported':True,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/equipment/gem-orbs-v5')),'files':[],'subMetas':{},'userData':{}}
target.with_name(target.name+'.meta').write_text(json.dumps(folder,indent=2)+'\n',encoding='utf-8')
board=Image.new('RGB',(640,182),(24,20,17))
for i,name in enumerate(colors):
    im=Image.open(target/(name+'.png'));large=im.resize((110,110),Image.Resampling.LANCZOS);small=im.resize((48,48),Image.Resampling.LANCZOS)
    board.paste(large,(i*128+9,3),large);board.paste(small,(i*128+40,126),small)
board.save(here/'preview.jpg',quality=94)
Image.fromarray(np.round(mask[:,:,0]*255).astype('uint8')).save(here/'interior-color-mask.png')
(here/'processing.json').write_text(json.dumps({'colors':colors,'output':str(target.relative_to(root)).replace('\\','/'),'files':report,'maskedOnly':True,'unchangedExteriorPixels':int((mask[:,:,0]==0).sum()),'sameAlphaAllColors':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'icons':len(report),'runtimeBytes':sum(r['bytes'] for r in report),'metalOutsideMaskUnchanged':True}))
