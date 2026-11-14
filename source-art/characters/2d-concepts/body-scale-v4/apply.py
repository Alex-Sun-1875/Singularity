"""Apply pose calibration and inverse head scaling using existing local pixels.

The renderer scales each physical frame about its own ground anchor. Its head
is inversely sized about the neck here, so body calibration cannot enlarge it.
No model inference, network request, full original backup, or colour edit.
"""
from pathlib import Path
import argparse
import collections
import copy
import importlib.util
import json
import os
import sys
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE=Path(__file__).resolve().parent
V3=HERE.parent/'local-qwen21-unified-v3'
sys.path.insert(0,str(V3))
import prepare
import appearance
packing=appearance.load('existing_phase_crop_tools',HERE.parent/'local-qwen21-consistency-v2/game-install/install.py')


def write(path,data):
    path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))


def head_geometry(record,head,old_hair,attack):
    """Recover the exact prior edit geometry, including out-of-window poses."""
    d=record['direction'];template,reference=appearance.canonical(d)
    method=head['method']
    if method.startswith('own acting'):
        shift=np.asarray(head.get('editingViewportShift',[0,0]))
        neck=np.asarray(head['acting_neck_anchor_xy'])-shift
        hc=np.asarray(old_hair['center']);b=old_hair['box']
        u=neck-hc;distance=np.linalg.norm(u);u/=max(distance,1)
        s=head['scale'];center=neck+s*(hc+u*10-neck)
        return dict(kind='ellipse',neck=neck,center=center,axis=u,
                    along=s*(distance+8)+3,across=s*(.60*max(b[2]-b[0],b[3]-b[1])+7)+3)
    if method.startswith('accepted standing-derived'):
        b=old_hair['box'];hc=np.asarray(old_hair['center'])
        neck=np.array([hc[0],b[3]+min(55,(b[3]-b[1])*{'down':.85,'right':.65,'up':.4,'left':.65}[d])])
        return dict(kind='ellipse',neck=neck,center=hc+np.array([0,12]),axis=np.array([0.,1.]),
                    along=max(neck[1]-hc[1]+6,(b[3]-b[1])*.8),across=(b[2]-b[0])*.68+3)
    h=attack[d] if method.startswith('standing-derived head plus') else head
    neck0=194 if d!='up' else 181
    cx,ny=h['original_neck_xy'];dx=round(cx-reference['center'][0]);dy=round(ny-neck0)
    return dict(kind='template',neck=np.array([reference['center'][0]+dx,neck0+dy]),
                template=template,translation=[dx,dy])


