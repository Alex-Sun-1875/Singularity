"""Three design previews rendered in the existing Cocos scene."""
from pathlib import Path
from functools import lru_cache
import importlib.util,json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import av

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/fire-ground-columns-v8/final'
PREVIOUS_CACHE=HERE.parents[2]/'src/.tmp/fire-kit-revision-v7/final'
MEDIA=HERE/'media';FPS=30
spec=importlib.util.spec_from_file_location('fire_v5_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
ORDER=['FIR_04','FIR_05','FIR_02']
NAMES={'FIR_04':'烈焰喷流 · 一列地面火柱','FIR_05':'焚焰火域 · 火墙与火海合并','FIR_02':'焚星坠落 · 扩大终极范围'}

def directory(take,skill):return (CACHE if skill=='FIR_04' else PREVIOUS_CACHE)/take/skill

@lru_cache(maxsize=6)
def report(take,skill):return json.loads((directory(take,skill)/'capture.json').read_text(encoding='utf8'))
@lru_cache(maxsize=2)
def seal(take):
 corners=report(take,'FIR_02')['presentation']['ringCorners']
 matrix=base.mapping([(0,0),(1024,0),(1024,1024),(0,1024)],corners)
 image=Image.open(HERE.parent/'reference-seals-v3/assets/FIR.png').convert('RGBA')
 return np.asarray(image.transform((960,470),Image.Transform.PERSPECTIVE,matrix,Image.Resampling.BICUBIC),dtype=np.float32)/255

def scene(take,skill,index):
 image=Image.open(directory(take,skill)/f'{index:03}.jpg').convert('RGB')
 age=index/FPS-.3
 if skill=='FIR_02' and 0<=age<1.02:
  layer=seal(take);bg=np.asarray(image,dtype=np.float32)/255
  strength=float(base.smooth(age/.16)*(1-base.smooth((age-.80)/.18)))
  visibility=base.smooth((bg.max(axis=2)-.25)/.30)*(1-base.smooth((bg[:,:,0]-bg[:,:,2]-.08)/.15))
  alpha=np.clip(layer[:,:,3]*1.45*strength*visibility,0,1)
  glow=np.asarray(Image.fromarray(np.uint8(alpha*255)).filter(ImageFilter.GaussianBlur(1.6)),dtype=np.float32)/255
  image=Image.fromarray(np.uint8(np.clip((bg*(1-alpha[:,:,None])+layer[:,:,:3]*alpha[:,:,None]+layer[:,:,:3]*glow[:,:,None]*.12)*255,0,255)))
 return image

def phase(skill,index):
 t=index/FPS
 if t<.3:return '准备'
 if skill=='FIR_04':
  return '施法准备' if t<.55 else '地面由近到远喷起' if t<.98 else '五道火柱 · 沿地面成列' if t<1.70 else '火柱回落 · 地面余焰渐退' if t<2.80 else '结束'
 if skill=='FIR_05':
  return '火浪展开' if t<1 else '地面持续燃烧 · 控场' if t<4.8 else '残焰逐渐消散' if t<6.3 else '结束'
 hit=min(e['time'] for e in report('design',skill)['events'] if e['type']=='hit')
 age=t-hit
 return '双圈法阵 · 半径 3.8 米' if age<0 else '持续爆燃' if age<1.2 else '火势回落' if age<1.65 else '地面残焰 · 余烬渐退' if age<4.55 else '消散完成'

def framed(skill,index):
 out=Image.new('RGB',(960,600),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(22,28),NAMES[skill],25,'#ffbe79',True)
 base.text(d,(938,29),'当前 3D 场景 / 设计预览',16,'#b6a99b',anchor='rm')
 out.paste(scene('design',skill,index),(0,58))
 d.line((20,543,940,543),fill='#65503a');base.text(d,(22,563),phase(skill,index),18,'#ffc78c')
 note={'FIR_04':'地面五道喷火柱，沿前方一列展开；技能规则待确认','FIR_05':'合并为一个火域；持续伤害＋减速为设计目标','FIR_02':'原半径 2.8m → 3.8m；保留延长爆燃'}[skill]
 base.text(d,(22,588),note,14,'#a99b8d')
 base.text(d,(938,565),f'{index/FPS:04.1f}s',16,'#b6a99b',anchor='rm')
 return out

def compare(index):
 out=Image.new('RGB',(1920,604),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,27),'陨石 · 原半径 2.8 米',25,'#bbae9d',True)
 base.text(d,(984,27),'陨石 · 候选半径 3.8 米',25,'#ffbe79',True)
 for col,take in enumerate(['previous','design']):out.paste(scene(take,'FIR_02',index),(col*960,54))
 base.text(d,(24,556),'同机位与目标；直径 5.6m → 7.6m，覆盖面积约增加 84%。',21)
 base.text(d,(24,587),'法阵、爆燃和地面余焰随同一范围调整；终极技能定位与 1.2 秒主爆燃保留。仅为设计预览。',15,'#a99b8d')
 return out

