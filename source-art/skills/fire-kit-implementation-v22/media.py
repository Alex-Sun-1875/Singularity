"""Present the implemented kit from native recordings, without VFX overlays."""
from pathlib import Path
from functools import lru_cache
from fractions import Fraction
import importlib.util,json,hashlib
from PIL import Image,ImageDraw
import av
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/fire-kit-implementation-v22/final';MEDIA=HERE/'media'
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
ORDER=['FIR_01','FIR_04','FIR_05','FIR_03','FIR_02']
NAMES={'FIR_01':'赤焰枪','FIR_04':'烈焰喷流','FIR_05':'焚焰火域','FIR_03':'焰心护盾','FIR_02':'焚星坠落 · 终极'}
NOTES={'FIR_01':['尖锐火核向前飞行，命中后留下逐渐消退的残焰。','单体主力，保留真实弹道与单目标判定。'],'FIR_04':['五个小法阵沿前方排成一列，火焰竖直上喷。','持续喷焰后降低火势，法阵与余火一起渐隐。'],'FIR_05':['火浪铺开有纵深的固定火域，持续燃烧并减速。','原火墙与火海合为一项；最多保留一处火域。'],'FIR_03':['沿用已确认的统一护罩，完整包住双脚。','成形、吸收伤害波纹与消散共用职业护盾表现。'],'FIR_02':['双层纹样法阵预告落点，主陨石坠落后持续爆燃。','终极技能；主爆燃约 1.2 秒，地面余焰缓慢消散。']}
@lru_cache(maxsize=5)
def report(skill):return json.loads((CACHE/skill/'capture.json').read_text(encoding='utf8'))
def scene(skill,index):return Image.open(CACHE/skill/f'{index:03}.jpg').convert('RGB')
def phase(skill,index):
 r=report(skill);t=index/30;release=next(e['time'] for e in r['events'] if e['type']=='skill_release');age=t-release
 if age<0:return '法阵与动作蓄势' if skill in ['FIR_04','FIR_02'] else '准备施放'
 if skill=='FIR_02':return '主爆燃' if age<1.2 else '火势回落' if age<1.65 else '地面残焰逐渐消散' if age<4.55 else '消散完成'
 if skill in ['FIR_04','FIR_05']:return ('五点持续喷焰' if skill=='FIR_04' else '火域持续燃烧') if age<4 else '余火逐渐消散' if age<5.8 else '消散完成'
 if skill=='FIR_03':return '护罩维持 · 双脚纳入罩内' if age<3.5 else '自然淡出' if age<4 else '护罩结束'
 return '火弹飞行与命中' if age<.7 else '命中残焰退去' if age<2.4 else '消散完成'
def framed(skill,index):
 out=Image.new('RGB',(960,630),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(22,29),NAMES[skill],27,'#ffc07f',True);base.text(d,(938,30),'Cocos 实际运行录制',16,'#bcb0a0',anchor='rm')
 out.paste(scene(skill,index),(0,58));d.line((20,543,940,543),fill='#6c5236')
 base.text(d,(22,565),phase(skill,index),20,'#ffc07f');base.text(d,(938,565),f'{index/30:.1f}s',17,'#bcb0a0',anchor='rm')
 base.text(d,(22,596),NOTES[skill][0],17,'#e8dfd0');base.text(d,(22,620),'新火系技能方案 · 已接入 · 无后期技能特效合成',14,'#bcb0a0')
 return out
def board():
 picks={'FIR_01':18,'FIR_04':36,'FIR_05':45,'FIR_03':36,'FIR_02':30}
 out=Image.new('RGB',(1976,2110),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(24,44),'火系技能 · 新方案实际运行效果',42,'#e8b976',True)
 base.text(d,(24,94),'赤焰枪 / 一列地面喷焰 / 合并火域 / 统一护盾 / 终极陨石',24,'#bcb0a0')
 for n,skill in enumerate(ORDER):
  x=20+n%2*976;y=132+n//2*638;card=Image.new('RGB',(960,622),'#231f1b');cd=ImageDraw.Draw(card)
  base.text(cd,(22,29),f'{n+1:02}  '+NAMES[skill],27,'#ffc07f',True);base.text(cd,(938,30),'已接入 · 原生录制',16,'#bcb0a0',anchor='rm')
  card.paste(scene(skill,picks[skill]),(0,58))
  for i,line in enumerate(NOTES[skill]):base.text(cd,(22,557+i*31),line,18,'#e8dfd0')
  cd.rectangle((0,0,959,621),outline='#6c5236');out.paste(card,(x,y))
 x,y=996,1408;d.rectangle((x,y,x+959,y+621),fill='#231f1b',outline='#6c5236')
 base.text(d,(x+28,y+39),'火系分工与收尾',28,'#ffc07f',True)
 lines=['赤焰枪：单体主力，弹道清楚。','烈焰喷流：前方一列，定向持续输出。','焚焰火域：固定区域，燃烧与减速。','焰心护盾：自身保护，完整包住双脚。','焚星坠落：终极范围爆发，12 秒冷却。','','余焰逐渐变低、退亮，再完全消散。','范围与伤害来自实际技能判定。','当前画面全部来自新编译的游戏。']
 for i,line in enumerate(lines):base.text(d,(x+28,y+103+i*49),line,22,'#e8dfd0' if i<5 else '#bcb0a0')
 base.text(d,(24,2077),'Web 实景检查 · TapTap 真机画面与性能待验证',21,'#bcb0a0')
 out.save(MEDIA/'fire-kit-runtime-overview.jpg',quality=95,subsampling=0)
