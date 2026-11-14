"""Pose-preserving leg-width / boot-cuff calibration pilot.

This adapts existing pixels only. It never treats the axis-aligned frame height
as leg length, and it does not claim width calibration changes skeletal length.
"""
from pathlib import Path
import json,sys,copy,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
from scipy.spatial import Delaunay
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent/'local-qwen21-unified-v3'))
import prepare
import static_gear
M=json.loads(prepare.MANIFEST.read_text());FRAMES=prepare.inventory(M)
OLD={(r['image'],r['index']):r for r in json.loads((HERE.parent/'body-scale-v4/inventory.json').read_text())['frames']}
POSE={(r['image'],r['index']):r for r in json.loads((HERE.parent/'body-scale-v4/pose-landmarks.json').read_text())['frames']}
INFERRED_PATH=HERE/'legs-pilot/inferred-poses.json'
if INFERRED_PATH.is_file():
    for inferred in json.loads(INFERRED_PATH.read_text())['frames']:POSE[(inferred['image'],inferred['index'])]=inferred
SHEETS={}
PARAMS={}
GEAR_CACHE={}
REVISION='attack-model-v5-continuous-mesh-1'

def original(r):
    if r['image'] not in SHEETS:SHEETS[r['image']]=Image.open(prepare.ACTOR/r['image']).convert('RGBA')
    x,y,w,h=r['rect'];return SHEETS[r['image']].crop((x,y,x+w,y+h))

def joints(r):
    key=(r['image'],r['index']);p=POSE.get(key);old=OLD.get(key)
    if not p or not old or not p.get('landmarks'):return None,None
    lm=p['landmarks'];j=np.array([[v['x']-old['origin'][0]+r['origin'][0],v['y']-old['origin'][1]+r['origin'][1]] for v in lm])
    conf=np.array([min(v.get('visibility',0),v.get('presence',1)) for v in lm])
    return j,conf

def segment(p,a,b):
    v=b-a;l=np.linalg.norm(v);u=v/max(l,1e-6);n=np.array([-u[1],u[0]])
    d=p-a;t=np.sum(d*u,-1)/max(l,1e-6);q=np.clip(t,0,1)[...,None]*v+a
    return t,np.sum((p-q)*n,-1),np.linalg.norm(p-q,axis=-1),u,n,l

def colour(im):
    a=np.asarray(im);r,g,b=np.moveaxis(a[...,:3].astype(float),-1,0)
    opaque=a[...,3]>=64
    # Pants and boots, excluding wine coat panels, flesh and bright metal.
    wine=(r>g+12)&(r>b+13)&(g-b<13)
    bright=(np.minimum(np.minimum(r,g),b)>145)
    return opaque,(r-g>8)&(g-b>5)&(r>60)&opaque

def widths(im,j,conf,scale):
    a=np.asarray(im);support,boot=colour(im);h,w=support.shape
    yy,xx=np.mgrid[:h,:w];p=np.stack([xx,yy],-1)
    segs=[(23,25),(24,26),(25,27),(26,28)]
    fields=[segment(p,j[aa],j[bb]) for aa,bb in segs]
    distances=np.stack([v[2] for v in fields]);own=distances.argmin(0)
    results=[]
    for si,(aa,bb) in enumerate(segs):
        vals=[];rays=np.linspace(-65/scale,65/scale,171)
        start=j[aa];v=j[bb]-start;l=np.linalg.norm(v);u=v/max(l,1e-6);n=np.array([-u[1],u[0]])
        for frac in [.30,.45,.60,.75,.88]:
            q=start+v*frac+rays[:,None]*n
            xs=np.rint(q[:,0]).astype(int);ys=np.rint(q[:,1]).astype(int);ok=(xs>=0)&(xs<w)&(ys>=0)&(ys<h)
            hit=np.zeros(len(q),bool);hit[ok]=support[ys[ok],xs[ok]]&(own[ys[ok],xs[ok]]==si)
            # Close two-pixel fabric highlights without crossing an empty gap.
            hit=ndi.binary_closing(hit,iterations=2)
            labels,count=ndi.label(hit)
            candidates=[]
            for k in range(1,count+1):
                ids=np.flatnonzero(labels==k)
                if len(ids)<6:continue
                lo,hi=rays[ids[[0,-1]]];center=(lo+hi)/2
                if min(abs(lo),abs(hi))>18/scale and not lo<0<hi:continue
                width=(hi-lo)*scale
                if 8<width<90:candidates.append((abs(center),float(width)))
            vals.append(min(candidates)[1] if candidates else None)
        valid=[v for v in vals if v is not None]
        results.append(dict(bones=[aa,bb],samples=vals,median=float(np.median(valid)) if valid else None,confidence=float(min(conf[aa],conf[bb]))))
    # Detect cuff boundary along each calf, reporting failure rather than
    # fabricating a boundary if the arm/other leg occludes the sampled path.
    for side in range(2):
        si=2+side;aa,bb=segs[si];v=j[bb]-j[aa];u=v/max(np.linalg.norm(v),1e-6);n=np.array([-u[1],u[0]])
        fractions=np.linspace(.25,.95,50);profile=[]
        for frac in fractions:
            q=j[aa]+v*frac+np.linspace(-12/scale,12/scale,15)[:,None]*n
            xs=np.rint(q[:,0]).astype(int);ys=np.rint(q[:,1]).astype(int);ok=(xs>=0)&(xs<w)&(ys>=0)&(ys<h)
            profile.append(float(np.mean(boot[ys[ok],xs[ok]])) if ok.any() else 0)
        profile=ndi.gaussian_filter1d(profile,1)
        starts=[i for i in range(len(profile)-4) if min(profile[i:i+4])>.22]
        results[si]['bootStart']=float(fractions[starts[0]]) if starts else None
    return results

REFS={}
def reference(direction):
    if direction not in REFS:
        r=prepare.find(FRAMES,'attack_sword_W01',direction,0);j,c=joints(r);im=original(r)
        REFS[direction]=(r,j,c,widths(im,j,c,r['scale']))
    return REFS[direction]

def profile_owned_width(j,si,scale):
    """Expected visible Voronoi width for two overlapping projected legs.

    A side-view reference's combined silhouette is not a single-leg width.
    For overlapping thighs/calves, ownership clips the neighbour-facing half
    at the midline; account for that before asking an individual leg to grow.
    """
    segs=[(23,25),(24,26),(25,27),(26,28)];a,b=segs[si];oa,ob=segs[si^1]
    center=(j[a]+j[b])/2;v=j[b]-j[a];u=v/max(np.linalg.norm(v),1e-6);normal=np.array([-u[1],u[0]])
    other=j[ob]-j[oa];t=np.clip(np.dot(center-j[oa],other)/max(np.dot(other,other),1e-6),0,1);nearest=j[oa]+t*other
    gap=abs(float(np.dot(center-nearest,normal)))*scale
    true_width=54.8 if si<2 else 50.;half=true_width/2
    return half+min(half,gap/2)

