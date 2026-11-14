"""Bounded collar-only assembly using existing native frame geometry.

The generated donor never replaces the face/hair. Original native pixels
outside the garment mask, all UVs, origins, equipment and lower body remain.
"""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy import ndimage as ndi

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'local-qwen21-unified-v3'))
import prepare,appearance
ACTOR=prepare.ACTOR
STAGE=HERE/'candidate'
Y,X=np.mgrid[:768,:512]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def selected(record):
    if record['direction']!='right':return False
    for ref in record['refs']:
        key,phase=ref['action'],ref['phase']
        if 'idle' in key:return True
        if key=='attack_sword_W01' and phase in [0,3]:return True
        if key.startswith(('attack_sword_W02','attack_bow','attack_staff','spell','interact')):return True
    return False

def build():
    installed=HERE/'install.json'
    if installed.exists():
        previous=json.loads(installed.read_text(encoding='utf8'))
        if all(sha(ACTOR/n)==v for n,v in previous['files'].items()):
            raise ValueError('The reviewed collar fix is already installed; do not process the installed pixels twice.')
    manifest=json.loads((ACTOR/'manifest.json').read_text(encoding='utf8'));frames=prepare.inventory(manifest);sheets={};changes=[];original_hashes={}
    ref=prepare.find(frames,'explore_idle_W07','right',0);reference=prepare.canvas(ref);source_head=appearance.hair(reference)[0];cx,cy=source_head['center']
    cloud=Image.open(HERE/'collar-cloud.png').convert('RGBA').resize((145,195),Image.Resampling.LANCZOS)
    donor=Image.new('RGBA',(512,768));donor.paste(cloud,(190,45))
    cloud_head=appearance.hair(donor)[0]['center'];dx,dy=cx-cloud_head[0],cy-cloud_head[1]
    donor=donor.convert('RGBa').transform((512,768),Image.Transform.AFFINE,(1,0,-dx,0,1,-dy),Image.Resampling.BICUBIC).convert('RGBA')
    mask=Image.new('L',(512,768));ImageDraw.Draw(mask).polygon([(218,138),(270,138),(307,140),(323,148),(322,192),(303,207),(269,202),(235,181),(218,166)],fill=255)
    # Feather only inside this collar envelope. The face above it stays exact.
    mask=Image.fromarray(np.uint8(np.asarray(mask,dtype=float)*np.clip((Y-138)/4,0,1)*np.clip((208-Y)/8,0,1)))
    for key,r in frames.items():
        if not selected(r):continue
        name=r['image']
        if name not in sheets:original_hashes[name]=sha(ACTOR/name);sheets[name]=Image.open(ACTOR/name).convert('RGBA')
        world=prepare.canvas(r);head=appearance.hair(world,r)[0];tx,ty=head['center'];scale=np.clip((head['box'][2]-head['box'][0])/(source_head['box'][2]-source_head['box'][0]),.9,1.12)
        # Donor and envelope share the existing profile head registration.
        inverse=(1/scale,0,cx-tx/scale,0,1/scale,cy-ty/scale)
        layer=donor.convert('RGBa').transform((512,768),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC).convert('RGBA')
        envelope=np.asarray(mask.transform((512,768),Image.Transform.AFFINE,inverse,Image.Resampling.BILINEAR)).copy()
        pixels=np.asarray(world);rr,gg,bb=np.moveaxis(pixels[...,:3].astype(float),-1,0)
        raised_bow=any(v['action'].startswith('attack_bow') and v['phase'] in [1,2] for v in r['refs'])
        if raised_bow:
            skin=(pixels[...,3]>128)&(rr>110)&(gg>70)&(bb>55)&(rr>gg+24)&(gg>bb+5)&(bb/rr.clip(1)>.52)&(gg/rr.clip(1)<.84)
            hand=skin&(Y>ty+90*scale)&(X>tx-25*scale)&(X<tx+78*scale)
            labels,_=ndi.label(hand);counts=np.bincount(labels.ravel());keep=counts>=70;keep[0]=False
            envelope[ndi.binary_dilation(keep[labels],iterations=2)]=0
        x,y,w,h=r['rect'];original=sheets[name].crop((x,y,x+w,y+h));s=r['scale'];ox,oy=r['origin'];mapping=(s,0,256-ox*s,0,s,712-oy*s)
        patch=layer.convert('RGBa').transform((w,h),Image.Transform.AFFINE,mapping,Image.Resampling.BICUBIC)
        weight=np.asarray(Image.fromarray(envelope).transform((w,h),Image.Transform.AFFINE,mapping,Image.Resampling.BILINEAR),float)/255
        a=np.asarray(original.convert('RGBa'),float);b=np.asarray(patch,float)
        out=Image.fromarray(np.rint(a*(1-weight[...,None])+b*weight[...,None]).clip(0,255).astype('uint8'),'RGBa').convert('RGBA')
        before=np.asarray(original);after=np.asarray(out).copy();after[weight==0]=before[weight==0]
        yy,xx=np.mgrid[:h,:w];wx=256+(xx-ox)*s;wy=712+(yy-oy)*s
        # Keep the original continuous back/shoulder silhouette. Only the
        # erroneous forward collar flap may be cut away into transparency.
        keep_alpha=(weight>0)&(wx<tx)&(before[...,3]>64)&(after[...,3]<before[...,3])
        empty=keep_alpha&(after[...,3]<32)
        if empty.any():
            _,nearest=ndi.distance_transform_edt(after[...,3]<128,return_indices=True)
            after[empty,:3]=after[nearest[0][empty],nearest[1][empty],:3]
        after[keep_alpha,3]=before[keep_alpha,3]
        # Removing a duplicated rim can detach its small old pointed tip.
        # Erase only complete tiny alpha islands inside the collar envelope;
        # never touch connected face/body pixels or remote weapon details.
        labels,_=ndi.label(after[...,3]>=16);counts=np.bincount(labels.ravel());main=counts[1:].argmax()+1
        collar_roi=(wx>tx-40*scale)&(wx<tx+85*scale)&(wy>ty+50*scale)&(wy<ty+140*scale)
        removed=0
        for index in range(1,len(counts)):
            if index==main or counts[index]>250:continue
            island=labels==index
            if np.all(collar_roi[island]):after[island]=0;weight[island]=1;removed+=int(island.sum())
        assert np.array_equal(after[weight==0],before[weight==0])
        final=Image.fromarray(after);sheets[name].paste(final,(x,y))
        changes.append(dict(image=name,index=r['index'],refs=r['refs'],maskPixels=int((weight>0).sum()),removedTipPixels=removed,outsideMaskExact=True,headCenter=[tx,ty],donorScale=float(scale)))
    for name,image in sheets.items():
        path=STAGE/name;path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    write(HERE/'prepare.json',dict(status='candidate; visual acceptance pending',manifestSHA256=sha(ACTOR/'manifest.json'),sourceFiles=original_hashes,files={n:sha(STAGE/n) for n in sheets},changes=changes,cloudCalls=1,scope='right-facing collar garment masks only; no manifest/metadata changes'))
    print(f'Prepared {len(changes)} collar crops across {len(sheets)} existing atlases.')

def install():
    report=json.loads((HERE/'prepare.json').read_text(encoding='utf8'));review=json.loads((HERE/'review.json').read_text(encoding='utf8'))
    assert review['status']=='accepted' and review['files']==report['files'] and review['manifestSHA256']==report['manifestSHA256']
    assert sha(ACTOR/'manifest.json')==report['manifestSHA256']
    for name,expected in report['sourceFiles'].items():assert sha(ACTOR/name)==expected
    for name,expected in report['files'].items():assert sha(STAGE/name)==expected
    master=report.get('authoringMaster')
    if master:
        target=HERE.parent/master['path'];assert sha(target)==master['sourceSHA256']
        assert sha(HERE/master['candidate'])==master['candidateSHA256']
    for name in report['files']:(ACTOR/name).write_bytes((STAGE/name).read_bytes())
    if master:target.write_bytes((HERE/master['candidate']).read_bytes())
    write(HERE/'install.json',dict(status='installed; compiled runtime review pending',manifestSHA256=report['manifestSHA256'],files=report['files']))
    print('Installed accepted collar pixels; manifest, UUIDs and original frame origins retained.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');args=p.parse_args();install() if args.install else build()
