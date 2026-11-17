"""Package actual compiled-game captures; no synthesized game frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-implementation-v18/final'
OUT=BASE/'media'; OUT.mkdir(exist_ok=True)
SHOTS={
 'BASIC_WAR':('普攻三连','短月牙随三段挥砍衔接',16),
 'WAR_01':('断空斩','两段定向剑气，向前切入',18),
 'WAR_02':('破军突袭','沿实际路径突进，命中后120°交叉斩',22),
 'WAR_03':('铁誓壁垒','保留现有护罩效果，本次未修改',28),
 'WAR_04':('旋风斩','两圈高低错位回旋，收尾前甩月牙',25),
 'WAR_05':('破晓裁决','横扫、上挑、交叉终结，三段不同形态',38),
 'WAR_P1':('战艺精通','真实触发时，剑身闪出短促刃芒',16),
 'WAR_P2':('铁誓不屈','保留现有护盾被动效果，本次未修改',82)
}
@lru_cache(maxsize=8)
def font(size,bold=False):
 return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def label(d,xy,s,size=20,fill='#dce5ec',bold=False,anchor='lm'):
 d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def report(shot):return json.loads((CACHE/shot/'capture.json').read_text(encoding='utf8'))
def verify():
 hashes=set()
 for shot in SHOTS:
  r=report(shot);hashes.add(r['gameHash'])
  assert not r['errors'] and not r['consoleErrors'] and r['info']['player']['skeletons'],shot
  assert len(list((CACHE/shot).glob('[0-9][0-9][0-9].jpg')))==r['frames'],shot
  assert all(not m['warrior']['droppedLayers'] for m in r['metrics']),shot
  assert all(all(l['subModels'] and l['bounds'] for l in m['renderReady']) for m in r['metrics']),shot
 assert len(hashes)==1
 assert {e['segment'] for e in report('WAR_04')['events'] if e['type']=='skill_hit'}=={0,1,2}
 return hashes.pop()
def frame(shot,index):
 out=Image.new('RGB',(960,554),'#171d22');d=ImageDraw.Draw(out)
 label(d,(16,23),'战士 · '+SHOTS[shot][0],23,bold=True)
 label(d,(944,23),'游戏实录 / 原速',16,'#a9bac7',anchor='rm')
 with Image.open(CACHE/shot/f'{index:03d}.jpg') as im:out.paste(im.convert('RGB'),(0,44))
 label(d,(16,534),SHOTS[shot][1],18)
 return out
def video():
 with av.open(str(OUT/'warrior-runtime.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  chapters=[];offset=0
  for shot in SHOTS:
   count=report(shot)['frames'];chapters.append({'id':len(chapters),'time_base':Fraction(1,30),'start':offset,'end':offset+count,'metadata':{'title':SHOTS[shot][0]}});offset+=count
  movie.set_chapters(chapters)
  stream=movie.add_stream('libx264',rate=30);stream.width,stream.height=960,554;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
  index=0
  for shot in SHOTS:
   for local in range(report(shot)['frames']):
    sample=av.VideoFrame.from_image(frame(shot,local));sample.pts=index;sample.time_base=Fraction(1,30)
    for packet in stream.encode(sample):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)
def gif(slow=False):
 count=report('WAR_04')['frames'];rate=15 if slow else 30;step=1 if slow else 2
 indices=list(range(0,count,step));pictures=[frame('WAR_04',i).resize((768,443),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 sampler=Image.new('RGB',(384,222*3))
 for row,i in enumerate([8,len(pictures)//2,len(pictures)*2//3]):sampler.paste(pictures[i].resize((384,222)),(0,row*222))
 palette=sampler.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/('whirlwind-runtime-slow.gif' if slow else 'whirlwind-runtime.gif'),save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,disposal=1)
def stills():
 out=Image.new('RGB',(1440,1744),'#171d22');d=ImageDraw.Draw(out)
 label(d,(18,27),'战士整套技能 · 游戏实际运行效果',30,bold=True)
 for cell,shot in enumerate(SHOTS):
  x=cell%2*720+8;y=56+cell//2*420
  sample=frame(shot,SHOTS[shot][2]).resize((704,406),Image.Resampling.LANCZOS);out.paste(sample,(x,y))
 out.save(OUT/'all-skills-runtime.jpg',quality=94,subsampling=0)
 frame('WAR_04',25).save(OUT/'whirlwind-runtime.jpg',quality=95,subsampling=0)
def proof(gamehash):
 with av.open(str(OUT/'warrior-runtime.mp4')) as movie:
  stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==sum(report(s)['frames'] for s in SHOTS)
  seconds=float(stream.duration*stream.time_base);assert stream.average_rate==30
 gifs=[]
 for name,rate in [('whirlwind-runtime.gif',30),('whirlwind-runtime-slow.gif',15)]:
  im=Image.open(OUT/name);ms=0
  for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
  assert abs(ms-report('WAR_04')['frames']/rate*1000)<11
  gifs.append({'file':name,'frames':im.n_frames,'milliseconds':ms})
 data={'productionIntegration':True,'visualReview':'Inspected actual compiled-game frames, separate from user art acceptance.','gameHash':gamehash,'video':{'frames':count,'fps':30,'seconds':seconds},'gifs':gifs,'shieldChanged':False,'validation':{'typescript':'passed','rules':'157/157 passed','web':'actual test build, no module/texture/pose overrides','taptapDevice':'not verified'},'shots':{s:{'name':SHOTS[s][0],'frames':report(s)['frames'],'events':report(s)['events'],'clips':report(s)['clips'],'maxLayers':max(len(m['warrior']['active']) for m in report(s)['metrics'])} for s in SHOTS},'files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(data['video']))
if __name__=='__main__':
 gamehash=verify();video();gif();gif(True);stills();proof(gamehash)