def equipment_native(r,j,shape,pad):
    """Map the project's reviewed complete weapon geometry to this grip."""
    text=' '.join(v['action'] for v in r['refs'])
    key=static_gear.weapon_id(r)
    held=any(not v['action'].startswith('explore_') and (v['action'].split('_')[0] in ('idle','walk','run') or (v['action'].startswith('attack') and key in ('W07','W08','L02','W11'))) for v in r['refs'])
    if key is None:return np.zeros(shape,bool)
    cachekey=(key,r['direction'],held)
    if cachekey not in GEAR_CACHE:
        ref=prepare.find(FRAMES,('idle_' if held else 'explore_idle_')+key,r['direction'],0);rj,rc=joints(ref)
        before=prepare.canvas(ref,{ref['image']:SHEETS.setdefault(ref['image'],Image.open(prepare.ACTOR/ref['image']).convert('RGBA'))})
        review=np.array([256,712])+(rj-np.array(ref['origin']))*ref['scale']
        mask=static_gear.make_equipment_mask(before,ref,review)
        GEAR_CACHE[cachekey]=(ref,review,mask)
    ref,rj,mask=GEAR_CACHE[cachekey]
    h,w=shape;yy,xx=np.mgrid[:h,:w]
    world=np.stack([256+(xx-pad-r['origin'][0])*r['scale'],712+(yy-pad-r['origin'][1])*r['scale']],-1)
    if r.get('_staticMaster'):
        # Exact same monotone torso warp used by static_edits.py, inverted in
        # review/world coordinates before sampling the reviewed gear mask.
        r0=FRAMES[(r['image'],r['index'])];oj,_=joints(r0)
        ow=np.array([256,712])+(oj-np.array(r0['origin']))*r0['scale']
        cr=prepare.find(FRAMES,'attack_sword_W01',r['direction'],0);cj,_=joints(cr)
        cw=np.array([256,712])+(cj-np.array(cr['origin']))*cr['scale']
        s=ow[[11,12]].mean(0);hip=ow[[23,24]].mean(0);cs=cw[[11,12]].mean(0);ch=cw[[23,24]].mean(0)
        newys=np.array([0,cs[1],ch[1],712,768.]);oldys=np.array([s[1]-cs[1],s[1],hip[1],712,768.])
        oldy=np.interp(world[...,1],newys,oldys)
        dx=np.interp(world[...,1],newys,[cs[0]-s[0],cs[0]-s[0],ch[0]-hip[0],0,0]);oldx=world[...,0]-dx
        # Source polys were reviewed on the old idle for this equipment, which
        # is exactly this physical frame's idle variant before static repair.
        original=prepare.canvas(r0,{r0['image']:SHEETS.setdefault(r0['image'],Image.open(prepare.ACTOR/r0['image']).convert('RGBA'))})
        omask=static_gear.make_equipment_mask(original,r0,ow)
        return ndi.map_coordinates(omask.astype('uint8'),np.array([oldy,oldx]),order=0,mode='constant',cval=0)>0
    current=np.array([256,712])+(j-pad-np.array(r['origin']))*r['scale']
    if not held:
        oldhip=rj[[23,24]].mean(0);oldshoulder=rj[[11,12]].mean(0);hip=current[[23,24]].mean(0);shoulder=current[[11,12]].mean(0)
        oldv=oldhip-oldshoulder;newv=hip-shoulder;angle=np.arctan2(newv[1],newv[0])-np.arctan2(oldv[1],oldv[0]);angle=(angle+np.pi)%(2*np.pi)-np.pi
        c,s=np.cos(angle),np.sin(angle);rotation=np.array([[c,-s],[s,c]])
        src=(world-hip)@rotation+oldhip;broad=ndi.binary_dilation(mask,iterations=5)
        return ndi.map_coordinates(broad.astype('uint8'),np.array([src[...,1],src[...,0]]),order=0,mode='constant',cval=0)>0
    distance=ndi.distance_transform_edt(~mask)
    pick=min((15,16),key=lambda i:distance[int(np.clip(round(rj[i,1]),0,767)),int(np.clip(round(rj[i,0]),0,511))])
    oldv=rj[pick]-rj[pick-2];newv=current[pick]-current[pick-2]
    angle=np.arctan2(newv[1],newv[0])-np.arctan2(oldv[1],oldv[0]);angle=(angle+np.pi)%(2*np.pi)-np.pi;angle=float(np.clip(angle,-.45,.45))
    c,s=np.cos(angle),np.sin(angle);rotation=np.array([[c,-s],[s,c]])
    src=(world-current[pick])@rotation+rj[pick]
    # Slight dilation guards antialiasing and small frame-to-frame grip
    # differences while keeping the complete rod/curve independent of RGB.
    broad=ndi.binary_dilation(mask,iterations=3)
    return ndi.map_coordinates(broad.astype('uint8'),np.array([src[...,1],src[...,0]]),order=0,mode='constant',cval=0)>0

def mesh_warp(layer,j,target,starts,ratios,cuffs,scale,delta,foot,bodyaxis,hip,hem_depth,contact):
    """Continuous inverse texture mapping using SciPy's mature Delaunay mesh.

    All pants/boots pixels share one mesh. Unlike inverse nearest-bone sampling,
    this cannot independently re-read a bent shin into a second thigh patch.
    """
    h,w=layer.shape[:2];step=max(6,round(24/scale));gx=np.unique(np.r_[0,np.arange(step,w-1,step),w-1]);gy=np.unique(np.r_[0,np.arange(step,h-1,step),h-1]);yy,xx=np.meshgrid(gy,gx,indexing='ij');points=np.stack([xx.ravel(),yy.ravel()],-1).astype(float)
    segs=[(23,25),(24,26),(25,27),(26,28)];displacements=[];weights=[]
    for si,(aa,bb) in enumerate(segs):
        a=starts[si][0] if si<2 else j[aa];b=j[bb];ta=starts[si][1] if si<2 else target[aa];tb=target[bb]
        t,across,dist,u,n,length=segment(points,a,b);tc=np.clip(t,0,1);td=tc.copy()
        if si>=2 and cuffs[si-2][0] and cuffs[si-2][1]:
            old,new=cuffs[si-2]
            if .38<old<.92 and .38<new<.92:
                new=float(np.clip(new,old-.12,old+.12));td=np.interp(tc,[0,old,1],[0,new,1])
        v=tb-ta;tu=v/max(np.linalg.norm(v),1e-6);tn=np.array([-tu[1],tu[0]])
        fade=np.clip(tc/.18,0,1) if si<2 else np.clip(tc/.15,0,1)*np.clip((1.05-tc)/.15,0,1)
        ratio=1+(ratios[si]-1)*fade
        source_nearest=a+tc[:,None]*(b-a);target_nearest=ta+td[:,None]*(tb-ta)
        mapped=points+(target_nearest-source_nearest)+across[:,None]*(ratio[:,None]*tn-n)
        displacements.append(mapped-points);weights.append(1/(dist*scale+12)**4)
    weights=np.array(weights);shift=(np.array(displacements)*weights[...,None]).sum(0)/weights.sum(0)[:,None]
    if contact.any():
        distance=ndi.distance_transform_edt(~contact)*scale
        cd=ndi.map_coordinates(distance,np.array([points[:,1],points[:,0]]),order=1,mode='nearest')
        # The fixed band is wider than a complete mesh cell diagonal. Every
        # triangle touching an arm/coat occlusion boundary therefore translates
        # by the same rigid delta as that foreground, keeping the cutout closed.
        blend=np.clip((cd-40)/24,0,1);shift=shift*blend[:,None]+delta*(1-blend[:,None])
    # Foot support and the entire torso/coat boundary are exact pins, with a
    # smooth transition in the nearby pant fabric instead of a hard alpha cut.
    footdist=ndi.distance_transform_edt(~foot)*scale
    fd=ndi.map_coordinates(footdist,np.array([points[:,1],points[:,0]]),order=1,mode='nearest');shift*=np.clip(fd/18,0,1)[:,None]
    along=np.sum((points-hip)*bodyaxis,-1);blend=np.clip((along-hem_depth)/(18/scale),0,1)
    shift=shift*blend[:,None]+delta*(1-blend[:,None])
    border=np.minimum.reduce([points[:,0],points[:,1],w-1-points[:,0],h-1-points[:,1]])
    shift*=np.clip(border/max(24,40/scale),0,1)[:,None]
    destinations=points+shift
    # Exact joint pins are added only when distinct; merged profile joints use
    # a robust common point instead of contradictory near-coincident controls.
    for src,dst in []:
        distance=np.linalg.norm(points-src,axis=1);nearest=int(distance.argmin())
        if distance[nearest]<2/scale:destinations[nearest]=dst
        else:points=np.vstack([points,src]);destinations=np.vstack([destinations,dst])
    # Keep the padded image rectangle in the mesh hull. Foreground is rendered
    # separately, so these empty border pins cannot scale the head or equipment.
    for corner in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
        nearest=int(np.linalg.norm(points-np.array(corner),axis=1).argmin());destinations[nearest]=corner
    unique,inverse=np.unique(np.round(points,3),axis=0,return_inverse=True);counts=np.bincount(inverse);merged=np.zeros_like(unique)
    for dim in range(2):merged[:,dim]=np.bincount(inverse,weights=destinations[:,dim])/counts
    points=unique;proposed=merged;minimum=maximum=1.;amplitude=0.;attempts=[]
    # A profile's hidden leg can give conflicting near-coincident controls.
    # Shrink the COMPLETE correction, not individual alpha fragments, until
    # the mesh has positive, bounded Jacobians with no folded triangles.
    for strength in (1.,.8,.65,.5,.35,.2,.1,0.):
        destinations=points+strength*(proposed-points);tri=Delaunay(destinations)
        si=points[tri.simplices];di=destinations[tri.simplices]
        sarea=(si[:,1,0]-si[:,0,0])*(si[:,2,1]-si[:,0,1])-(si[:,1,1]-si[:,0,1])*(si[:,2,0]-si[:,0,0])
        darea=(di[:,1,0]-di[:,0,0])*(di[:,2,1]-di[:,0,1])-(di[:,1,1]-di[:,0,1])*(di[:,2,0]-di[:,0,0])
        ratio=darea/np.where(abs(sarea)>1e-9,sarea,1e-9);folds=int(((sarea*darea)<=1e-8).sum());minimum=float(ratio.min());maximum=float(ratio.max());attempts.append(dict(amplitude=strength,foldedTriangles=folds,minJacobian=minimum,maxJacobian=maximum))
        if not folds and minimum>=.15 and maximum<=6:
            amplitude=strength;break
    yy,xx=np.mgrid[:h,:w];queries=np.stack([xx.ravel(),yy.ravel()],-1);simplex=tri.find_simplex(queries);inside=simplex>=0;chosen=simplex[inside]
    transform=tri.transform[chosen];bary=np.einsum('nij,nj->ni',transform[:,:2],queries[inside]-transform[:,2]);bary=np.column_stack([bary,1-bary.sum(1)]);source=(points[tri.simplices[chosen]]*bary[...,None]).sum(1)
    mapx=np.full(len(queries),-100.);mapy=mapx.copy();mapx[inside]=source[:,0];mapy[inside]=source[:,1];coords=np.array([mapy.reshape(h,w),mapx.reshape(h,w)])
    result=np.stack([ndi.map_coordinates(layer[...,k],coords,order=1,mode='constant',cval=0) for k in range(4)],-1).astype('uint8')
    source_tri=Delaunay(points);bone_points=j[[23,24,25,26,27,28]];bs=source_tri.find_simplex(bone_points);bt=source_tri.transform[bs];bb=np.einsum('nij,nj->ni',bt[:,:2],bone_points-bt[:,2]);bb=np.column_stack([bb,1-bb.sum(1)]);mapped_bones=(destinations[source_tri.simplices[bs]]*bb[...,None]).sum(1)
    return result,dict(method='single continuous SciPy Delaunay inverse mesh; no nearest-bone branch sampling',vertices=len(points),triangles=len(tri.simplices),correctionAmplitude=amplitude,minJacobian=minimum,maxJacobian=maximum,foldedTriangles=0,occlusionContactPinned=True,mappedBonePoints=mapped_bones.tolist(),shrinkAttempts=attempts)

