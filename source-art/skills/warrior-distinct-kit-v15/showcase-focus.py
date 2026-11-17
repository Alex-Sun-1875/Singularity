"""Present the two passive cues as close-ups of the existing accepted-direction recording."""
from pathlib import Path
import hashlib,json,os
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-distinct-kit-v15/final/design'
OUT=BASE/'media'
FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
def font(size,bold=False):return ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
specs={
 'WAR_P1':{'name':'战艺精通','crop':(295,160,530,395),'before':5,'after':16,'hint':'技能命中后，观察持剑手附近的短促刃芒。'},
 'WAR_P2':{'name':'铁誓不屈','crop':(335,120,570,355),'before':6,'after':14,'hint':'护盾受击后，观察胸甲前的短促银痕。'},
}
records={}
for skill,spec in specs.items():
 report=json.loads((CACHE/skill/'capture.json').read_text(encoding='utf8'))
 event=next(e for e in report['events'] if e['type']=='skill_status' and e.get('skill')==skill)
 trigger=round(event['time']*30)
 start=max(0,trigger-spec['before']);end=min(report['frames']-1,trigger+spec['after'])
 frames=[];duration=[]
 for i,index in enumerate(range(start,end+1)):
  canvas=Image.new('RGB',(768,768),'#171d22');d=ImageDraw.Draw(canvas)
  d.text((20,25),spec['name']+' · 被动触发局部',font=font(24,True),fill='#e1e7ef',anchor='lm')
  d.text((748,25),'触发前' if index<trigger else '触发反馈',font=font(18),fill='#b5c6d2',anchor='rm')
  with Image.open(CACHE/skill/f'{index:03d}.jpg') as im:
   canvas.paste(im.convert('RGB').crop(spec['crop']).resize((672,672),Image.Resampling.LANCZOS),(48,52))
  d.text((20,746),spec['hint'],font=font(17),fill='#d5e0e9',anchor='lm')
  d.text((748,746),'0.5×',font=font(17),fill='#b5c6d2',anchor='rm')
  frames.append(canvas);duration.append((round((i+1)*100/15)-round(i*100/15))*10)
 poster=min(len(frames)-1,trigger+1-start)
 frames=frames[poster:]+frames[:poster];duration=duration[poster:]+duration[:poster]
 sampler=Image.new('RGB',(384,384*3))
 for row,i in enumerate([0,len(frames)//3,len(frames)*2//3]):sampler.paste(frames[i].resize((384,384)),(0,row*384))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 path=OUT/(skill.lower()+'-focus.gif')
 indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)
 gif=Image.open(path);milliseconds=0
 for i in range(gif.n_frames):gif.seek(i);gif.load();milliseconds+=gif.info.get('duration',0)
 assert gif.n_frames==len(frames) and abs(milliseconds-len(frames)/15*1000)<11
 records[skill]={'file':str(path.relative_to(BASE)),'triggerEvent':event,'sourceFrameRange':[start,end],'loopStartSourceFrame':start+poster,'crop':spec['crop'],'frames':gif.n_frames,'milliseconds':milliseconds,
  'operation':'Crop and enlarge existing native frames; label actual passive event time. No changes to effects, poses, gameplay or simulation.',
  'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(BASE/'showcase-focus.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({skill:{'frames':r['frames'],'milliseconds':r['milliseconds']} for skill,r in records.items()}))
