"""Encode real training-range canvas frames. Only crop/resize/layout is used."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json
import av
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
FPS=30
NAMES={'FIR_01':'赤焰枪','FIR_05':'焚焰火域','FIR_02':'陨星天坠 · 终极','FIR_04':'烈焰喷流 · 已确认效果回归','FIR_03':'焰心护盾 · 统一护盾回归'}
STAGES={'FIR_01':[(16,'抬手聚焰'),(19,'火弹前进'),(23,'命中扩散'),(47,'余焰消散')],
        'FIR_05':[(26,'地面起焰'),(63,'持续燃烧'),(145,'停止输出'),(175,'余火淡出')],
        'FIR_02':[(24,'法阵与陨石'),(42,'陨石落地'),(75,'范围爆燃'),(180,'余焰消散')],
        'FIR_04':[(28,'逐点起焰'),(65,'火舌上流'),(145,'停止喷发'),(174,'余焰淡出')],
        'FIR_03':[(25,'护盾展开'),(65,'完整包覆脚部'),(135,'结束退亮'),(165,'透明消散')]}

def video(path,frames,size):
 with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=FPS)
  stream.width,stream.height=size;stream.pix_fmt='yuv420p'
  stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  for n,im in enumerate(frames):
   f=av.VideoFrame.from_image(im);f.pts=n;f.time_base=Fraction(1,FPS)
   for packet in stream.encode(f):movie.mux(packet)
  for packet in stream.encode():movie.mux(packet)

def label(draw,xy,value,size=24,color='#efbb7f'):
 draw.text(xy,value,font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size),fill=color)

def summary(shot):
 events=shot['events'];last=shot['metrics'][-1]
 casts=[e for e in events if e['type']=='skill_cast' and e.get('skillId')==shot['id']]
 releases=[e for e in events if e['type']=='skill_release' and e.get('skillId')==shot['id']]
 hits=[e for e in events if e['type']=='hit' and float(e.get('hpLost',0))>0]
 return {'casts':len(casts),'releases':len(releases),'hits':last['hits'],'damage':last['damage'],
         'positiveHitEvents':len(hits),'hitEventDamage':sum(float(e['hpLost']) for e in hits),
         'misses':last['misses'],'criticalHits':last['criticalHits'],
         'peakFire':max(len(m['fire']['active']) for m in shot['metrics']),
         'peakGround':max(len(m['ground']['active']) for m in shot['metrics']),
         'maxCooldown':max(m['cooldowns'].get(shot['id'],0) for m in shot['metrics']),
         'endFireCleared':not last['fire']['active'],'endGroundCleared':not last['ground']['active'],
         'endMeteorCleared':not last['meteor']['active']}

def animation_signature(snapshot):
 return json.dumps({'fire':[(s['key'],s['phase'],s.get('frameBlend')) for s in snapshot['fire']['active']],
                    'ground':[(s['key'],s['frames']) for s in snapshot['ground']['active']]},sort_keys=True)

def validate(report,shots,cache):
 assert report['stableBuild'] and not report['errors'] and not report['consoleErrors']
 info=report['info']
 assert info['area']=='TRAINING' and info['cameraBound']
 assert info['viewport']==[2560,1272] and info['cameraHeight']==4.3
 assert info['activeSlots']==['FIR_01','FIR_04','FIR_03','FIR_05'] and info['ultimate']=='FIR_02'
 checks={}
 for shot in shots:
  last=shot['metrics'][-1]
  folder=cache/shot['id'];assert len(list(folder.glob('[0-9][0-9][0-9].jpg')))==shot['frames']
  assert len(shot['metrics'])==shot['frames'] and all(m['cameraHeight']==4.3 for m in shot['metrics'])
  result=summary(shot)
  assert result['casts']==1 and result['releases']==1,(shot['id'],result)
  assert (result['hits']>0 or shot['id']=='FIR_03' or info.get('emptyGround')) and result['positiveHitEvents']==result['hits']
  if info.get('emptyGround'):assert result['hits']==0 and result['damage']==0
  assert abs(result['hitEventDamage']-result['damage'])<1e-6
  assert result['endFireCleared'] and result['endGroundCleared'] and result['endMeteorCleared']
  assert all(len(m['fire']['active'])<=m['fire']['capacity'] for m in shot['metrics'])
  assert all(len(m['ground']['active'])<=m['ground']['capacity'] for m in shot['metrics'])
  if shot['id']!='FIR_02':
   assert not any(s['kind']=='meteorSeal' for m in shot['metrics'] for s in m['ground']['active'])
  if shot['id']=='FIR_04':
   assert any(s['kind']=='jets' and s['emitters']==5 for m in shot['metrics'] for s in m['ground']['active'])
  if shot['id']=='FIR_03':
   assert result['hits']==0 and result['damage']==0
   assert any(m['shield']['visible'] and m['shield']['family']=='FIR' for m in shot['metrics'])
   assert not last['shield']['visible']
  checks[shot['id']]=result
 for test in report.get('lifecycle',[]):
  assert test['pauseStable'],test['id']
  assert not test['paused']['fire']['active'] and not test['paused']['ground']['active']
  assert not test['paused']['meteor']['active'] and not test['paused']['shield']['visible']
  assert not test['reset']['fire']['active'] and not test['reset']['ground']['active']
  assert not test['reset']['meteor']['active'] and not test['reset']['shield']['visible']
  if test['id']=='FIR_03':assert test['resumed']['shield']['visible']
  else:assert test['resumed']['fire']['active'] or test['resumed']['ground']['active']
  if test['id']!='FIR_03':assert animation_signature(test['reducedMotionFirst'])!=animation_signature(test['reducedMotionSecond']),test['id']
 for switch in report.get('switches',[]):
  assert switch['after']['family']==switch['family']
  assert not switch['after']['fire']['active'] and not switch['after']['ground']['active']
  assert not switch['after']['meteor']['active'] and not switch['after']['shield']['visible']
 return checks

def verification(args,report,checks,encoded):
 comparison=None;before_file=HERE/f'before-r{args.rank}'/'verification.json'
 if not report.get('emptyGround') and args.stage in ('after','final') and before_file.exists():
  before=json.loads(before_file.read_text(encoding='utf8'));comparison={}
  for skill,result in checks.items():
   old=before['skills'].get(skill)
   if old:
    fields=['casts','releases','hits','damage','positiveHitEvents','misses','criticalHits','maxCooldown']
    comparison[skill]={'unchanged':all(abs(old[f]-result[f])<1e-8 for f in fields),'before':{f:old[f] for f in fields},'after':{f:result[f] for f in fields}}
 return {'gameHash':report['gameHash'],'stableBuildDuringCapture':True,'rank':args.rank,'emptyGround':report.get('emptyGround',False),
         'nativeCanvas':[2560,1272],'normalRangeHUDAndCamera':True,'realInputsAndHitEvents':True,
         'frameAlteration':'Full per-skill videos encode actual canvas JPEGs only. Reel/details use labelled crop/resize/layout only.',
         'skills':checks,'gameplayComparison':comparison,'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],
         'lifecycle':{'pauseResume':len(report.get('lifecycle',[])),
                      'reducedMotionAnimates':[s['id'] for s in report.get('lifecycle',[]) if s['id']!='FIR_03' and animation_signature(s['reducedMotionFirst'])!=animation_signature(s['reducedMotionSecond'])],
                      'familySwitches':[s['family'] for s in report.get('switches',[])]},
         'mediaEncoded':encoded,'visualAcceptance':'Pending visual inspection and user review; recording completion is not art approval.',
         'taptapDeviceValidation':'Not performed by this browser recording.'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',default='after');parser.add_argument('--rank',type=int,default=1);parser.add_argument('--verify-only',action='store_true');parser.add_argument('--empty',action='store_true')
 args=parser.parse_args();folder=HERE/f'{args.stage}{"-empty" if args.empty else ""}-r{args.rank}'
 report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
 shots=[json.loads((folder/(s['id']+'.json')).read_text(encoding='utf8')) for s in report['shots']]
 cache=ROOT/report['cache'];media=folder/'media';media.mkdir(exist_ok=True)
 checks=validate(report,shots,cache)
 if args.verify_only:
  result=verification(args,report,checks,False)
  (folder/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(json.dumps(result,ensure_ascii=False));return
 def frame(shot,index):return Image.open(cache/shot['id']/f'{index:03}.jpg').convert('RGB')
 for shot in shots:
  skill=shot['id'];clip=media/(skill+'.mp4')
  video(clip,(frame(shot,i) for i in range(shot['frames'])),(2560,1272))
  with av.open(str(clip)) as movie:assert sum(1 for _ in movie.decode(video=0))==shot['frames']
  contact=Image.new('RGB',(1536,870),'#1d1916');draw=ImageDraw.Draw(contact)
  for n,(i,title) in enumerate(STAGES[skill]):
   i=min(i,shot['frames']-1);x=n%2*768;y=n//2*435
   label(draw,(x+16,y+9),f'{NAMES[skill]}  {i/FPS:.2f}s · {title}',22)
   contact.paste(frame(shot,i).resize((768,382),Image.Resampling.LANCZOS),(x,y+48))
  contact.save(media/(skill+'-stages.jpg'),quality=95,subsampling=0)
  frame(shot,STAGES[skill][1][0]).save(media/(skill+'.jpg'),quality=95,subsampling=0)
 # This reel adds a title above each resized native frame. The full-resolution
 # per-skill videos above preserve the complete canvas without any overlays.
 def reel():
  for shot in shots:
   for i in range(shot['frames']):
    canvas=Image.new('RGB',(1280,700),'#1d1916');draw=ImageDraw.Draw(canvas)
    label(draw,(20,16),NAMES[shot['id']]+'  |  '+('无靶空地轮廓 · 同一默认镜头与 HUD' if args.empty else '真实训练场 · 默认镜头与 HUD'),25)
    canvas.paste(frame(shot,i).resize((1280,636),Image.Resampling.LANCZOS),(0,64))
    yield canvas
 video(media/'fire-family-native-reel.mp4',reel(),(1280,700))
 # Same crop for every skill, keeping real camera perspective and timings.
 # Clearly labelled details are not a replacement for the full-canvas videos.
 for shot in shots:
  end=min(shot['frames'],210)
  detail=[]
  for i in range(12,end,3):
   canvas=Image.new('RGB',(900,736),'#1d1916');draw=ImageDraw.Draw(canvas)
   label(draw,(16,9),NAMES[shot['id']]+' · 实录局部',23)
   im=frame(shot,i).crop((360,380,1530,1272)).resize((900,686),Image.Resampling.LANCZOS)
   canvas.paste(im,(0,50));detail.append(canvas)
  detail[0].save(media/(shot['id']+'-detail.webp'),save_all=True,append_images=detail[1:],duration=100,loop=0,quality=84,method=4)
 # Compare real hit events and cooldowns independently of the visual change.
 result=verification(args,report,checks,True)
 (folder/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