def resize_head(crop,record,factor,head,old_hair,attack,pose):
    pad=16
    if abs(factor-1)<.001:return crop,(0,0),dict(applied=False,physicalHeadScale=factor,reason='sub-per-mille resampling omitted')
    size=(crop.width+2*pad,crop.height+2*pad)
    original=Image.new('RGBA',size);original.paste(crop,(pad,pad))
    a=np.asarray(original);s=record['scale']
    # Each native pixel is mapped back into the old 400px/world review space.
    yy,xx=np.mgrid[:size[1],:size[0]]
    x=256+(xx-pad-record['origin'][0])*s
    y=712+(yy-pad-record['origin'][1])*s
    g=head_geometry(record,head,old_hair,attack);nx,ny=g['neck']
    if g['kind']=='template':
        alpha=g['template'].getchannel('A')
        dx,dy=g['translation'];tx=256+(-pad-record['origin'][0])*s-dx;ty=712+(-pad-record['origin'][1])*s-dy
        mask=np.asarray(alpha.transform(size,Image.Transform.AFFINE,(s,0,tx,0,s,ty),Image.Resampling.BILINEAR))>1
        mask=ndi.binary_dilation(mask,iterations=max(1,round(2/s)))
    else:
        ux,uy=g['axis'];cx,cy=g['center']
        along=(x-cx)*ux+(y-cy)*uy;across=-(x-cx)*uy+(y-cy)*ux
        mask=(along/g['along'])**2+(across/g['across'])**2<=1
    # Preserve weapon hardware and hands which happen to cross the head area.
    rgb=a[...,:3].astype(int)
    gold=(rgb[...,0]-rgb[...,1]>27)&(rgb[...,1]-rgb[...,2]>24)&(rgb[...,0]>105)&(a[...,3]>0)
    guard=ndi.binary_dilation(gold,iterations=1)
    if pose and pose.get('landmarks'):
        for lm in pose['landmarks'][15:23]:
            if lm['visibility']<.7:continue
            hx=256+(lm['x']-record['origin'][0])*s;hy=712+(lm['y']-record['origin'][1])*s
            if np.hypot(hx-nx,hy-ny)<120:
                guard|=((x-hx)**2+(y-hy)**2<11**2)&(a[...,3]>0)
    mask&=~guard
    # The neck root stays fixed; feather the last 10 review pixels into collar.
    if g['kind']=='ellipse':
        u=g['axis'];distance=(x-nx)*u[0]+(y-ny)*u[1]
    else:distance=y-ny
    # Full native head support, no alpha resampling of unrelated body pixels.
    layer=a.copy();layer[~mask]=0
    nx_native=pad+record['origin'][0]+(nx-256)/s;ny_native=pad+record['origin'][1]+(ny-712)/s
    inv=1/factor
    affine=(1/inv,0,nx_native-nx_native/inv,0,1/inv,ny_native-ny_native/inv)
    moved=Image.fromarray(layer).convert('RGBa').transform(size,Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC).convert('RGBA')
    # Erase the old head once, then composite premultiplied resized head once.
    base=a.copy();base[mask]=0
    composed=Image.alpha_composite(Image.fromarray(base),moved)
    # Feather premultiplied colours once; multiplying both base and layer alpha
    # before an over operation would make an opaque neck partially transparent.
    transition=np.clip(-distance/10,0,1)*(mask|(np.asarray(moved)[...,3]>0))
    result=np.asarray(Image.composite(composed,original,Image.fromarray(np.uint8(np.rint(transition*255))))).copy()
    result[guard]=a[guard]
    changed=np.any(result!=a,axis=-1)&((result[...,3]>0)|(a[...,3]>0))
    union=ndi.binary_dilation(mask|(np.asarray(moved)[...,3]>0),iterations=2)
    if np.any(changed&~union&~guard):raise RuntimeError('Pixel change escaped head region')
    return Image.fromarray(result),(-pad,-pad),dict(applied=True,inverseTextureScale=inv,physicalHeadScale=inv*factor,
        nativePixelsChanged=int(changed.sum()),neck=g['neck'].tolist(),method=g['kind'])


