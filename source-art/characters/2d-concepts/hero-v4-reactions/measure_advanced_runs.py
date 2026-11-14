"""Read-only alpha geometry and byte-preserving copies for advanced run edits.

No image pixels are written by Pillow. PNG bytes are copied unchanged.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,statistics,shutil

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
SOURCE=HERE/'advanced-runs'
BASE=HERE.parent/'hero-v4'
RUNTIME=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
DIRECTIONS=['down','right','up','left']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def longest(mask,y):
    runs=[];start=None
    for x in range(mask.width+1):
        active=x<mask.width and bool(mask.getpixel((x,y)))
        if active and start is None:start=x
        elif not active and start is not None:runs.append((start,x));start=None
    return max(runs,key=lambda v:v[1]-v[0])
def head_component(mask,top,height):
    # Advanced bow tips and quiver arrows may share head-height rows. The
    # largest connected opaque component in the upper11% is the hair/face,
    # whereas taking the whole horizontal band's bbox also includes the prop.
    bottom=min(mask.height,top+round(height*.11))
    pending={(x,y) for y in range(top,bottom) for x in range(mask.width) if mask.getpixel((x,y))}
    groups=[]
    while pending:
        seed=pending.pop();todo=[seed];points=[seed]
        while todo:
            x,y=todo.pop()
            for neighbour in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if neighbour in pending:pending.remove(neighbour);todo.append(neighbour);points.append(neighbour)
        groups.append(points)
    head=max(groups,key=len)
    return [min(p[0] for p in head),min(p[1] for p in head),max(p[0] for p in head)+1,max(p[1] for p in head)+1]
def metrics(alpha,row,col):
    cell=(col*256,row*384,(col+1)*256,(row+1)*384)
    a=alpha.crop(cell);m=a.point(lambda q:255 if q>=32 else 0)
    l,t,r,b=m.getbbox();height=b-t
    ys=range(t+round(height*.41),t+round(height*.46))
    centre=statistics.median(sum(longest(m,y))/2 for y in ys)
    head=head_component(m,t,height)
    return {'bodyCentreX':centre,'rawSoleY':b,'headTopY':t,'headCentreX':sum((head[0],head[2]))/2,'headWidthPixels':head[2]-head[0]}

record_path=SOURCE/'generation-record.json'
record=json.loads(record_path.read_text(encoding='utf-8'))
bow_record_path=SOURCE/'bow-generation-record.json'
if bow_record_path.exists():
    for item in json.loads(bow_record_path.read_text(encoding='utf-8'))['files']:
        if not any(v['name']==item['name'] for v in record['files']):record['files'].append(item)
base_meta=json.loads((BASE/'metadata-readable.json').read_text(encoding='utf-8'))
family_meta=json.loads((BASE/'metadata-families.json').read_text(encoding='utf-8')) if (BASE/'metadata-families.json').exists() else None
upp=base_meta['actions']['run']['worldUnitsPerPixel']
sheets={}
for item in record['files']:
    generated=Path(item['generatedPath']);dest=SOURCE/(item['name']+'.png')
    if not dest.exists() or sha(dest)!=sha(generated):shutil.copyfile(generated,dest)
    im=Image.open(dest);assert im.mode=='RGBA' and im.size==(1024,1536),(dest,im.mode,im.size)
    alpha=im.getchannel('A');hist=alpha.histogram()
    base_alpha=Image.open(Path(item['target'])).getchannel('A')
    frames=[]
    for row in range(4):
        for col in range(4):
            cell=(col*256,row*384,(col+1)*256,(row+1)*384)
            a=alpha.crop(cell);bbox=a.point(lambda q:255 if q>=16 else 0).getbbox();assert bbox
            l,t,r,b=bbox
            # Two unmodified source pixels of padding protect antialiased edges.
            cl=max(0,l-2);ct=max(0,t-2);cr=min(256,r+2);cb=min(384,b+2)
            rect=[cell[0]+cl,cell[1]+ct,cr-cl,cb-ct]
            edge=max(a.crop(e).getextrema()[1] for e in [(0,0,256,1),(0,383,256,384),(0,0,1,384),(255,0,256,384)])
            assert edge<16,('Body crosses a cell boundary or opaque background',item['name'],row,col,edge)
            measured=metrics(alpha,row,col);base=metrics(base_alpha,row,col)
            frames.append({'direction':DIRECTIONS[row],'column':col,'rect':rect,'cropOffset':[cl,ct],
                'alphaBounds':[l-cl,t-ct,r-cl,b-ct], 'alphaBoundsCell':[l,t,r,b],
                'minimumCellMargin':min(l,t,256-r,384-b),'cellBorderMaxAlpha':edge,**measured,
                'driftFromTarget':{k:round(measured[k]-base[k],3) for k in measured}})
    image='hero-v4/'+dest.name
    item.update({'sourceFile':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest),'generatedSHA256':sha(generated),
        'targetSHA256':sha(Path(item['target'])),'referenceSHA256s':{p:sha(Path(p)) for p in item['references']},
        'dimensions':list(im.size),'alphaExtrema':list(alpha.getextrema()),'alpha0Fraction':hist[0]/sum(hist)})
    if item.get('retry'):
        refs=[item['retry'][key] for key in ('target','companion','weaponAtlas')]
        item['retry']['referenceSHA256s']={p:sha(Path(p)) for p in refs}
    sheets[item['name']]={'image':image,'size':list(im.size),'columns':4,'frameWidth':256,'frameHeight':384,
        'perFrameRects':[f['rect'] for f in frames],'alphaBounds':[f['alphaBounds'] for f in frames],
        'sha256':item['sha256'],'alphaExtrema':item['alphaExtrema'],'alpha0Fraction':item['alpha0Fraction'],'frames':frames,
        'runtimeInstalled':False}
actions={}
for weapon in ['W02','L01','W08','L02']:
    a=sheets.get(weapon+'-run-a-readable');b=sheets.get(weapon+'-run-b-readable')
    if not (a and b):continue
    target_action=family_meta['actions']['run_bow'] if weapon in ['W08','L02'] else base_meta['actions']['run']
    origins={};bounds={}
    for row,direction in enumerate(DIRECTIONS):
        phases=[*a['frames'][row*4:row*4+4],*b['frames'][row*4:row*4+4]]
        target_origins=[]
        for i,origin in enumerate(target_action['perFrameOrigins'][direction]):
            target_name=target_action['frameImages'][i].removesuffix('.png')
            target_rect=target_action['frameRectsByImage'][target_name][row*4+i%4]
            target_origins.append([origin[0]+target_rect[0]-(i%4)*256,origin[1]+target_rect[1]-row*384])
        ground_delta=statistics.median(f['driftFromTarget']['rawSoleY'] for f in phases)
        # Cosmetic guard edits can connect a fist to the waist alpha silhouette.
        # Preserve the approved pelvis/support-plane pivot and transfer only
        # the measured unchanged-head translation; never anchor to a blade or
        # let a newly connected forearm shift the body horizontally.
        origins[direction]=[[round(target_origins[i][0]+f['driftFromTarget']['headCentreX']-f['cropOffset'][0],3),
            target_origins[i][1]+ground_delta-f['cropOffset'][1]] for i,f in enumerate(phases)]
        bounds[direction]=[f['alphaBounds'] for f in phases]
        for i,(f,origin) in enumerate(zip(phases,origins[direction])):f['origin']=origin;f['fixedGroundPlaneCellY']=target_origins[i][1]+ground_delta
    actions['run_'+weapon]={'image':a['image'],'frameImages':[a['image']]*4+[b['image']]*4,
        'columns':4,'frameWidth':256,'frameHeight':384,'frames':8,'fps':14,'loop':True,'frameIndices':[0,1,2,3,0,1,2,3],
        'perFrameRects':a['perFrameRects'],'frameRectsByImage':{a['image'][:-4]:a['perFrameRects'],b['image'][:-4]:b['perFrameRects']},
        'perFrameOrigins':origins,'alphaBounds':a['alphaBounds'],'perPhaseAlphaBounds':bounds,'alphaBoundsThreshold':16,
        'worldUnitsPerPixel':upp,'originMethod':'Approved W01 or frozen W07 pelvis/support-plane origin transferred by measured head X translation (largest connected opaque hair/face in upper11%, excluding bow tips and quiver arrows). Y approved fixed8phase support plane plus median sole translation per direction. Target and new crop offsets correctly converted. Raw belt alpha remains diagnostic because a newly connected forearm can move its longest-run centre without moving the body.',
        'originReferenceAction':'hero-v4/metadata-families.json#actions.run_bow' if weapon in ['W08','L02'] else 'hero-v4/metadata-readable.json#actions.run',
        'sourcePNGs':[f['sourceFile'] for f in record['files'] if f['id']==weapon],
        'sourcePNGSHA256s':[a['sha256'],b['sha256']],
        'notes':'Existing W01 eight-phase A/B targets, decorative weapon substitution only. Same whole-action source-body UPP, no phase-height normalization. Raw built-in PNG bytes; parent native review required.'}
frames=[f for s in sheets.values() for f in s['frames']]
drift={key:{'min':min(f['driftFromTarget'][key] for f in frames),'max':max(f['driftFromTarget'][key] for f in frames)} for key in frames[0]['driftFromTarget']}
result={'version':'hero-v4-advanced-runs-readable-v1','status':'SOURCE_READY_PENDING_PARENT_NATIVE_QA','runtimeInstalled':False,
    'directions':DIRECTIONS,'actions':actions,'sheets':sheets,'worldScaleReference':{'worldUnitsPerPixel':upp,
        'standingReferenceMetres':1.556,'sourceBodyHeightReferencePixels':353,'referenceFile':(BASE/'metadata-readable.json').relative_to(ROOT).as_posix()},
    'geometryDriftPixels':drift,'pixelEditsAfterGeneration':False,
    'alphaPolicy':'Alpha>=16 crop; alpha>=32 stable-body geometry. Some generated gutters reach8/255; native alpha test .025 strips1..6 but a few3% low-alpha pixels can remain and require native review. Raw source bytes preserved.',
    'limits':['Decorative weapon edits are not guaranteed pixel-identical; measured drift recorded.','Source-only metadata; no game manifest/action timing/code changed.','Parent must verify native A/B phase loop, held prop and ground anchor.']}
dump(record_path,record);dump(HERE/'metadata-advanced-runs.json',result)
print(json.dumps({'actions':list(actions),'upp':upp,'drift':drift,'sheets':{k:{'size':s['size'],'alpha':s['alphaExtrema'],'maxBorderAlpha':max(f['cellBorderMaxAlpha'] for f in s['frames']),'minMargin':min(f['minimumCellMargin'] for f in s['frames'])} for k,s in sheets.items()}},ensure_ascii=False,indent=2))
