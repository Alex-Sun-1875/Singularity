"""Render and verify the isolated native 3D ground-slam redesign."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,json,os
import av
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
CACHE=ROOT/'src/.tmp/warrior-ground-impact-v16/final/design/WAR_04'
BEFORE=ROOT/'src/.tmp/warrior-distinct-kit-v15/final/design/WAR_04'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
CROP=(245,45,750,375)
def read(folder):return json.loads((folder/'capture.json').read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
@lru_cache(maxsize=20)
def font(size,bold=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,s,size=23,fill='#e2e8ed',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def stage(index):
 if index<9:return '起势 · 重劈蓄力'
 if index<21:return '落刀 · 力量压向落点'
 if index<25:return '触地爆发 · 银白气浪与石片掀起'
 if index<33:return '地面撕开 · 断层、飞石与贴地尘浪'
 if index<45:return '尘土散开 · 显露石质裂隙'
 return '余势消散'

def checks():
 a,b=read(BEFORE),read(CACHE)
 result={'sameGameHash':a['gameHash']==b['gameHash'],'sameCombatEvents':a['events']==b['events'],
  'sameTargets':a['info']['targets']==b['info']['targets'],'sameCamera':a['presentation']['camera']==b['presentation']['camera'],
  'sameFrames':a['frames']==b['frames'],'nativeHeavyClip':'attack_sword_3' in b['clips'],
  'noPageErrors':not b['errors'],'noPoolOverflow':not b['style']['droppedLayers']}
 assert all(result.values()),result
 for name,value in b['reviewInputs'].items():assert sha(BASE/name)==value,name
 roles=sorted({r for f in b['roleFrames'] for r in f['roles']})
 required={'rupture-surface','raised-slab','ballistic-debris','slam-edge','ground-pressure','dust-roll','impact-flash'}
 assert required<=set(roles),roles
 ground=b['style']['groundRecord'];assert ground['maxDistance']<=ground['radius'] and ground['maxGroundOffset']<=.046
 target=b['info']['targets'][0];assert abs(target['x']-ground['centre']['x'])+abs(target['z']-ground['centre']['z'])<1e-6
 sample=b['groundSampling'];assert sample['queries']>0 and sample['hits']==sample['queries']
 result.update(roles=roles,ground=ground,groundSampling=sample,maxElements=max(f['elements'] for f in b['roleFrames']))
 return result

def frame(index,detail=False,slow=False):
 out=Image.new('RGB',(1280,720),'#171d22');d=ImageDraw.Draw(out)
 text(d,(20,27),'战士 / 裂地审判 · 重做',28,'#e0e8ef',True)
 text(d,(1260,27),'0.5× 动作细节' if slow else '原速',19,'#b6c6d0',anchor='rm')
 with Image.open(CACHE/f'{index:03d}.jpg') as im:
  if detail:out.paste(im.convert('RGB').crop(CROP).resize((960,626),Image.Resampling.LANCZOS),(160,52))
  else:out.paste(im.convert('RGB').resize((1280,626),Image.Resampling.LANCZOS),(0,52))
 text(d,(20,699),stage(index),21)
 text(d,(1260,699),'设计预览 · 未接入',17,'#aebfca',anchor='rm')
 return out

def movie():
 count=read(CACHE)['frames']
 with av.open(str(OUT/'ground-cleave.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as out:
  out.set_chapters([{'id':0,'time_base':Fraction(1,30),'start':0,'end':count,'metadata':{'title':'原速'}},{'id':1,'time_base':Fraction(1,30),'start':count,'end':count*3,'metadata':{'title':'局部慢放'}}])
  stream=out.add_stream('libx264',rate=30);stream.width,stream.height=1280,720;stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  pts=0
  for detail in [False,True]:
   for i in range(count):
    picture=frame(i,detail,detail)
    for _ in range(2 if detail else 1):
     f=av.VideoFrame.from_image(picture);f.pts=pts;f.time_base=Fraction(1,30);pts+=1
     for p in stream.encode(f):out.mux(p)
  for p in stream.encode():out.mux(p)

def savegif(pictures,durations,path):
 sampler=Image.new('RGB',(480,270*3))
 for row,index in enumerate([0,len(pictures)//3,len(pictures)*2//3]):sampler.paste(pictures[index].resize((480,270)),(0,row*270))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
 indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,transparency=255,disposal=1)

def gifs():
 count=read(CACHE)['frames'];duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(count)]
 pictures=[frame(i,True,True).resize((960,540),Image.Resampling.LANCZOS) for i in range(count)]
 savegif(pictures,duration,OUT/'ground-cleave-detail.gif')
 pictures=[]
 for i in range(count):
  out=Image.new('RGB',(1280,540),'#171d22');d=ImageDraw.Draw(out)
  text(d,(18,25),'裂地审判 · 同帧对照',27,bold=True)
  text(d,(1262,25),'0.5×',18,'#aebfca',anchor='rm')
  for col,(folder,label) in enumerate([(BEFORE,'上一版'),(CACHE,'重做 · 破口 / 石片 / 尘浪')]):
   text(d,(col*640+14,65),label,22,bold=True)
   with Image.open(folder/f'{i:03d}.jpg') as im:out.paste(im.convert('RGB').crop(CROP).resize((632,413),Image.Resampling.LANCZOS),(col*640+4,83))
  text(d,(18,520),'保持当前 3D 角色、镜头与实际命中时机',19)
  pictures.append(out.resize((960,405),Image.Resampling.LANCZOS))
 savegif(pictures,duration,OUT/'ground-cleave-comparison.gif')

def stills():
 out=Image.new('RGB',(1280,950),'#171d22');d=ImageDraw.Draw(out)
 text(d,(20,28),'裂地审判 · 重劈触地与破碎反馈',29,bold=True)
 for cell,index in enumerate([20,22,28,36]):
  x=cell%2*640;y=56+cell//2*442
  with Image.open(CACHE/f'{index:03d}.jpg') as im:out.paste(im.convert('RGB').crop(CROP).resize((632,413),Image.Resampling.LANCZOS),(x+4,y+25))
  text(d,(x+14,y+12),stage(index),20,bold=True)
 text(d,(20,936),'设计动画 · 当前 3D 场景 · 待审',17,'#aebfca')
 out.save(OUT/'ground-cleave-stages.jpg',quality=95,subsampling=0)

def proof():
 result=checks();count=read(CACHE)['frames']
 with av.open(str(OUT/'ground-cleave.mp4')) as movie:
  stream=movie.streams.video[0];decoded=sum(1 for _ in movie.decode(stream));assert decoded==count*3 and stream.average_rate==30
  video={'frames':decoded,'fps':30,'seconds':float(stream.duration*stream.time_base),'size':[stream.width,stream.height]}
 gifs=[]
 for path in OUT.glob('*.gif'):
  im=Image.open(path);duration=0
  for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
  assert abs(duration-count/15*1000)<11,(path.name,duration)
  gifs.append({'file':path.name,'frames':im.n_frames,'milliseconds':duration,'size':list(im.size)})
 data={'status':'Generated texture inspected and native animation visually reviewed; user art acceptance pending','productionIntegration':False,
  'nativeValidation':result,'video':video,'gifs':gifs,'source':'Existing Cocos native actors, heavy sword clip and unchanged skill release/hit events.',
  'assetGeneration':'Built-in cloud OpenAI image_gen for rupture texture; exact prompt in imagegen-prompt.txt. Project Kenney CC0 smoke/light masks reused.',
  'scope':'Only WAR_04 visual design. Fissure and slabs are temporary preview meshes; no gameplay, range, collision or terrain deformation changes.',
  'files':{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file() and p.name!='provenance.json' and '__pycache__' not in str(p)}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'video':video,'gifs':gifs,'checks':result},ensure_ascii=False))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['video','gifs','stills','verify']);args=parser.parse_args();checks()
 if args.mode=='video':movie()
 elif args.mode=='gifs':gifs()
 elif args.mode=='stills':stills()
 else:proof()