def prepare_all():
    inv=json.loads((HERE/'inventory.json').read_text());cal=json.loads((HERE/'calibration.json').read_text())
    if prepare.digest(prepare.MANIFEST)!=inv['manifestSHA256']:raise RuntimeError('Source manifest changed')
    manifest=json.loads(prepare.MANIFEST.read_text());updated=copy.deepcopy(manifest)
    factors={(r['image'],r['index']):r['scale'] for r in cal['frames']}
    old={(r['image'],r['index']):r['head'] for r in json.loads((V3/'batch-report.json').read_text())['phases']}
    hair={(r['image'],r['index']):r['hair'] for r in json.loads((V3/'head-locations.json').read_text())['frames']}
    poses={(r['image'],r['index']):r for r in json.loads((HERE/'pose-landmarks.json').read_text())['frames']}
    attack={r['direction']:r for r in json.loads((V3/'attack-head-guide-report.json').read_text())}
    grouped=collections.defaultdict(list)
    for r in inv['frames']:grouped[r['image']].append(r)
    candidate=HERE/'candidate-runtime';candidate.mkdir(exist_ok=True)
    geometry={};reports=[];image_reports=[]
    for ordinal,(name,records) in enumerate(grouped.items()):
        source=Image.open(prepare.ACTOR/name).convert('RGBA');patches=[]
        action=manifest['actions'][records[0]['action']];columns=action.get('columns',manifest['columns'])
        rows=max(r['index']//columns for r in records)+1
        for r in records:
            key=name,r['index'];x,y,w,h=r['rect'];crop=source.crop((x,y,x+w,y+h))
            patch,(dx,dy),report=resize_head(crop,r,factors[key],old[key],hair[key],attack,poses.get(key))
            patches.append((r,patch,x+dx,y+dy));reports.append(dict(image=name,index=r['index'],factor=factors[key],head=report))
        # Retain current placement, adding only the atlas gutters actually needed.
        left=max(0,-min(x for _,_,x,_ in patches));top=max(0,-min(y for _,_,_,y in patches))
        right=max(0,max(x+p.width for _,p,x,_ in patches)-source.width)
        bottom=max(0,max(y+p.height for _,p,_,y in patches)-source.height)
        for gutter in (0,16,32,64):
            page=Image.new('RGBA',(source.width+left+right+(columns-1)*gutter,source.height+top+bottom+(rows-1)*gutter))
            labels=np.zeros((page.height,page.width),np.uint16);placed=[];safe=True;pending={}
            for number,(r,patch,x,y) in enumerate(patches,1):
                dx=left+(r['index']%columns)*gutter;dy=top+(r['index']//columns)*gutter;px=x+dx;py=y+dy
                alpha=np.asarray(patch)[...,3];region=labels[py:py+patch.height,px:px+patch.width]
                if np.any((alpha>=16)&(region!=0)):safe=False;break
                region[alpha>=16]=number
                page.paste(patch,(px,py),Image.fromarray(np.uint8(alpha>0)*255));placed.append((r,patch,px,py,dx,dy))
            if not safe:continue
            for number,(r,patch,x,y,dx,dy) in enumerate(placed,1):
                b=packing.bounds(patch)
                for padding in (2,1,0):
                    c=[max(0,b[0]-padding),max(0,b[1]-padding),min(patch.width,b[2]+padding),min(patch.height,b[3]+padding)]
                    px=x+c[0];py=y+c[1];w=c[2]-c[0];h=c[3]-c[1];region=labels[py:py+h,px:px+w]
                    if not np.any((region!=0)&(region!=number)):break
                else:safe=False;break
                anchor=r['absolute_anchor'];pending[(name,r['index'])]=dict(rect=[px,py,w,h],origin=[anchor[0]+dx-px,anchor[1]+dy-py],bounds=[b[0]-c[0],b[1]-c[1],b[2]-c[0],b[3]-c[1]])
            if safe:geometry.update(pending);break
        else:raise RuntimeError('Could not separate complete head patches: '+name)
        if max(page.size)>2048:raise RuntimeError('Atlas exceeded existing texture budget')
        dest=candidate/name;dest.parent.mkdir(parents=True,exist_ok=True);page.save(dest)
        image_reports.append(dict(image=name,sha256=prepare.digest(dest),size=list(page.size),gutterAdded=gutter))
        print(f'Prepared {ordinal+1}/{len(grouped)} atlases',flush=True)
    hashes={r['image']:r['sha256'] for r in image_reports}
    for key,a in updated['actions'].items():
        original=manifest['actions'][key];names=list(dict.fromkeys(a.get('frameImages',[a['image']])))
        for name in names:
            rects=a.get('frameRectsByImage',{}).get(name.removesuffix('.png'),a['perFrameRects'])
            for i in range(len(rects)):
                if (name,i) in geometry:rects[i]=geometry[(name,i)]['rect']
        a['perFrameRects']=[geometry.get((a['image'],i),{'rect':r})['rect'] for i,r in enumerate(original['perFrameRects'])]
        origins=copy.deepcopy(original['perFrameOrigins']);bounds=copy.deepcopy(original.get('alphaBounds',[]));phase_bounds=copy.deepcopy(original.get('perPhaseAlphaBounds',{}))
        for r in inv['frames']:
            for ref in r['refs']:
                if ref['action']!=key:continue
                g=geometry[(r['image'],r['index'])]
                if isinstance(origins,list):origins[r['index']]=g['origin']
                else:origins[ref['direction']][ref['phase']]=g['origin']
                if r['image']==a['image'] and r['index']<len(bounds):bounds[r['index']]=g['bounds']
                if ref['direction'] in phase_bounds:phase_bounds[ref['direction']][ref['phase']]=g['bounds']
        a['perFrameOrigins']=origins;a['alphaBounds']=bounds
        if phase_bounds:a['perPhaseAlphaBounds']=phase_bounds
        a['sourcePNGs']=[str(candidate/n) for n in names];a['sourcePNGSHA256s']=[hashes[n] for n in names]
        a['originMethod']='Complete phase-owned crops; body scale calibrated about existing support/flight anchor; inverse head sizing about neck.'
    updated['frameScaleFactors']={}
    for name,records in grouped.items():
        values=[1.]*(max(r['index'] for r in records)+1)
        for r in records:values[r['index']]=factors[(name,r['index'])]
        updated['frameScaleFactors'][name.removesuffix('.png')]=values
    updated['revision']='concept-image-2d-body-scale-v4'
    updated['bodyScaleCalibration']={'revision':'body-scale-v4','reference':'explore_idle_W01; standing head and world scale held fixed',
        'method':cal['method'],'atlases':len(grouped),'physicalFrames':len(reports),'newModelInferences':0,
        'localPoseMeasurements':cal['reliableMeasurements'],'headSizeCompensated':True,'extraOriginalBackups':False,
        'report':str(HERE/'calibration.json')}
    write(candidate/'manifest.json',updated)
    write(HERE/'apply-report.json',dict(status='prepared',images=image_reports,frames=reports,actions=len(updated['actions']),geometry=[dict(image=k[0],index=k[1],**v) for k,v in geometry.items()]))
    review(inv,updated,candidate,geometry)


def review(inv,manifest,candidate,geometry):
    actions=['explore_idle_W01','idle_W01','explore_walk_W01','explore_run_W01','run_W01','attack_sword_W01','attack_bow_W07','spell']
    board=Image.new('RGB',(1200,840),'#252628');draw=ImageDraw.Draw(board);sheets={}
    for col,action in enumerate(actions):
        for row,d in enumerate(prepare.DIRECTIONS):
            phase=1 if action=='attack_sword_W01' else 0
            r=copy.deepcopy(next(r for r in inv['frames'] if any(v==dict(action=action,direction=d,phase=phase) for v in r['refs'])))
            g=geometry[(r['image'],r['index'])];r.update(g);r['scale']*=manifest['frameScaleFactors'][r['image'].removesuffix('.png')][r['index']]
            if r['image'] not in sheets:sheets[r['image']]=Image.open(candidate/r['image']).convert('RGBA')
            thumb=prepare.canvas(r,sheets).resize((140,210),Image.Resampling.LANCZOS)
            x=col*150;y=row*210
            draw.line((x,y+194,x+149,y+194),fill='#65716c')
            draw.line((x,y+24,x+149,y+24),fill='#444c55')
            board.paste(thumb,(x+5,y),thumb);draw.text((x+3,y+2),action.replace('explore_','e_').replace('_W01','')[:20],fill='white')
            draw.text((x+3,y+15),d,fill='#aaaaaa')
    board.save(HERE/'calibrated-states-small.jpg',quality=90)


def install():
    inv=json.loads((HERE/'inventory.json').read_text());report=json.loads((HERE/'apply-report.json').read_text());candidate=HERE/'candidate-runtime'
    if prepare.digest(prepare.MANIFEST)!=inv['manifestSHA256']:raise RuntimeError('Source manifest changed')
    for r in inv['images']:
        if prepare.digest(prepare.ACTOR/r['image'])!=r['sha256'] or prepare.digest(str(prepare.ACTOR/r['image'])+'.meta')!=r['metaSHA256']:raise RuntimeError('Source or meta changed')
    for r in report['images']:
        if prepare.digest(candidate/r['image'])!=r['sha256']:raise RuntimeError('Candidate changed')
    paths=[(prepare.ACTOR/r['image'],candidate/r['image']) for r in report['images']]+[(prepare.MANIFEST,candidate/'manifest.json')]
    for dest,src in paths:dest.with_name(dest.name+'.scale-stage').write_bytes(src.read_bytes())
    for dest,src in paths:os.replace(dest.with_name(dest.name+'.scale-stage'),dest)
    for r in inv['images']:
        if prepare.digest(str(prepare.ACTOR/r['image'])+'.meta')!=r['metaSHA256']:raise RuntimeError('Meta changed')
    report.update(status='installed',manifestSHA256=prepare.digest(prepare.MANIFEST));write(HERE/'apply-report.json',report)
    print({'status':'installed','actions':report['actions'],'atlases':len(report['images']),'frames':len(report['frames'])})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install',action='store_true');args=p.parse_args()
    install() if args.install else prepare_all()
