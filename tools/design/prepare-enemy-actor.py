"""Source-only enemy sheet processing, reusing the two accepted pilot flows.

Pillow repacks pixels; scipy labels subjects and translates walking core ROIs.
No image model, per-frame scaling, runtime install or generation-ledger writes.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage,optimize
from enemy_atlas_runtime import prepare_runtime

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'source-art/encounters/cloud-world-v2'
PRODUCTION=ART/'actor-production-v1'
REGISTRY=ART/'actor-batch-reference-v1/registry.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
def rel(path):return str(path.relative_to(ROOT)).replace('\\','/')
def record_for(identity):return next(item for item in json.loads(REGISTRY.read_text('utf-8'))['items']if item['id']==identity)

def source_file(folder,spec,args):
    name=args.sheet or spec.get('sheet')or spec.get('selectedSource')
    if name:return folder/name
    generation=folder/'generation.json'
    if generation.exists():
        data=json.loads(generation.read_text('utf-8'));name=data.get('output')or data.get('generation',{}).get('output')or data.get('generation',{}).get('rawOutput')
        if isinstance(name,str)and(folder/name).is_file():return folder/name
    for name in ['raw.png','sheet.png']:
        if (folder/name).exists():return folder/name
    raise ValueError('Specify --sheet or processing-spec.json.sheet; source choice is never guessed among multiple images')

def core_registration(idle,moving,roi,bound):
    """Translation-only fit of the same helmet/gear core, never a scale fit."""
    a=np.asarray(idle,dtype=float)/255;b=np.asarray(moving,dtype=float)/255
    af=np.stack([ndimage.gaussian_filter(a[:,:,:3].mean(2)*a[:,:,3],1.2),a[:,:,3]])
    bf=np.stack([ndimage.gaussian_filter(b[:,:,:3].mean(2)*b[:,:,3],1.2),b[:,:,3]])
    x1,y1,x2,y2=roi;ys,xs=np.mgrid[y1:y2:3,x1:x2:3];target=af[:,ys,xs];weight=.25+target[1]
    def loss(v):
        dx,dy=v;sample=np.stack([ndimage.map_coordinates(channel,[ys-dy,xs-dx],order=1,mode='constant')for channel in bf])
        return float(np.mean((np.abs(sample[0]-target[0])+.6*np.abs(sample[1]-target[1]))*weight))
    fit=optimize.minimize(loss,[0,0],method='Powell',bounds=[(-bound,bound),(-bound,bound)],options={'maxiter':40,'xtol':.04,'ftol':.0001})
    return [float(x)for x in fit.x],dict(before=loss([0,0]),after=float(fit.fun),translationOnly=True,nearSearchBoundary=bool(np.max(np.abs(fit.x))>=bound-1))

def prepare(folder,args):
    folder=folder.resolve();assert folder.is_relative_to(ART),'Only repository source-art encounter folders are supported'
    spec_path=folder/'processing-spec.json';spec=json.loads(spec_path.read_text('utf-8'))if spec_path.exists()else{}
    identity=args.id or spec.get('id');assert identity,'Provide --id or processing-spec.json.id'
    registry=record_for(identity);source=source_file(folder,spec,args);original=np.asarray(Image.open(source))
    assert original.ndim==3 and original.shape[2]==4,'Expected original transparent RGBA source; do not infer alpha from an opaque review image'
    assert np.count_nonzero(original[:,:,3]<=3)>original.shape[0]*original.shape[1]*.05 or(identity=='ELITE_07'and spec.get('backgroundFloodE07')),'Source has no genuine transparent background; request alpha repair, do not erase white/grey armour by RGB threshold'
    source_hash=sha(source);h,w=original.shape[:2];assert .95<w/h<1.05,'Expected the actual4x4 sheet; a two-cell targeted edit must first be conservatively composited'
    upp=args.units_per_pixel or spec.get('worldUnitsPerPixel')
    assert upp and upp>0,'Set one reviewed worldUnitsPerPixel for the entire source asset; no automatic per-frame fitting'
    directions=spec.get('directions',['down','left','up','right']);assert sorted(directions)==['down','left','right','up']
    rows=spec.get('rows',spec.get('actualRows',registry['requestedSheet']['rows']));assert len(rows)==4 and rows[0]=='idle'
    body=spec.get('body',registry['bodyTemplate']);lens=registry['supportCount']==0 and body!='three-statues-one-plinth';formation=body=='three-statues-one-plinth'
    pixels=original.copy();flood_report=None
    protected=ndimage.binary_dilation(original[:,:,3]>=64,structure=np.ones((3,3)),iterations=3)if spec.get('backgroundFloodE07')else np.zeros((h,w),bool)
    cleanup=(pixels[:,:,3]>0)&(pixels[:,:,3]<=3)&~protected;cleared=int(np.count_nonzero(cleanup));pixels[cleanup,3]=0
    if spec.get('backgroundFloodE07'):
        assert identity=='ELITE_07','Background fog exception is authorized only for E07'
        eligible=(pixels[:,:,3]<=8)&~protected;seeds=np.zeros((h,w),bool);seeds[[0,-1],:]=True;seeds[:,[0,-1]]=True
        for i in [1,2,3]:
            x=round(i*w/4);y=round(i*h/4);seeds[:,max(0,x-2):min(w,x+3)]=True;seeds[max(0,y-2):min(h,y+3),:]=True
        flood=ndimage.binary_propagation(seeds&eligible,structure=np.ones((3,3)),mask=eligible)
        pixels[flood,3]=0;changed=original[:,:,3]!=pixels[:,:,3];higher=original[:,:,3]>8
        assert np.array_equal(pixels[protected],original[protected])and np.array_equal(pixels[higher],original[higher])
        folder.joinpath('processed').mkdir(exist_ok=True)
        mask_path=folder/'processed/background-flood-mask.png';Image.fromarray(np.uint8(changed)*255).save(mask_path)
        protect_path=folder/'processed/background-protected-mask.png';Image.fromarray(np.uint8(protected)*255).save(protect_path)
        flood_report=dict(authorization='Root E07-only maxA<=8 background flood connected to outer edge/nominal gutters, outside solid64 dilated3px',maxAlpha=8,protectedSolidAlpha=64,protectedDilationPixels=3,totalChangedAlphaPixels=int(changed.sum()),removedAlphaAbove3BackgroundPixels=int(np.count_nonzero(changed&(original[:,:,3]>3))),protectedRgbaByteExact=True,allAlphaAbove8RgbaByteExact=True,protectedRgbaSha256=hashlib.sha256(original[protected].tobytes()).hexdigest(),mask=rel(mask_path),maskSha256=sha(mask_path),protectedMask=rel(protect_path),protectedMaskSha256=sha(protect_path),rawUnchanged=True,rgbThresholdUsed=False)
    excluded=[]
    if spec.get('excludeDetachedRois'):
        # Explicit root-approved E05 source residue exception, not a batch
        # alpha filter. Complete8-connected components only; never a body pixel.
        approved=[[915,930,1010,985],[1060,935,1160,985]]
        assert identity=='ELITE_05'and spec['excludeDetachedRois']==approved,'No generic authorization to delete alpha>3 components'
        residue_labels,_=ndimage.label(pixels[:,:,3]>3,structure=np.ones((3,3)))
        candidates=set()
        for x1,y1,x2,y2 in approved:candidates.update(int(v)for v in np.unique(residue_labels[y1:y2,x1:x2])if v)
        for component in candidates:
            yy,xx=np.where(residue_labels==component);bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];maximum=int(pixels[yy,xx,3].max())
            inside=next((roi for roi in approved if bbox[0]>=roi[0]and bbox[1]>=roi[1]and bbox[2]<=roi[2]and bbox[3]<=roi[3]),None)
            if inside and maximum<=16:
                excluded.append(dict(component=component,sourceRect=bbox,roi=inside,pixels=len(xx),maxAlpha=maximum,connectedToSolid64=False,sourceRgbaSha256=hashlib.sha256(pixels[yy,xx].tobytes()).hexdigest()))
                pixels[yy,xx,3]=0
    # Faint contact shadows may connect adjacent cells. Detect solid body
    # seeds at64 while retaining EVERY original alpha>3 pixel for assignment.
    # Detection is not alpha deletion or a painted segmentation mask.
    detection=int(spec.get('bodyDetectionAlpha',64))
    labels,count=ndimage.label(pixels[:,:,3]>=detection);sizes=np.bincount(labels.ravel());threshold=max(250,int(w*h/16*.008))
    main=np.flatnonzero(sizes>=threshold);main=main[main>0];assert len(main)>=16,'Some cells lack an identifiable subject; inspect original, do not clone a neighboring identity'
    seeds=np.zeros((h,w),np.int16);components=[];assignments=spec.get('componentAssignments',{})
    for label in main:
        yy,xx=np.where(labels==label);row=min(3,int(yy.mean()/h*4));col=min(3,int(xx.mean()/w*4))
        if str(int(label))in assignments:row,col=assignments[str(int(label))]
        seeds[labels==label]=row*4+col+1
        components.append(dict(label=int(label),pixels=int(sizes[label]),sourceRect=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],row=row,column=col))
    assert set(np.unique(seeds))==set(range(17)),'A connected subject crosses/touches another cell; explicit component assignments or conservative separation review is required'
    # All primary components in one lens/formation cell stay grouped. Tiny
    # detached tips/alpha edge islands return to the nearest subject seed.
    _,nearest=ndimage.distance_transform_edt(seeds==0,return_indices=True)
    owners=seeds[nearest[0],nearest[1]];owners[pixels[:,:,3]==0]=0
    xedges=[round(i*w/4)for i in range(5)];yedges=[round(i*h/4)for i in range(5)]
    records={};required=384
    for row in range(4):
        for col in range(4):
            yy,xx=np.where(owners==row*4+col+1);bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
            cx=(xedges[col]+xedges[col+1])/2;cy=(yedges[row]+yedges[row+1])/2
            required=max(required,math.ceil(2*max(cx-bounds[0],bounds[2]-cx,cy-bounds[1],bounds[3]-cy)+32))
            records[(row,col)]=dict(sourceRow=row,sourceColumn=col,direction=directions[col],pose=rows[row],sourceRect=bounds,nominalSourceRect=[xedges[col],yedges[row],xedges[col+1],yedges[row+1]],retainedPixels=int(len(xx)),crossesNominalCell=bool(bounds[0]<xedges[col]or bounds[2]>xedges[col+1]or bounds[1]<yedges[row]or bounds[3]>yedges[row+1]))
    cell=math.ceil(required/128)*128;assert cell<=1024,'Unexpected broad/noisy ownership envelope: review component labels before exporting'
    output=folder/'processed';output.mkdir(exist_ok=True);atlas=Image.new('RGBA',(cell*4,cell*4));frames={};warnings=[]
    for (row,col),record in records.items():
        left,top,right,bottom=record['sourceRect'];patch=pixels[top:bottom,left:right].copy();own=owners[top:bottom,left:right]==row*4+col+1;patch[~own]=[0,0,0,0]
        assert np.array_equal(patch[own],original[top:bottom,left:right][own])
        grid=record['nominalSourceRect'];cx=(grid[0]+grid[2])/2;cy=(grid[1]+grid[3])/2
        px=round(cell/2+left-cx);py=round(cell/2+top-cy)
        frame=Image.new('RGBA',(cell,cell));frame.paste(Image.fromarray(patch),(px,py));bound=frame.getchannel('A').getbbox()
        assert min(bound[:2])>=15 and max(bound[2:])<=cell-15
        record.update(atlasRect=[row*cell,col*cell,cell,cell],sourceToFrame=[px-left,py-top],alphaBounds=list(bound),scaleFactor=1)
        frames[(row,col)]=frame;atlas.paste(frame,(row*cell,col*cell))
    assert sum(r['retainedPixels']for r in records.values())==int(np.count_nonzero(pixels[:,:,3]))
    def point(record,value):
        # Overrides are local to the original nominal source cell, independent
        # of output packing dimensions. No source image is moved or redrawn.
        grid=record['nominalSourceRect'];tx,ty=record['sourceToFrame'];return [grid[0]+value[0]+tx,grid[1]+value[1]+ty]
    def roi_for(record):
        default=[.18,.68,.82,.96]if formation else[.2,.15,.8,.8]if lens else[.3,.02,.7,.22]if body=='human'else[.25,.07,.75,.55]
        fraction=spec.get('coreRois',{}).get(str(record['sourceColumn']),spec.get('coreRoi',default))
        grid=record['nominalSourceRect'];tx,ty=record['sourceToFrame'];gw=grid[2]-grid[0];gh=grid[3]-grid[1]
        return [max(0,round(grid[0]+fraction[0]*gw+tx)),max(0,round(grid[1]+fraction[1]*gh+ty)),min(cell,round(grid[0]+fraction[2]*gw+tx)),min(cell,round(grid[1]+fraction[3]*gh+ty))]
    landmarks=spec.get('corePoints',{});origins=spec.get('origins',{})
    for col in range(4):
        idle=records[(0,col)];frame=frames[(0,col)];alpha=np.asarray(frame)[:,:,3];roi=roi_for(idle);x1,y1,x2,y2=roi
        yy,xx=np.where(alpha[y1:y2,x1:x2]>=128);assert len(xx),f'No core in ROI direction{col}; author coreRoi/corePoints explicitly'
        core=[float(xx.mean()+x1),float(yy.mean()+y1)];idle['coreLandmark']=point(idle,landmarks[f'0,{col}'])if f'0,{col}'in landmarks else core
        if lens:ground=idle['coreLandmark'][1]+float(spec.get('lensCoreHeightMetres',.65))/upp
        elif formation:
            # A broad horizontal plinth row, not the narrow sword tip below it.
            rows_count=np.count_nonzero(alpha>=128,axis=1);minimum=max(8,(idle['alphaBounds'][2]-idle['alphaBounds'][0])*.3)
            valid=np.flatnonzero((rows_count>=minimum)&(np.arange(cell)>idle['alphaBounds'][1]+(idle['alphaBounds'][3]-idle['alphaBounds'][1])*.65))
            assert len(valid),'Author an explicit idle base origin; no broad plinth detected'
            ground=float(valid.max()+1)
        else:
            sx1,sy1,sx2,sy2=spec.get('supportRoi',[.1,.6,.9,1]);grid=idle['nominalSourceRect'];tx,ty=idle['sourceToFrame'];gw=grid[2]-grid[0];gh=grid[3]-grid[1]
            rx1=max(0,round(grid[0]+sx1*gw+tx));rx2=min(cell,round(grid[0]+sx2*gw+tx));ry1=max(0,round(grid[1]+sy1*gh+ty));ry2=min(cell,round(grid[1]+sy2*gh+ty))
            yy,_=np.where(alpha[ry1:ry2,rx1:rx2]>=128);assert len(yy),'Author explicit idle support origin; no support inside ROI'
            ground=float(ry1+yy.max()+1)
        idle['origin']=point(idle,origins[f'0,{col}'])if f'0,{col}'in origins else[idle['coreLandmark'][0],ground]
        for row in range(1,4):
            record=records[(row,col)];key=f'{row},{col}'
            align_walk=row in [1,2]or formation or lens
            if key in landmarks:
                core=point(record,landmarks[key]);delta=[core[i]-idle['coreLandmark'][i]for i in [0,1]];record['coreLandmark']=core
                record['origin']=[idle['origin'][i]+delta[i]for i in [0,1]]if align_walk else idle['origin'][:]
                record['registration']=dict(explicitCorePoint=True)
            elif align_walk:
                delta,quality=core_registration(frame,frames[(row,col)],roi,float(spec.get('maxCoreTranslationPixels',min(60,cell*.12))))
                record['coreLandmark']=[idle['coreLandmark'][i]-delta[i]for i in [0,1]];record['origin']=[idle['origin'][i]-delta[i]for i in [0,1]];record['registration']=quality|dict(movingToIdle=delta)
                if quality['nearSearchBoundary']or quality['after']>quality['before']+.002:warnings.append(f'{key}: inspect core translation search/ROI before acceptance')
            else:
                # Attack keeps the idle support-plane projection by default,
                # preserving a real crouch. Never ground the lowest tool tip.
                record['origin']=idle['origin'][:];record['coreLandmark']=None
                if key not in origins:warnings.append(f'{key}: attack uses idle support-plane projection; review planted feet/base and supply origins override if source ground placement drifted')
            if key in origins:record['origin']=point(record,origins[key])
    ordered=[records[(row,col)]for col in range(4)for row in range(4)]
    for record in ordered:record['origin']=[round(float(v),3)for v in record['origin']]
    atlas.save(output/'atlas.png');pose=registry['primaryRuntimePose'];actions={'idle':dict(image='atlas.png',frames=1,frameIndices=[0],fps=1,loop=True)}
    if not formation:actions['walk']=dict(image='atlas.png',frames=2,frameIndices=[1,2],fps=float(spec.get('walkFps',3.5)),loop=True,nominalSpeedMetresPerSecond=float(spec.get('nominalSpeed',1.7)))
    actions[pose]=dict(image='atlas.png',frames=5 if formation else 3,frameIndices=[0,1,2,3,0]if formation else[0,3,0],phaseStarts=[0,.2,.4,.6,.85]if formation else spec.get('phaseStarts',[0,.75,.875]if pose=='attack_bow'else[0,.28,.6]),fps=5,loop=False)
    if formation:
        for index in range(3):actions[pose+'_step'+str(index)]=dict(image='atlas.png',frames=3,frameIndices=[0,index+1,0],phaseStarts=[0,.28,.6],fps=5,loop=False)
        actions[pose]=dict(actions[pose+'_step0'])
    manifest=dict(revision=identity.lower()+'-source-actor-v1',sourceDesign=rel(source),loaded3DModel=False,image='atlas.png',columns=4,frameWidth=cell,frameHeight=cell,directions=directions,origin=ordered[0]['origin'],perFrameOrigins=[r['origin']for r in ordered],alphaBounds=[r['alphaBounds']for r in ordered],frameScaleFactors={'atlas':[1]*16},alphaThreshold=.025,camera=dict(worldUnitsPerPixel=upp),actions=actions,limitations=['Four actual drawn directions and16 actual source drawings only; no mirrored/invented poses.','One reviewed global pixel/world scale; no frame fitting or generated in-betweens.','Primary pose source only; additional requiredCombatMoves are not implicitly covered.','No independently drawn hit/death; own idle fallback/hide remains explicit.','Static review and actual game gait/collision/texture-lifetime acceptance are separate.']+(['Stationary shared base: no walk clip; per-step pose/origin runtime integration must be reviewed separately.']if formation else[]))
    write(output/'manifest.json',manifest)
    contact=Image.new('RGBA',(cell*4,(cell+24)*4),(50,50,54,255));draw=ImageDraw.Draw(contact)
    for col in range(4):
        for row in range(4):
            x=row*cell;y=col*(cell+24);record=records[(row,col)];ox,oy=record['origin'];contact.alpha_composite(frames[(row,col)],(round(x+cell/2-ox),round(y+cell-40-oy)));draw.line((x+6,y+cell-40,x+cell-6,y+cell-40),fill=(180,135,70,255));draw.text((x+6,y+cell+3),directions[col]+' / '+rows[row],fill='white')
    contact.convert('RGB').save(output/'anchor-contact.jpg',quality=93)
    preview=contact.convert('RGB');preview.thumbnail((1500,1500));preview.save(output/'anchor-contact-preview.jpg',quality=93)
    loop=[]
    for row in [1,2]:
        image=Image.new('RGBA',(cell*2,cell*2),(50,50,54,255));draw=ImageDraw.Draw(image)
        for col in range(4):
            x=col%2*cell;y=col//2*cell;ox,oy=records[(row,col)]['origin'];image.alpha_composite(frames[(row,col)],(round(x+cell/2-ox),round(y+cell-40-oy)));draw.line((x+5,y+cell-40,x+cell-5,y+cell-40),fill=(180,135,70,255));draw.text((x+5,y+5),directions[col],fill='white')
        image.thumbnail((900,900));loop.append(image.convert('RGB'))
    loop[0].save(output/('pose-loop.gif'if formation else'walk-loop.gif'),save_all=True,append_images=loop[1:],duration=286,loop=0)
    _,resample=prepare_runtime(output)
    assert sha(source)==source_hash
    report=dict(status='source-prepared-awaiting-static-review',id=identity,source=rel(source),sourceSha256=source_hash,sourceDimensions=[w,h],sourceUnchanged=True,directionsActuallyConfigured=directions,rowsActuallyConfigured=rows,body=body,grouping='Multiple independent components per lens/formation cell remain one logical subject; no one-body assumption'if lens or formation else'Whole connected bodies plus nearest detached edge pixels; no hard-grid tip clipping',bodyDetectionAlpha=detection,components=components,alphaCleanup=dict(threshold=3,affectedPixels=cleared,allHigherAlphaRgbaPreservedExactlyOnce=not bool(excluded or flood_report),allRetainedBodyRgbaPreservedExactlyOnce=True,backgroundFloodException=flood_report,explicitE05DetachedResidueException=excluded,removedAlphaAbove3NonBodyPixels=sum(x['pixels']for x in excluded)),sourceAtlasSize=list(atlas.size),cellSize=cell,worldUnitsPerPixel=upp,perFrameScale=False,coreRegistration='Translation only, helmet/gear/core ROI; no toe-height body lift. Review configured ROI against identity.',attackAnchorBasis='Explicit source support override or idle support-plane projection, never automatic weapon-tip bottom.',frames=ordered,warnings=warnings,runtimeProduction='processed/runtime-1024',runtimeAtlasSha256=resample['runtimeAtlasSha256'],runtimeInstalled=False,artAcceptance='pending independent static/pose/edge review',gameAcceptance='pending actual game review')
    write(output/'processing.json',report)
    print(identity+':16 exact-pixel subjects ->'+str(cell*4)+' source atlas ->1024 production; source-only, review pending')
    return report

def batch():
    PRODUCTION.mkdir(exist_ok=True);records=[]
    plan_path=PRODUCTION/'batch-plan.json';plan=json.loads(plan_path.read_text('utf-8'))if plan_path.exists()else{};holds=plan.get('holds',{})
    for folder in sorted(PRODUCTION.iterdir()):
        if not folder.is_dir():continue
        generation=folder/'generation.json'
        if not generation.exists():continue
        data=json.loads(generation.read_text('utf-8'));processing=folder/'processed/processing.json';review=folder/'art-review.json'
        prepared=json.loads(processing.read_text('utf-8'))if processing.exists()else{}
        packed_review=folder/'processed/review.json'
        identity=prepared.get('id',data.get('id',folder.name)).upper()
        records.append(dict(directory=rel(folder),generationFile=rel(generation),generationSha256=sha(generation),id=identity,generation=data,processed=bool(prepared),processingFile=rel(processing)if processing.exists()else None,reviewFile=rel(review)if review.exists()else None,review=json.loads(review.read_text('utf-8'))if review.exists()else None,packedReview=json.loads(packed_review.read_text('utf-8'))if packed_review.exists()else None,holdReason=holds.get(identity),runtimeInstalled=bool(json.loads(packed_review.read_text('utf-8')).get('runtimeInstalled'))if packed_review.exists()else False))
    width=1500;cw=250;ch=250;height=max(ch,min(1500,math.ceil(max(1,len(records))/6)*ch));contact=Image.new('RGB',(width,height),(47,47,51));draw=ImageDraw.Draw(contact)
    for index,record in enumerate(records[:36]):
        folder=ROOT/record['directory'];path=folder/'processed/runtime-1024/atlas.png'
        if not path.exists():
            try:path=source_file(folder,{},argparse.Namespace(sheet=None))
            except ValueError:path=folder/'raw.png'
        x=index%6*cw;y=index//6*ch
        if path.exists():
            image=Image.open(path).convert('RGBA');image.thumbnail((cw-12,ch-44));contact.paste(image,(x+(cw-image.width)//2,y+4+(ch-44-image.height)//2),image)
        label='HOLD: repair/review'if record['holdReason']else'static passed / source only'if record['packedReview']else'processed / review pending'if record['processed']else'raw / processing pending'
        draw.text((x+6,y+ch-36),record['id'],fill='white');draw.text((x+6,y+ch-20),label,fill=(245,140,120)if record['holdReason']else(230,200,150))
    contact.save(PRODUCTION/'batch-review-contact.jpg',quality=93)
    groups=PRODUCTION/'review-groups';groups.mkdir(exist_ok=True);group_files=[]
    for group_index in range(math.ceil(len(records)/6)):
        page=Image.new('RGB',(1024,1584),(47,47,51));page_draw=ImageDraw.Draw(page)
        for index,record in enumerate(records[group_index*6:(group_index+1)*6]):
            x=index%2*512;y=index//2*528;folder=ROOT/record['directory'];preview=folder/'processed/anchor-contact-preview.jpg'
            if not preview.exists():
                try:preview=source_file(folder,{},argparse.Namespace(sheet=None))
                except ValueError:continue
            im=Image.open(preview).convert('RGBA');im.thumbnail((500,480));page.paste(im,(x+(512-im.width)//2,y+4),im)
            page_draw.text((x+10,y+492),record['id'],fill='white');page_draw.text((x+10,y+509),'source static passed / root review pending'if record['packedReview']else'pipeline static review pending',fill=(230,200,150))
        path=groups/('group-'+str(group_index+1).zfill(2)+'.jpg');page.save(path,quality=94);group_files.append(rel(path))
    expected=set(sum(plan.get('assigned',{}).values(),[]));delivered={r['id']for r in records}
    summary=dict(newIdentityTotal=32,pilotsInstalledAndGameAccepted=2,batchExpected=30,independentGenerationRecords=len(records),batchSourceProcessed=sum(r['processed']for r in records),batchPipelineStaticReviewed=sum(bool(r['packedReview'])for r in records),batchRuntimeInstalled=sum(bool(r['runtimeInstalled'])for r in records),awaitingDeliveryMetadata=sorted(expected-delivered),runtimeAcceptance='Only mine-crawler/mine-worker representatives game accepted so far; new30 batch source-static approved and installed, pending game QA')
    write(PRODUCTION/'batch-status.json',dict(status='derived read-only aggregation of per-ID evidence; not a generation ledger',summary=summary,records=records,contact=rel(PRODUCTION/'batch-review-contact.jpg'),reviewGroups=group_files,generationFilesWritten=False,runtimeWritten=False))
    print('Aggregated'+str(len(records))+' independent generation records; originals untouched.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path,nargs='?');parser.add_argument('--id');parser.add_argument('--sheet');parser.add_argument('--units-per-pixel',type=float);parser.add_argument('--batch',action='store_true');args=parser.parse_args()
    if args.batch:batch()
    else:
        assert args.folder,'Provide a per-ID source folder or --batch';prepare(args.folder,args)

if __name__=='__main__':main()