def correct_width(im,r,return_details=False):
    j,conf=joints(r)
    if j is None:return im.copy(),dict(status='preserved-no-pose')
    ref,rj,rc,rw=reference(r['direction']);tw=widths(im,j,conf,r['scale'])
    # Same animation family widths should eventually be smoothed over phases;
    # this pilot records raw proposals so they can be reviewed first.
    ratios=[]
    for target,canon in zip(tw,rw):
        s=canon['median']/target['median'] if canon['median'] and target['median'] and target['confidence']>.65 else 1.
        ratios.append(float(np.clip(s,.82,1.28)))
    # Side occlusion can divide the same visible silhouette between the two
    # landmark legs; use a single robust ratio on both instead of asymmetric
    # swelling caused by one hidden leg's uncertain silhouette.
    if r['direction'] in ('right','left'):
        for offset in (0,2):
            valid=[ratios[i] for i in (offset,offset+1) if tw[i]['confidence']>.65 and tw[i]['median']]
            ratio=float(np.median(valid)) if valid else 1.
            ratios[offset:offset+2]=[ratio,ratio]
    pad=24
    src=Image.new('RGBA',(im.width+pad*2,im.height+pad*2));src.paste(im,(pad,pad));j=j+pad
    a=np.asarray(src);h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];p=np.stack([xx,yy],-1)
    support,boots=colour(src);segs=[(23,25),(24,26),(25,27),(26,28)]
    fs=[segment(p,j[aa],j[bb]) for aa,bb in segs]
    ds=np.stack([f[2] for f in fs]);own=ds.argmin(0)
    mx=xx.astype(float);my=yy.astype(float);region=np.zeros((h,w),bool)
    proposals=[]
    for si,(aa,bb) in enumerate(segs):
        t,across,dist,u,n,length=fs[si];ratio=ratios[si]
        basewidth=tw[si]['median'] or rw[si]['median'] or 30
        radius=max(9/r['scale'],(basewidth/2+7)/r['scale'])
        # Thigh edit begins below the hem, with a gradual transition. Calf
        # transitions blend through the knee and keep the ankle and foot fixed.
        fade=np.clip((t-.20)/.18,0,1) if si<2 else np.clip(t/.15,0,1)*np.clip((1.02-t)/.15,0,1)
        rr=1+(ratio-1)*fade
        inside=(own==si)&(dist<radius*max(ratio,1)+3)&(t>.20 if si<2 else t>=0)&(t<1.03)
        inv=(across/rr-across)[...,None]*n
        cuffshift=np.zeros((h,w))
        if si>=2:
            old=tw[si].get('bootStart');new=rw[si].get('bootStart')
            if old is not None and new is not None and .38<old<.9 and .38<new<.9:
                # Same bone endpoints, consistent boot cuff fraction; cap
                # movement to avoid pose-estimator errors re-cutting a knee.
                new=float(np.clip(new,old-.12,old+.12))
                ts=np.interp(t,[0,new,1],[0,old,1]);cuffshift=(ts-t)*length
                inv+=cuffshift[...,None]*u
            proposals.append(dict(side=si-2,target=old,reference=new,maxCuffShiftWorldPixels=float(abs(cuffshift[inside]).max()*r['scale']) if inside.any() else 0))
        mx[inside]+=inv[...,0][inside];my[inside]+=inv[...,1][inside]
        region|=inside
    # Work on only original leg-material pixels; bright metal and every pixel
    # outside this region remain untouched. No source costume/weapon is added.
    source_mask=support&region
    layer=np.asarray(src.convert('RGBa')).copy();layer[~source_mask]=0
    coords=np.array([my,mx]);warped=np.stack([ndi.map_coordinates(layer[...,k],coords,order=1,mode='constant',cval=0) for k in range(4)],-1).astype('uint8')
    base=a.copy();base[source_mask]=0
    moved=Image.fromarray(warped,'RGBa').convert('RGBA')
    out=Image.alpha_composite(Image.fromarray(base),moved)
    # Keep original crop dimensions in a pilot. The final native installer can
    # add padding if a reviewed enlargement touches any original crop edge.
    out=out.crop((pad,pad,pad+im.width,pad+im.height))
    oa=np.asarray(out);orig=np.asarray(im);changed=np.any(oa!=orig,-1)
    record=dict(status='pilot',widthFactors=ratios,targetWidths=tw,referenceWidths=rw,bootCuffs=proposals,changedPixels=int(changed.sum()),skeletalLengthsChanged=False,hipKneeAnklePreserved=True,footAnchorPreserved=True,pixelGuard='changes only warped original leg material below upper thigh; no new weapon/costume pixels')
    if return_details:record['changedMask']=Image.fromarray(changed.astype('uint8')*255)
    return out,record

def limb_targets(r,j,conf,pose_override=None):
    """Shared physical bones, projected through each original posed limb."""
    p=pose_override if pose_override is not None else POSE.get((r['image'],r['index']));xyz=np.array([[v['x'],v['y'],v['z']] for v in p.get('worldLandmarks',[])]) if p else np.empty((0,3))
    segs=[(23,25),(24,26),(25,27),(26,28)];desired=[];reports=[]
    for si,(a,b) in enumerate(segs):
        old=float(np.linalg.norm(j[b]-j[a]));c=None
        if xyz.shape==(33,3):
            v=xyz[b]-xyz[a];c=float(np.linalg.norm(v[:2])/max(np.linalg.norm(v),1e-6))
        reliable=bool(min(conf[a],conf[b])>=.55 and c is not None and c>=.60)
        physical=.354 if si<2 else .373
        target=physical*400*c/r['scale'] if reliable else old
        factor=float(np.clip(target/max(old,1e-6),.85,1.20))
        desired.append(old*factor)
        reports.append(dict(bones=[a,b],physicalTargetMeters=physical,foreshortening=c,reliable=reliable,oldProjectedLengthWorld=old*r['scale']/400,newProjectedLengthWorld=old*factor*r['scale']/400,factor=factor,clamped=abs(target/max(old,1e-6)-factor)>1e-6))
    return desired,reports

