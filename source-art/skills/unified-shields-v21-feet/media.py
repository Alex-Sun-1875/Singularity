"""Review actual native foot coverage after the shared shell geometry fix."""
from pathlib import Path
import importlib.util,json,hashlib
from PIL import Image,ImageDraw
import av
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/unified-shields-v21-feet/final';MEDIA=HERE/'media'
spec=importlib.util.spec_from_file_location('previous_runtime',HERE.parent/'unified-shields-v20/runtime-media.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous);base=previous.base
ORDER=previous.ORDER;NAMES=previous.NAMES;COLORS=previous.COLORS
def report(key):return json.loads((CACHE/key/'capture.json').read_text(encoding='utf8'))
def image(key,frame):return Image.open(CACHE/key/f'{frame:03}.jpg').convert('RGB')
def four(frame):
 out=Image.new('RGB',(1240,1320),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,34),'统一护盾 · 双脚完整包覆',33,'#e7bc7d',True)
 base.text(d,(20,77),'下移中心并加深下部；四系同步调整',22,'#bfb2a1')
 for n,key in enumerate(ORDER):
  x=18+n%2*612;y=109+n//2*568
  base.text(d,(x+10,y+23),NAMES[n],24,COLORS[n],True)
  out.paste(image(key,frame).crop((205,60,655,450)).resize((600,520),Image.Resampling.LANCZOS),(x,y+45))
  d.rectangle((x,y,x+600,y+565),outline='#655039')
 base.text(d,(20,1262),'实际游戏录制 · 保留原有护盾动画、纹样与颜色',21,'#e7bc7d')
 base.text(d,(20,1296),'战士、火系为技能施放；弓系、雷系展示已有护盾状态的职业外观',16,'#bfb2a1')
 return out
def compare():
 out=Image.new('RGB',(1280,770),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(24,35),'护盾脚部包覆 · 实际场景对比',34,'#e7bc7d',True)
 old=Image.open(ROOT/'src/.tmp/unified-shields-v20/final/fire-active/036.jpg').convert('RGB')
 for n,(name,source) in enumerate([('调整前 · 下沿挤在鞋底',old),('调整后 · 双脚留在罩内',image('fire-active',36))]):
  x=20+n*635
  base.text(d,(x+10,87),name,25,'#c4b6a4' if n==0 else '#ffb476',True)
  crop=source.crop((245,105,550,410)).resize((610,610),Image.Resampling.LANCZOS)
  out.paste(crop,(x,111));d.rectangle((x,111,x+610,721),outline='#655039')
 base.text(d,(24,749),'同一机位、角色与施放时刻；只调整护罩中心和下部空间',21,'#bfb2a1')
 out.save(MEDIA/'shield-feet-before-after.jpg',quality=95,subsampling=0)
def walking(frame):
 out=Image.new('RGB',(960,582),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,30),'护盾脚部包覆 · 站立与迈步实景',28,'#e7bc7d',True)
 out.paste(image('fire-walking',frame),(0,56))
 base.text(d,(20,550),'移动时持续跟随；脚底和迈步中的脚尖纳入护罩下部',21,'#e7bc7d')
 base.text(d,(940,550),f'{frame/30:.1f}s',19,'#bfb2a1',anchor='rm')
 return out
def main():
 result={'scope':'Shared shell feet enclosure; rendering geometry only','checks':{},'typeCheck':'passed','cocosWebBuild':'passed','taptapDeviceValidation':'not performed'}
 for key in ORDER+['fire-walking']:
  r=report(key);assert not r['errors'] and not r['consoleErrors'];assert r['frames']==165
  visible=[m for m in r['metrics'] if m['shield']['visible']]
  feet=[foot for m in visible for foot in m['feet']]
  assert feet,key+' missing actual foot joints'
  maximum=max(f['enclosure'] for f in feet)
  assert maximum<=1,key+' foot joint outside shell: '+str(maximum)
  assert all(m['shield']['scale']=={'x':1.88,'y':2.68,'z':1.88} for m in visible)
  result['checks'][key]={'runtimeErrors':r['errors'],'consoleErrors':r['consoleErrors'],'sampledFootPoints':len(feet),'jointNames':sorted({f['name'] for f in feet}),'maximumEllipsoidEquation':maximum,'jointsEnclosed':True,'frames':r['frames'],'gameHash':r['gameHash']}
  if key=='fire-walking':
   spread=max(m['shield']['position']['x'] for m in visible)-min(m['shield']['position']['x'] for m in visible)
   spread+=max(m['shield']['position']['z'] for m in visible)-min(m['shield']['position']['z'] for m in visible)
   assert spread>.15,'Walking recording did not move the character'
   result['checks'][key]['movementSpanXZ']=spread
   result['checks'][key]['nativeAnimationStates']=r['clips']
 compare();four(36).save(MEDIA/'unified-shields-feet.jpg',quality=95,subsampling=0)
 base.video(MEDIA/'shield-feet-walking.mp4',(walking(i) for i in range(165)),(960,582))
 base.video(MEDIA/'unified-shields-feet.mp4',(four(i) for i in range(165)),(1240,1320))
 for filename in ['shield-feet-walking','unified-shields-feet']:
  with av.open(str(MEDIA/(filename+'.mp4'))) as movie:
   s=movie.streams.video[0];assert s.frames==165 and float(s.average_rate)==30
 result['sourceHashes']={name:hashlib.sha256((ROOT/'src/cocos'/name).read_bytes()).hexdigest() for name in ['assets/scripts/features/combat/runtime/UnifiedShieldEffects.ts','assets/scripts/features/combat/runtime/Effects.ts']}
 (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
