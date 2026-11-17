"""Review timing revision, rendered by Cocos; same artwork as the previous design."""
from pathlib import Path
from functools import lru_cache
import importlib.util
import json
import hashlib
import numpy as np
import av
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/fire-meteor-burn-v6/final'
MEDIA=HERE/'media'
spec=importlib.util.spec_from_file_location('fire_v5_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
FPS=30

@lru_cache(maxsize=2)
def report(take):return json.loads((CACHE/take/'FIR_02/capture.json').read_text(encoding='utf8'))

@lru_cache(maxsize=1)
def seal():
 corners=report('design')['presentation']['ringCorners']
 matrix=base.mapping([(0,0),(1024,0),(1024,1024),(0,1024)],corners)
 image=Image.open(HERE.parent/'reference-seals-v3/assets/FIR.png').convert('RGBA')
 return np.asarray(image.transform((960,470),Image.Transform.PERSPECTIVE,matrix,Image.Resampling.BICUBIC),dtype=np.float32)/255

def scene(take,index):
 image=Image.open(CACHE/take/'FIR_02'/f'{index:03}.jpg').convert('RGB')
 age=index/FPS-.3
 if 0<=age<1.02:
  layer=seal();bg=np.asarray(image,dtype=np.float32)/255
  strength=float(base.smooth(age/.16)*(1-base.smooth((age-.80)/.18)))
  visibility=base.smooth((bg.max(axis=2)-.25)/.30)*(1-base.smooth((bg[:,:,0]-bg[:,:,2]-.08)/.15))
  alpha=np.clip(layer[:,:,3]*1.45*strength*visibility,0,1)
  glow=np.asarray(Image.fromarray(np.uint8(alpha*255)).filter(ImageFilter.GaussianBlur(1.6)),dtype=np.float32)/255
  image=Image.fromarray(np.uint8(np.clip((bg*(1-alpha[:,:,None])+layer[:,:,:3]*alpha[:,:,None]+layer[:,:,:3]*glow[:,:,None]*.12)*255,0,255)))
 return image

def phase(index):
 time=index/FPS;hit=min(e['time'] for e in report('design')['events'] if e['type']=='hit')
 if time<.3:return '准备'
 age=time-hit
 if age<0:return '法阵聚能 · 陨石下压'
 if age<.18:return '命中 · 快速爆开'
 if age<1.20:return '持续爆燃 · 火焰翻卷'
 if age<1.65:return '火势回落'
 if age<4.55:return '低位残焰 · 余烬渐退'
 return '消散完成'

def framed(index):
 out=Image.new('RGB',(960,590),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(22,28),'焚星坠落 · 延长爆燃',25,'#ffbe79',True)
 base.text(d,(938,29),'火系终极技能 / 动态修订',17,'#b6a99b',anchor='rm')
 out.paste(scene('design',index),(0,58));d.line((20,542,940,542),fill='#65503a')
 base.text(d,(22,564),phase(index),19,'#ffc78c')
 base.text(d,(938,564),f'{index/FPS:04.1f}s / 设计预览',16,'#b6a99b',anchor='rm')
 return out

def compare(index):
 out=Image.new('RGB',(1920,604),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,27),'上一版 · 主焰快速回落',25,'#bbae9d',True)
 base.text(d,(984,27),'本轮 · 高火焰持续翻卷',25,'#ffbe79',True)
 for col,take in enumerate(['previous','design']):out.paste(scene(take,index),(col*960,54))
 base.text(d,(24,558),'同一施放与命中时刻；主焰延长后，继续自然退成余烬。',21)
 base.text(d,(24,588),'当前 Cocos 3D 场景录制；法阵沿用确认稿作透视合成。仅为设计预览。',15,'#a99b8d')
 return out

def verify():
 previous,current=[report(t) for t in ['previous','design']]
 for take,r in [('previous',previous),('design',current)]:
  assert not r['errors'] and r['info']['player']['skeletons']
  assert r['info']['loadout']['ultimate']=='FIR_02'
  assert len(list((CACHE/take/'FIR_02').glob('*.jpg')))==r['frames']==195
  assert not r['metrics'][-1]['active']
 assert previous['events']==current['events'],'Gameplay or action timings changed'
 for key in ['origin','targets','skillGeometry','loadout','renderer']:assert previous['info'][key]==current['info'][key],key
 assert previous['presentation']==current['presentation']
 assert previous['gameHash']==current['gameHash']
 def last_use(r):return max(m['frame']/FPS for m in r['metrics'] if m['active'])
 result={'generation':'No new generation; reuse v5 cloud-generated atlases. Native preview retiming only.',
  'previousBlastEnvelopeSeconds':.55,'highFlameUntilSecondsAfterHit':1.2,'settlingUntilSecondsAfterHit':1.65,
  'totalFireVisualSecondsAfterHit':4.55,'lastFirePoolUse':{'previous':last_use(previous),'design':last_use(current)},
  'sameGameplayEvents':True,'sameCameraTargetsAndAction':True,'runtimeErrors':[],
  'sourceArt':'../fire-spells-design-v5/provenance.json','artAcceptance':'Pending user review','productIntegration':False}
 (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result,ensure_ascii=False),flush=True)

def main():
 verify();MEDIA.mkdir(exist_ok=True)
 count=report('design')['frames']
 base.video(MEDIA/'meteor-long-burn-motion.mp4',(framed(i) for i in range(count)),(960,590))
 base.preview([framed(round(i*1.5)) for i in range(130)],MEDIA/'meteor-long-burn-motion.gif')
 base.video(MEDIA/'meteor-burn-before-after.mp4',(compare(i) for i in range(count)),(1920,604))
 out=Image.new('RGB',(1920,742),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,30),'陨石终极技能 / 延长爆燃',30,'#ffbe79',True)
 hit=min(e['time'] for e in report('design')['events'] if e['type']=='hit')
 for i,(age,label) in enumerate([(.30,'爆燃展开'),(.90,'高火焰持续翻卷'),(1.35,'火势开始回落'),(2.50,'残焰渐退')]):
  x=(i%2)*960;y=70+(i//2)*320
  base.text(d,(x+24,y),f'命中后 {age:.2f}s · {label}',21,'#ffc78c',True)
  out.paste(scene('design',round((hit+age)*FPS)).resize((588,288),Image.Resampling.LANCZOS),(x+186,y+23))
 base.text(d,(24,722),'沿用上一版造型与法阵；调整爆燃节奏，余焰继续渐退。设计预览，尚未接入正式实现。',18,'#bbae9d')
 out.save(MEDIA/'meteor-long-burn-stages.jpg',quality=95,subsampling=0)
 result={}
 for file in sorted(MEDIA.glob('*.mp4')):
  with av.open(str(file)) as container:
   stream=container.streams.video[0];decoded=sum(1 for _ in container.decode(video=0))
   assert decoded==195 and float(stream.average_rate)==30
   result[file.name]={'frames':decoded,'fps':30,'size':[stream.width,stream.height]}
 with Image.open(MEDIA/'meteor-long-burn-motion.gif') as image:assert image.n_frames==130
 (HERE/'media-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result),flush=True)

if __name__=='__main__':main()
