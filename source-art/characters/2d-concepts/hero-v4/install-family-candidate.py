"""Copy approved ordinary-family source bytes; measure alpha, never save pixels."""
from pathlib import Path
import hashlib,json,shutil,statistics,sys,uuid
from PIL import Image

SOURCE=Path(__file__).parent;ROOT=SOURCE.parents[3]
DEST=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
DIRECTIONS=['down','right','up','left'];THRESHOLD=32
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def longest(mask,y):
    runs=[]
    for x in range(mask.width):
        if mask.getpixel((x,y)):
            if not runs or x!=runs[-1][-1]+1:runs.append([x])
            else:runs[-1].append(x)
    z=max(runs,key=len);return z[0],z[-1]+1
def measure(path):
    image=Image.open(path);assert image.mode=='RGBA';alpha=image.getchannel('A');w,h=image.width//4,image.height//4
    assert image.width%4==image.height%4==0
    frames=[]
    for row in range(4):
        rowmask=alpha.crop((0,row*h,image.width,(row+1)*h)).point(lambda a:255 if a>THRESHOLD else 0)
        occupied=[x for x in range(image.width) if rowmask.crop((x,0,x+1,h)).getbbox()]
        gaps=sorted([(b-a,a,b) for a,b in zip(occupied,occupied[1:]) if b-a>1],reverse=True)[:3]
        assert len(gaps)==3,(path,row,'Could not isolate four characters')
        cuts=[0]+sorted((a+b)//2 for gap,a,b in gaps)+[image.width]
        for col in range(4):
            lo,hi=cuts[col],cuts[col+1];island=rowmask.crop((lo,0,hi,h)).getbbox();assert island
            l,t,r,b=island;l+=lo;r+=lo
            rect=[max(0,l-3),max(row*h,row*h+t-3),min(image.width,r+3)-max(0,l-3),min((row+1)*h,row*h+b+3)-max(row*h,row*h+t-3)]
            nominal=alpha.crop((col*w,row*h,(col+1)*w,(row+1)*h)).point(lambda a:255 if a>THRESHOLD else 0)
            # Isolate by measured island even when a foot/prop crosses its nominal column.
            mask=alpha.crop((lo,row*h,hi,(row+1)*h)).point(lambda a:255 if a>THRESHOLD else 0)
            height=b-t;ys=range(t+round(height*.41),t+round(height*.46))
            centre=lo+statistics.median(sum(longest(mask,y))/2 for y in ys)
            foot=mask.crop((0,b-15,hi-lo,b)).getbbox();footx=lo+(foot[0]+foot[2])/2
            head=mask.crop((0,t,hi-lo,t+round(height*.14))).getbbox()
            frames.append({'direction':DIRECTIONS[row],'column':col,'rect':rect,
                'alphaBounds':[l-rect[0],row*h+t-rect[1],r-rect[0],row*h+b-rect[1]],
                'bodyCentreGlobalX':centre,'footMidGlobalX':footx,'soleGlobalY':row*h+b,
                'headTopSourceY':row*h+t,'headWidthPixels':head[2]-head[0],
                'bodyHeightPixels':height,'nominalCell':[col*w,row*h,w,h]})
    return {'size':list(image.size),'mode':image.mode,'alphaExtrema':list(alpha.getextrema()),'frameWidth':w,'frameHeight':h,'frames':frames}

name,generated=sys.argv[1],Path(sys.argv[2]);family=name.split('-')[0]
assert family in ['W07','W11'] and name.endswith('-readable')
source=SOURCE/(name+'.png');runtime=DEST/source.name
for target in [source,runtime]:
    assert not target.exists() or target.read_bytes()==generated.read_bytes(),(target,'Use a sibling or explicit correction before overwriting')
    shutil.copyfile(generated,target)
meta=Path(str(runtime)+'.meta')
if not meta.exists():
    template=json.loads((DEST/'hero-v4-run-readable-a.png.meta').read_text(encoding='utf8'))
    old=template['uuid'];template['subMetas']['6c48a']['displayName']=name
    meta.write_text(json.dumps(template,ensure_ascii=False,indent=2).replace(old,str(uuid.uuid4()))+'\n',encoding='utf8')
p=SOURCE/'metadata-families.json';report=json.loads(p.read_text(encoding='utf8')) if p.exists() else {'directions':DIRECTIONS,'actions':{},'records':{}}
record={'name':name,'family':family,'image':'hero-v4/'+source.name,'generatedInput':str(generated),
    'generatedInputSHA256':sha(generated),'sourcePNG':source.relative_to(ROOT).as_posix(),'sourcePNGSHA256':sha(source),
    'runtimePNG':runtime.relative_to(ROOT).as_posix(),'runtimePNGSHA256':sha(runtime),'pixelEditsAfterGeneration':False,**measure(source)}
report['records'][name]=record

def common(record,upp):
    return {'image':record['image'],'columns':4,'frameWidth':record['frameWidth'],'frameHeight':record['frameHeight'],
        'perFrameRects':[f['rect'] for f in record['frames']],'alphaBounds':[f['alphaBounds'] for f in record['frames']],
        'alphaBoundsThreshold':THRESHOLD,'worldUnitsPerPixel':upp,'sourcePNG':record['sourcePNG'],'sourcePNGSHA256':record['sourcePNGSHA256'],
        'sourceDesign':'source-art/characters/2d-concepts/hero-v4/hero-v4-idle-readable.png',
        'sourceDesignSHA256':sha(SOURCE/'hero-v4-idle-readable.png')}
def origins(record,idle=False):
    result=[];height=record['frameHeight']
    for row in range(4):
        phases=record['frames'][row*4:row*4+4];ground=statistics.median(f['soleGlobalY'] for f in phases[1:])
        for f in phases:
            x=f['footMidGlobalX'] if idle else f['bodyCentreGlobalX'];y=f['soleGlobalY'] if idle else ground
            result.append([round(x-f['rect'][0],2),round(y-f['rect'][1],2)])
    return result
for fam in ['W07','W11']:
    walk=report['records'].get(fam+'-walk-readable');attack=report['records'].get(fam+'-attack-readable')
    runa=report['records'].get(fam+'-run-a-readable');runb=report['records'].get(fam+'-run-b-readable')
    kind='bow' if fam=='W07' else 'staff'
    if walk:
        upp=1.556/walk['frames'][0]['bodyHeightPixels'];base=common(walk,upp)
        report['actions']['idle_'+fam]={**base,'frames':1,'frameIndices':[0],'fps':1,'loop':True,'perFrameOrigins':origins(walk,True),
            'originMethod':'Both boots support midpoint for idle column0; actual sole, prop excluded by held-above-boot design.'}
        report['actions']['walk_'+fam]={**base,'frames':4,'frameIndices':[1,2,3,2],'fps':7,'loop':True,'perFrameOrigins':origins(walk),
            'originMethod':'Belt/upper-pelvis core X; common ground Y across walk phases1-3 per direction.'}
    if attack:
        upp=report['actions'].get('walk_'+fam,{}).get('worldUnitsPerPixel',1.556/attack['frames'][0]['bodyHeightPixels'])
        report['actions']['attack_'+kind+'_'+fam]={**common(attack,upp),'frames':4,'frameIndices':[0,1,2,3],'fps':6,'loop':False,
            'phaseStarts':[0,.2,.75,.88] if fam=='W07' else [0,.28,.55,.78], 'perFrameOrigins':origins(attack),
            'phaseNotes':'Bow aim max.74 holds draw column1; .75+ release samples column2 then recover.' if fam=='W07' else 'Staff core emits at.20/.70=.286; fire column1 starts.28.',
            'originMethod':'Belt/upper-pelvis core X, common ground Y; no per-frame height normalization.'}
    if runa and runb:
        upp=1.556/353;profile=common(runa,upp);profile.pop('perFrameRects',None)
        profile.update({'frameImages':[runa['image']]*4+[runb['image']]*4,'frames':8,'frameIndices':[0,1,2,3,0,1,2,3],'fps':14,'loop':True,
            'frameRectsByImage':{runa['image'][:-4]:[f['rect'] for f in runa['frames']],runb['image'][:-4]:[f['rect'] for f in runb['frames']]},
            'sourcePNGs':[runa['sourcePNG'],runb['sourcePNG']],'sourcePNGSHA256s':[runa['sourcePNGSHA256'],runb['sourcePNGSHA256']]})
        mapping={}
        for row,d in enumerate(DIRECTIONS):
            phases=[*runa['frames'][row*4:row*4+4],*runb['frames'][row*4:row*4+4]];ground=statistics.median(f['soleGlobalY'] for f in phases)
            mapping[d]=[[round(f['bodyCentreGlobalX']-f['rect'][0],2),round(ground-f['rect'][1],2)] for f in phases]
        profile['perFrameOrigins']=mapping;profile['originMethod']='Core X and per-direction fixed ground Y across8phases, exact unchangedW01 source physical scale1.556/353.'
        report['actions']['run_'+kind]=profile
report['scope']='Ordinary W07/W11 candidates only. No runtime manifest/source code changes.'
report['scalePolicy']='Walk column0 sets1.556m family body; attack shares walk UPP; run uses fixedW01-readable1.556/353, never per-frame silhouette normalization.'
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'installed':name,'source':str(source),'sha256':sha(source),'size':record['size'],'actionsReady':list(report['actions'])},ensure_ascii=False,indent=2))
