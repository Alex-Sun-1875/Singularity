"""Read actual 30fps samples; report support separately from visible ignition."""
from pathlib import Path
import json, math, shutil
from PIL import Image, ImageDraw, ImageOps

REQUESTED_AGES=[0,.033,.066,.1,.15,.2,.3,.45,.65]
SUPPORT_FIELDS=('footprintRadius','supportWidth','supportDepth','geometryScale')
FRONT_FIELDS=('frontRadius','ignitionProgress')


def evidence(shot):
 impact=next(event['time'] for event in shot['events'] if event['type']=='skill_segment' and event.get('skillId')=='FIR_02' and event.get('segment')==0)
 samples=[]
 for metric in shot['metrics']:
  age=metric['time']-impact
  if age < -1e-8 or age > .65+1e-8:continue
  active=[item for item in metric['fire'].get('impact',{}).get('active',[]) if item.get('kind')=='meteor']
  samples.append({'frame':metric['frame'],'actualImpactAge':age,'nativeTime':metric['time'],
   'model':metric['fire'].get('impact',{}).get('model'),'active':active,
   'worldBoundsWidthIsNotSupport':[{key:item.get(key) for key in ('key','width','height','vertices')} for item in active]})
 assert samples and all(len(sample['active'])==1 for sample in samples),'Expected one actual registered meteor surface in every early sample'
 points=[]
 for requested in REQUESTED_AGES:
  point=min(samples,key=lambda sample:abs(sample['actualImpactAge']-requested))
  points.append({'slug':f'ignition-{round(requested*1000):04}ms','requestedImpactAge':requested,**point})
 missing=sorted({field for field in (*SUPPORT_FIELDS,*FRONT_FIELDS) if any(not isinstance(sample['active'][0].get(field),(int,float)) for sample in samples)})
 diagnostics={}
 for field in (*SUPPORT_FIELDS,*FRONT_FIELDS):
  values=[sample['active'][0][field] for sample in samples if isinstance(sample['active'][0].get(field),(int,float))]
  diagnostics[field]={'minimum':min(values),'maximum':max(values),'span':max(values)-min(values),
   'constantWithin1e-6':max(values)-min(values)<1e-6,
   'nondecreasingWithin1e-6':all(b+1e-6>=a for a,b in zip(values,values[1:]))} if values else None
 duplicate={str(point['frame']):[p['requestedImpactAge'] for p in points if p['frame']==point['frame']] for point in points}
 return {'requestedImpactAges':REQUESTED_AGES,'requestedStages':points,'actualConsecutiveFrames':samples,
  'actualFrameRange':[samples[0]['frame'],samples[-1]['frame']],'actualFrameCount':len(samples),
  'requestedAgesSharingAnActualFrame':{frame:ages for frame,ages in duplicate.items() if len(ages)>1},
  'missingInspectFields':missing,'reportedDiagnostics':diagnostics,
  'samplingQualification':'Nearest real exported 30fps frame. Requested ages may share a frame; actual ages remain authoritative. No interpolated frames or timing changes.',
  'geometryQualification':'Explicit supportWidth/supportDepth/footprintRadius describe the fixed carrier; width is a world-bounds measurement and is not substituted for support. Inspector constants alone do not prove visible ignition propagation or art acceptance.'}


def render(review,cache,media,label):
 def raw(frame):return Image.open(cache/f'{frame:03}.jpg').convert('RGB')
 # A single fixed native ROI is used in all tiles; no per-frame recentering,
 # perspective transform, alpha reconstruction, colour adjustment, or effects.
 roi=(0,0,1550,1272)
 review['nativeComparisonRoi']=list(roi)
 for point in review['requestedStages']:
  shutil.copyfile(cache/f'{point["frame"]:03}.jpg',media/f'{point["slug"]}.jpg')
 board=Image.new('RGB',(1800,1440),'#1d1916');draw=ImageDraw.Draw(board)
 for index,point in enumerate(review['requestedStages']):
  x=index%3*600;y=index//3*480
  label(draw,(x+14,y+10),f"请求 {point['requestedImpactAge']:.3f}s / 实际 {point['actualImpactAge']:.4f}s",20)
  label(draw,(x+14,y+40),f"F{point['frame']} · 原镜头实景局部",17,color='#cfc3b5')
  image=ImageOps.contain(raw(point['frame']).crop(roi),(570,390),Image.Resampling.LANCZOS)
  board.paste(image,(x+15,y+78+(390-image.height)//2))
 board.save(media/'ignition-requested-stages.jpg',quality=95,subsampling=0)
 count=len(review['actualConsecutiveFrames']);sheet=Image.new('RGB',(1920,math.ceil(count/5)*354),'#1d1916');draw=ImageDraw.Draw(sheet)
 for index,point in enumerate(review['actualConsecutiveFrames']):
  x=index%5*384;y=index//5*354
  label(draw,(x+8,y+8),f"F{point['frame']} · {point['actualImpactAge']:.4f}s",18)
  image=ImageOps.contain(raw(point['frame']).crop(roi),(374,307),Image.Resampling.LANCZOS)
  sheet.paste(image,(x+5,y+42))
 sheet.save(media/'ignition-every-frame.jpg',quality=95,subsampling=0)
 (media/'ignition-inspect-series.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def render_before_after(review,before,before_cache,cache,media,label):
 board=Image.new('RGB',(1800,2250),'#1d1916');draw=ImageDraw.Draw(board)
 for index,(old,new) in enumerate(zip(before['requestedStages'],review['requestedStages'])):
  x=index%3*600;y=index//3*750
  label(draw,(x+14,y+10),f"请求 {new['requestedImpactAge']:.3f}s · 两段原镜头实景局部",19)
  for offset,title,point,directory in [(40,'v33 · 修改前',old,before_cache),(390,'v34 · 当前',new,cache)]:
   label(draw,(x+14,y+offset),f"{title} · F{point['frame']} / {point['actualImpactAge']:.4f}s",18)
   image=Image.open(directory/f"{point['frame']:03}.jpg").convert('RGB').crop((0,0,1550,1272))
   image=ImageOps.contain(image,(560,305),Image.Resampling.LANCZOS)
   board.paste(image,(x+20+(560-image.width)//2,y+offset+32))
 board.save(media/'ignition-before-vs-after.jpg',quality=95,subsampling=0)
