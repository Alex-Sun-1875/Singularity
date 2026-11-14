"""Read-only native alpha measurements for color-only candidates; JSON output only."""
from pathlib import Path
from PIL import Image
import json,hashlib,statistics,copy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
base=json.loads((HERE/'metadata.json').read_text(encoding='utf-8'))
result=json.loads((HERE/'metadata-readable.json').read_text(encoding='utf-8'))
SOURCES=HERE/'sources';RUN=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def split_rects(mask):
 rects=[];bbs=[]
 for row in range(4):
  ry=row*384;counts=[sum(mask.getpixel((x,y))>0 for y in range(ry,ry+384))for x in range(1024)];gaps=[];start=None
  for x,n in enumerate(counts):
   if n==0 and start is None:start=x
   if n and start is not None:
    if x-start>=1:gaps.append((start,x))
    start=None
  splits=[0]
  for boundary in [256,512,768]:
   g=min([g for g in gaps if abs((g[0]+g[1])/2-boundary)<140],key=lambda g:abs((g[0]+g[1])/2-boundary));splits.append((g[0]+g[1])//2)
  splits.append(1024)
  for col in range(4):
   left,right=splits[col:col+2];b=mask.crop((left,ry,right,ry+384)).getbbox();x0,y0,x1,y1=left+b[0],ry+b[1],left+b[2],ry+b[3]
   assert x0>0 and x1<1024
   rect=[max(left,x0-2),max(ry,y0-2),0,0];rect[2]=min(right,x1+2)-rect[0];rect[3]=min(ry+384,y1+2)-rect[1]
   rects.append(rect);bbs.append([x0,y0,x1,y1])
 return rects,bbs
def belt_centre(mask,rect,y):
 x0,y0,w,h=rect;centres=[]
 for yy in range(max(y0,y-6),min(y0+h,y+7)):
  segments=[];start=None
  for xx in range(x0,x0+w):
   occupied=mask.getpixel((xx,yy))>0
   if occupied and start is None:start=xx
   if not occupied and start is not None:segments.append((start,xx));start=None
  if start is not None:segments.append((start,x0+w))
  if segments:
   s=max(segments,key=lambda t:t[1]-t[0]);centres.append((s[0]+s[1])/2)
 return statistics.median(centres)
summary={}
for kind,key in [('walk','walk_W01'),('attack','attack_sword_W01')]:
 oldname=f'hero-v4-w01-{kind}.png';newname=f'hero-v4-w01-{kind}-readable.png'
 oldpath=SOURCES/oldname;newpath=SOURCES/newname
 oldim=Image.open(oldpath);newim=Image.open(newpath);assert oldim.size==newim.size==(1024,1536)
 olda=oldim.getchannel('A');newa=newim.getchannel('A');oldmask=olda.point(lambda v:255 if v>32 else 0);newmask=newa.point(lambda v:255 if v>32 else 0)
 oldrects,oldbbs=split_rects(oldmask);newrects,newbbs=split_rects(newmask)
 act=copy.deepcopy(base['actions'][key]);oldorig=act['perFrameOrigins'];act['image']='hero-v4/'+newname;act['perFrameRects']=newrects;act['perFrameOrigins']=[];act['alphaBounds']=[]
 shifts=[];landmarks=[]
 for i,(orr,nrr,obb,nbb,point)in enumerate(zip(oldrects,newrects,oldbbs,newbbs,base['records'][oldname]['landmarks'])):
  y=point['waistBeltMidpointEstimate'][1]
  ox=belt_centre(oldmask,orr,y);nx=belt_centre(newmask,nrr,y)
  dx=nx-ox;dy=nbb[3]-obb[3]
  absOrigin=[base['actions'][key]['perFrameRects'][i][0]+oldorig[i][0]+dx,base['actions'][key]['perFrameRects'][i][1]+oldorig[i][1]+dy]
  origin=[absOrigin[0]-nrr[0],absOrigin[1]-nrr[1]]
  assert 0<=origin[0]<nrr[2] and 0<=origin[1]<nrr[3],(key,i,nrr,origin)
  act['perFrameOrigins'].append(origin);act['alphaBounds'].append([nbb[0]-nrr[0],nbb[1]-nrr[1],nbb[2]-nrr[0],nbb[3]-nrr[1]])
  shifts.append({'frameIndex':i,'waistCoreCentreXBefore':ox,'waistCoreCentreXAfter':nx,'registrationDelta':[dx,dy],'absoluteGroundPoint':absOrigin,'nativeAlphaHeightDelta':(nbb[3]-nbb[1])-(obb[3]-obb[1])})
  lm=copy.deepcopy(point)
  for name in ['headTop','shoulderMidpointEstimate','waistBeltMidpointEstimate','bothFeetMidpoint']:
   lm[name]=[round(lm[name][0]+dx,2),round(lm[name][1]+dy,2)]
  lm['note']='Base manual landmarks transferred by measured local color-edit registration; not a new anatomy measurement.';landmarks.append(lm)
 # Keep body-size target at1.556m using original accepted geometry; no per-phase resizing.
 body=base['records'][oldname]['bodyScaleReference']['bodyHeightPixels'];act['worldUnitsPerPixel']=1.556/body
 act['sourcePNG']=str(newpath.relative_to(ROOT)).replace('\\','/');act['sourcePNGSHA256']=sha(newpath);act['alphaBoundsThreshold']=32
 act['originMethod']='Preserved base pose origin plus measured belt-core X drift and sole-line Y drift; then relative to new complete native rect. No single-boot re-anchoring or image stretch.'
 result['actions'][key]=act
 edge=[{'x':x,'alpha':newa.getpixel((x,1535))}for x in range(1024)if newa.getpixel((x,1535))>32]
 result['records'][newname]={'sourcePNG':act['sourcePNG'],'sourceSHA256':sha(newpath),'inputSourcePNG':str(oldpath.relative_to(ROOT)).replace('\\','/'),'inputSourceSHA256':sha(oldpath),'size':newim.size,'sourceRuntimeSHAEqual':sha(newpath)==sha(RUN/newname),'alphaExtrema':newa.getextrema(),'alphaBlankSamples':[newa.getpixel(q)for q in[(0,0),(1023,0),(0,1535),(1023,1535),(250,50)]],'bodyScaleReference':{'bodyHeightPixels':body,'targetProjectedBodyHeightMetres':1.556,'method':'Original body geometry retained. Only registration changed after local material edit, no per-pose height normalization.'},'registration':shifts,'landmarks':landmarks,'bottomEdgeAlphaOver32':edge,'limitations':['Native engine source-to-ground readability and15-20px face review still required.','Original body/pose geometry was requested unchanged; generative local edits can shift source registration. Measured drift is explicit, not concealed by image processing.']}
 summary[key]={'image':act['image'],'UPP':act['worldUnitsPerPixel'],'maxAbsDx':max(abs(s['registrationDelta'][0])for s in shifts),'maxAbsDy':max(abs(s['registrationDelta'][1])for s in shifts),'bottomEdgeOver32':edge,'sourceRuntimeSHAEqual':sha(newpath)==sha(RUN/newname)}
result['candidate']=True;result['status']='W01 readability-only closed loop; advanced/bow/staff paused; source and metadata frozen pending root engine review'
(HERE/'metadata-readable.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