def verify():
 results={}
 for skill in ORDER:
  r=report('design',skill)
  assert not r['errors'] and r['info']['player']['skeletons']
  assert r['info']['loadout']['ultimate']=='FIR_02'
  assert len(list(directory('design',skill).glob('*.jpg')))==r['frames']
  assert not r['metrics'][-1]['active'],skill
  results[skill]={'frames':r['frames'],'runtimeErrors':r['errors'],'geometry':r['info']['skillGeometry']}
 previous,design=[report(t,'FIR_02') for t in ['previous','design']]
 assert previous['info']['targets']==design['info']['targets']
 assert previous['presentation']['camera']==design['presentation']['camera']
 assert previous['gameHash']==design['gameHash']
 assert previous['info']['skillGeometry']['radiusMetres']==2.8
 assert design['info']['skillGeometry']['radiusMetres']==3.8
 def hits(r):return {e['id']:e['value'] for e in r['events'] if e['type']=='hit'}
 old,new=hits(previous),hits(design)
 assert old.keys()<=new.keys(),(old,new)
 assert all(new[k]==v for k,v in old.items())
 peak=lambda r:max(a['width'] for m in r['metrics'] for a in m['active'] if a['key'].startswith('impact:') and ':main:' in a['key'])
 assert abs(peak(design)/peak(previous)-3.8/2.8)<.001
 results['meteorChange']={'previousHitCount':len(old),'candidateHitCount':len(new),'commonTargetDamageUnchanged':True,'geometryChanged':True,'nativeMainFlameWidthMetres':{'previous':peak(previous),'design':peak(design)},'additionalTargetCoverageConfirmed':len(new)>len(old),'note':'This recording does not establish expanded hit coverage. Collision and visibility acceptance remains separate from the range design.'}
 jet=report('design','FIR_04')
 assert not any(e['type']=='hit' and e.get('value',0)>0 for e in jet['events'])
 results['jetConceptOnly']={'newRulesImplemented':False,'damageDisabledInAnimationCarrier':True,'handStream':False,'columns':5,'existingNativeCastAndRecovery':True}
 active=[a['key'] for m in jet['metrics'] for a in m['active']]
 assert all(any(':column:'+str(i)+':' in k for k in active) for i in range(5))
 results['productIntegration']=False
 (HERE/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(results,ensure_ascii=False),flush=True)

def main():
 verify();MEDIA.mkdir(exist_ok=True)
 base.video(MEDIA/'fire-kit-revision-motion.mp4',(framed(s,i) for s in ORDER for i in range(report('design',s)['frames'])),(960,600))
 for skill,name in [('FIR_04','flame-jet'),('FIR_02','meteor-expanded')]:
  count=report('design',skill)['frames']
  base.video(MEDIA/(name+'.mp4'),(framed(skill,i) for i in range(count)),(960,600))
  base.preview([framed(skill,round(i*1.5)) for i in range(int(count/1.5))],MEDIA/(name+'.gif'))
 count=report('design','FIR_02')['frames']
 base.video(MEDIA/'meteor-range-comparison.mp4',(compare(i) for i in range(count)),(1920,604))
 out=Image.new('RGB',(1920,1200),'#1d1916');d=ImageDraw.Draw(out)
 for i,(take,skill,index,title,note) in enumerate([
  ('previous','FIR_02',24,'陨石 · 旧范围','半径 2.8 米 / 直径 5.6 米'),
  ('design','FIR_02',24,'陨石 · 扩大范围','半径 3.8 米 / 直径 7.6 米'),
  ('design','FIR_05',60,'焚焰火域 · 合并技能','火浪展开 → 持续燃烧；统一伤害预算，附减速'),
  ('design','FIR_04',36,'烈焰喷流 · 地面一列喷火柱','由近到远喷起五道火柱；喷发后回落为地面余焰')]):
  x=(i%2)*960;y=(i//2)*600
  base.text(d,(x+22,y+28),title,25,'#ffbe79',True)
  out.paste(scene(take,skill,index),(x,y+58))
  base.text(d,(x+22,y+563),note,18,'#ffc78c')
  base.text(d,(x+22,y+588),'动态设计候选，尚未接入正式技能',14,'#a99b8d')
 out.save(MEDIA/'fire-kit-design-board.jpg',quality=95,subsampling=0)
 results={}
 for file in sorted(MEDIA.glob('*.mp4')):
  with av.open(str(file)) as container:
   stream=container.streams.video[0];count=sum(1 for _ in container.decode(video=0))
   assert count>0 and float(stream.average_rate)==30
   results[file.name]={'frames':count,'fps':30,'dimensions':[stream.width,stream.height]}
 (HERE/'media-validation.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')
 print(json.dumps(results),flush=True)

if __name__=='__main__':main()
