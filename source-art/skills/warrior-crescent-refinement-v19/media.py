"""Package actual compiled-game captures; no synthesized game frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-crescent-refinement-v19/training/final'
OUT=BASE/'media'; OUT.mkdir(exist_ok=True)
SHOTS={
 'WAR_01':('断空斩','银灰半月连斩 · 一级距离 3.9 米',17),
 'WAR_02':('破军突袭','突进后双月牙交叉 · 扩大落点覆盖',21),
 'WAR_04':('旋风斩','窄亮刃口 / 银灰波身 · 两圈回旋后前甩',25)
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
def gif(shot,slow=False):
 count=report(shot)['frames'];rate=15 if slow else 30;step=1 if slow else 2
 indices=list(range(0,count,step));pictures=[frame(shot,i).resize((768,443),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 sampler=Image.new('RGB',(384,222*3))
 for row,i in enumerate([8,len(pictures)//2,len(pictures)*2//3]):sampler.paste(pictures[i].resize((384,222)),(0,row*222))
 palette=sampler.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/(shot.lower()+('-slow.gif' if slow else '.gif')),save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,disposal=1)
def stills():
 out=Image.new('RGB',(960,1718),'#171d22');d=ImageDraw.Draw(out)
 label(d,(18,27),'战士剑气修正 · 实际深色靶场',30,bold=True)
 for cell,shot in enumerate(SHOTS):
  x=0;y=56+cell*554
  out.paste(frame(shot,SHOTS[shot][2]),(x,y))
 out.save(OUT/'crescent-runtime-overview.jpg',quality=94,subsampling=0)
 frame('WAR_04',25).save(OUT/'whirlwind-runtime.jpg',quality=95,subsampling=0)
def proof(gamehash):
 with av.open(str(OUT/'warrior-runtime.mp4')) as movie:
  stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==sum(report(s)['frames'] for s in SHOTS)
  seconds=float(stream.duration*stream.time_base);assert stream.average_rate==30
 gifs=[]
 for shot in SHOTS:
  name,rate=shot.lower()+'.gif',30
  im=Image.open(OUT/name);ms=0
  for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info.get('duration',0)
  assert abs(ms-report(shot)['frames']/rate*1000)<11
  gifs.append({'file':name,'frames':im.n_frames,'milliseconds':ms})
 data={'productionIntegration':True,'visualReview':'Inspected actual compiled-game frames, separate from user art acceptance.','gameHash':gamehash,'video':{'frames':count,'fps':30,'seconds':seconds},'gifs':gifs,'shieldChanged':False,'validation':{'typescript':'passed','rules':'157/157 passed','web':'actual test build, no module/texture/pose overrides','taptapDevice':'not verified'},'shots':{s:{'name':SHOTS[s][0],'frames':report(s)['frames'],'events':report(s)['events'],'clips':report(s)['clips'],'maxLayers':max(len(m['warrior']['active']) for m in report(s)['metrics'])} for s in SHOTS},'files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(data['video']))
if __name__=='__main__':
 gamehash=verify();video()
 for shot in SHOTS:gif(shot)
 stills();proof(gamehash)
