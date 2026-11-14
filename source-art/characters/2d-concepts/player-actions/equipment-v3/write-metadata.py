"""Read alpha masks and emit native-UV crop metadata; never writes image pixels."""
from pathlib import Path
from PIL import Image
import json, hashlib, statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OUT=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
TARGET_HEIGHT=1.5562753036437247

def inspect(path):
 im=Image.open(path); a=im.getchannel('A'); w,h=im.size
 assert w==1536 and h==1024, (path.name,im.size)
 mask=a.point(lambda v:255 if v>32 else 0)
 perrects=[]; origins=[]; alphabounds=[]; absolute=[]; fullbounds=[]
 for row in range(4):
  ry=row*256
  counts=[sum(mask.getpixel((x,y))>0 for y in range(ry,ry+256)) for x in range(w)]
  gaps=[]; start=None
  for x in range(w):
   if counts[x]==0 and start is None:start=x
   if counts[x]>0 and start is not None:
    if x-start>=8:gaps.append((start,x))
    start=None
  splits=[0]
  for col in range(1,4):
   boundary=col*384
   candidates=[p for p in gaps if abs((p[0]+p[1])/2-boundary)<180]
   assert candidates,(path.name,row,boundary)
   gap=min(candidates,key=lambda p:abs((p[0]+p[1])/2-boundary))
   splits.append((gap[0]+gap[1])//2)
  splits.append(w)
  for col in range(4):
   left,right=splits[col:col+2]
   bb=mask.crop((left,ry,right,ry+256)).getbbox()
   assert bb
   bx0,by0,bx1,by1=left+bb[0],ry+bb[1],left+bb[2],ry+bb[3]
   assert 0<bx0<bx1<w,(path.name,row,col,'lost outer sword tip')
   # Two pixel transparent margin where the native source contains it.
   x0=max(left,bx0-2); y0=max(ry,by0-2); x1=min(right,bx1+2); y1=min(ry+256,by1+2)
   crop=[x0,y0,x1-x0,y1-y0]
   lower=max(by0,by1-round((by1-by0)*.28))
   support=[]
   for xx in range(bx0,bx1):
    hits=sum(mask.getpixel((xx,yy))>0 for yy in range(lower,by1))
    if hits>=max(6,round((by1-lower)*.18)):support.append(xx)
   gx=round((support[0]+support[-1])/2) if support else round((bx0+bx1)/2)
   gy=by1-1
   perrects.append(crop); absolute.append([gx,gy]); origins.append([gx-x0,gy-y0])
   alphabounds.append([bx0-x0,by0-y0,bx1-x0,by1-y0]); fullbounds.append([bx0,by0,bx1,by1])
 # Front-row body height excludes side attack sword extents, and retains full head-to-sole.
 bodyheight=statistics.median(bb[3]-bb[1] for bb in fullbounds[:4])
 return {'image':path.name,'columns':4,'frameWidth':384,'frameHeight':256,'directions':['down','right','up','left'],'perFrameRects':perrects,'perFrameOrigins':origins,'alphaBounds':alphabounds,'absoluteGroundPoints':absolute,'alphaBoundsThreshold':32,'worldUnitsPerPixel':TARGET_HEIGHT/bodyheight,'bodyScaleReference':{'bodyHeightPixels':bodyheight,'targetProjectedBodyHeightMetres':TARGET_HEIGHT,'method':'Median front head-to-sole height. Crop-specific origins measured from dense lower 28% alpha support, avoiding thin sword-tip bias.'},'sourcePNG':str(path.relative_to(ROOT)).replace('\\','/'),'sourcePNGSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'originMethod':'perFrameOrigins are relative to perFrameRects, not fixed 384x256 cells. perFrameRects uses original PNG pixels and preserves internal-crossing long tips.','notes':'Only source PNG and metadata delivered; action registration belongs to runtime owner. No pixels were edited or resampled.'}

existing_path=HERE/'metadata.json'
metadata=json.loads(existing_path.read_text(encoding='utf-8')) if existing_path.exists() else {}
for path in sorted(HERE.glob('*.png')):
 current_sha=hashlib.sha256(path.read_bytes()).hexdigest()
 if metadata.get(path.stem,{}).get('sourcePNGSHA256')!=current_sha:
  metadata[path.stem]=inspect(path)
(HERE/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:{'size':[1536,1024],'frames':len(v['perFrameRects']),'bodyHeight':v['bodyScaleReference']['bodyHeightPixels'],'worldUnitsPerPixel':v['worldUnitsPerPixel']} for k,v in metadata.items()},ensure_ascii=False))
