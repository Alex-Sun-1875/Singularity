"""Deliver the native warrior shockwave study and inspect the exported animation."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,json,os
import av
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-distinct-kit-v15/final/design'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SHOTS={
 'BASIC_WAR':('普攻三连','短刀光随左右挥砍衔接，第三击向下收刀。',16),
 'WAR_01':('断空斩','两次定向剑气前推，突出纵深与切割感。',18),
 'WAR_02':('破军突袭','风痕跟随实际突进路径，抵达后爆出交叉冲击波。',22),
 'WAR_03':('铁誓壁垒','贴身菱盾保持防御轮廓，受击时银白边缘亮起。',28),
 'WAR_04':('裂地审判','重劈触地，地表裂纹扩开，碎石弹起后回落。',28),
 'WAR_05':('破晓裁决','横扫、上挑、120°交叉终结，三段各有形态。',38),
 'WAR_P1':('战艺精通','技能实际命中后，持剑处闪出短促刃芒。',16),
 'WAR_P2':('铁誓不屈','护盾受到实际攻击时，胸甲前浮现短促银痕。',82),
}
@lru_cache(maxsize=16)
def font(size,bold=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,s,size=23,fill='#e3e6e8',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def report(shot):return json.loads((CACHE/shot/'capture.json').read_text(encoding='utf8'))
def verify(shots=SHOTS):
 for shot in shots:
  data=report(shot);assert not data['errors'] and data['info']['player']['skeletons'],shot
  assert len(list((CACHE/shot).glob('[0-9][0-9][0-9].jpg')))==data['frames'],shot
  if shot in ['WAR_P1','WAR_P2']:assert any(e['type']=='skill_status' and e.get('skill')==shot for e in data['events']),shot
  if shot in ['WAR_02','WAR_05']:assert data['crossGeometrySamples'],shot
  assert not data['style']['droppedLayers'],shot
  roles={r for sample in data['roleFrames'] for r in sample['roles']}
  expected={'BASIC_WAR':'basic-trail','WAR_01':'focused-cut','WAR_02':'rush-streak','WAR_03':'shield-outline','WAR_04':'ground-crack','WAR_05':'finisher-rise','WAR_P1':'blade-glint','WAR_P2':'armour-pulse'}
  assert expected[shot] in roles,(shot,roles)

def frame(shot,index,detail=False,slow=False):
 out=Image.new('RGB',(960,694) if detail else (1280,720),'#171d22');d=ImageDraw.Draw(out)
 name,hint,_=SHOTS[shot]
 text(d,(20,27),'战士 / '+name,28,'#d9e7f0',True)
 text(d,(out.width-20,27),'技能分化 · 银白质感',18,'#aebfca',anchor='rm')
 with Image.open(CACHE/shot/f'{index:03d}.jpg') as im:
  if detail:picture=im.convert('RGB').crop((245,25,740,405)).resize((768,590),Image.Resampling.LANCZOS);out.paste(picture,(96,50))
  else:out.paste(im.convert('RGB').resize((1280,626),Image.Resampling.LANCZOS),(0,52))
 if detail:
  text(d,(20,670),'裂纹沿实际地表展开 / 碎石起落' if shot=='WAR_04' else '银白波前 / 两段定向切割',17)
  text(d,(940,670),'0.5× 动作细节' if slow else '原速',16,'#aebfca',anchor='rm')
 else:
  text(d,(20,698),hint,21)
  text(d,(1260,698),'原速 / 30 fps',16,'#aebfca',anchor='rm')
 return out

def video():
 with av.open(str(OUT/'warrior-all-skills.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  chapters=[];offset=0
  for shot in SHOTS:
   count=report(shot)['frames'];chapters.append({'id':len(chapters),'time_base':Fraction(1,30),'start':offset,'end':offset+count,'metadata':{'title':SHOTS[shot][0]}});offset+=count
  movie.set_chapters(chapters)
  stream=movie.add_stream('libx264',rate=30);stream.width,stream.height=1280,720;stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  index=0
  for shot in SHOTS:
   for local in range(report(shot)['frames']):
    sample=av.VideoFrame.from_image(frame(shot,local));sample.pts=index;sample.time_base=Fraction(1,30)
    for p in stream.encode(sample):movie.mux(p)
    index+=1
  for p in stream.encode():movie.mux(p)

def gif(shot,slow=False,detail=False,output_name=None):
 count=report(shot)['frames'];step=1 if slow else 2;rate=15 if slow else 30
 indices=list(range(0,count,step));peak=SHOTS[shot][2];poster=min(range(len(indices)),key=lambda i:abs(indices[i]-peak))
 pictures=[frame(shot,i,detail,slow).resize((768,555) if detail else (768,432),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 pictures=pictures[poster:]+pictures[:poster];duration=duration[poster:]+duration[:poster]
 sampler=Image.new('RGB',(384,260*3))
 for row,i in enumerate([0,len(pictures)//3,len(pictures)*2//3]):sampler.paste(pictures[i].resize((384,260)),(0,row*260))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 name=output_name or ('shockwave-detail.gif' if detail else shot.lower()+'.gif')
 indexed[0].save(OUT/name,save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)

def stills():
 out=Image.new('RGB',(1440,1960),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,28),'战士整套技能 · 动作与特效分化设计',31,'#d9e7f0',True)
 for cell,shot in enumerate(SHOTS):
  col,row=cell%2,cell//2;x=col*720;y=62+row*472
  peak=SHOTS[shot][2]
  if shot in ['WAR_P1','WAR_P2']:
   trigger=next(e for e in report(shot)['events'] if e['type']=='skill_status' and e.get('skill')==shot);peak=min(report(shot)['frames']-1,round(trigger['time']*30)+1)
  im=frame(shot,peak).resize((704,396),Image.Resampling.LANCZOS);out.paste(im,(x+8,y))
  text(d,(x+20,y+422),SHOTS[shot][0],23,'#d9e7f0',True)
 out.save(OUT/'all-skills-overview.jpg',quality=94,subsampling=0)
 frame('WAR_01',18).save(OUT/'shockwave-peak.jpg',quality=95,subsampling=0)

def proof():
 expected=sum(report(s)['frames'] for s in SHOTS)
 with av.open(str(OUT/'warrior-all-skills.mp4')) as movie:
  stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==expected and stream.average_rate==30
  seconds=float(stream.duration*stream.time_base)
 media=[]
 for path in OUT.glob('*.gif'):
  im=Image.open(path);duration=0
  for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
  if path.name=='shockwave-detail.gif':assert duration==4800,path.name
  elif path.name=='ground-cleave-detail.gif':assert abs(duration-report('WAR_04')['frames']/15*1000)<11,path.name
  elif path.name=='skill-contrast.gif':assert duration==3600,path.name
  elif path.stem.upper() in SHOTS:assert abs(duration-report(path.stem.upper())['frames']/30*1000)<11,path.name
  media.append({'file':path.name,'frames':im.n_frames,'milliseconds':duration})
 data={'status':'Differentiated warrior kit awaiting visual review; accepted silver material retained.','directionAccepted':False,'latestDirection':'Different skills have distinct shapes. Basic short trails; two focused cuts; rush lines and impact cross; kite shield; ground fracture and chips; sweep-rise-cross finisher. Crossings only on rush and finisher.',
  'source':'Native Cocos 3D actors and actual skill events. Existing silver textures reused. New code-native ground fissures, rock chips and shield edges; no image generation in this revision.',
  'video':{'frames':count,'fps':30,'seconds':seconds},'gifs':media,'gameHash':report('WAR_01')['gameHash'],
  'shots':{s:{'name':SHOTS[s][0],'frames':report(s)['frames'],'roles':sorted({r for sample in report(s)['roleFrames'] for r in sample['roles']}),'events':report(s)['events'],'clips':report(s)['clips'],'reviewInputs':report(s)['reviewInputs']} for s in SHOTS},
  'opacityPolicy':{'waveLayerPeak':1,'centralVertexOpacity':1,'coreTextureAlpha':255,'bodyGain':1.8,'state':'Opaque central body, with a soft outline, temporal entrance/exit and fading wake.'},
  'geometryRevision':{'baseMaterial':'warrior-reference120-v14','targetProjectedObtuseAngleDegrees':120,'crossAppliedTo':['WAR_02 impact','WAR_05 final beat'],'groundFracture':report('WAR_04')['style']['groundRecord'],'groundGeometry':'Visual fissure conforms to sampled terrain inside original impact disk. No collision, damage or terrain deformation changes.'},
  'productionIntegration':False,'platformPerformance':'TapTap device performance not assessed'}
 data['files']={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*') if p.is_file() and p.name not in {'provenance.json','palette-provenance.json'} and '__pycache__' not in str(p)}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(data['video']))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['video','gifs','stills','verify','sample']);args=parser.parse_args();verify(['WAR_01'] if args.mode=='sample' else SHOTS)
 if args.mode=='video':video()
 elif args.mode=='gifs':
  for shot in SHOTS:gif(shot)
  gif('WAR_01',True,True)
  gif('WAR_04',True,True,'ground-cleave-detail.gif')
 elif args.mode=='stills':stills()
 elif args.mode=='sample':gif('WAR_01',True,True)
 else:proof()