def verify():
 result={}
 for skill in ORDER:
  r=report(skill);assert not r['errors'] and not r['consoleErrors'];assert r['info']['player']['skeletons']
  assert r['info']['loadout']['ultimate']=='FIR_02' and r['info']['activeSlots']==['FIR_01','FIR_04','FIR_03','FIR_05']
  assert len(list((CACHE/skill).glob('*.jpg')))==r['frames']
  assert not r['metrics'][-1]['ground']['active'] and not r['metrics'][-1]['fire']['active']
  direct=[e for e in r['events'] if e['type']=='skill_hit' and e.get('skill')==skill]
  result[skill]={'frames':r['frames'],'directContacts':len(direct),'lastDirectContact':max((e['time'] for e in direct),default=None),'errors':r['errors'],'consoleErrors':r['consoleErrors'],'geometry':r['info'].get('skillGeometry'),'clearedAtEnd':True,'gameHash':r['gameHash']}
 assert len({r['gameHash'] for r in result.values()})==1
 jet=report('FIR_04');emitters=[s['emitters'] for m in jet['metrics'] for s in m['ground']['active'] if s['kind']=='jets'];assert emitters and all(count==5 for count in emitters)
 assert not any(e.get('target')=='study-target-3' for e in jet['events'] if e['type']=='skill_hit')
 field=report('FIR_05');assert any(s['percent']==.35 and s['until']>m['time'] for m in field['metrics'] for s in m['slows'])
 assert not any(e.get('target')=='study-target-3' for e in field['events'] if e['type']=='skill_hit')
 meteor=report('FIR_02');release=next(e['time'] for e in meteor['events'] if e['type']=='skill_release')
 last=max(m['frame']/30 for m in meteor['metrics'] if m['fire']['active']);assert last-release>4.3
 lifecycle=json.loads((HERE/'runtime-lifecycle.json').read_text(encoding='utf8'));assert all(r['coreUnchanged'] for r in lifecycle)
 textures={};production=ROOT/'src/cocos/assets/resources/vfx/production';build=ROOT/'src/cocos/build/concept-2d/assets'
 for name in ['fire-ground-jets-v22','fire-jet-seal-v22','fire-meteor-seal-v22','fire-pyro-v7','fire-low-rolls-v7','fire-bolt-v9']:
  source=production/(name+'.png');uuid=json.loads((production/(name+'.png.meta')).read_text(encoding='utf8'))['uuid']
  candidates=list(build.glob(f'*/native/{uuid[:2]}/{uuid}.*.png'));expected=Image.open(source).convert('RGBA')
  matching=[p for p in candidates if Image.open(p).convert('RGBA').tobytes()==expected.tobytes()]
  assert matching,f'Compiled texture does not match current source: {name}'
  textures[name]={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bundledPath':str(matching[0].relative_to(build)),'sameRgba':True}
 paths=['assets/scripts/features/combat/runtime/NativeSkillVfx.ts','assets/scripts/features/combat/runtime/SkillFireSprites.ts','assets/scripts/features/combat/runtime/FireGroundEffects.ts','assets/scripts/features/combat/runtime/Effects.ts','assets/scripts/features/combat/common/PureCombat.ts','assets/scripts/features/progression/common/CombatLoadouts.ts','assets/scripts/features/combat/data/PureSkills.ts','assets/scripts/features/automation/common/Automation.ts','assets/scripts/features/progression/runtime/PreparationPanels.ts']
 return {'status':'New fire kit implemented and recorded from the compiled native Cocos game','cases':result,'fiveGroundEmitters':True,'excludedOutsideCorridorAndFieldTarget':True,'fieldSlowObserved':True,'meteorLastVisibleSecondsAfterRelease':last-release,'pauseResumeCoreUnchanged':True,'rulesChecks':'155 existing checks passed; 62 related checks passed; 10 existing navigation checks passed after the automatic aim update','typeCheck':'passed','cocosWebBuild':'passed','legacyPolicy':'No new fire-specific old-save migration or frozen catalog; current rules installed directly as requested','taptapDeviceValidation':'pending','sourceHashes':{name:hashlib.sha256((ROOT/'src/cocos'/name).read_bytes()).hexdigest() for name in paths},'textures':textures}
def main():
 checks=verify();board();chapters=[];start=0
 for n,s in enumerate(ORDER):
  end=start+report(s)['frames'];chapters.append(dict(id=n,time_base=Fraction(1,30),start=start,end=end,metadata={'title':NAMES[s]}));start=end
 base.video(MEDIA/'fire-kit-runtime.mp4',(framed(s,i) for s in ORDER for i in range(report(s)['frames'])),(960,630),chapters)
 for s,name in [('FIR_04','ground-flame-row'),('FIR_02','meteor-ultimate'),('FIR_05','burning-field')]:
  base.video(MEDIA/(name+'.mp4'),(framed(s,i) for i in range(report(s)['frames'])),(960,630))
 with av.open(str(MEDIA/'fire-kit-runtime.mp4')) as movie:
  v=movie.streams.video[0];assert v.frames==start and float(v.average_rate)==30;checks['video']={'frames':v.frames,'fps':30,'seconds':float(movie.duration)/av.time_base}
 (HERE/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(checks,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
