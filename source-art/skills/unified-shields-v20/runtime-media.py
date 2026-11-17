"""Typeset actual native captures; no composited shield art or scene alteration."""
from pathlib import Path
from functools import lru_cache
import importlib.util,json,hashlib
from PIL import Image,ImageDraw
import av
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/unified-shields-v20/final';MEDIA=HERE/'media'
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
ORDER=['war-active','bow-state-fixture','fire-active','thunder-state-fixture']
NAMES=['战士 · 银金刃纹','弓系 · 青绿风纹','火系 · 橙金焰纹','雷系 · 蓝紫雷纹']
COLORS=['#e2c792','#72d8b8','#ff9746','#9698ff']
@lru_cache(maxsize=5)
def report(key):return json.loads((CACHE/key/'capture.json').read_text(encoding='utf8'))
def source(key,index):return Image.open(CACHE/key/f'{index:03}.jpg').convert('RGB')
def phase(key,index):
 m=report(key)['metrics'][index];s=m['shield']
 if not s['visible']:return '消散完成' if index>30 else '准备施放'
 if s['broken']:return '提前击破 · 碎光渐退'
 if m['time']-s['start']<.32:return '由下向上成形'
 if 0<=m['time']-(s['hitAt'] or -1e9)<.22:return '实际吸收伤害 · 局部波纹'
 if s['opacity']<.98:return '自然到期 · 逐渐消散'
 return '随人物维持护罩'
def four(index):
 out=Image.new('RGB',(1240,1320),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,34),'统一护盾 · 原生 3D 运行效果',33,'#e7bc7d',True)
 base.text(d,(20,77),'同一网格与材质，只切换职业颜色和花纹',22,'#bfb2a1')
 for n,key in enumerate(ORDER):
  x=18+n%2*612;y=109+n//2*568
  base.text(d,(x+10,y+23),NAMES[n],24,COLORS[n],True)
  out.paste(source(key,index).crop((205,60,655,450)).resize((600,520),Image.Resampling.LANCZOS),(x,y+45))
  d.rectangle((x,y,x+600,y+565),outline='#655039')
 base.text(d,(20,1262),phase('fire-active',index),21,'#e7bc7d')
 base.text(d,(20,1296),'战士、火系为技能施放；弓系、雷系展示已有护盾状态的职业外观',16,'#bfb2a1')
 base.text(d,(1220,1262),f'{index/30:.1f}s',19,'#bfb2a1',anchor='rm')
 return out
def broken(index):
 out=Image.new('RGB',(960,600),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,30),'统一护盾 · 实际伤害击破',28,'#e7bc7d',True)
 out.paste(source('fire-break',index),(0,57))
 base.text(d,(20,550),phase('fire-break',index),21,'#e7bc7d')
 base.text(d,(20,582),'原生游戏录制 · 护盾耗尽时触发短暂溶解，不增加攻击爆炸',16,'#bfb2a1')
 return out
def verify():
 results={}
 for key in ORDER+['fire-break']:
  r=report(key);assert not r['errors'] and not r['consoleErrors'] and r['info']['player']['skeletons']
  assert r['frames']==165 and len(list((CACHE/key).glob('*.jpg')))==165
  metrics=r['metrics'];positive=[m for m in metrics if m['amount']>0];visible=[m for m in metrics if m['shield']['visible']]
  assert positive and visible and not metrics[-1]['shield']['visible']
  assert all(m['shield']['family']==r['scenario']['family'] for m in visible)
  assert all(m['shield']['scale']=={'x':1.88,'y':2.36,'z':1.88} for m in visible)
  hits=[m for m in metrics if (m['shield']['hitAt'] or -1e9)>10]
  assert hits and len({m['shield']['start'] for m in positive})==1
  has_broken=any(m['shield']['broken'] and m['shield']['visible'] for m in metrics)
  assert has_broken==bool(r['scenario'].get('break')),key
  results[key]={'frames':165,'nativeSkinnedActor':True,'runtimeErrors':r['errors'],'consoleErrors':r['consoleErrors'],'visibleFrames':len(visible),'firstAmount':positive[0]['amount'],'endsInvisible':True,'actualAbsorptionRipple':True,'earlyBreakObserved':has_broken,'activeSource':r['scenario']['id'],'gameHash':r['gameHash']}
 lifecycle=json.loads((HERE/'runtime-lifecycle.json').read_text(encoding='utf8'))
 assert lifecycle['pausedStartUnchanged'] and lifecycle['followedMovement'] and not lifecycle['cleared']['visible']
 files=['assets/scripts/features/combat/runtime/UnifiedShieldEffects.ts','assets/scripts/features/combat/runtime/Effects.ts','assets/scripts/features/combat/runtime/NativeSkillVfx.ts','assets/resources/vfx/production/shield-unified-v1.effect','assets/resources/vfx/production/shield-unified-motifs-v1.png']
 verification={'status':'Native implementation captured; not a post-composited shield preview','cases':results,'lifecycle':{'pauseDoesNotReplayFormation':True,'followsPlayerMovement':True,'clearHidesShield':True},'checks':{'typeCheck':'npm --prefix src/cocos run check passed','existingShieldRules':'2 existing shield-related chapter rule tests passed','cocosBuild':'Build-Local.ps1 web-mobile concept-2d test passed'},'sourceHashes':{f:hashlib.sha256((ROOT/'src/cocos'/f).read_bytes()).hexdigest() for f in files},'taptapDeviceValidation':'Pending; no App/device performance or platform acceptance claimed','packaging':'No TapTap package or version increment requested/performed','artApproval':'User approved design; current native output supplied for review'}
 return verification
def main():
 checks=verify();four(36).save(MEDIA/'unified-shields-runtime.jpg',quality=95,subsampling=0)
 base.video(MEDIA/'unified-shields-runtime.mp4',(four(i) for i in range(165)),(1240,1320))
 base.video(MEDIA/'shield-break-runtime.mp4',(broken(i) for i in range(120)),(960,600))
 for name in ['unified-shields-runtime','shield-break-runtime']:
  with av.open(str(MEDIA/(name+'.mp4'))) as movie:
   v=movie.streams.video[0];assert float(v.average_rate)==30
   checks[name]={'frames':v.frames,'seconds':float(movie.duration)/av.time_base,'fps':30}
 (HERE/'runtime-verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(checks,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
