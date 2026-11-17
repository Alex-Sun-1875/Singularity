"""Package four colour treatments rendered on each identical native 3D frame."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,json,os
import av,numpy as np
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-aura-v8-palettes'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
PALETTES=json.loads((BASE/'palette-candidates.json').read_text(encoding='utf8'))['palettes']
SHOTS={'WAR_01':('断空斩',72,16),'WAR_03':('铁誓壁垒',108,16)}
ACCENTS={'A':'#c4d9e7','B':'#ed9179','C':'#dcc28b','D':'#c9aceb'}
CROP=(245,25,740,405)
@lru_cache(maxsize=16)
def font(size,bold=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,s,size=24,fill='#e9e7df',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def report(shot):return json.loads((CACHE/'final/design'/shot/'capture.json').read_text(encoding='utf8'))
def verify():
 for shot,(_,count,peak) in SHOTS.items():
  data=report(shot);assert data['frames']==count and not data['errors'] and data['info']['player']['skeletons']
  pictures=[]
  for key in PALETTES:
   directory=CACHE/'frames'/key/shot
   assert len(list(directory.glob('[0-9][0-9][0-9].jpg')))==count,(key,shot)
   with Image.open(directory/f'{peak:03d}.png') as im:pictures.append(np.asarray(im.convert('RGB')))
  for image in pictures[1:]:
   assert np.array_equal(pictures[0][:,:210],image[:,:210]),'Background changed between palette draws'
 if not report('WAR_03')['events']:raise ValueError('No real shield events')

def panel(key,shot,index,still=False):
 out=Image.new('RGB',(720,624),'#171c20');d=ImageDraw.Draw(out)
 text(d,(18,24),key+'  '+PALETTES[key]['name'],26,ACCENTS[key],True)
 text(d,(18,604),PALETTES[key]['detail'],20,'#c0c4c5')
 directory=CACHE/'frames'/key/shot
 source=directory/(f'{index:03d}.png' if still and (directory/f'{index:03d}.png').exists() else f'{index:03d}.jpg')
 with Image.open(source) as im:
  image=im.convert('RGB').crop(CROP).resize((704,540),Image.Resampling.LANCZOS)
  out.paste(image,(8,44))
 return out

def frame(shot,index,still=False):
 out=Image.new('RGB',(1440,1320),'#171c20');d=ImageDraw.Draw(out)
 text(d,(24,28),'战士配色候选 / '+SHOTS[shot][0],28,'#ece8df',True)
 text(d,(1416,29),'同帧 · 同动作 · 同镜头',19,'#b6c0c6',anchor='rm')
 for j,key in enumerate(PALETTES):out.paste(panel(key,shot,index,still),(j%2*720,62+j//2*624))
 return out

def video():
 with av.open(str(OUT/'palette-comparison.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=30);stream.width,stream.height=1440,1320;stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
  index=0
  for shot,(_,count,_) in SHOTS.items():
   for local in range(count):
    f=av.VideoFrame.from_image(frame(shot,local));f.pts=index;f.time_base=Fraction(1,30)
    for packet in stream.encode(f):movie.mux(packet)
    index+=1
  for packet in stream.encode():movie.mux(packet)

def gif(shot,filename,key=None):
 count=SHOTS[shot][1];poster=SHOTS[shot][2]//2
 indices=list(range(0,count,2))
 pictures=[(panel(key,shot,i) if key else frame(shot,i)).resize((648,562) if key else (1008,924),Image.Resampling.LANCZOS) for i in indices]
 durations=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(len(pictures))]
 pictures=pictures[poster:]+pictures[:poster];durations=durations[poster:]+durations[:poster]
 sampler=Image.new('RGB',(504,450*3))
 for row,i in enumerate([0,len(pictures)//3,len(pictures)*2//3]):sampler.paste(pictures[i].resize((504,450)),(0,row*450))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/filename,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,transparency=255,disposal=1)

def stills():
 for shot,(_,_,peak) in SHOTS.items():
  frame(shot,peak,True).save(OUT/('palette-attack.jpg' if shot=='WAR_01' else 'palette-guard.jpg'),quality=96,subsampling=0)
  for key in PALETTES:panel(key,shot,peak,True).save(OUT/(key+'-'+shot.lower()+'.jpg'),quality=96,subsampling=0)

def proof():
 media=[]
 with av.open(str(OUT/'palette-comparison.mp4')) as movie:
  stream=movie.streams.video[0];count=sum(1 for _ in movie.decode(stream));assert count==180 and stream.average_rate==30
  media.append({'file':'palette-comparison.mp4','frames':count,'fps':30,'seconds':float(stream.duration*stream.time_base)})
 for p in OUT.glob('palette-*.gif'):
  im=Image.open(p);duration=0
  for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
  assert duration in [2400,3600],p.name
  media.append({'file':p.name,'frames':im.n_frames,'milliseconds':duration})
 data={'status':'Four pale sword-qi colour candidates awaiting user choice','basis':'Latest user direction: pale sword qi shaped as propagating pressure waves, with an opaque luminous wavefront and dispersing wake.',
  'method':'Advance native simulation once per frame, then swap only cached blade/guard textures and render all four palettes at dt=0.',
  'verified':'Same native skeleton, actor pose, targets and camera. Untouched background pixels match exactly between all four PNG peak captures.',
  'gameHash':report('WAR_01')['gameHash'],'palettes':PALETTES,'shots':{s:{'frames':report(s)['frames'],'overlapFrames':report(s)['overlapFrames'],'events':report(s)['events']} for s in SHOTS},
  'media':media,'productionIntegration':False,'artReview':'Pending user selection'}
 data['files']={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*') if p.is_file() and p.name not in {'provenance.json','palette-provenance.json'} and '__pycache__' not in str(p)}
 (BASE/'palette-provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(media,ensure_ascii=False))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stills','video','gifs','verify']);args=parser.parse_args();verify()
 if args.mode=='stills':stills()
 elif args.mode=='video':video()
 elif args.mode=='gifs':
  gif('WAR_01','palette-comparison.gif');gif('WAR_03','palette-guard.gif')
  for key in PALETTES:gif('WAR_01','palette-'+key+'.gif',key)
 else:proof()
