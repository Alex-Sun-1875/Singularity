"""One reviewed body cycle, separate existing weapon cutouts and pose sockets.

Reuses the project's physical-frame inventory, palette adapter, gear extraction,
Pillow/SciPy transforms and native shelf packer. No new inference/dependencies.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('existing_locomotion_pixels', HERE/'repair.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
M, FRAMES, ACTOR = base.M, base.FRAMES, base.ACTOR
STAGE = HERE/'shared-candidate'
DIRECTIONS = M['directions']
WEAPONS = ['W01','W02','L01','W07','W08','L02','W11']
OLD_DIR = HERE.parent/'body-scale-v4'
OLD = {(r['image'],r['index']):r for r in json.loads((OLD_DIR/'inventory.json').read_text())['frames']}
POSE = {(r['image'],r['index']):r for r in json.loads((OLD_DIR/'pose-landmarks.json').read_text())['frames']}
inferred = HERE.parent/'attack-identity-v5/legs-pilot/inferred-poses.json'
if inferred.exists():
    for r in json.loads(inferred.read_text())['frames']:
        POSE[r['image'],r['index']] = r
DELTA = {}
for path in (HERE.parent/'attack-identity-v5/edits/legs/frames').glob('*.report.json'):
    report = json.loads(path.read_text())
    edit, details = report['edit'], report['report']
    DELTA[edit['image'],edit['index']] = np.asarray(details.get('upperBodyTranslationWorldPixels',[0,0]))
X, Y = base.X, base.Y
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
REFERENCE_TORSO={
    'down':np.asarray([[256,215],[256,383]],float),
    'right':np.asarray([[251,207],[255,385]],float),
    'up':np.asarray([[254,218],[256,384]],float),
    'left':np.asarray([[263,208],[255,385]],float),
}
REFERENCE_HILT={'down':[197,135],'right':[200,140],'up':[307,133],'left':[309,141]}


def write_json(path, data):
    base.write_json(path, data)


def joints(record):
    key = record['image'],record['index']
    old, pose = OLD[key], POSE[key]
    points = np.asarray([[p['x'],p['y']] for p in pose['landmarks']],float)
    return (points-np.asarray(old['origin']))*record['scale']+[256,712]+DELTA.get(key,[0,0])


def nearest_hand(image, estimated):
    a = np.asarray(image)
    r,g,b = np.moveaxis(a[...,:3].astype(float),-1,0)
    near = (X-estimated[0])**2+(Y-estimated[1])**2 < 36**2
    flesh = (a[...,3]>180)&(r>105)&(g/r.clip(1)>.58)&(g/r.clip(1)<.88)&(b/r.clip(1)>.40)&(b/r.clip(1)<.78)&(r>g+12)&(g>b+7)&near
    labels,_ = ndi.label(flesh)
    choices=[]
    for i,bounds in enumerate(ndi.find_objects(labels),1):
        if bounds is None:continue
        ys,xs=np.where(labels==i)
        if len(xs)<25:continue
        center=np.asarray([np.median(xs),np.median(ys)])
        choices.append((np.linalg.norm(center-estimated),center))
    return min(choices,key=lambda v:v[0])[1] if choices else estimated


def affine(source, target):
    matrix=np.linalg.lstsq(np.column_stack([source,np.ones(len(source))]),target,rcond=None)[0].T
    return np.vstack([matrix,[0,0,1]])


def torso(points):
    return np.asarray([points[11],points[12],points[[23,24]].mean(0)])


def similarity(source,target):
    u,v=source[0]-source[1],target[0]-target[1]
    angle=math.atan2(v[1],v[0])-math.atan2(u[1],u[0])
    c,s=math.cos(angle),math.sin(angle)
    scale=np.linalg.norm(v)/np.linalg.norm(u)
    rotation=scale*np.asarray([[c,-s],[s,c]])
    translation=target[1]-rotation@source[1]
    return np.vstack([np.column_stack([rotation,translation]),[0,0,1]])


def reference_grip(reference,gear_image):
    a=np.asarray(reference);r,g,b=np.moveaxis(a[...,:3].astype(float),-1,0)
    skin=(a[...,3]>128)&(Y>310)&(Y<540)&(r>115)&(r>g+15)&(g>b+7)&(g/r.clip(1)>.58)&(b/r.clip(1)>.44)&(b/r.clip(1)<.78)
    labels,_=ndi.label(ndi.binary_closing(skin,iterations=1))
    gear=np.asarray(gear_image)[...,3]>32
    distance=ndi.distance_transform_edt(~gear)
    choices=[]
    for i,bounds in enumerate(ndi.find_objects(labels),1):
        if bounds is None:continue
        ys,xs=np.where(labels==i)
        if len(xs)<80 or len(xs)>5000:continue
        center=np.asarray([np.median(xs),np.median(ys)])
        choices.append((np.percentile(distance[ys,xs],20),center))
    if not choices:raise ValueError('No reviewed standing grip candidate')
    center=min(choices,key=lambda v:v[0])[1]
    ys,xs=np.where(gear);i=((xs-center[0])**2+(ys-center[1])**2).argmin()
    return np.asarray([xs[i],ys[i]],float)


def held_geometry(weapon,direction,image):
    gear=base.gear
    if weapon in ['W01','W02','L01']:return gear.sword_geometry(weapon,direction)
    if weapon=='W11':return gear.polygon(gear.STAFF_HEAD[direction])|gear.polygon(gear.STAFF_SHAFT[direction])
    if weapon=='W07':return gear.line(gear.SIMPLE_BOW[direction],6.5)|gear.line(gear.SIMPLE_STRING[direction],2)
    if weapon=='W08':
        mask=gear.line(gear.ORNATE_MAIN[direction],13)|gear.line(gear.ORNATE_LOWER[direction],12)
        for points in gear.ORNATE_TIPS[direction]:mask|=gear.line(points,3.5)
        orb,handle,string=gear.ORNATE_GRIP[direction]
        return mask|gear.circle(orb,14)|gear.line(handle,5.5)|gear.line(string,2)
    mask=gear.line(gear.MOON_UPPER[direction],11)|gear.line(gear.MOON_LOWER[direction],11)
    for ordinal,(point,radius) in enumerate(gear.MOON_CIRCLES[direction]):
        ring=gear.circle(point,radius+3)&~gear.circle(point,radius-5)
        if direction=='left':ring[:,:327 if ordinal==0 else 315]=False
        mask|=ring
    orb,handle,string=gear.MOON_GRIPS[direction]
    mask|=gear.circle(orb,21)|gear.line(handle,7)|gear.line(string,2.5)
    mask|=gear.circle(orb,62)&(np.asarray(image)[...,3]<240)
    return mask


def erase_carried_weapon(image, record):
    idle, idle_record = base.world('explore_idle_W01',record['direction'])
    target_points=joints(record)
    target_torso=np.asarray([target_points[[11,12]].mean(0),target_points[[23,24]].mean(0)])
    transform=similarity(REFERENCE_TORSO[record['direction']],target_torso)
    inverse=np.linalg.inv(transform)
    reference_gear=Image.open(HERE.parent/'attack-identity-v5/edits/static-gear-validation'/f'explore-W01-{record["direction"]}-gear.png').convert('RGBA')
    raw=reference_gear.getchannel('A')
    mask=np.asarray(raw.transform((512,768),Image.Transform.AFFINE,tuple(inverse[:2].ravel()),Image.Resampling.BILINEAR))>40
    a=np.asarray(image).copy()
    hair,_=base.appearance.hair(image,record)
    hx0,hy0,hx1,hy1=hair['box']
    # Protect the real head/neck and hands even where a hilt crosses their ROI.
    r,g,b=np.moveaxis(a[...,:3].astype(float),-1,0)
    expected=(transform@np.asarray([*REFERENCE_HILT[record['direction']],1]))[:2]
    gold=(r>130)&(r>g+12)&(g>b+15)&(a[...,3]>100)&(Y<260)&(Y>30)
    labels,_=ndi.label(gold);choices=[]
    for i,bounds in enumerate(ndi.find_objects(labels),1):
        if bounds is None:continue
        ys,xs=np.where(labels==i)
        if len(xs)<20 or len(xs)>900:continue
        center=np.asarray([np.mean(xs),np.mean(ys)])
        if np.linalg.norm(center-expected)<65:choices.append((np.linalg.norm(center-expected),center))
    if choices:
        center=min(choices,key=lambda v:v[0])[1]
        shift=center-expected
        mask=np.asarray(base.translated(Image.fromarray(mask.astype('uint8')*255).convert('RGBA'),*shift))[...,0]>80
        hilt=center
    else:
        hilt=expected
    mask=ndi.binary_dilation(mask,iterations=10)
    hip=target_points[[23,24]].mean(0)
    end_offset={'down':[-75,85],'right':[-65,35],'up':[-85,75],'left':[65,35]}[record['direction']]
    end=hip+end_offset
    line=Image.new('L',(512,768));draw=ImageDraw.Draw(line)
    draw.line([tuple(hilt),tuple(end)],fill=255,width=32)
    draw.ellipse((hilt[0]-18,hilt[1]-18,hilt[0]+18,hilt[1]+18),fill=255)
    mask|=np.asarray(line)>0
    face=(X>hx0-15)&(X<hx1+24)&(Y>hy0-5)&(Y<hy1+50)&(a[...,3]>64)
    neutral=(np.max(a[...,:3],axis=-1).astype(float)-np.min(a[...,:3],axis=-1)<35)
    skin=(r>g+12)&(g>b+5)&(r>115)&(b/r.clip(1)>.40)
    mask &= ~(face&(neutral|skin))
    for indices in [[15,19],[16,20]]:
        hand=target_points[indices].mean(0)
        near=(X-hand[0])**2+(Y-hand[1])**2<38**2
        mask&=~(near&(skin|((r>135)&neutral)))
    support=ndi.binary_closing(ndi.binary_opening(a[...,3]>32,iterations=9),iterations=3)
    labels,_=ndi.label(support);counts=np.bincount(labels.ravel());counts[0]=0
    support=labels==counts.argmax()
    master=Image.open(HERE.parent/'attack-identity-v5/masters'/f'neutral-{record["direction"]}.png').convert('RGBA')
    patch=master.convert('RGBa').transform(image.size,Image.Transform.AFFINE,tuple(inverse[:2].ravel()),Image.Resampling.BICUBIC).convert('RGBA')
    patch=np.asarray(patch)
    valid=(~mask)&support&(a[...,3]>64)
    indices=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
    recovered=a[indices[0],indices[1]].copy()
    use_reference=patch[...,3]>160
    recovered[use_reference,:3]=patch[use_reference,:3]
    a[mask]=patch[mask]
    components,_=ndi.label(a[...,3]>=16);sizes=np.bincount(components.ravel());small=sizes<300;small[0]=False
    a[small[components]]=0
    return Image.fromarray(a),int(mask.sum())


def body(action,direction,phase,positions):
    original,record=base.world(action,direction,phase)
    image,removed=erase_carried_weapon(original,record)
    if 'walk' in action and direction=='up':
        repaired,_=base.back_walk_candidate(phase)
        before,after=np.asarray(image).copy(),np.asarray(repaired)
        before[Y>=573]=after[Y>=573]
        image=Image.fromarray(before)
    head=np.asarray(positions[phase])
    idle,_=base.world('explore_idle_W01',direction)
    target=np.asarray(base.appearance.hair(idle)[0]['center']) if 'walk' in action else np.median(positions,axis=0)
    bob=([0,-1,0,-1] if 'walk' in action else [2,0,-2,0,2,0,-2,0])[phase]
    dy=round(target[1]+bob-head[1])
    # A rigid head/shoulder translation blends to zero ABOVE the hips. The
    # complete original legs, ankles, boot silhouettes and ground/flight are pinned.
    weight=1-np.clip((Y-218)/202,0,1)**2*(3-2*np.clip((Y-218)/202,0,1))
    map_y=Y-dy*weight
    a=np.asarray(image.convert('RGBa'))
    moved=np.stack([ndi.map_coordinates(a[...,ch],[map_y,X],order=1,mode='constant',cval=0,prefilter=False) for ch in range(4)],axis=-1)
    image=Image.fromarray(moved.astype('uint8'),'RGBa').convert('RGBA')
    transformed_info=dict(box=[head[0]-45,head[1]+dy-30,head[0]+45,head[1]+dy+30],center=[head[0],head[1]+dy])
    image,grading=base.appearance.grade(image,idle,info=transformed_info)
    origin=[256+float(head[0]-target[0]),712]
    points=joints(record)
    # Exact inversion of the same monotonic vertical sample map for sockets.
    points[:,1]=np.interp(points[:,1],map_y[:,0],np.arange(768))
    hand=nearest_hand(image,points[[16,20]].mean(0))
    back=points[[11,12]].mean(0)
    lean=math.degrees(math.atan2((back-points[[23,24]].mean(0))[0],-(back-points[[23,24]].mean(0))[1]))
    anchors={kind:dict(x=float((point[0]-origin[0])/400),y=float((origin[1]-point[1])/400),angle=float(np.clip(-lean,-18,18)))
             for kind,point in [('held',hand),('stowed',back)]}
    hands=[nearest_hand(image,points[indices].mean(0)).tolist() for indices in [[16,20],[15,19]]]
    return image,origin,anchors,dict(removedWeaponMaskPixels=removed,headBefore=head.tolist(),headTarget=target.tolist(),headDy=dy,grade=grading,hands=hands)


def native_item(image,origin,index):
    im=image.convert('RGBa').resize((320,480),Image.Resampling.LANCZOS).convert('RGBA')
    bounds=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
    bounds=[max(0,bounds[0]-2),max(0,bounds[1]-2),min(320,bounds[2]+2),min(480,bounds[3]+2)]
    crop=im.crop(bounds)
    return dict(record=dict(index=index),crop=crop,origin=[origin[0]*.625-bounds[0],origin[1]*.625-bounds[1]])


def pack(name,items):
    positions,size,_=base.packer.shelf_placements(items)
    im=Image.new('RGBA',size)
    geometry={}
    for item in items:
        index=item['record']['index'];rect=positions[index]
        im.paste(item['crop'],rect[:2])
        geometry[index]=dict(rect=rect,origin=item['origin'],bounds=base.packer.alpha_bounds(item['crop']))
    path=STAGE/name;path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    return geometry


def write_meta(path):
    template=ACTOR/'locomotion-v2/W01-explore-run-a.png.meta'
    meta=json.loads(template.read_text('utf-8'))
    old_id=meta['uuid'];new_id=str(uuid.uuid4())
    text=json.dumps(meta,ensure_ascii=False).replace(old_id,new_id).replace('W01-explore-run-a',path.stem)
    path.with_suffix(path.suffix+'.meta').write_text(text+'\n',encoding='utf-8')


def prepare_shared():
    if M.get('movementEquipment'):
        raise ValueError('Shared locomotion is already installed; do not reprocess installed body frames.')
    updated=copy.deepcopy(M);bodies={};files=[];metrics=[];hand_items={'walk':[],'run':[]}
    for state,count in [('walk',4),('run',8)]:
        action='explore_'+state+'_W01'
        pages={page:[] for page in range((count+3)//4)}
        info={};anchors={kind:{direction:[] for direction in DIRECTIONS} for kind in ['held','stowed']}
        board=Image.new('RGB',(count*144,4*238),'#22211f');draw=ImageDraw.Draw(board)
        for di,direction in enumerate(DIRECTIONS):
            positions=[base.appearance.hair(base.world(action,direction,p)[0])[0]['center'] for p in range(count)]
            for phase in range(count):
                image,origin,sockets,report=body(action,direction,phase,positions)
                index=di*4+phase%4;page=phase//4
                pages[page].append(native_item(image,origin,index))
                pixels=np.asarray(image).copy();r,g,b=np.moveaxis(pixels[...,:3].astype(float),-1,0)
                near=np.zeros((768,512),bool)
                for hx,hy in report['hands']:near|=(X-hx)**2+(Y-hy)**2<31**2
                skin=(r>75)&(r>g+10)&(g>b+5)&(b/r.clip(1)>.40)
                cuff=(r>150)&(np.max(pixels[...,:3],axis=-1).astype(float)-np.min(pixels[...,:3],axis=-1)<35)
                pixels[~(near&(skin|cuff))]=0
                hand_items[state].append((di*count+phase,native_item(Image.fromarray(pixels),origin,0)))
                info[direction,phase]=page,index
                for kind in anchors:anchors[kind][direction].append(sockets[kind])
                thumb=image.resize((144,216),Image.Resampling.LANCZOS);board.paste(thumb,(phase*144,di*238+20),thumb)
                draw.text((phase*144+2,di*238+1),f'{direction} {state}{phase}',font=FONT,fill='white')
                metrics.append(dict(state=state,direction=direction,phase=phase,**report))
        geometries={}
        for page,items in pages.items():
            name=f'locomotion-v3/body-{state}-{page}.png'
            geometries[page]=pack(name,items);files.append(name)
        images=[f'locomotion-v3/body-{state}-{p//4}.png' for p in range(count)]
        rectangles={name.removesuffix('.png'):[geometries[page][i]['rect'] for i in range(16)]
                    for page,name in enumerate(dict.fromkeys(images))}
        origins={direction:[geometries[info[direction,p][0]][info[direction,p][1]]['origin'] for p in range(count)] for direction in DIRECTIONS}
        bodies[state]=dict(image=images[0],frameImages=images,frames=count,frameWidth=320,frameHeight=480,columns=4,
            frameIndices=[p%4 for p in range(count)],worldUnitsPerPixel=.004,fps=7 if state=='walk' else 14,loop=True,
            frameRectsByImage=rectangles,perFrameRects=rectangles[images[0].removesuffix('.png')],
            perFrameOrigins=origins,equipmentAnchors=anchors,sharedBody='raphael-locomotion-v3')
        bodies[state]['handOcclusion']=state
        board.save(HERE/f'shared-body-{state}.jpg',quality=95)
    gear_items=[];gear_defs={};quivers={};gear_board=Image.new('RGB',(7*180,2*4*275),'#22211f');draw=ImageDraw.Draw(gear_board)
    for wi,weapon in enumerate(WEAPONS):
        gear_defs[weapon]={}
        for ci,carry in enumerate(['held','stowed']):
            indices=[]
            for di,direction in enumerate(DIRECTIONS):
                idle=('explore_idle_' if carry=='stowed' else 'idle_')+weapon
                reference,record=base.world(idle,direction)
                filename=f'{"explore-" if carry=="stowed" else ""}{weapon}-{direction}-gear.png'
                image=Image.open(HERE.parent/'attack-identity-v5/edits/static-gear-validation'/filename).convert('RGBA')
                if carry=='held':
                    pixels=np.asarray(image).copy()
                    if weapon in ['W07','W08','L02']:
                        stored=Image.open(HERE.parent/'attack-identity-v5/edits/static-gear-validation'/f'explore-{weapon}-{direction}-gear.png').convert('RGBA')
                        quiver=np.asarray(stored).copy();quiver[~base.gear.quiver_geometry(weapon,direction,True)]=0
                        quivers[weapon,direction]=Image.fromarray(quiver)
                    keep=held_geometry(weapon,direction,image)
                    pixels[~keep]=0
                    image=Image.fromarray(pixels)
                socket=REFERENCE_TORSO[direction][0] if carry=='stowed' else reference_grip(reference,image)
                box=image.getchannel('A').getbbox();index=len(gear_items)
                gear_items.append(dict(record=dict(index=index),crop=image.crop(box),origin=(socket-np.asarray(box[:2])).tolist()))
                indices.append(index)
                thumb=image.resize((180,270),Image.Resampling.LANCZOS);gear_board.paste(thumb,(wi*180,(ci*4+di)*275),thumb)
                draw.text((wi*180+2,(ci*4+di)*275),f'{weapon} {carry} {direction}',font=FONT,fill='white')
            gear_defs[weapon][carry]=dict(directionFrameIndices=indices,foreground=carry=='held')
    for weapon in ['W07','W08','L02']:
        indices=[]
        for direction in DIRECTIONS:
            image=quivers[weapon,direction];box=image.getchannel('A').getbbox() or (0,0,1,1);index=len(gear_items)
            socket=REFERENCE_TORSO[direction][0]
            gear_items.append(dict(record=dict(index=index),crop=image.crop(box),origin=(socket-np.asarray(box[:2])).tolist()))
            indices.append(index)
        gear_defs[weapon]['quiver']=dict(directionFrameIndices=indices)
    hand_bases={}
    for state,entries in hand_items.items():
        hand_bases[state]=len(gear_items)
        for offset,item in sorted(entries,key=lambda v:v[0]):
            item['record']['index']=hand_bases[state]+offset;gear_items.append(item)
    gear_name='locomotion-v3/equipment.png';gear_geometry=pack(gear_name,gear_items);files.append(gear_name)
    gear_board.save(HERE/'shared-equipment.jpg',quality=94)
    rects=[gear_geometry[i]['rect'] for i in range(len(gear_items))]
    origins=[gear_geometry[i]['origin'] for i in range(len(gear_items))]
    for weapon in gear_defs:
        for carry,entry in gear_defs[weapon].items():
            entry.update(image=gear_name,frames=1,worldUnitsPerPixel=.0025,perFrameRects=rects,perFrameOrigins=origins)
    hand_defs={state:dict(image=gear_name,frames=count,columns=count,
        frameIndices=[hand_bases[state]+p for p in range(count)],worldUnitsPerPixel=.004,
        perFrameRects=rects,perFrameOrigins=origins) for state,count in [('walk',4),('run',8)]}
    updated['movementEquipment']=dict(weapons=gear_defs,image=gear_name,hands=hand_defs)
    for name,action in list(updated['actions'].items()):
        if not base.movement(name):continue
        state='run' if 'run' in name else 'walk'
        updated['actions'][name]=copy.deepcopy(bodies[state])
        updated['actions'][name]['equipmentLayer']='stowed' if name.startswith('explore_') else 'held'
    for name in files:
        if name!=gear_name:updated.setdefault('frameScaleFactors',{})[name.removesuffix('.png')]=[1]*16
    write_json(STAGE/'manifest.json',updated)
    for name in files:write_meta(STAGE/name)
    directory_meta=dict(ver='1.2.0',importer='directory',imported=True,uuid=str(uuid.uuid4()),files=[],subMetas={},userData={})
    write_json(STAGE/'locomotion-v3.meta',directory_meta)
    write_json(HERE/'shared-frame-report.json',metrics)
    write_json(HERE/'shared-prepare-report.json',dict(status='candidate prepared; art review pending',
        sourceManifestSHA256=base.digest(ACTOR/'manifest.json'),candidateManifestSHA256=base.digest(STAGE/'manifest.json'),
        bodyAtlases=3,weaponAtlas=1,bodyFrames=48,weaponViews=56,sharedMovementActions=sum(base.movement(n) for n in M['actions']),
        files={name:base.digest(STAGE/name) for name in files},modelCalls=1,
        cloudPixels='four back-walk calves/boots; upper bodies protected',sourceEquipment='existing reviewed 56 isolated gear views'))
    print('Prepared one shared walk/run body (48 frames) and 56 existing weapon views.',flush=True)


def install_shared():
    report=json.loads((HERE/'shared-prepare-report.json').read_text())
    review=json.loads((HERE/'shared-art-review.json').read_text())
    if review.get('status')!='accepted' or review.get('manifestSHA256')!=report['candidateManifestSHA256']:
        raise ValueError('Matching art review required')
    if base.digest(ACTOR/'manifest.json')!=report['sourceManifestSHA256']:raise ValueError('Current manifest changed')
    for name,sha in report['files'].items():
        if base.digest(STAGE/name)!=sha:raise ValueError('Candidate changed: '+name)
        destination=ACTOR/name;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes((STAGE/name).read_bytes())
        Path(str(destination)+'.meta').write_bytes(Path(str(STAGE/name)+'.meta').read_bytes())
    (ACTOR/'locomotion-v3.meta').write_bytes((STAGE/'locomotion-v3.meta').read_bytes())
    (ACTOR/'manifest.json').write_bytes((STAGE/'manifest.json').read_bytes())
    write_json(HERE/'shared-install-report.json',dict(status='installed; runtime verification pending',manifestSHA256=base.digest(ACTOR/'manifest.json')))
    print('Installed shared body/weapon layers; original source atlases and metadata retained.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--install',action='store_true');args=parser.parse_args()
    if args.install:install_shared()
    else:prepare_shared()
