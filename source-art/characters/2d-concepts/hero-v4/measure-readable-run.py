"""Read alpha-only geometry for readable-colour W01 run siblings."""
from pathlib import Path
import hashlib,json,statistics
from PIL import Image

SOURCE=Path(__file__).parent
ROOT=SOURCE.parents[3]
DIRECTIONS=['down','right','up','left']
UPP=1.556/353
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def longest(mask,y):
    runs=[]
    for x in range(mask.width):
        if mask.getpixel((x,y)):
            if not runs or x!=runs[-1][-1]+1:runs.append([x])
            else:runs[-1].append(x)
    run=max(runs,key=len)
    return run[0],run[-1]+1
def sheet(name,baseline):
    p=SOURCE/(name+'.png');im=Image.open(p);assert im.mode=='RGBA' and im.size==(1024,1536)
    original_alpha=Image.open(SOURCE/(name.replace('-readable','')+'.png')).getchannel('A')
    alpha=im.getchannel('A');frames=[]
    for row in range(4):
        for col in range(4):
            rect=[col*256,row*384,256,384];a=alpha.crop((rect[0],rect[1],rect[0]+256,rect[1]+384));mask=a.point(lambda q:255 if q>32 else 0)
            l,t,r,b=mask.getbbox();height=b-t
            # Below the bent forearm bridge, this belt/upper-pelvis core is
            # more stable than35-41% which occasionally joined the fist.
            ys=range(t+round(height*.41),t+round(height*.46));waist=statistics.median((longest(mask,y)[0]+longest(mask,y)[1])/2 for y in ys)
            hbox=mask.crop((0,t,256,t+round(height*.14))).getbbox()
            foot=mask.crop((0,b-5,256,b)).getbbox();foot_x=(foot[0]+foot[2])/2
            edge=max(a.crop(e).getextrema()[1] for e in [(0,0,256,1),(0,383,256,384),(0,0,1,384),(255,0,256,384)])
            margin=min(l,t,256-r,384-b);assert margin>=1,(name,row,col,[l,t,r,b])
            old=baseline[row*4+col]
            om=original_alpha.crop((rect[0],rect[1],rect[0]+256,rect[1]+384)).point(lambda q:255 if q>32 else 0)
            ob=om.getbbox();ot=ob[1];oh=ob[3]-ot
            oys=range(ot+round(oh*.41),ot+round(oh*.46));old_body_x=statistics.median((longest(om,y)[0]+longest(om,y)[1])/2 for y in oys)
            old_head_x=sum(old['head']['silhouetteXBounds'])/2
            frames.append({'direction':DIRECTIONS[row],'column':col,'rect':rect,'alphaBounds':[l,t,r,b],
                'bodyCentreX':waist,'waistBandY':[ys.start,ys.stop],'rawSoleY':b,'headTopY':t,
                'headWidthPixels':hbox[2]-hbox[0],'minimumMargin':margin,'cellBorderMaxAlpha':edge,
                'lowestBootRelativeToWaistX':foot_x-waist,
                'driftFromOriginal':{'bodyCentreX':waist-old_body_x,'headCentreX':(hbox[0]+hbox[2])/2-old_head_x,'soleY':b-old['rawSoleY'],
                    'headTopY':t-old['alphaBounds'][1],'headWidth':hbox[2]-hbox[0]-old['head']['silhouetteWidthPixels']}})
    return {'name':name,'image':'hero-v4/'+name+'.png','size':list(im.size),'frameWidth':256,'frameHeight':384,
        'sourcePNG':p.relative_to(ROOT).as_posix(),'sourcePNGSHA256':sha(p),'alphaExtrema':list(alpha.getextrema()),'frames':frames}

old=json.loads((SOURCE/'metadata.json').read_text(encoding='utf8'))
A=sheet('hero-v4-run-readable-a',old['records']['hero-v4-run-a']['frames'])
B=sheet('hero-v4-run-readable-b',old['records']['hero-v4-run-b']['frames'])
origins={};bounds={};support={}
for row,direction in enumerate(DIRECTIONS):
    phases=[*A['frames'][row*4:row*4+4],*B['frames'][row*4:row*4+4]]
    ground=round(statistics.median(f['rawSoleY'] for f in phases))
    origins[direction]=[[round(f['bodyCentreX'],2),ground] for f in phases]
    bounds[direction]=[f['alphaBounds'] for f in phases]
    support[direction]=[f['lowestBootRelativeToWaistX'] for f in phases]
action={'image':A['image'],'frameImages':[A['image']]*4+[B['image']]*4,'columns':4,'frameWidth':256,'frameHeight':384,
    'frames':8,'fps':14,'loop':True,'frameIndices':[0,1,2,3,0,1,2,3],
    'perFrameRects':[f['rect'] for f in A['frames']],
    'frameRectsByImage':{A['image'][:-4]:[f['rect'] for f in A['frames']],B['image'][:-4]:[f['rect'] for f in B['frames']]},
    'perFrameOrigins':origins,'alphaBounds':[f['alphaBounds'] for f in A['frames']],'perPhaseAlphaBounds':bounds,
    'worldUnitsPerPixel':UPP,'alphaBoundsThreshold':32,
    'originMethod':'X median longest opaque belt/upper-pelvis core at41-46%visible height, below forearm bridge; Y fixed median sole plane per direction across8phases, no single-foot anchoring.',
    'sourcePNGs':[A['sourcePNG'],B['sourcePNG']],'sourcePNGSHA256s':[A['sourcePNGSHA256'],B['sourcePNGSHA256']],
    'sourceDesign':'source-art/characters/2d-concepts/hero-v4/hero-v4-idle-readable.png',
    'sourceDesignSHA256':sha(SOURCE/'hero-v4-idle-readable.png'),
    'bodyProportionReference':'source-art/characters/2d-concepts/hero-v4-proportion/hero-v4-proportion-master-v1.png',
    'bodyProportionReferenceSHA256':'313bdfe8c4e26c91cfcada97f42dbe1ddd045d725b3e0cc3c3259c69fd2b45fa',
    'notes':'Local colour/material edit candidates. UPP fixed1.556/353 for whole action, never per-frame silhouette normalization. No intentional head/body/weapon/pose edits; actual alpha drift measured separately.'}
frames=A['frames']+B['frames']
drift={key:{'min':min(f['driftFromOriginal'][key] for f in frames),'max':max(f['driftFromOriginal'][key] for f in frames)} for key in ['bodyCentreX','headCentreX','soleY','headTopY','headWidth']}
report={'directions':DIRECTIONS,'actions':{'run':action},'records':{A['name']:A,B['name']:B},
    'sourceReference':{'idleReadableSHA256':action['sourceDesignSHA256'],'motherSHA256':action['bodyProportionReferenceSHA256']},
    'worldScaleReference':{'worldUnitsPerPixel':UPP,'standingReferenceMetres':1.556,'sourceBodyHeightReferencePixels':353,
        'method':'User/root fixed action-level scale. Curl/head-width statistics do not mechanically trigger head redraw.'},
    'geometryDriftPixels':drift,'supportEvidence':support,'pixelEditsAfterGeneration':False,
    'visualScope':'W01 readable colours only, all8source phases retained. Original metadata/PNG/manifest left intact. Root native camera review required.'}
(SOURCE/'metadata-readable.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'action':action,'geometryDriftPixels':drift,'supportEvidence':support},ensure_ascii=False,indent=2))
