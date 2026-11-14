"""Read candidate PNG alpha into native action profiles. No pixel writes."""
from pathlib import Path
import hashlib,json,statistics
from PIL import Image

SOURCE=Path(__file__).parent
ROOT=SOURCE.parents[3]
THRESHOLD=32
DIRECTIONS=['down','right','up','left']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def longest(mask,y):
    runs=[]
    for x in range(mask.width):
        if mask.getpixel((x,y)):
            if not runs or x!=runs[-1][-1]+1:runs.append([x])
            else:runs[-1].append(x)
    r=max(runs,key=len)
    return r[0],r[-1]+1
def band_read(mask,top,height,lo,hi):
    ys=range(top+round(height*lo),top+round(height*hi))
    rows=[longest(mask,y) for y in ys]
    box=mask.crop((0,ys.start,mask.width,ys.stop)).getbbox()
    return {'bandY':[ys.start,ys.stop],'silhouetteXBounds':[box[0],box[2]],'silhouetteWidthPixels':box[2]-box[0],
        'coreMedianWidthPixels':statistics.median(r-l for l,r in rows),
        'coreCentreX':statistics.median((l+r)/2 for l,r in rows)}
def sheet(name,columns,rows):
    path=SOURCE/(name+'.png');image=Image.open(path);a=image.getchannel('A');w,h=image.width//columns,image.height//rows
    out=[]
    for row in range(rows):
        for col in range(columns):
            rect=[col*w,row*h,w,h];cell=a.crop((rect[0],rect[1],rect[0]+w,rect[1]+h));mask=cell.point(lambda q:255 if q>THRESHOLD else 0)
            box=mask.getbbox();l,t,r,b=box;height=b-t
            head=band_read(mask,t,height,0,.14);shoulder=band_read(mask,t,height,.19,.26);waist=band_read(mask,t,height,.35,.41)
            foot=mask.crop((0,b-15,w,b)).getbbox()
            lowest=mask.crop((0,b-5,w,b)).getbbox()
            foot_mid=(foot[0]+foot[2])/2
            waist_c=waist['coreCentreX']
            edge=max(cell.crop(e).getextrema()[1] for e in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])
            margin=min(l,t,w-r,h-b)
            assert margin>=1,(name,row,col,box)
            neck_candidates=[(longest(mask,y)[1]-longest(mask,y)[0],y) for y in range(t+round(height*.09),t+round(height*.17))]
            neck_y=min(neck_candidates)[1]
            out.append({'direction':DIRECTIONS[row*columns+col] if name=='hero-v4-idle' else DIRECTIONS[row],
                'column':col,'rect':rect,'alphaBounds':list(box),'heightPixels':height,'head':head,'shoulder':shoulder,'waist':waist,
                'headToNeckPixels':neck_y-t,'estimatedHeadUnitsFromNeck':height/max(1,neck_y-t),
                'footBandY':[b-15,b],'footBandXBounds':[foot[0],foot[2]],'doubleFootMidpointX':foot_mid,'rawSoleY':b,
                'lowestBootRelativeToWaistX':(lowest[0]+lowest[2])/2-waist_c,'minimumMargin':margin,'cellBorderMaxAlpha':edge})
    return {'name':name,'size':list(image.size),'mode':image.mode,'alphaExtrema':list(a.getextrema()),'frameSize':[w,h],'columns':columns,
        'sourcePNG':path.relative_to(ROOT).as_posix(),'sourcePNGSHA256':sha(path),'frames':out}

idle=sheet('hero-v4-idle',2,2)
A=sheet('hero-v4-run-a',4,4)
B=sheet('hero-v4-run-b',4,4)
idle_upp=1.8/idle['frames'][0]['heightPixels']
idle_head_width=idle['frames'][0]['head']['silhouetteWidthPixels']
head_world=idle_head_width*idle_upp
front=[*A['frames'][:4],*B['frames'][:4]]
run_head_pixels=statistics.median(f['head']['silhouetteWidthPixels'] for f in front)
run_upp=head_world/run_head_pixels
run_equal_height_upp=1.8/statistics.median(f['heightPixels'] for f in front)
idle_action={'image':'hero-v4/hero-v4-idle.png','columns':2,'frameWidth':768,'frameHeight':512,'frames':1,'fps':1,'loop':True,
    'frameIndices':[0],'directionFrameIndices':[0,1,2,3],'perFrameRects':[f['rect'] for f in idle['frames']],
    'perFrameOrigins':[[f['doubleFootMidpointX'],f['rawSoleY']] for f in idle['frames']],
    'alphaBounds':[f['alphaBounds'] for f in idle['frames']],'worldUnitsPerPixel':idle_upp,
    'sourcePNG':idle['sourcePNG'],'sourcePNGSHA256':idle['sourcePNGSHA256'],
    'originMethod':'Midpoint of both boot support extent in lowest15px above sole, excluding sword tip; no single-boot anchor.'}
