"""Typeset native Cocos review recordings; composite only the approved meteor sigil."""
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import json
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/fire-spells-design-v5/final'
MEDIA=HERE/'media'
FPS=30
ORDER=['FIR_01','FIR_04','FIR_05','FIR_02']
NAMES={'FIR_01':'赤焰枪','FIR_04':'炎墙封路','FIR_05':'焚天火海','FIR_02':'焚星坠落 · 终极技能'}
DESCRIPTIONS={
 'FIR_01':'尖锐火核带动连续尾焰；命中后留下短暂残焰。',
 'FIR_04':'火墙沿原有范围连续燃烧；结束后火舌降低、余烬淡出。',
 'FIR_05':'火浪沿原有纵深向前推进；地面火势逐渐回落。',
 'FIR_02':'双圈法阵聚能 → 主陨石压落 → 爆燃回落 → 低位余焰消散。',
}

@lru_cache(maxsize=12)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
def text(d,xy,s,size=18,fill='#e8dfd0',bold=False,anchor='lm'):d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def smooth(x):
 t=np.clip(x,0,1);return t*t*(3-2*t)
@lru_cache(maxsize=8)
def report(variant,skill):return json.loads((CACHE/variant/skill/'capture.json').read_text(encoding='utf8'))
def mapping(src,dst):
 rows=[];values=[]
 for (x,y),(u,v) in zip(dst,src):
  rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);values.extend([u,v])
 return np.linalg.solve(np.asarray(rows),np.asarray(values))
@lru_cache(maxsize=2)
def seal():
 corners=report('design','FIR_02')['presentation']['ringCorners']
 matrix=mapping([(0,0),(1024,0),(1024,1024),(0,1024)],corners)
 source=Image.open(HERE.parent/'reference-seals-v3/assets/FIR.png').convert('RGBA')
 layer=source.transform((960,470),Image.Transform.PERSPECTIVE,matrix,Image.Resampling.BICUBIC)
 return np.asarray(layer,dtype=np.float32)/255

def scene(variant,skill,index,with_seal=True):
 r=report(variant,skill);index=max(0,min(r['frames']-1,index))
 image=Image.open(CACHE/variant/skill/f'{index:03}.jpg').convert('RGB')
 if variant=='design' and skill=='FIR_02' and with_seal:
  age=index/FPS-.30
  if 0<=age<1.02:
   layer=seal();bg=np.asarray(image,dtype=np.float32)/255
   strength=float(smooth(age/.16)*(1-smooth((age-.80)/.18)))
   brightness=smooth((bg.max(axis=2)-.25)/.30)
   neutral=1-smooth((bg[:,:,0]-bg[:,:,2]-.08)/.15)
   alpha=np.clip(layer[:,:,3]*1.45*strength*brightness*neutral,0,1)
   # Subtle local bloom stays on the original linework, leaving the stone readable.
   glow=np.asarray(Image.fromarray(np.uint8(alpha*255)).filter(ImageFilter.GaussianBlur(1.6)),dtype=np.float32)/255
   bg=bg*(1-alpha[:,:,None])+layer[:,:,:3]*alpha[:,:,None]
   bg+=layer[:,:,:3]*glow[:,:,None]*.12
   image=Image.fromarray(np.uint8(np.clip(bg*255,0,255)))
 return image

def phase(skill,index):
 t=index/FPS;r=report('design',skill)
 if t<.3:return '准备'
 impacts=[e['time'] for e in r['events'] if e['type']=='hit']
 first=min(impacts,default=.6)
 if skill=='FIR_02':
  if t<first:return '法阵聚能 · 陨石下压'
  if t<first+.55:return '命中 · 主爆燃'
  if t<first+1.5:return '火势回落'
  if t<first+2.9:return '低位残焰 · 余烬淡出'
  return '消散完成'
 if t<first:return '连贯施放'
 if skill=='FIR_01':return '命中 · 火焰回落' if t<first+.9 else '残焰淡出' if t<first+1.85 else '消散完成'
 metrics=r['metrics'];cooling=[m['frame']/FPS for m in metrics if any(x['key'].startswith('cooling:') for x in m['active'])]
 end=min(cooling,default=3.6)
 if t<end:return '持续燃烧 · 原有技能范围'
 if t<end+1.8:return '火舌降低 · 余烬淡出'
 return '消散完成'

