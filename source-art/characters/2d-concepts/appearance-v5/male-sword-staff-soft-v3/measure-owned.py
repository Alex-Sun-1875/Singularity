"""Read-only native alpha measurement; writes JSON metadata, never PNG pixels."""
from pathlib import Path
from PIL import Image
import json, hashlib, statistics, copy
import numpy as np
from scipy import ndimage

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
RUNTIME=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
MANIFEST=json.loads((RUNTIME/'manifest.json').read_text(encoding='utf8'))
RECORDS=json.loads((HERE/'generation-records.json').read_text(encoding='utf8'))
NAMES={r['name'] for r in RECORDS}
DIRS=MANIFEST['directions']
THRESHOLD=15

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mask(path,threshold=THRESHOLD):
    im=Image.open(path)
    assert im.mode=='RGBA'
    return im,im.getchannel('A').point(lambda v:255 if v>threshold else 0)

def _rects_for(im,alpha,full):
    if im.size==(1536,1024):
        return [[0,0,768,512],[768,0,768,512],[0,512,768,512],[768,512,768,512]],[]
    assert im.size==(1024,1536),im.size
    if full:return [[c*256,r*384,256,384] for r in range(4) for c in range(4)],[]
    rects=[];splits=[]
    for row in range(4):
        ry=row*384
        occupied=[alpha.crop((x,ry,x+1,ry+384)).getbbox() is not None for x in range(1024)]
        gaps=[];start=None
        for x,active in enumerate(occupied+[True]):
            if not active and start is None:start=x
            elif active and start is not None:
                gaps.append((start,x));start=None
        cuts=[0]
        for edge in [256,512,768]:
            candidates=[g for g in gaps if g[1]-g[0]>=2 and abs((g[0]+g[1])/2-edge)<140]
            assert candidates,('no transparent separation',row,edge)
            gap=min(candidates,key=lambda g:abs((g[0]+g[1])/2-edge))
            cuts.append((gap[0]+gap[1])//2)
        cuts.append(1024);assert cuts==sorted(cuts)
        splits.append(cuts)
        for col in range(4):
            left,right=cuts[col:col+2]
            b=alpha.crop((left,ry,right,ry+384)).getbbox();assert b
            l,t,r,b=left+b[0],ry+b[1],left+b[2],ry+b[3]
            x=max(left,l-2);y=max(ry,t-2)
            rects.append([x,y,min(right,r+2)-x,min(ry+384,b+2)-y])
    return rects,splits

def rects_for(im,alpha,full):
    try:return _rects_for(im,alpha,full)
    except AssertionError:
        rects=[]
        for row in range(4):
            labels,count=ndimage.label(np.asarray(alpha)[row*384:(row+1)*384]>0)
            sizes=np.bincount(labels.ravel());objects=ndimage.find_objects(labels)
            major=[i for i in range(1,count+1) if sizes[i]>1000]
            assert len(major)==4,('component count',row,len(major))
            major.sort(key=lambda i:(objects[i-1][1].start+objects[i-1][1].stop)/2)
            for i in major:
                ys,xs=objects[i-1];x=max(0,xs.start-2);y=max(0,ys.start-2)
                rects.append([x,row*384+y,min(1024,xs.stop+2)-x,min(384,ys.stop+2)-y])
        return rects,['connected-component bounds; inspect neighbour contamination']

def bbox(alpha,rect):
    x,y,w,h=rect;b=alpha.crop((x,y,x+w,y+h)).getbbox();assert b
    return [x+b[0],y+b[1],x+b[2],y+b[3]]

def centre(alpha,rect,ys,expected):
    x,y,w,h=rect;values=[]
    for yy in ys:
        runs=[];start=None
        for xx in range(x,x+w+1):
            active=xx<x+w and alpha.getpixel((xx,yy))>0
            if active and start is None:start=xx
            elif not active and start is not None:runs.append((start,xx));start=None
        if runs:
            # Body/vest span is wider than the thin separate sword or staff.
            run=max(runs,key=lambda p:(p[1]-p[0])-0.1*abs((p[0]+p[1])/2-expected))
            values.append((run[0]+run[1])/2)
    assert values
    return statistics.median(values)

measured={}
for record in RECORDS:
    name=record['name'];path=Path(record['sourcePath']);oldpath=RUNTIME/'hero-v4'/name
    im,a=mask(path);oldim,oa=mask(oldpath)
    assert im.size==oldim.size
    assert sha(path)==sha(record['runtimePath'])==sha(record['rawOutputPath'])
    full=name in {'hero-v4-idle-readable.png','hero-v4-run-readable-a.png','hero-v4-run-readable-b.png'}
    threshold=THRESHOLD;geometry_warning=None
    print('Measuring',name,flush=True)
    try:rects,cuts=rects_for(im,a,full)
    except AssertionError:
        # Historical baseline with an opaque backdrop is explicitly rejected.
        # A higher alpha segmentation is only for reviewable provisional geometry.
        threshold=128;_,a=mask(path,threshold)
        rects,cuts=rects_for(im,a,full)
        geometry_warning='Provisional alpha>128 segmentation; source background fails threshold16 and requires regeneration.'
    oldrects,_=rects_for(oldim,oa,full)
    alpha=im.getchannel('A');hist=alpha.histogram();frames=[]
    for i,(rect,oldrect) in enumerate(zip(rects,oldrects)):
        b=bbox(a,rect);ob=bbox(oa,oldrect)
        height=ob[3]-ob[1];ys=range(ob[1]+round(height*.41),ob[1]+round(height*.46))
        expected=(oldrect[0]+oldrect[2]/2)
        oldcentre=centre(oa,oldrect,ys,expected);newcentre=centre(a,rect,ys,oldcentre)
        frames.append({'index':i,'direction':DIRS[i//(2 if full and im.size==(1536,1024) else 4)] if im.size!=(1536,1024) else DIRS[i],
            'rect':rect,'absoluteAlphaBounds':b,'alphaBounds':[b[0]-rect[0],b[1]-rect[1],b[2]-rect[0],b[3]-rect[1]],
            'bodyCentreX':newcentre,'oldBodyCentreX':oldcentre,'soleY':b[3],'oldSoleY':ob[3],
            'registrationDelta':[newcentre-oldcentre,b[3]-ob[3]],'alphaHeightDelta':(b[3]-b[1])-(ob[3]-ob[1])})
    measured[name]={'size':list(im.size),'alphaExtrema':list(alpha.getextrema()),'below16Fraction':sum(hist[:16])/(im.width*im.height),
        'corner20MaxAlpha':max(alpha.crop((0,0,20,20)).getextrema()),'rects':rects,'rowSplits':cuts,'frames':frames,
        'geometryThreshold':threshold,'geometryWarning':geometry_warning,'sourceSHA256':sha(path),'runtimeSHA256':sha(record['runtimePath']),
        'inputSHA256s':{p:sha(p) for p in record['inputs']},'rawSHA256':sha(record['rawOutputPath'])}
    record.update({'inputSHA256s':measured[name]['inputSHA256s'],'sourceSHA256':sha(path),'runtimeSHA256':sha(record['runtimePath']),
        'rawSHA256':sha(record['rawOutputPath']),'builtinTool':True,'pixelEditsAfterGeneration':False})

actions={}
for key,old in MANIFEST['actions'].items():
    oldnames=[Path(p).name for p in (old.get('frameImages') or [old['image']])]
    if not set(oldnames)<=NAMES:continue
    act=copy.deepcopy(old);act['image']=old['image'].replace('hero-v4/','hero-v6/')
    name=Path(old['image']).name;sheet=measured[name]
    act['perFrameRects']=copy.deepcopy(sheet['rects']);act['alphaBounds']=[f['alphaBounds'] for f in sheet['frames']]
    if old.get('frameImages'):
        act['frameImages']=[p.replace('hero-v4/','hero-v6/') for p in old['frameImages']]
        act['frameRectsByImage']={'hero-v6/'+n[:-4]:copy.deepcopy(measured[n]['rects']) for n in dict.fromkeys(oldnames)}
        origins={};phase_bounds={}
        for row,direction in enumerate(DIRS):
            phases=[measured[n]['frames'][row*4+(old.get('frameIndices') or list(range(8)))[ordinal]] for ordinal,n in enumerate(oldnames)]
            local_sol=[f['soleY']-row*384 for f in phases];ground=statistics.median(local_sol)
            points=[];phase_bounds[direction]=[]
            for ordinal,(n,frame) in enumerate(zip(oldnames,phases)):
                index=row*4+old['frameIndices'][ordinal]
                oldr=(old.get('frameRectsByImage') or {}).get(old['frameImages'][ordinal][:-4],old.get('perFrameRects',[]))[index]
                oldorigin=old['perFrameOrigins'][direction][ordinal]
                rect=act['frameRectsByImage']['hero-v6/'+n[:-4]][index]
                if rect[1]+rect[3]<row*384+ground+1:rect[3]=min((row+1)*384,row*384+ground+2)-rect[1]
                points.append([round(oldr[0]+oldorigin[0]+frame['registrationDelta'][0]-rect[0],2),row*384+ground-rect[1]])
                phase_bounds[direction].append([frame['absoluteAlphaBounds'][0]-rect[0],frame['absoluteAlphaBounds'][1]-rect[1],frame['absoluteAlphaBounds'][2]-rect[0],frame['absoluteAlphaBounds'][3]-rect[1]])
            origins[direction]=points
        act['perFrameOrigins']=origins;act['perPhaseAlphaBounds']=phase_bounds
        act['perFrameRects']=act['frameRectsByImage'][act['image'][:-4]]
    else:
        origins=[]
        for i,frame in enumerate(sheet['frames']):
            oldr=old['perFrameRects'][i];oldorigin=old['perFrameOrigins'][i];rect=act['perFrameRects'][i]
            origins.append([round(oldr[0]+oldorigin[0]+frame['registrationDelta'][0]-rect[0],2),oldr[1]+oldorigin[1]+frame['registrationDelta'][1]-rect[1]])
        act['perFrameOrigins']=origins
    act['alphaBoundsThreshold']=sheet['geometryThreshold']
    act['originMethod']='Native alpha-only measured torso registration relative to original pose origin; run Y uses fixed per-direction sole median over8phases. Crops follow transparent gaps, never nominal sword cells. No PNG scaling.'
    act['sourcePNGs']=[str((HERE/n).relative_to(ROOT)).replace('\\','/') for n in dict.fromkeys(oldnames)]
    act['sourcePNGSHA256s']=[measured[n]['sourceSHA256'] for n in dict.fromkeys(oldnames)]
    act['sourceDesign']='source-art/characters/2d-concepts/appearance-v5/male-direction-soft-geralt-v3.png'
    act['sourceDesignSHA256']=sha(ROOT/act['sourceDesign'])
    # Original accepted action-level scale (approximately1.556world height) is retained.
    # Outfit/curl silhouette changes do not justify normalizing individual poses.
    act['worldUnitsPerPixel']=old['worldUnitsPerPixel']
    actions[key]=act

report={'status':'soft-Geralt-v3 native sources measured; pending root engine review','actions':actions,
        'records':measured,'directions':DIRS,'pixelEditsAfterGeneration':False,
        'worldScaleMethod':'Preserve original accepted action-level UPP and1.556world stature; measured registration/crops only, no1.8rescale.',
        'pendingBackgroundSources':[n for n,r in measured.items() if r['below16Fraction']<.65 or r['corner20MaxAlpha']>=16]}
(HERE/'owned-actions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(HERE/'generation-records.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'sourceCount':len(measured),'actionCount':len(actions),'actionKeys':list(actions),'pendingBackgroundSources':report['pendingBackgroundSources'],
                 'thresholds':{n:r['geometryThreshold'] for n,r in measured.items()},'allSourceRuntimeSHAEqual':all(r['sourceSHA256']==r['runtimeSHA256'] for r in measured.values())},ensure_ascii=False,indent=2))

