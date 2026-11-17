"""Package actual compiled-game captures; no synthesized game frames."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json, hashlib
import av
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-pressure-wave-v20/training/final'
OUT=BASE/'media'; OUT.mkdir(exist_ok=True)
SHOTS={
 'WAR_01':('断空斩','月牙冲击波 · 流动尾迹 / 局部消散',18),
 'WAR_02':('破军突袭','双月牙冲击 · 尾流先后散开',22),
 'WAR_04':('旋风斩','回旋气浪 · 拖尾拉开后自然消散',25)
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
 count=report(shot)['frames'];rate=15 if slow else 30;step=1
 indices=list(range(0,count,step));pictures=[frame(shot,i).resize((768,443),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 sampler=Image.new('RGB',(384,222*3))
 for row,i in enumerate([8,len(pictures)//2,len(pictures)*2//3]):sampler.paste(pictures[i].resize((384,222)),(0,row*222))
 palette=sampler.quantize(256,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/(shot.lower()+('-slow.gif' if slow else '.gif')),save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,disposal=1)
def stills():
 out=Image.new('RGB',(960,1718),'#171d22');d=ImageDraw.Draw(out)
 label(d,(18,27),'战士月牙冲击波 · 实际深色靶场',30,bold=True)
 for cell,shot in enumerate(SHOTS):
  x=0;y=56+cell*554
  out.paste(frame(shot,SHOTS[shot][2]),(x,y))
 out.save(OUT/'crescent-runtime-overview.jpg',quality=94,subsampling=0)
 frame('WAR_04',25).save(OUT/'whirlwind-runtime.jpg',quality=95,subsampling=0)
def comparison():
 old=CACHE.parents[2]/'warrior-crescent-refinement-v19/training/final'
 # Both recordings use the same default game camera, targets and timestamps.
 with av.open(str(OUT/'before-after.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=30);stream.width,stream.height=1536,466;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
  index=0
  for shot in SHOTS:
   for local in range(report(shot)['frames']):
    out=Image.new('RGB',(1536,466),'#171d22');d=ImageDraw.Draw(out)
    label(d,(16,25),'上版 · '+SHOTS[shot][0],25,bold=True)
    label(d,(784,25),'本版 · 月牙冲击波',25,bold=True)
    for x,p in [(0,old/shot/f'{local:03d}.jpg'),(768,CACHE/shot/f'{local:03d}.jpg')]:
     with Image.open(p) as im:out.paste(im.convert('RGB').resize((768,376),Image.Resampling.LANCZOS),(x,50))
    label(d,(16,446),'相同机位与时刻 / 游戏实录',18)
    label(d,(784,446),'流动波前 / 气流拖尾 / 局部消散',18)
    sample=av.VideoFrame.from_image(out);sample.pts=index;sample.time_base=Fraction(1,30)
    for packet in stream.encode(sample):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)
def tail_stages():
 out=Image.new('RGB',(1920,452),'#171d22');d=ImageDraw.Draw(out)
 label(d,(18,29),'月牙冲击波 · 尾流消散过程（实际连续帧节选）',30,bold=True)
 strike=next(e['time'] for e in report('WAR_02')['events'] if e['type']=='skill_hit')
 for col,index in enumerate([19,22,25,28,31]):
  with Image.open(CACHE/'WAR_02'/f'{index:03d}.jpg') as im:out.paste(im.convert('RGB').crop((330,20,710,330)),(col*384+2,70))
  label(d,(col*384+16,414),f'命中后 {(index+1)/30-strike:.2f} 秒',22)
 out.save(OUT/'tail-dissolve-stages.jpg',quality=95,subsampling=0)
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
 with av.open(str(OUT/'before-after.mp4')) as comparison_movie:
  assert sum(1 for _ in comparison_movie.decode(video=0))==count
 data={'productionIntegration':True,'visualReview':'Inspected actual compiled-game frames, separate from user art acceptance.','gameHash':gamehash,'video':{'frames':count,'fps':30,'seconds':seconds},'gifs':gifs,'shieldChanged':False,'validation':{'typescript':'passed','rules':'unchanged from v19; prior 157 checks passed, not rerun for this rendering revision','web':'actual test build, no module/texture/pose overrides','taptapDevice':'not verified'},'shots':{s:{'name':SHOTS[s][0],'frames':report(s)['frames'],'events':report(s)['events'],'clips':report(s)['clips'],'maxLayers':max(len(m['warrior']['active']) for m in report(s)['metrics'])} for s in SHOTS},'files':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*') if p.is_file()}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(data['video']))
if __name__=='__main__':
 gamehash=verify();video()
 for shot in SHOTS:gif(shot)
 stills();comparison();tail_stages();proof(gamehash)
