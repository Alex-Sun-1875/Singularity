"""Compare true same-frame flame and sigil appearance without recolouring."""
import shutil
from PIL import Image,ImageDraw,ImageOps

AGES=[.65,2.8,3.5]


def evidence(shot,before):
 def select(record,age):
  impact=next(event['time'] for event in record['events'] if event['type']=='skill_segment' and event.get('skillId')=='FIR_02' and event.get('segment')==0)
  metric=min(record['metrics'],key=lambda metric:abs(metric['time']-impact-age))
  return {'frame':metric['frame'],'actualImpactAge':metric['time']-impact,'groundInspect':metric['ground'],'impactInspect':metric['fire'].get('impact',{})}
 return {'stages':[{'requestedImpactAge':age,'before':select(before,age),'after':select(shot,age)} for age in AGES],
  'qualification':'Each actual native frame contains the central flame and sigil. Compare the faint orange interior fill and visible ground through the more translucent sigil. Texture alpha is intentionally allowed to change; renderer draw opacity is separate. Only fixed cropping/uniform resizing is used, with no exact pixel-colour match claim.'}


def render(review,cache,before_cache,media,label,crop):
 board=Image.new('RGB',(1600,len(review['stages'])*750),'#1d1916');draw=ImageDraw.Draw(board)
 for row,point in enumerate(review['stages']):
  age=point['requestedImpactAge'];after=point['after'];shutil.copyfile(cache/f"{after['frame']:03}.jpg",media/f'colour-match-{round(age*1000):04}ms.jpg')
  for x,title,metric,directory in [(0,'v36 · 原生修改前',point['before'],before_cache),(800,'v37 · 原生填色/透明调整后',after,cache)]:
   label(draw,(x+16,row*750+10),f"{title} · 实际{metric['actualImpactAge']:.4f}s / F{metric['frame']}",20)
   label(draw,(x+16,row*750+40),'同一帧法阵 + 中央火焰 · 原镜头/原颜色',17,color='#cfc3b5')
   image=Image.open(directory/f"{metric['frame']:03}.jpg").convert('RGB').crop(crop)
   image=ImageOps.contain(image,(760,660),Image.Resampling.LANCZOS);board.paste(image,(x+20,row*750+80+(660-image.height)//2))
 board.save(media/'sigil-flame-v36-vs-v37-native.jpg',quality=95,subsampling=0)