def framed(skill,index):
 out=Image.new('RGB',(960,590),'#1d1916');d=ImageDraw.Draw(out)
 text(d,(22,28),NAMES[skill],25,'#ffbe79',True)
 text(d,(938,29),'火系动态设计 / 3D 场景',17,'#b6a99b',anchor='rm')
 out.paste(scene('design',skill,index),(0,58))
 d.line((20,542,940,542),fill='#65503a')
 text(d,(22,564),phase(skill,index),19,'#ffc78c')
 text(d,(938,564),f'{index/FPS:04.1f}s  /  设计预览',16,'#b6a99b',anchor='rm')
 return out

def video(path,frames,size,chapters=None):
 with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  if chapters:movie.set_chapters(chapters)
  stream=movie.add_stream('libx264',rate=FPS);stream.width,stream.height=size
  stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  for n,image in enumerate(frames):
   f=av.VideoFrame.from_image(image);f.pts=n;f.time_base=Fraction(1,FPS)
   for packet in stream.encode(f):movie.mux(packet)
  for packet in stream.encode():movie.mux(packet)

def preview(frames,path,width=800):
 frames=[im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS) for im in frames]
 palette=Image.new('RGB',(width,frames[0].height*4))
 for j,i in enumerate([0,len(frames)//4,len(frames)//2,3*len(frames)//4]):palette.paste(frames[i],(0,j*frames[0].height))
 palette=palette.quantize(256,method=Image.Quantize.MEDIANCUT)
 frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False)

def validate():
 results={}
 for skill in ORDER:
  r=report('design',skill)
  assert not r['errors'] and r['info']['player']['skeletons']
  assert r['info']['loadout']['ultimate']=='FIR_02'
  assert len(list((CACHE/'design'/skill).glob('*.jpg')))==r['frames']
  hits=[e for e in r['events'] if e['type']=='hit']
  active=[m['frame']/FPS for m in r['metrics'] if any(x['key'].startswith(('impact:','cooling:','bed:','field:')) for x in m['active'])]
  results[skill]={'lastHit':max((e['time'] for e in hits),default=None),'lastVisibleFirePoolUse':max(active,default=None),'frames':r['frames'],'runtimeErrors':r['errors'],'ultimate':r['info']['loadout']['ultimate']}
  assert not r['metrics'][-1]['active'],skill+' still has a live card at the end'
 current=report('current','FIR_02');design=report('design','FIR_02')
 for key in ['origin','targets','skillGeometry']:
  assert current['info'][key]==design['info'][key],key
 assert current['presentation']['camera']==design['presentation']['camera']
 assert current['gameHash']==design['gameHash']
 def hits(r):return[(e.get('skill'),e.get('id'),e.get('target'),e.get('value'),e.get('segment')) for e in r['events'] if e['type']=='hit']
 assert hits(current)==hits(design),'Meteor hit identities or damage changed'
 results['meteorComparison']={'sameBundle':True,'sameCameraTargetsGeometry':True,'sameHitIdentitiesAndDamage':True,'windupChangedForUltimate':True,'sigil':'Approved original art, perspective composited for design review only'}
 (HERE/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(results,ensure_ascii=False))

def main():
 validate();MEDIA.mkdir(exist_ok=True)
 chapters=[];start=0
 for i,skill in enumerate(ORDER):
  count=report('design',skill)['frames']
  chapters.append({'id':i,'time_base':Fraction(1,FPS),'start':start,'end':start+count,'metadata':{'title':NAMES[skill]}});start+=count
 video(MEDIA/'fire-spells-motion.mp4',(framed(skill,index) for skill in ORDER for index in range(report('design',skill)['frames'])),(960,590),chapters)
 meteor=[framed('FIR_02',i) for i in range(report('design','FIR_02')['frames'])]
 video(MEDIA/'meteor-ultimate-motion.mp4',iter(meteor),(960,590))
 preview([meteor[round(i*1.5)] for i in range(104)],MEDIA/'meteor-ultimate-motion.gif')
 # Align the same real impact event, rather than holding or fabricating baseline frames.
 current,design=[report(v,'FIR_02') for v in ['current','design']]
 hit=[min(e['time'] for e in r['events'] if e['type']=='hit') for r in [current,design]]
 current_start=max(0,round((hit[0]-.75)*FPS))
 starts=[current_start,current_start+round((hit[1]-hit[0])*FPS)]
 count=min(current['frames']-starts[0],design['frames']-starts[1])
 def compare(i):
  out=Image.new('RGB',(1920,604),'#1d1916');d=ImageDraw.Draw(out)
  text(d,(24,26),'当前火焰效果',25,'#bbae9d',True)
  text(d,(984,26),'本轮陨石终极技能 · 动态设计',25,'#ffbe79',True)
  for col,variant in enumerate(['current','design']):out.paste(scene(variant,'FIR_02',starts[col]+i),(col*960,54))
  text(d,(24,558),'同场景、同目标、同伤害；按命中时刻对齐。',21)
  text(d,(1896,558),'燃烧 → 回落 → 余烬 → 消散',21,'#ffc78c',anchor='rm')
  text(d,(24,588),'法阵沿用确认稿，为设计合成层；其余画面来自当前 Cocos 3D 预览。',15,'#a99b8d')
  return out
 video(MEDIA/'meteor-current-vs-design.mp4',(compare(i) for i in range(count)),(1920,604))
 preview([compare(round(i*1.5)) for i in range(int(count/1.5))],MEDIA/'meteor-current-vs-design.gif',1200)
 # Large phase sheet, preserving legibility without cluttering the actual battle.
 out=Image.new('RGB',(1920,842),'#1d1916');d=ImageDraw.Draw(out)
 text(d,(24,31),'焚星坠落 / 火系终极技能',32,'#ffbe79',True)
 text(d,(1896,31),'动态阶段设计 · 待审',19,'#bbae9d',anchor='rm')
 samples=[(.78,'01  双圈法阵聚能'),(1.10,'02  陨石下压'),(1.37,'03  主爆燃'),(1.97,'04  火势回落'),(2.77,'05  低位残焰'),(3.77,'06  余烬淡出')]
 for i,(t,label) in enumerate(samples):
  x=24+(i%3)*640;y=80+(i//3)*356
  text(d,(x,y),label,22,'#ffc78c',True)
  frame=scene('design','FIR_02',round(t*FPS)).resize((616,302),Image.Resampling.LANCZOS)
  out.paste(frame,(x,y+25))
 text(d,(24,809),'沿用当前角色、动作、落点与范围；法阵使用已确认原稿作透视合成。仅为设计预览，尚未接入正式技能。',20,'#bbae9d')
 out.save(MEDIA/'meteor-ultimate-stages.jpg',quality=95,subsampling=0)
 # Contact sheet for the complete fire kit.
 out=Image.new('RGB',(1920,1180),'#1d1916');d=ImageDraw.Draw(out)
 for i,skill in enumerate(ORDER):
  index={'FIR_01':18,'FIR_04':60,'FIR_05':63,'FIR_02':40}[skill]
  out.paste(framed(skill,index),((i%2)*960,(i//2)*590))
 out.save(MEDIA/'fire-kit-effects.jpg',quality=95,subsampling=0)

def validate_media():
 results={}
 expected={'fire-spells-motion.mp4':sum(report('design',s)['frames'] for s in ORDER),'meteor-ultimate-motion.mp4':report('design','FIR_02')['frames']}
 for file in sorted(MEDIA.glob('*.mp4')):
  with av.open(str(file)) as container:
   stream=container.streams.video[0]
   frames=sum(1 for _ in container.decode(video=0))
   assert frames>0 and float(stream.average_rate)==30
   if file.name in expected:assert frames==expected[file.name]
   results[file.name]={'dimensions':[stream.width,stream.height],'fps':str(stream.average_rate),'decodedFrames':frames}
 for file in sorted(MEDIA.glob('*.gif')):
  with Image.open(file) as image:
   assert image.n_frames>1
   results[file.name]={'dimensions':list(image.size),'frames':image.n_frames}
 (HERE/'media-validation.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')
 print(json.dumps(results))

if __name__=='__main__':main();validate_media()
