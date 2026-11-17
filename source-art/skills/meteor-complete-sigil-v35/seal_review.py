"""Observe the actual meteor seal after impact; flame visibility is separate."""
import json, shutil
from PIL import Image, ImageDraw, ImageOps

AGES=[.25,.65,1.2,1.6,2.2,2.8,3.5,4.3,4.62]


def evidence(shot):
 impact=next(event['time'] for event in shot['events'] if event['type']=='skill_segment' and event.get('skillId')=='FIR_02' and event.get('segment')==0)
 def sample(metric):
  seals=[surface for surface in metric['ground']['active'] if surface.get('kind')=='meteorSeal']
  return {'frame':metric['frame'],'nativeTime':metric['time'],'actualImpactAge':metric['time']-impact,'meteorSeals':seals,
   'present':bool(seals),'reportedOpacities':[surface.get('opacity') for surface in seals]}
 metrics=[metric for metric in shot['metrics'] if metric['time']>=impact-1e-8]
 points=[{'slug':f'seal-held-{round(age*1000):04}ms','requestedImpactAge':age,**sample(min(metrics,key=lambda metric:abs(metric['time']-impact-age)))} for age in AGES]
 consecutive=[sample(metric) for metric in metrics if metric['time']-impact<=4.62+1e-8]
 missing=[point['frame'] for point in consecutive if point['present'] and any(not isinstance(alpha,(int,float)) for alpha in point['reportedOpacities'])]
 alphas=[max(point['reportedOpacities']) for point in consecutive if point['present'] and all(isinstance(alpha,(int,float)) for alpha in point['reportedOpacities'])]
 return {'requestedImpactAges':AGES,'representativeStages':points,'actualConsecutiveFrames':consecutive,
  'missingOpacityFrames':missing,'reportedPresentThrough4p3':all(point['present'] for point in points if point['requestedImpactAge']<=4.3),
  'reportedClearedAt4p62':not points[-1]['present'],'reportedOpacityNonincreasing':all(b<=a+1e-6 for a,b in zip(alphas,alphas[1:])),
  'qualification':'Ground meteorSeal records and their actual opacity are checked independently of fire/impact records. Native images still establish visible carving clarity, rear completeness and gradual fading; inspector alpha alone is not art acceptance.'}


def render(review,cache,media,label,crop):
 board=Image.new('RGB',(1800,1440),'#1d1916');draw=ImageDraw.Draw(board)
 for index,point in enumerate(review['representativeStages']):
  shutil.copyfile(cache/f"{point['frame']:03}.jpg",media/f"{point['slug']}.jpg")
  x=index%3*600;y=index//3*480
  label(draw,(x+14,y+10),f"{point['actualImpactAge']:.4f}s · 落地后法阵",21)
  alpha=', '.join('missing' if value is None else f'{value:.4f}' for value in point['reportedOpacities']) if point['present'] else 'absent'
  label(draw,(x+14,y+40),f"F{point['frame']} · ground.opacity {alpha}",17,color='#cfc3b5')
  image=Image.open(cache/f"{point['frame']:03}.jpg").convert('RGB').crop(crop)
  image=ImageOps.contain(image,(570,390),Image.Resampling.LANCZOS)
  board.paste(image,(x+15,y+78+(390-image.height)//2))
 board.save(media/'seal-after-impact-stages.jpg',quality=95,subsampling=0)
 (media/'seal-after-impact-inspect.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
