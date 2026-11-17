"""Deliver the isolated whirlwind skill concept, without gameplay integration."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,json,os
import av
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
CACHE=BASE.parents[2]/'src/.tmp/warrior-whirlwind-v17/final/design/SPIN_WAR'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
CROP=(225,55,740,390)
def report():return json.loads((CACHE/'capture.json').read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
@lru_cache(maxsize=12)
def font(n,bold=False):return ImageFont.truetype(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/('msyhbd.ttc' if bold else 'msyh.ttc')),n)
def text(d,xy,s,size=23,fill='#e2e8ef',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def verify():
 d=report();assert not d['errors'] and d['designOnly'] and not d['style']['droppedLayers']
 assert d['info']['player']['skeletons'] and d['castResult']==['concept_preview']
 assert not any(e['type'] in ['hit','skill_hit','attack','skill_release'] for e in d['events'])
 assert len(d['conceptContacts'])>=3 and len({p['target'] for p in d['conceptContacts']})==3
 assert all(p['sourceClip']=='attack_sword_2' for p in d['poseSamples'])
 turns=[p['turnDegrees'] for p in d['poseSamples']];assert max(turns)>=719 and min(turns)<-25
 roles={r for f in d['roleFrames'] for r in f['roles']};assert {'spin:primary','spin:secondary','spin:finisher'}<=roles
 assert not any('ground-crack' in r or 'cleave:' in r for r in roles)
 for name,value in d['reviewInputs'].items():assert sha(BASE/name)==value,name
 return {'nativeSkeleton':True,'sourceClip':'attack_sword_2','rootTurnDegrees':[min(turns),max(turns)],'authoredVisualContacts':len(d['conceptContacts']),'noGameplaySkillCastOrDamage':True,'roles':sorted(roles),'maxElements':max(f['elements'] for f in d['roleFrames'])}

def frame(index,detail=False,slow=False):
 out=Image.new('RGB',(1280,720),'#171d22');d=ImageDraw.Draw(out)
 text(d,(20,27),'战士 / 旋风斩 · 替代方案',28,bold=True)
 text(d,(1260,27),'0.5× 动作细节' if slow else '原速',19,'#b4c5d0',anchor='rm')
 with Image.open(CACHE/f'{index:03d}.jpg') as im:
  if detail:out.paste(im.convert('RGB').crop(CROP).resize((960,626),Image.Resampling.LANCZOS),(160,52))
  else:out.paste(im.convert('RGB').resize((1280,626),Image.Resampling.LANCZOS),(0,52))
 hint='短蓄力 · 回身起刀' if index<15 else '连续回旋 · 高低两道月牙刀气' if index<44 else '收尾甩斩 · 刀气向前释放' if index<54 else '收刀复位'
 text(d,(20,699),hint,21)
 text(d,(1260,699),'概念动画 · 未接入',17,'#aebfca',anchor='rm')
 return out

def movie():
 count=report()['frames']
 with av.open(str(OUT/'whirlwind-skill.mp4'),'w',format='mp4',options={'movflags':'+faststart'}) as out:
  out.set_chapters([{'id':0,'time_base':Fraction(1,30),'start':0,'end':count,'metadata':{'title':'原速'}},{'id':1,'time_base':Fraction(1,30),'start':count,'end':count*3,'metadata':{'title':'动作慢放'}}])
  stream=out.add_stream('libx264',rate=30);stream.width,stream.height=1280,720;stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  pts=0
  for detail in [False,True]:
   for i in range(count):
    picture=frame(i,detail,detail)
    for _ in range(2 if detail else 1):
     f=av.VideoFrame.from_image(picture);f.pts=pts;f.time_base=Fraction(1,30);pts+=1
     for p in stream.encode(f):out.mux(p)
  for p in stream.encode():out.mux(p)

def gif(slow=False):
 count=report()['frames'];step=1;rate=15 if slow else 30;indices=range(0,count,step)
 pictures=[frame(i,slow,slow).resize((960,540),Image.Resampling.LANCZOS) for i in indices]
 duration=[(round(min(i+step,count)*100/rate)-round(i*100/rate))*10 for i in indices]
 sampler=Image.new('RGB',(480,810))
 for row,index in enumerate([0,len(pictures)//3,len(pictures)*2//3]):sampler.paste(pictures[index].resize((480,270)),(0,row*270))
 palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT);indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in pictures]
 indexed[0].save(OUT/('whirlwind-detail.gif' if slow else 'whirlwind-skill.gif'),save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)

def stills():
 out=Image.new('RGB',(1280,940),'#171d22');d=ImageDraw.Draw(out);text(d,(20,28),'旋风斩 · 回旋与收尾动作',29,bold=True)
 for cell,index in enumerate([17,24,34,48]):
  x=cell%2*640;y=55+cell//2*438
  with Image.open(CACHE/f'{index:03d}.jpg') as im:out.paste(im.convert('RGB').crop(CROP).resize((632,411),Image.Resampling.LANCZOS),(x+4,y+25))
  text(d,(x+14,y+12),['起刀回旋','月牙交错','第二圈扫击','收尾甩斩'][cell],20,bold=True)
 out.save(OUT/'whirlwind-stages.jpg',quality=95,subsampling=0)

def proof():
 check=verify();count=report()['frames'];gifs=[]
 with av.open(str(OUT/'whirlwind-skill.mp4')) as movie:
  stream=movie.streams.video[0];frames=sum(1 for _ in movie.decode(stream));assert frames==count*3 and stream.average_rate==30
  video={'frames':frames,'fps':30,'seconds':float(stream.duration*stream.time_base)}
 for path in OUT.glob('*.gif'):
  im=Image.open(path);duration=0
  for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
  expected=count/(15 if 'detail' in path.name else 30)*1000;assert abs(duration-expected)<11
  gifs.append({'file':path.name,'frames':im.n_frames,'milliseconds':duration})
 data={'status':'Concept rendered and media checked; awaiting user art review','proposedSkill':'旋风斩, replacing the rejected WAR_04 ground-slam direction','productionIntegration':False,'gameplayImplemented':False,
  'source':'Existing native Cocos character, authored attack_sword_2 skeleton poses with design root rotation. Enemy recoil and silver contact flashes are authored concept cues, not gameplay damage events. New native curved crescent mesh; no new image generation.',
  'checks':check,'video':video,'gifs':gifs,'files':{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file() and p.name!='provenance.json' and '__pycache__' not in str(p)}}
 (BASE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'checks':check,'video':video,'gifs':gifs},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['video','gifs','stills','verify']);mode=p.parse_args().mode;verify()
 if mode=='video':movie()
 elif mode=='gifs':gif();gif(True)
 elif mode=='stills':stills()
 else:proof()
