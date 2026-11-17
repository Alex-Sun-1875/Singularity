"""Deliver the native warrior shockwave study and inspect the exported animation."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,json,os
import av
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-silvercyan-v10/final/design'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SHOTS={
 'BASIC_WAR':('普攻三连','气浪随挥剑交错推进，末段以加厚波前收尾。',16),
 'WAR_01':('断空斩','两道气浪前后推进，在目标处形成收紧的交叉。',18),
 'WAR_02':('破军突袭','风痕跟随实际突进路径，抵达后爆出交叉冲击波。',22),
 'WAR_03':('铁誓壁垒','三道剑气聚成护身气幕，受击时局部压缩亮起。',16),
 'WAR_04':('裂地审判','竖向重压气浪落下，触地后推出低位冲击。',27),
 'WAR_05':('破晓裁决','三段气浪逐次加强，末段以厚重的交错波前终结。',38),
 'WAR_P1':('战艺精通','技能实际命中后，持剑处短促浮现一段剑气。',16),
 'WAR_P2':('铁誓不屈','护盾受到实际攻击时，身前气幕短促加亮。',82),
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
  if shot in ['WAR_01','WAR_02','WAR_04','WAR_05']:assert data['overlapFrames'],shot

def frame(shot,index,detail=False,slow=False):
 out=Image.new('RGB',(960,694) if detail else (1280,720),'#171d22');d=ImageDraw.Draw(out)
 name,hint,_=SHOTS[shot]
 text(d,(20,27),'战士 / '+name,28,'#d9e7f0',True)
 text(d,(out.width-20,27),'银青剑气 · 半透明设计动画',18,'#aebfca',anchor='rm')
 with Image.open(CACHE/shot/f'{index:03d}.jpg') as im:
  if detail:picture=im.convert('RGB').crop((245,25,740,405)).resize((768,590),Image.Resampling.LANCZOS);out.paste(picture,(96,50))
  else:out.paste(im.convert('RGB').resize((1280,626),Image.Resampling.LANCZOS),(0,52))
 if detail:
  text(d,(20,670),'银青半透明 / 波身加厚 / 40°交错',17)
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

def gif(shot,slow=False,detail=False):
 count=report(shot)['frames'];step=1 if slow else 2;rate=15 if slow else 30
 indices=list(range(0,count,step));peak=SHOTS[shot][2];poster=min(range(len(indices)),key=lambda i:abs(indices[i]-peak))
 pictures=[frame(shot,i,detail,slow).resize((768,555) if detail else (768,432),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 pictures=pictures[poster:]+pictures[:poster];duration=duration[poster:]+duration[:poster]
 sampler=Image.new('RGB',(384,260*3))
 for row,i in enumerate([0,len(pictures)//3,len(pictures)*2//3]):sampler.paste(pictures[i].resize((384,260)),(0,row*260))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 name='shockwave-detail.gif' if detail else shot.lower()+'.gif'
 indexed[0].save(OUT/name,save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)

def stills():
 out=Image.new('RGB',(1440,1960),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,28),'战士整套技能 · 银青冲击波剑气',31,'#d9e7f0',True)
 for cell,shot in enumerate(SHOTS):
  col,row=cell%2,cell//2;x=col*720;y=62+row*472
  peak=SHOTS[shot][2]
  if shot=='WAR_P2':
   trigger=next(e for e in report(shot)['events'] if e['type']=='skill_status' and e.get('skill')=='WAR_P2');peak=min(report(shot)['frames']-1,round(trigger['time']*30)+1)
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
  elif path.stem.upper() in SHOTS:assert abs(duration-report(path.stem.upper())['frames']/30*1000)<11,path.name
  media.append({'file':path.name,'frames':im.n_frames,'milliseconds':duration})
 data={'status':'Silver-cyan translucent design animation awaiting user review','latestDirection':'Silver-cyan semi-transparent pressure waves. Increase wave thickness to 1.65x, propagation depth to 1.22x and tighten the crossing acute angle to 40 degrees.',
  'source':'Native Cocos 3D actors and actual skill events. Reused historical cloud image_gen flow artwork with deterministic local silver-cyan processing; no new generation in this revision.',
  'video':{'frames':count,'fps':30,'seconds':seconds},'gifs':media,'gameHash':report('WAR_01')['gameHash'],
  'shots':{s:{'name':SHOTS[s][0],'frames':report(s)['frames'],'overlapFrames':report(s)['overlapFrames'],'events':report(s)['events'],'clips':report(s)['clips'],'reviewInputs':report(s)['reviewInputs']} for s in SHOTS},
  'opacityPolicy':{'waveLayerPeak':.55,'barrierAdditionalGain':.65,'state':'All wavefronts remain semi-transparent, with additional body and wake feathering.'},
  'geometryRevision':{'crossAcuteAngleDegrees':40,'thicknessScale':1.65,'depthScale':1.22},
  'productionIntegration':False,'platformPerformance':'TapTap device performance not assessed'}
 data['files']={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*') if p.is_file() and p.name not in {'provenance.json','palette-provenance.json'} and '__pycache__' not in str(p)}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(data['video']))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['video','gifs','stills','verify','sample']);args=parser.parse_args();verify(['WAR_01'] if args.mode=='sample' else SHOTS)
 if args.mode=='video':video()
 elif args.mode=='gifs':
  for shot in SHOTS:gif(shot)
  gif('WAR_01',True,True)
 elif args.mode=='stills':stills()
 elif args.mode=='sample':gif('WAR_01',True,True)
 else:proof()