origins={};phase_bounds={};phase_metrics={}
for row,direction in enumerate(DIRECTIONS):
    phases=[*A['frames'][row*4:row*4+4],*B['frames'][row*4:row*4+4]]
    ground=round(statistics.median(f['rawSoleY'] for f in phases))
    origins[direction]=[[round(f['waist']['coreCentreX'],2),ground] for f in phases]
    phase_bounds[direction]=[f['alphaBounds'] for f in phases]
    phase_metrics[direction]=phases
run_action={'image':'hero-v4/hero-v4-run-a.png','frameImages':['hero-v4/hero-v4-run-a.png']*4+['hero-v4/hero-v4-run-b.png']*4,
    'columns':4,'frameWidth':256,'frameHeight':384,'frames':8,'fps':14,'loop':True,'frameIndices':[0,1,2,3,0,1,2,3],
    'perFrameRects':[f['rect'] for f in A['frames']],
    'frameRectsByImage':{'hero-v4/hero-v4-run-a':[f['rect'] for f in A['frames']],'hero-v4/hero-v4-run-b':[f['rect'] for f in B['frames']]},
    'perFrameOrigins':origins,'alphaBounds':[f['alphaBounds'] for f in A['frames']],'perPhaseAlphaBounds':phase_bounds,
    'worldUnitsPerPixel':run_upp,'worldScaleMethod':'Match front head/hair alpha width to common idle adult reference. Equal-height comparison UPP is supplied separately; do not conceal source proportion differences by independent body-height normalization.',
    'sourcePNGs':[A['sourcePNG'],B['sourcePNG']],'sourcePNGSHA256s':[A['sourcePNGSHA256'],B['sourcePNGSHA256']],
    'originMethod':'X waist/belt-band longest opaque body segment centre median, no boot anchor switching; Y fixed median sole line per direction overA/B.'}
mother='source-art/characters/2d-concepts/hero-v4-proportion/hero-v4-proportion-master-v1.png'
for action in [idle_action,run_action]:
    action['sourceDesign']=mother;action['sourceDesignSHA256']='313bdfe8c4e26c91cfcada97f42dbe1ddd045d725b3e0cc3c3259c69fd2b45fa'
    action['alphaBoundsThreshold']=THRESHOLD
report={'directions':DIRECTIONS,'actions':{'idle':idle_action,'run':run_action},'records':{s['name']:s for s in [idle,A,B]},
    'scaleReference':{'targetStandingHeightMetres':1.8,'idleUPP':idle_upp,'idleHeadWidthPixels':idle_head_width,'idleHeadWidthWorldMetres':head_world,
        'runFrontMedianHeadWidthPixels':run_head_pixels,'runHeadWidthMatchedUPP':run_upp,'runEqualHeightComparisonUPP':run_equal_height_upp,
        'runFrontMedianHeightAtHeadMatchedScale':statistics.median(f['heightPixels'] for f in front)*run_upp,
        'runHeadWidthAtEqualHeightScale':run_head_pixels*run_equal_height_upp,
        'equalHeightRunHeadWidthRatioToIdle':run_head_pixels*run_equal_height_upp/head_world,
        'note':'Head alpha includes curls. Band definitions and core body widths are explicit; shoulders include cape/pauldron silhouette. Neck-based head count is an approximate silhouette locator, not a verified anatomical jaw measure.'},
    'supportEvidence':{d:[f['lowestBootRelativeToWaistX'] for f in fs] for d,fs in phase_metrics.items()},
    'visualStatus':'W01 small-scope candidates. Front/back A/B support sides exchanged on visual inspection; source proportion and actual camera comparison remain pending root. No runtime manifest changed.'}
report['waistlineReadings']={
    'method':'Manual visual centre of horizontal belt/buckle, not hip/crotch. Coordinates are source-cell local; belt thickness gives about2px uncertainty.',
    'idleFront':{'hairTopY':12,'beltCentreY':196,'beltUncertaintyPixels':2,'soleY':497,'upperShare':(196-12)/(497-12),'lowerShare':(497-196)/(497-12)},
    'runAFrontPhase0':{'hairTopY':20,'beltCentreY':162,'beltUncertaintyPixels':2,'soleY':373,'upperShare':(162-20)/(373-20),'lowerShare':(373-162)/(373-20)},
    'runBFrontPhase4':{'hairTopY':20,'beltCentreY':162,'beltUncertaintyPixels':2,'soleY':373,'upperShare':(162-20)/(373-20),'lowerShare':(373-162)/(373-20)}}
report['requestedWorldCalibration']={'standingHeightMetres':1.556,'idleUPPForRequestedHeight':1.556/485,
    'runEqualHeightComparisonUPP':1.556/statistics.median(f['heightPixels'] for f in front),
    'runHeadWidthMatchedUPP':run_upp*1.556/1.8,
    'note':'Root owns actual runtime choice. Action UPP values retain the1.8m diagnostic reference explicitly reported earlier; these requested values expose both constraints instead of concealing source head/body discrepancy.'}
report['generationPromptRecord']='source-art/characters/2d-concepts/hero-v4/generation-prompts.json'
(SOURCE/'metadata-partial.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(SOURCE/'metadata.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'scaleReference':report['scaleReference'],'supportEvidence':report['supportEvidence']},ensure_ascii=False,indent=2))
