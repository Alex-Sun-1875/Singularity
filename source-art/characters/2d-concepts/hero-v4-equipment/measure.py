"""Only reads native PNG alpha; writes candidate action metadata, never image pixels."""
from pathlib import Path
from PIL import Image
import json,hashlib,statistics
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TARGET=1.5562753036437247
SOURCES=HERE/'sources'
runtime=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
# Visually located head centres and shoulder/belt bands, absolute source pixels.
heads={
 'walk':[[134,393,650,905],[135,391,651,908],[132,393,650,906],[123,374,632,891]],
 'attack':[[123,350,605,898],[103,325,605,895],[107,335,591,897],[111,355,632,900]]}
bands={'walk':{'shoulder':[89,91,89,88],'waist':[161,163,163,161]},'attack':{'shoulder':[111,113,114,112],'waist':[174,177,180,174]}}
result={'candidate':True,'notAnatomyApproved':True,'status':'W01 only; advanced derivation paused after readability feedback','actions':{},'records':{}}
for kind in ['walk','attack']:
 name=f'hero-v4-w01-{kind}.png';path=SOURCES/name;im=Image.open(path);a=im.getchannel('A');mask=a.point(lambda v:255 if v>32 else 0)
 assert im.size==(1024,1536)
 assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256((runtime/name).read_bytes()).digest()
 rects=[];origins=[];ab=[];landmarks=[];heights=[]
 for row in range(4):
  ry=row*384;counts=[sum(mask.getpixel((x,y))>0 for y in range(ry,ry+384))for x in range(1024)];gaps=[];start=None
  for x,n in enumerate(counts):
   if n==0 and start is None:start=x
   if n>0 and start is not None:
    if x-start>=5:gaps.append((start,x))
    start=None
  splits=[0]
  for boundary in [256,512,768]:
   candidates=[g for g in gaps if abs((g[0]+g[1])/2-boundary)<140]
   g=min(candidates,key=lambda g:abs((g[0]+g[1])/2-boundary));splits.append((g[0]+g[1])//2)
  splits.append(1024)
  for col in range(4):
   l,r=splits[col:col+2];bb=mask.crop((l,ry,r,ry+384)).getbbox();assert bb
   bx0,by0,bx1,by1=l+bb[0],ry+bb[1],l+bb[2],ry+bb[3]
   assert bx0>0 and bx1<1024 and by0>=ry and by1<=(ry+384)
   x0=max(l,bx0-2);y0=max(ry,by0-2);x1=min(r,bx1+2);y1=min(ry+384,by1+2)
   rects.append([x0,y0,x1-x0,y1-y0]);ab.append([bx0-x0,by0-y0,bx1-x0,by1-y0])
   # Thin blade tips cannot move dense boot-support registration.
   bottom=max(by0,by1-55);xs=[]
   for x in range(bx0,bx1):
    if sum(mask.getpixel((x,y))>0 for y in range(bottom,by1))>=8:xs.append(x)
   footx=round((xs[0]+xs[-1])/2);sole=by1-1
   origins.append([footx-x0,sole-y0])
   hx=heads[kind][row][col];searchTop=ry+(0 if kind=='walk' else 25);searchBottom=ry+105
   pixels=[(x,y)for y in range(searchTop,searchBottom)for x in range(max(0,hx-24),min(1024,hx+25))if mask.getpixel((x,y))]
   hy=min(p[1]for p in pixels)
   shoulders=[hx,ry+bands[kind]['shoulder'][col]];waist=[hx,ry+bands[kind]['waist'][col]]
   landmarks.append({'frameIndex':row*4+col,'direction':['down','right','up','left'][row],'headTop':[hx,hy],'shoulderMidpointEstimate':shoulders,'waistBeltMidpointEstimate':waist,'bothFeetMidpoint':[footx,sole],'manualPointUncertaintyPixels':{'headCentreX':4,'shoulder':6,'waist':6},'bodyHeightHairToSolePixels':sole-hy+1})
   if row==0:heights.append(sole-hy+1)
 body=statistics.median(heights);upp=TARGET/body
 action={'image':'hero-v4/'+name,'columns':4,'frameWidth':256,'frameHeight':384,'frames':4,'frameIndices':[0,1,2,3],'fps':7 if kind=='walk'else 9,'loop':kind=='walk','perFrameRects':rects,'perFrameOrigins':origins,'alphaBounds':ab,'worldUnitsPerPixel':upp}
 if kind=='attack':action['phaseStarts']=[0,.15,.28,.6]
 result['actions']['walk_W01'if kind=='walk'else'attack_sword_W01']=action
 result['records'][name]={'sourcePNG':str(path.relative_to(ROOT)).replace('\\','/'),'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':im.size,'mode':im.mode,'alphaExtrema':a.getextrema(),'bodyScaleReference':{'bodyHeightPixels':body,'targetProjectedBodyHeightMetres':TARGET,'method':'Median front hair-top to sole; excludes overhead sword by local head search. Existing1.556 projection kept; not1.8 enlargement.'},'landmarks':landmarks,'landmarkMethod':'Head local alpha top with manually located head centre. Shoulder and belt are manual visual band estimates, not automatic anatomical landmarks. Both-feet dense lower support midpoint is alpha measurement. All points are absolute atlas pixels.','limitations':['Candidate source proportions/materials still require user/native review.','Walk has four walking phases and does not supply idle; keep independently approved idle_W01.','Attack may cross original256px columns into empty gaps; perFrameRects includes full long blade without adjacent bodies.']}
(HERE/'metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actions':{k:{'image':v['image'],'size':[1024,1536],'frames':v['frames'],'UPP':v['worldUnitsPerPixel']}for k,v in result['actions'].items()},'records':{k:v['bodyScaleReference']for k,v in result['records'].items()}},ensure_ascii=False))