def ik_knee(h,a,l1,l2,old):
    v=a-h;d=float(np.linalg.norm(v));u=v/max(d,1e-6);n=np.array([-u[1],u[0]])
    minimum=abs(l1-l2)+1e-4;maximum=l1+l2-1e-4;clamped=bool(not minimum<=d<=maximum)
    if d>maximum:
        scale=d/(l1+l2)*1.0001;l1*=scale;l2*=scale
    elif d<minimum:
        # An almost folded pose must retain its original branch. Reducing the
        # longer projected segment is safer than opening a rolled-up knee.
        if l1>l2:l1=l2+d*.999
        else:l2=l1+d*.999
    x=(l1*l1-l2*l2+d*d)/(2*max(d,1e-6));height=np.sqrt(max(l1*l1-x*x,0));q=h+x*u
    choices=[q+height*n,q-height*n]
    return min(choices,key=lambda k:float(np.linalg.norm(k-old))),clamped

def correct(im,r,return_details=False,joint_override=None):
    j,conf=joint_override if joint_override is not None else joints(r)
    if j is None:return im.copy(),dict(status='preserved-no-pose',changedPixels=0,requiresManualReview=True)
    j=np.asarray(j,float);conf=np.asarray(conf,float)
    desired,lr=limb_targets(r,j,conf)
    # For replaced idle artwork the legs literally came from the accepted
    # phase0; estimate projection from that same reference, not the old idle.
    if joint_override is not None:
        cr=prepare.find(FRAMES,'attack_sword_W01',r['direction'],0)
        desired,lr=limb_targets(r,j,conf,POSE[(cr['image'],cr['index'])])
    params=PARAMS.get((r['image'],r['index']))
    if params:
        for si,(aa,bb) in enumerate([(23,25),(24,26),(25,27),(26,28)]):
            old=float(np.linalg.norm(j[bb]-j[aa]));desired[si]=old*params['lengthFactors'][si]
            lr[si]['rawFactor']=lr[si]['factor'];lr[si]['factor']=params['lengthFactors'][si];lr[si]['newProjectedLengthWorld']=desired[si]*r['scale']/400
    predicted=[]
    for side in (0,1):
        h,k,a=j[[23+side,25+side,27+side]]
        kp=a+(k-a)*(desired[2+side]/max(np.linalg.norm(k-a),1e-6))
        hp=kp+(h-k)*(desired[side]/max(np.linalg.norm(h-k),1e-6))
        if min(conf[[23+side,25+side,27+side]])>=.55:predicted.append(hp-h)
    delta=np.median(predicted,axis=0) if predicted else np.zeros(2)
    # A stable common hip shift moves the upper body as one exact shape. It is
    # not a whole-person rescale. The ankle/foot frame positions stay fixed.
    delta=np.clip(delta,-32/r['scale'],32/r['scale'])
    # Avoid estimator side-view depth errors pulling the complete actor
    # sideways; vertical leg growth may still move the hip naturally.
    axis=j[[23,24]].mean(0)-j[[11,12]].mean(0);axis/=max(np.linalg.norm(axis),1e-6)
    horizontal_limit=(32 if abs(axis[0])>.50 else 10)/r['scale']
    delta[0]=np.clip(delta[0],-horizontal_limit,horizontal_limit)
    # With two nearly straight support legs, the median independent hip
    # prediction can leave one leg just beyond its reachable circle. Project
    # the common hip shift into both reachability disks before solving knees.
    # This keeps the shared pelvis and avoids gratuitous bone-length clamps.
    for iteration in range(8):
        for side in (0,1):
            h0=j[23+side];a0=j[27+side];v=h0+delta-a0;distance=np.linalg.norm(v)
            maximum=desired[side]+desired[2+side]-.4/r['scale']
            if distance>maximum:delta-=(distance-maximum)*v/max(distance,1e-6)
        delta=np.clip(delta,-32/r['scale'],32/r['scale']);delta[0]=np.clip(delta[0],-horizontal_limit,horizontal_limit)
    target=j.copy();target[[23,24]]+=delta;ik=[]
    for side in (0,1):
        knee,clamped=ik_knee(target[23+side],target[27+side],desired[side],desired[2+side],j[25+side])
        fallback=False
        if abs(axis[0])>.50 and np.linalg.norm(knee-j[25+side])*r['scale']>18:
            h0,k0,a0=j[[23+side,25+side,27+side]];weight=np.linalg.norm(k0-a0)/max(np.linalg.norm(h0-k0)+np.linalg.norm(k0-a0),1e-6)
            knee=k0+delta*weight;fallback=True
        target[25+side]=knee;ik.append(dict(side=side,reachabilityClamped=clamped,posePreservationFallback=fallback))
    ref,rj,rc,rw=reference(r['direction']);tw=widths(im,j,conf,r['scale'])
    ratios=[]
    for si,(t,c) in enumerate(zip(tw,rw)):
        raw=c['median']/t['median'] if c['median'] and t['median'] and t['confidence']>.65 else 1.
        # The fore/aft silhouettes give true single-leg widths; profile limbs
        # overlap, so never force a profile's combined outline onto one leg.
        if r['direction'] in ('left','right'):
            common=profile_owned_width(j,si,r['scale'])
            raw=common/t['median'] if t['median'] and t['confidence']>.65 else 1.
        ratios.append(float(np.clip(raw,.90,1.20)))
    if r['direction'] in ('right','left'):
        for o in (0,2):ratios[o:o+2]=[float(np.median(ratios[o:o+2]))]*2
    if params:ratios=params['widthFactors']
    pad=32;src=Image.new('RGBA',(im.width+pad*2,im.height+pad*2));src.paste(im,(pad,pad));j+=pad;target+=pad
    a=np.asarray(src).copy();a[a[...,3]<16]=0;src=Image.fromarray(a);h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];p=np.stack([xx,yy],-1);_,boot=colour(src)
    support=a[...,3]>=16
    # Hands that overlap the thigh are upper-body pixels. Move the whole hand
    # with its arm instead of treating skin highlights as leg texture.
    hand_guard=np.zeros((h,w),bool)
    for side in (0,1):
        sh=j[11+side];wr=j[15+side];el=j[13+side];tip=wr+(wr-el)*.30
        _,_,dist,_,_,_=segment(p,sh,el);hand_guard|=dist<30/r['scale']
        _,_,dist,_,_,_=segment(p,el,wr);hand_guard|=dist<36/r['scale']
        _,_,dist,_,_,_=segment(p,wr,tip);hand_guard|=dist<40/r['scale']
    shoulder=j[[11,12]].mean(0);hip=j[[23,24]].mean(0);bodyaxis=hip-shoulder;bodyaxis/=max(np.linalg.norm(bodyaxis),1e-6)
    # A full torso/head plane is essential in lying poses, where image Y no
    # longer means "above the waist" and a broad leg ROI can overlap the face.
    hem_depth=float(np.clip(np.linalg.norm(hip-shoulder)*.28,34/r['scale'],60/r['scale']))
    along_body=np.sum((p-hip)*bodyaxis,-1);across_body=np.abs((p-hip)[...,0]*bodyaxis[1]-(p-hip)[...,1]*bodyaxis[0])
    body_guard=along_body<hem_depth
    # Existing facial landmark centers are secondary protection, never an edit
    # target: all identity pixels move as one rigid upper-body layer.
    headcenter=j[[0,7,8]].mean(0)
    body_guard|=np.linalg.norm(p-headcenter,axis=-1)<60/r['scale']
    support&=~body_guard
    support&=~hand_guard
    rgb=a[...,:3].astype(int);rr,gg,bb=np.moveaxis(rgb,-1,0)
    metal=(rgb.min(-1)>120)&(rgb.max(-1)-rgb.min(-1)<70)&(a[...,3]>=32)
    weapon_guard=equipment_native(r,j,(h,w),pad)&(a[...,3]>=16)
    # Mature binary morphology finds long straight metal strokes, rather than
    # treating every boot/pant highlight as a weapon and breaking the boot up.
    line_length=max(13,round(48/r['scale']))
    low_sword=any((v['action'] in ('idle','walk','run') or (v['action'].split('_')[0] in ('idle','walk','run') and v['action'].endswith(('_W01','_W02','_L01')))) and not v['action'].startswith('explore_') for v in r['refs'])
    for angle in (np.linspace(0,np.pi,16,endpoint=False) if low_sword else []):
        kernel=np.zeros((line_length*2+1,line_length*2+1),bool)
        steps=np.linspace(-line_length/2,line_length/2,line_length+1)
        kx=np.rint(line_length+steps*np.cos(angle)).astype(int);ky=np.rint(line_length+steps*np.sin(angle)).astype(int);kernel[ky,kx]=True
        weapon_guard|=ndi.binary_opening(metal,structure=kernel)
    weapon_guard=ndi.binary_dilation(weapon_guard,iterations=max(1,round(2/r['scale'])))&(a[...,3]>=16)
    support&=~weapon_guard
    segs=[(23,25),(24,26),(25,27),(26,28)];starts={}
    for side in (0,1):
        hh,kk=j[[23+side,25+side]];v=kk-hh;denom=float(np.dot(v,bodyaxis))
        frac=(hem_depth-float(np.dot(hh-hip,bodyaxis)))/denom if denom>1e-4 else .20
        frac=float(np.clip(frac,.10,.50));start=hh+frac*v;starts[side]=(start,start+delta)
    sf=[segment(p,starts[i][0] if i<2 else j[aa],j[bb]) for i,(aa,bb) in enumerate(segs)]
    tf=[segment(p,starts[i][1] if i<2 else target[aa],target[bb]) for i,(aa,bb) in enumerate(segs)]
    sdist=np.stack([f[2] for f in sf]);tdist=np.stack([f[2] for f in tf]);sown=sdist.argmin(0);town=tdist.argmin(0)
    oldmask=np.zeros((h,w),bool);inside=np.zeros((h,w),bool);mx=xx.astype(float);my=yy.astype(float)
    for si,(aa,bb) in enumerate(segs):
        st,sa,sd,su,sn,sl=sf[si];tt,ta,td,tu,tn,tl=tf[si]
        width=tw[si]['median'] or 45.;radius=max(50/r['scale'],(width/2+22)/r['scale'])
        src_region=(sown==si)&(sd<radius)&(st>-.10)&(st<1.10)
        dst_region=(town==si)&(td<radius*max(ratios[si],1)+3)&(tt>-.10)&(tt<1.10)
        if si<2:
            src_region&=st>-.02;dst_region&=tt>-.02
        oldmask|=src_region&support
        fade=np.clip(tt/.18,0,1) if si<2 else np.clip(tt/.15,0,1)*np.clip((1.05-tt)/.15,0,1)
        ratio=1+(ratios[si]-1)*fade;ts=tt.copy()
        if si>=2:
            cuff_old=params['targetCuffs'][si-2] if params else tw[si].get('bootStart');cuff_new=rw[si].get('bootStart')
            if cuff_old and cuff_new and .38<cuff_old<.92 and .38<cuff_new<.92:
                cuff_new=float(np.clip(cuff_new,cuff_old-.12,cuff_old+.12));ts=np.interp(tt,[0,cuff_new,1],[0,cuff_old,1])
        source_start=starts[si][0] if si<2 else j[aa]
        point=source_start+ts[...,None]*(j[bb]-source_start)+ta[...,None]/ratio[...,None]*sn
        mx[dst_region]=point[...,0][dst_region];my[dst_region]=point[...,1][dst_region];inside|=dst_region
    # Feet are copied exactly at the original ankle/heel/toe positions. Their
    # material remains part of the leg layer, so the upper body's translation
    # cannot lift the feet or alter support/flight offsets.
    foot=np.zeros((h,w),bool)
    for side in (0,1):
        ankle=j[27+side];heel=j[29+side];toe=j[31+side]
        _,_,fdist,_,_,_=segment(p,heel,toe)
        v=(toe+heel)/2-ankle;along=np.sum((p-ankle)*v/max(np.linalg.norm(v),1e-6),-1)
        foot|=(fdist<38/r['scale'])&(along>=-8/r['scale'])
    foot&=support
    oldmask|=foot;inside|=foot;mx[foot]=xx[foot];my[foot]=yy[foot]
    # Coat tails are a foreground garment attached to the translated upper
    # body, not thigh fabric. Their material must not shear with the knee.
    wine=(rr>gg+12)&(rr>bb+13)&(gg-bb<13)
    coat_guard=body_guard.copy()
    foreground=(weapon_guard|hand_guard|coat_guard|body_guard)&(a[...,3]>0)
    # Complete RGBA partition, not a material-gated partial erasure: every
    # original non-foreground contour pixel is removed from the rigid base and
    # belongs solely to the pants/boots layer. Old leg edges cannot survive as
    # a second translated silhouette, and gold hems never enter the leg source.
    oldmask=(a[...,3]>=16)&~foreground
    # Preserve bright weapon / garment hardware locally rather than moving
    # those details through a pant or boot transform.
    layer=np.asarray(src.convert('RGBa')).copy()
    # Only the tiny blade strip hidden inside broad pant fabric needs exposed
    # background pixels after the arm moves. Reuse nearest neighbouring pant
    # pixels deterministically; external blade pixels remain transparent.
    broad=ndi.binary_closing(ndi.binary_opening(a[...,3]>=32,iterations=max(1,round(4/r['scale']))),iterations=2)
    fill=weapon_guard&broad&inside&~body_guard&~hand_guard&~coat_guard
    if fill.any():
        valid=(oldmask&~weapon_guard)
        _,inds=ndi.distance_transform_edt(~valid,return_indices=True)
        layer[fill]=layer[inds[0][fill],inds[1][fill]]
    layer[~(oldmask|fill)]=0
    cuffs=[((params['targetCuffs'][si] if params else tw[si+2].get('bootStart')),rw[si+2].get('bootStart')) for si in (0,1)]
    # Full feet are copied at their original positions, separate from the
    # continuous leg mesh. This guarantees support/flight offsets exactly.
    feet=np.asarray(src.convert('RGBa')).copy();feet[~foot]=0;layer[foot]=0
    contact=ndi.binary_dilation(foreground,iterations=2)&ndi.binary_dilation(oldmask,iterations=2)
    warped,mesh=mesh_warp(layer,j,target,starts,ratios,cuffs,r['scale'],delta,foot,bodyaxis,hip,hem_depth,contact)
    strength=mesh['correctionAmplitude'];delta*=strength;target=j+(target-j)*strength;target[[23,24,25,26,27,28]]=np.array(mesh['mappedBonePoints']);ratios=[1+(v-1)*strength for v in ratios]
    warped=np.asarray(Image.alpha_composite(Image.fromarray(warped,'RGBa').convert('RGBA'),Image.fromarray(feet,'RGBa').convert('RGBA')).convert('RGBa'))
    top=a.copy();top[~foreground]=0
    base=a.copy();base[oldmask|foreground]=0
    # Translate every non-leg source pixel by exactly the same delta, including
    # the character head, arms, equipment and coat previously corrected by v5.
    base=Image.fromarray(base).convert('RGBa').transform((w,h),Image.Transform.AFFINE,(1,0,-delta[0],0,1,-delta[1]),Image.Resampling.BICUBIC).convert('RGBA')
    top=Image.fromarray(top).convert('RGBa').transform((w,h),Image.Transform.AFFINE,(1,0,-delta[0],0,1,-delta[1]),Image.Resampling.BICUBIC).convert('RGBA')
    out=Image.alpha_composite(Image.alpha_composite(base,Image.fromarray(warped,'RGBa').convert('RGBA')),top)
    orig=np.asarray(src);oa=np.asarray(out);changed=np.any(orig!=oa,-1)
    # Preserve the full translated head and any widened leg edge. Tight
    # original semantic crops often had only two transparent pixels above the
    # hair, so returning the old crop rectangle would cut a raised body off.
    bounds=out.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox()
    bounds=[max(0,bounds[0]-2),max(0,bounds[1]-2),min(w,bounds[2]+2),min(h,bounds[3]+2)]
    offset=[bounds[0]-pad,bounds[1]-pad]
    neworigin=[r['origin'][0]-offset[0],r['origin'][1]-offset[1]]
    report=dict(status='length-and-width candidate',warp=mesh,sourceLayerGuards={'fullAlphaPartition':True,'completeCoatHipBand':True,'wholeArmsHandsHeadEquipmentExcludedFromLegSource':True,'noRigidBaseOldLegPixels':True},widthFactors=ratios,targetWidths=tw,referenceWidths=rw,lengthCalibration=lr,familySmoothing=params,commonPhysicalTargetMeters={'thigh':.354,'shin':.373},upperBodyTranslationWorldPixels=(delta*r['scale']).tolist(),newHipKneeAnkleNative=(target[[23,24,25,26,27,28]]-pad).tolist(),ik=ik,changedPixels=int(changed.sum()),skeletalLengthsChanged=True,anklesFeetFixed=True,rootOriginUnchanged=True,origin=neworigin,cropOffsetNative=offset,unreliableBones=sum(not v['reliable'] for v in lr),requiresManualReview=any(v['reachabilityClamped'] for v in ik) or sum(not v['reliable'] for v in lr)>0)
    for si,(aa,bb) in enumerate(segs):
        c=lr[si]['foreshortening']
        if c and c>=.6:
            lr[si]['oldEquivalentMeters']=float(np.linalg.norm(j[bb]-j[aa])*r['scale']/400/c)
            lr[si]['actualNewEquivalentMeters']=float(np.linalg.norm(target[bb]-target[aa])*r['scale']/400/c)
            lr[si]['actualNewPhysicalErrorRatio']=lr[si]['actualNewEquivalentMeters']/lr[si]['physicalTargetMeters']-1
    if return_details:report['changedMask']=Image.fromarray(changed.astype('uint8')*255).crop(bounds)
    return out.crop(bounds),report

def review_canvas(im,r):
    s=r['scale'];ox,oy=r['origin'];tx=256-ox*s;ty=712-oy*s
    return im.convert('RGBa').transform((512,768),Image.Transform.AFFINE,(1/s,0,-tx/s,0,1/s,-ty/s),Image.Resampling.BICUBIC).convert('RGBA')

def input_records(paths):
    edits={}
    for filename in paths:
        filename=Path(filename);data=json.loads(filename.read_text(encoding='utf-8-sig'));rows=data.get('edits',[]) if isinstance(data,dict) else data
        for row in rows:
            row=copy.deepcopy(row);row['_path']=(filename.parent/row['cropPath']).resolve();edits[(row['image'],row['index'])]=row
    result=[]
    for r0 in FRAMES.values():
        r=copy.deepcopy(r0);key=(r['image'],r['index']);edit=edits.get(key)
        if edit:
            r['_inputEdit']=edit;r['origin']=edit['origin'];oldfactor=M['frameScaleFactors'][r['image'].removesuffix('.png')][r['index']]
            r['scale']*=edit.get('newFactor',oldfactor)/oldfactor
            r['_staticMaster']='static-' in str(edit['_path'].name) or '/static/' in edit['_path'].as_posix()
        result.append(r)
    return result

def infer_missing_poses():
    """Reuse matching, already existing motion poses via local alpha alignment.

    No pose model is run. These estimates remain explicitly marked and get a
    separate review sheet; an image match is not independent anatomical truth.
    """
    missing=[r for r in FRAMES.values() if not POSE.get((r['image'],r['index']),{}).get('landmarks')]
    folder=HERE/'legs-pilot';folder.mkdir(exist_ok=True);results=[]
    board=Image.new('RGB',(1000,((len(missing)+4)//5)*230),'#34383b');draw=ImageDraw.Draw(board)
    anchor=np.array([512.,800.]);size=(1024,900);quarter=(256,225)
    def alpha_view(r):
        im=original(r);s=r['scale'];tx=anchor[0]-r['origin'][0]*s;ty=anchor[1]-r['origin'][1]*s
        return im.getchannel('A').transform(size,Image.Transform.AFFINE,(1/s,0,-tx/s,0,1/s,-ty/s),Image.Resampling.BICUBIC).resize(quarter,Image.Resampling.BILINEAR)
    for ordinal,r in enumerate(missing):
        refs=r['refs'];v=refs[0];a=v['action'];phase=v['phase'];direction=r['direction']
        action='death' if 'death' in a else 'explore_walk_W01' if 'walk' in a else 'explore_run_W01'
        candidates=[action]
        if 'run' in a:candidates+=['explore_run_L02','explore_run_L01','explore_run_W02']
        donor=None
        for candidate in candidates:
            try:d=prepare.find(FRAMES,candidate,direction,phase)
            except StopIteration:continue
            if POSE.get((d['image'],d['index']),{}).get('landmarks'):donor=d;break
        if donor is None:continue
        dj,dc=joints(donor);world=anchor+(dj-np.array(donor['origin']))*donor['scale']
        src=np.asarray(alpha_view(r))>100;ref=alpha_view(donor)
        leg=world[23:33];lo=(leg.min(0)-[65,35])/4;hi=(leg.max(0)+[65,35])/4
        yy,xx=np.mgrid[:quarter[1],:quarter[0]];roi=(xx>=lo[0])&(xx<=hi[0])&(yy>=lo[1])&(yy<=hi[1])
        source=src&roi;best=None
        for scale in np.arange(.86,1.141,.02):
            center=anchor/4
            moved=ref.transform(quarter,Image.Transform.AFFINE,(1/scale,0,center[0]-center[0]/scale,0,1/scale,center[1]-center[1]/scale),Image.Resampling.BILINEAR)
            target=(np.asarray(moved)>100)&roi
            corr=fftconvolve(source.astype(float),target[::-1,::-1].astype(float),mode='same')
            cy,cx=np.array(corr.shape)//2;window=corr[cy-12:cy+13,cx-12:cx+13];wy,wx=np.unravel_index(window.argmax(),window.shape);dy=wy-12;dx=wx-12
            intersection=float(window[wy,wx]);union=float(source.sum()+target.sum()-intersection);score=intersection/max(union,1)
            if best is None or score>best[0]:best=(score,float(scale),np.array([dx,dy])*4)
        score,scale,translation=best;transferred=anchor+scale*(world-anchor)+translation
        dp=copy.deepcopy(POSE[(donor['image'],donor['index'])]);old=OLD[(r['image'],r['index'])]
        for i,lm in enumerate(dp['landmarks']):
            xy=np.array(old['origin'])+(transferred[i]-anchor)/r['scale'];lm['x']=float(xy[0]);lm['y']=float(xy[1]);lm['visibility']=float(min(lm.get('visibility',1),.75));lm['presence']=float(min(lm.get('presence',1),.75))
        dp.update(image=r['image'],index=r['index'],inferredLocally=True,inference={'donorImage':donor['image'],'donorIndex':donor['index'],'donorAction':action,'direction':direction,'phase':phase,'method':'same-phase/same-direction existing pose; coarse local alpha similarity scale/translation fit','legRegionAlphaIoU':score,'worldScaleFit':scale,'worldTranslation':translation.tolist(),'artReview':'pending review of overlaid joints'})
        results.append(dp);POSE[(r['image'],r['index'])]=dp
        im=prepare.canvas(r,{r['image']:SHEETS[r['image']]});d=ImageDraw.Draw(im)
        review=transferred-anchor+np.array([256,712])
        for aa,bb in [(23,25),(24,26),(25,27),(26,28),(27,31),(28,32)]:d.line([tuple(review[aa]),tuple(review[bb])],fill='#42e8c4',width=3)
        thumb=im.resize((140,210),Image.Resampling.LANCZOS);x=(ordinal%5)*200;y=(ordinal//5)*230;board.paste(thumb,(x+30,y+20),thumb);draw.text((x+2,y+2),f'{a} {direction} p{phase}',fill='white');draw.text((x+2,y+214),f'alpha IoU {score:.2f} / scale {scale:.2f}',fill='white')
        print('Inferred existing pose',ordinal+1,'/',len(missing),a,direction,phase,round(score,3),flush=True)
    INFERRED_PATH.write_text(json.dumps({'status':'local same-pose estimates; art review required','newModelInference':False,'frames':results},indent=2))
    board.save(folder/'inferred-poses-review.jpg',quality=92)
    print({'missingPoses':len(missing),'samePoseLocalEstimates':len(results)},flush=True)

def input_image(r):
    return Image.open(r['_inputEdit']['_path']).convert('RGBA') if '_inputEdit' in r else original(r)

def driver(r):
    if not r.get('_staticMaster'):return None
    # The new idle body/legs are literal attack phase0 pixels in world space.
    # Retain the old idle gripping-arm positions after its torso warp so hand
    # protection still follows the real lowered hand rather than attack hand.
    original_record=FRAMES[(r['image'],r['index'])];oj,oc=joints(original_record)
    cr=prepare.find(FRAMES,'attack_sword_W01',r['direction'],0);cj,cc=joints(cr)
    ow=np.array([256,712])+(oj-np.array(original_record['origin']))*original_record['scale']
    cw=np.array([256,712])+(cj-np.array(cr['origin']))*cr['scale']
    s=ow[[11,12]].mean(0);h=ow[[23,24]].mean(0);cs=cw[[11,12]].mean(0);ch=cw[[23,24]].mean(0)
    dst=np.array([0,cs[1],ch[1],712,768.]);src=np.array([s[1]-cs[1],s[1],h[1],712,768.])
    q=ow.copy();q[:,1]=np.interp(ow[:,1],src,dst)
    q[:,0]+=np.interp(q[:,1],[0,cs[1],ch[1],712,768],[cs[0]-s[0],cs[0]-s[0],ch[0]-h[0],0,0])
    q[23:33]=cw[23:33];oc[23:33]=cc[23:33]
    return np.array(r['origin'])+(q-np.array([256,712]))/r['scale'],oc

def smooth_parameters(records):
    parents={r['image']:r['image'] for r in FRAMES.values()}
    def root(x):
        while parents[x]!=x:x=parents[x]
        return x
    for a in M['actions'].values():
        names=a.get('frameImages',[a['image']]);rr=root(names[0])
        for name in names:parents[root(name)]=rr
    groups=defaultdict(list);raw=[]
    for ordinal,r in enumerate(records):
        over=driver(r);j,c=over if over else joints(r)
        if j is None:continue
        im=input_image(r);tw=widths(im,j,c,r['scale']);ref,rj,rc,rw=reference(r['direction'])
        p=POSE[(ref['image'],ref['index'])] if over else None
        desired,lr=limb_targets(r,j,c,p);rat=[]
        for si,(t,canon) in enumerate(zip(tw,rw)):
            wanted=canon['median']
            if r['direction'] in ('left','right'):wanted=profile_owned_width(j,si,r['scale'])
            v=wanted/t['median'] if wanted and t['median'] and t['confidence']>.65 else None
            rat.append(float(np.clip(v,.90,1.20)) if v is not None else None)
        family='static-accepted-master' if r.get('_staticMaster') else root(r['image'])
        phase=min(v['phase'] for v in r['refs']);key=(family,r['direction']);row=dict(record=r,phase=phase,length=[v['factor'] if v['reliable'] else None for v in lr],width=rat,cuffs=[tw[i].get('bootStart') for i in (2,3)])
        groups[key].append(row)
        if (ordinal+1)%100==0:print('Measured leg proposals',ordinal+1,'/',len(records),flush=True)
    summaries=[]
    for key,rows in groups.items():
        rows.sort(key=lambda v:(v['phase'],v['record']['image'],v['record']['index']))
        loop=any(any('walk' in a['action'] or 'run' in a['action'] for a in row['record']['refs']) for row in rows)
        values={}
        for attr,columns,bounds in [('length',4,(.85,1.20)),('width',4,(.90,1.20)),('cuffs',2,(.38,.92))]:
            matrix=[]
            for col in range(columns):
                valid=[row[attr][col] for row in rows if row[attr][col] is not None]
                median=float(np.median(valid)) if valid else (1. if attr!='cuffs' else .70)
                v=np.array([row[attr][col] if row[attr][col] is not None else median for row in rows])
                if attr=='cuffs':v=np.full(len(rows),median)
                elif loop:
                    smoothed=ndi.gaussian_filter1d(np.log(v),.85,mode='wrap')
                    v=np.clip(np.exp(.7*np.log(median)+.3*smoothed),median*.98,median*1.02)
                else:v=np.full(len(rows),median)
                matrix.append(np.clip(v,*bounds))
            values[attr]=np.array(matrix).T
        for i,row in enumerate(rows):
            r=row['record'];PARAMS[(r['image'],r['index'])]=dict(family=key[0],direction=key[1],lengthFactors=values['length'][i].tolist(),widthFactors=values['width'][i].tolist(),targetCuffs=values['cuffs'][i].tolist(),rawLength=row['length'],rawWidth=row['width'],loop=loop,method='stable family median + 30% Gaussian-smoothed residual bounded to ±2%; cuffs use family median')
        summaries.append(dict(family=key[0],direction=key[1],frames=len(rows),loop=loop))
    return summaries

def batch(records,args,merge=False):
    out=HERE/'edits/legs';out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
    summaries=smooth_parameters(records);reports=[];edits=[]
    inventory_order={key:i for i,key in enumerate(FRAMES)}
    def work(pair):
        _,r=pair;ordinal=inventory_order[(r['image'],r['index'])];im=input_image(r);over=driver(r);after,report=correct(im,r,joint_override=over)
        filename=f'frames/leg-{ordinal:04d}.png';after.save(out/filename)
        edit=dict(image=r['image'],index=r['index'],cropPath=filename,origin=report.get('origin',r['origin']))
        if '_inputEdit' in r and 'newFactor' in r['_inputEdit']:edit['newFactor']=r['_inputEdit']['newFactor']
        report.update(image=r['image'],index=r['index'],direction=r['direction'],actions=r['refs'],inputCostumeEdit='_inputEdit' in r,staticAcceptedMaster=r.get('_staticMaster',False),inputOrigin=r['origin'],inputScale=r['scale'],inputCropPath=str(r['_inputEdit']['_path']) if '_inputEdit' in r else None,inferredPose=POSE.get((r['image'],r['index']),{}).get('inferredLocally',False),output=filename)
        (out/'frames'/f'leg-{ordinal:04d}.report.json').write_text(json.dumps({'edit':edit,'report':report},indent=2))
        return ordinal,edit,report
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending=[pool.submit(work,pair) for pair in enumerate(records)]
        for future in as_completed(pending):
            ordinal,e,report=future.result();edits.append((ordinal,e));reports.append((ordinal,report))
            if len(reports)%40==0:print('Prepared leg candidates',len(reports),'/',len(records),flush=True)
    edits=[v for _,v in sorted(edits)];reports=[v for _,v in sorted(reports)]
    if merge:
        # Incremental filenames must not reuse unrelated existing frame paths.
        # The worker receives original inventory ordinals below, so the same
        # physical frame always addresses the same deterministic output file.
        prior=json.loads((HERE/'legs-report.json').read_text());prior_edits=json.loads((out/'edits.json').read_text())
        bykey={(r['image'],r['index']):r for r in prior['frames']};ebykey={(r['image'],r['index']):r for r in prior_edits}
        bykey.update({(r['image'],r['index']):r for r in reports});ebykey.update({(r['image'],r['index']):r for r in edits})
        ordered=list(FRAMES);reports=[bykey[k] for k in ordered if k in bykey];edits=[ebykey[k] for k in ordered if k in ebykey]
        summaries=prior.get('families',[])+summaries
    input_map={(r['image'],r['index']):r for r in input_records(args.input_edits)}
    for row in reports:
        r=input_map[(row['image'],row['index'])]
        row.setdefault('inputOrigin',r['origin']);row.setdefault('inputScale',r['scale']);row.setdefault('inputCropPath',str(r['_inputEdit']['_path']) if '_inputEdit' in r else None)
        row['inferredPose']=POSE.get((r['image'],r['index']),{}).get('inferredLocally',False)
    (out/'edits.json').write_text(json.dumps(edits,indent=2))
    manual=[dict(image=r['image'],index=r['index'],direction=r['direction'],reason=r['status'],unreliableBones=r.get('unreliableBones')) for r in reports if r.get('requiresManualReview')]
    metrics=[]
    for row in reports:
        for bone in row.get('lengthCalibration',[]):
            if bone['reliable'] and 'actualNewEquivalentMeters' in bone:metrics.append((abs(bone['oldEquivalentMeters']/bone['physicalTargetMeters']-1),abs(bone['actualNewPhysicalErrorRatio'])))
    metrics=np.array(metrics)
    summary=dict(method='Projection-corrected original pose estimator; AFTER uses actual continuous-mesh mapped joint coordinates, not the old hard-segment proposal.',reliableBoneSamples=len(metrics),medianAbsolutePhysicalErrorBefore=float(np.median(metrics[:,0])) if len(metrics) else None,medianAbsolutePhysicalErrorAfter=float(np.median(metrics[:,1])) if len(metrics) else None,p90AbsolutePhysicalErrorBefore=float(np.percentile(metrics[:,0],90)) if len(metrics) else None,p90AbsolutePhysicalErrorAfter=float(np.percentile(metrics[:,1],90)) if len(metrics) else None,widthLowerBoundHits=sum(sum(abs(v-.90)<1e-4 for v in r.get('widthFactors',[])) for r in reports),widthUpperBoundHits=sum(sum(abs(v-1.20)<1e-4 for v in r.get('widthFactors',[])) for r in reports),measurementCaveat='Same estimator, not independent anatomical truth; bounded width factors preserve silhouettes and do not guarantee identical world widths under occlusion.')
    amplitudes=defaultdict(int)
    for row in reports:amplitudes[str(row.get('warp',{}).get('correctionAmplitude','none'))]+=1
    mesh_summary=dict(revision=REVISION,amplitudeDistribution=dict(amplitudes),minimumJacobian=min((r.get('warp',{}).get('minJacobian',1) for r in reports),default=1),maximumJacobian=max((r.get('warp',{}).get('maxJacobian',1) for r in reports),default=1),foldedTriangles=sum(r.get('warp',{}).get('foldedTriangles',0) for r in reports),rigidForegroundDeltaMatchesContactPins=True,actualRigidDeltaIncludesMeshRetraction=True,sourceScriptSHA256=prepare.digest(__file__))
    report=dict(revision=REVISION,status='candidate-only; art review required before installation',physicalFrames=len(reports),inputCostumeFrames=sum(r.get('inputCostumeEdit',False) for r in reports),sharedPhysicalBonesMeters={'thigh':.354,'shin':.373},continuousMesh=mesh_summary,measurementSummary=summary,families=summaries,frames=reports,manualReview=manual,sourceManifestSHA256=prepare.digest(prepare.MANIFEST),workers=args.workers)
    (HERE/'legs-report.json').write_text(json.dumps(report,indent=2))
    print({'frames':len(records),'inputCostumeFrames':report['inputCostumeFrames'],'manualReview':len(manual),'noPose':sum(r['status']=='preserved-no-pose' for r in reports)},flush=True)

def reviews():
    report=json.loads((HERE/'legs-report.json').read_text());folder=HERE/'legs-pilot/outliers';folder.mkdir(exist_ok=True)
    rows=report['frames'];criteria={};ranking=[]
    for row in rows:
        errors=[abs(v.get('actualNewPhysicalErrorRatio',0)) for v in row.get('lengthCalibration',[]) if v.get('reliable')]
        worst=max(errors,default=0);delta=float(np.linalg.norm(row.get('upperBodyTranslationWorldPixels',[0,0])))
        reasons=[]
        if row.get('requiresManualReview'):reasons.append('manual')
        if row.get('inferredPose'):reasons.append('same-pose estimate')
        if row.get('unreliableBones',0):reasons.append('low bone confidence')
        if any(v.get('reachabilityClamped') for v in row.get('ik',[])):reasons.append('IK limited')
        if any(v.get('clamped') for v in row.get('lengthCalibration',[])):reasons.append('length bounded')
        if worst>.10:reasons.append('residual>10%')
        criteria[(row['image'],row['index'])]=dict(reasons=reasons,worst=worst,delta=delta)
        ranking.append((worst*350+delta+(80 if row.get('inferredPose') else 0)+(20 if row.get('unreliableBones',0) else 0),row))
    selected={}
    for _,row in ranking:
        c=criteria[(row['image'],row['index'])]
        if c['reasons']:selected[(row['image'],row['index'])]=row
    for _,row in sorted(ranking,key=lambda v:v[0],reverse=True)[:48]:selected[(row['image'],row['index'])]=row
    order=[row for _,row in sorted(ranking,key=lambda v:v[0],reverse=True) if (row['image'],row['index']) in selected]
    index=[]
    for page in range((len(order)+11)//12):
        board=Image.new('RGB',(1120,1500),'#34383b');draw=ImageDraw.Draw(board)
        for cell,row in enumerate(order[page*12:(page+1)*12]):
            r=FRAMES[(row['image'],row['index'])];before=Image.open(row['inputCropPath']).convert('RGBA') if row.get('inputCropPath') else original(r)
            origin=row.get('inputOrigin',r['origin']);scale=row.get('inputScale',r['scale']);after=Image.open(HERE/'edits/legs'/row['output']).convert('RGBA')
            x=(cell%2)*560;y=(cell//2)*250
            for off,im,o in [(0,before,origin),(280,after,row.get('origin',origin))]:
                # One fixed 400px/world canvas, no per-pose bbox fitting. This
                # includes the complete horizontal death silhouette.
                tx=700-o[0]*scale;ty=850-o[1]*scale
                full=im.convert('RGBa').transform((1400,1000),Image.Transform.AFFINE,(1/scale,0,-tx/scale,0,1/scale,-ty/scale),Image.Resampling.BICUBIC).convert('RGBA')
                thumb=full.resize((280,200),Image.Resampling.LANCZOS);board.paste(thumb,(x+off,y+25),thumb)
            c=criteria[(row['image'],row['index'])];label=f'{row["image"].split("/")[-1]} #{row["index"]} {row["direction"]}'
            draw.text((x+3,y+1),label[:73],fill='white');draw.text((x+3,y+226),f'error {c["worst"]:.1%}; hip delta {c["delta"]:.1f}px; '+', '.join(c['reasons'])[:51],fill='#f1c98d')
            index.append(dict(page=page,cell=cell,image=row['image'],frameIndex=row['index'],**c))
        board.save(folder/f'exceptions-{page:02d}.jpg',quality=92)
    categories=dict(physicalFrames=len(rows),requiresManualReview=sum(r.get('requiresManualReview',False) for r in rows),inferredPose=sum(r.get('inferredPose',False) for r in rows),noPose=sum(r['status']=='preserved-no-pose' for r in rows),lowConfidenceFrames=sum(r.get('unreliableBones',0)>0 for r in rows),ikLimitedFrames=sum(any(v.get('reachabilityClamped') for v in r.get('ik',[])) for r in rows),lengthBoundedFrames=sum(any(v.get('clamped') for v in r.get('lengthCalibration',[])) for r in rows),reviewFrames=len(order),pages=(len(order)+11)//12,measurementSummary=report.get('measurementSummary'))
    (folder/'index.json').write_text(json.dumps({'summary':categories,'frames':index},indent=2));print(json.dumps(categories),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',action='store_true');p.add_argument('--reviews',action='store_true');p.add_argument('--update-only',action='store_true');p.add_argument('--refresh-held',action='store_true');p.add_argument('--refresh-profile',action='store_true');p.add_argument('--refresh-special',action='store_true');p.add_argument('--infer-missing',action='store_true');p.add_argument('--input-edits',action='append',default=[]);p.add_argument('--workers',type=int,default=3);args=p.parse_args()
    if args.infer_missing:return infer_missing_poses()
    if args.reviews:return reviews()
    if args.batch or args.update_only or args.refresh_held or args.refresh_profile or args.refresh_special:
        rows=input_records(args.input_edits)
        if args.update_only:rows=[r for r in rows if '_inputEdit' in r]
        if args.refresh_held or args.refresh_profile or args.refresh_special:rows=[r for r in rows if r.get('_staticMaster') or (args.refresh_profile and r['direction'] in ('left','right')) or (args.refresh_held and any(not v['action'].startswith('explore_') and v['action'].split('_')[0] in ('idle','walk','run') for v in r['refs'])) or (args.refresh_special and any(any(word in v['action'] for word in ('death','hit','dodge')) for v in r['refs']))]
        return batch(rows,args,merge=args.update_only or args.refresh_held or args.refresh_profile or args.refresh_special)
    out=HERE/'legs-pilot';out.mkdir(exist_ok=True);(out/'frames').mkdir(exist_ok=True)
    choices=[('explore_idle_W01',0),('walk_W01',1),('explore_run_W01',4),('spell',0),('dodge',1)]
    board=Image.new('RGB',(1000,4*230),'#34383b');draw=ImageDraw.Draw(board);reports=[]
    for col,(action,phase) in enumerate(choices):
        for row,d in enumerate(prepare.DIRECTIONS):
            r=prepare.find(FRAMES,action,d,phase);im=original(r);after,report=correct(im,r,True);mask=report.pop('changedMask',None)
            name=f'{action}-{d}-{phase}';after.save(out/'frames'/f'{name}.png')
            if mask:mask.save(out/'frames'/f'{name}-changed.png')
            report.update(action=action,direction=d,image=r['image'],index=r['index'],nativeCropPath=f'frames/{name}.png');reports.append(report)
            for off,img in [(0,im),(100,after)]:
                rr=copy.deepcopy(r)
                if off:rr['origin']=report.get('origin',r['origin'])
                thumb=review_canvas(img,rr).resize((100,150),Image.Resampling.LANCZOS);board.paste(thumb,(col*200+off,row*230+35),thumb)
            draw.text((col*200+2,row*230+2),f'{action} {d}',fill='white')
            draw.text((col*200+2,row*230+17),'before            after',fill='#b0b6b8')
            draw.text((col*200+2,row*230+190),' / '.join(f'{x:.2f}' for x in report['widthFactors']),fill='#b0b6b8')
    board.save(out/'comparison.jpg',quality=92)
    (out/'report.json').write_text(json.dumps({'status':'unreviewed pilot; no official installation','frames':reports},indent=2))
    print({'frames':len(reports),'changedPixels':sum(r['changedPixels'] for r in reports),'skeletalLengthChanges':True})

if __name__=='__main__':main()


