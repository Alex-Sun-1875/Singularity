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
STAGES={'FIR_01':[(16,'抬手聚焰'),(19,'火矛前进'),(25,'命中展开'),(47,'余焰消散')],
        'FIR_05':[(26,'地面起焰'),(63,'持续燃烧'),(145,'停止输出'),(175,'余火淡出')],
        'FIR_02':[(24,'法阵与陨石'),(42,'陨石落地'),(75,'范围爆燃'),(180,'余焰消散')],
        'FIR_04':[(28,'逐点起焰'),(65,'火舌上流'),(145,'停止喷发'),(174,'余焰淡出')],
        'FIR_03':[(25,'护盾展开'),(65,'完整包覆脚部'),(135,'结束退亮'),(165,'透明消散')]}
EMPTY_LANCE_STAGES=[(16,'凝焰出手'),(19,'穿刺火矛'),(24,'飞行伸展'),(33,'飞离画面')]

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

def contact_detail(image):
 canvas=Image.new('RGB',(800,804),'#1d1916');draw=ImageDraw.Draw(canvas)
 label(draw,(18,17),'火矛接触 · 实景录制局部 · 原镜头',24)
 canvas.paste(image.crop((600,710,1000,1080)).resize((800,740),Image.Resampling.LANCZOS),(0,64))
 return canvas

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
         'peakFieldSurfaces':max(len(m['fire'].get('field',{}).get('active',[])) for m in shot['metrics']),
         'peakImpactSurfaces':max(len(m['fire'].get('impact',{}).get('active',[])) for m in shot['metrics']),
         'renderedKinds':sorted({s.get('kind','unknown') for m in shot['metrics'] for s in m['fire']['active']}),
         'endFireCleared':not last['fire']['active'],'endGroundCleared':not last['ground']['active'],
         'endMeteorCleared':not last['meteor']['active']}

def animation_signature(snapshot):
 return json.dumps({'fire':[(s['key'],s['phase'],s.get('frameBlend')) for s in snapshot['fire']['active']],
                    'ground':[(s['key'],s['frames']) for s in snapshot['ground']['active']]},sort_keys=True)

def visible(snapshot):
 return bool(snapshot['fire']['active'] or snapshot['ground']['active'] or snapshot['meteor']['active'] or snapshot['shield']['visible'])

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
  assert all(m['fire']['model']=='distinct-fire-shapes-v30' for m in shot['metrics'])
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
  if shot['id']=='FIR_01':
   assert any(s.get('kind')=='lance' and s['width']>s['height']*2 for m in shot['metrics'] for s in m['fire']['active'])
  if shot['id']=='FIR_05':
   fields=[s for m in shot['metrics'] for s in m['fire']['field']['active']]
   assert fields and all(s['connectedSurfaces']==1 for s in fields)
   release=next(e['time'] for e in shot['events'] if e['type']=='skill_release')
   assert all(len(m['fire']['field']['active'])<=1 for m in shot['metrics'] if m['time']>release+.4)
  if shot['id']=='FIR_02':
   impacts=[s for m in shot['metrics'] for s in m['fire']['impact']['active']]
   assert any(s['kind']=='meteor' for s in impacts)
   if report['rank']==1:assert result['peakImpactSurfaces']<=1
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
  if visible(test['before']):assert visible(test['resumed']),test['id']
  if report.get('recorderRevision',1)>=2:assert visible(test['before']),test['id']
  if test['id']!='FIR_03' and (visible(test['reducedMotionFirst']) or report.get('recorderRevision',1)>=2):
   assert animation_signature(test['reducedMotionFirst'])!=animation_signature(test['reducedMotionSecond']),test['id']
 for switch in report.get('switches',[]):
  assert switch['after']['family']==switch['family']
  assert not switch['after']['fire']['active'] and not switch['after']['ground']['active']
  assert not switch['after']['meteor']['active'] and not switch['after']['shield']['visible']
 return checks

def verification(args,report,checks,encoded):
 comparison=None;before_file=HERE.parent/'fire-family-wisps-v28'/f'before-r{args.rank}'/'verification.json'
 same_sequence=[s['id'] for s in report['shots']][:4]==['FIR_01','FIR_05','FIR_02','FIR_04']
 if not report.get('emptyGround') and not report.get('singleTarget') and before_file.exists():
  before=json.loads(before_file.read_text(encoding='utf8'));comparison={}
  for skill,result in checks.items():
   old=before['skills'].get(skill)
   if old:
    fields=['casts','releases','hits','damage','positiveHitEvents','misses','criticalHits','maxCooldown']
    comparison[skill]={'sameSequence':same_sequence,'numbersEqual':all(abs(old[f]-result[f])<1e-8 for f in fields),'before':{f:old[f] for f in fields},'after':{f:result[f] for f in fields}}
 return {'gameHash':report['gameHash'],'stableBuildDuringCapture':True,'rank':args.rank,'emptyGround':report.get('emptyGround',False),'singleTarget':report.get('singleTarget',False),
         'nativeCanvas':[2560,1272],'normalRangeHUDAndCamera':True,'realInputsAndHitEvents':True,
         'frameAlteration':'Full per-skill videos encode actual canvas JPEGs only. Reel/details use labelled crop/resize/layout only.',
         'skills':checks,'gameplayComparison':comparison,'comparisonBasis':'Complete fixed skill sequence' if same_sequence else 'Independent selected cast; RNG sequence position differs from full baseline',
         'gameplayUnchanged':all(s['numbersEqual'] for s in comparison.values()) if comparison and same_sequence else None,'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],
         'lifecycle':{'pauseResume':len(report.get('lifecycle',[])),
                      'activeVisualRestored':[s['id'] for s in report.get('lifecycle',[]) if visible(s['before']) and visible(s['resumed'])],
                      'reducedMotionAnimates':[s['id'] for s in report.get('lifecycle',[]) if s['id']!='FIR_03' and animation_signature(s['reducedMotionFirst'])!=animation_signature(s['reducedMotionSecond'])],
                      'familySwitches':[s['family'] for s in report.get('switches',[])]},
         'mediaEncoded':encoded,'visualAcceptance':'Pending visual inspection and user review; recording completion is not art approval.',
         'taptapDeviceValidation':'Not performed by this browser recording.'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',default='after');parser.add_argument('--rank',type=int,default=1);parser.add_argument('--verify-only',action='store_true');parser.add_argument('--empty',action='store_true');parser.add_argument('--single',action='store_true');parser.add_argument('--details',action='store_true');parser.add_argument('--only',default='')
 args=parser.parse_args();folder=HERE/f'{args.stage}{"-empty" if args.empty else "-single" if args.single else ""}-r{args.rank}'
 report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
 shots=[json.loads((folder/(s['id']+'.json')).read_text(encoding='utf8')) for s in report['shots']]
 cache=ROOT/report['cache'];media=folder/'media';media.mkdir(exist_ok=True)
 checks=validate(report,shots,cache)
 if args.verify_only:
  result=verification(args,report,checks,False)
  (folder/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  assert result['gameplayUnchanged'] is not False,'Actual gameplay differs from before-r1; inspect recorded hit/cooldown evidence'
  print(json.dumps(result,ensure_ascii=False));return
 encode_shots=[s for s in shots if not args.only or s['id'] in args.only.split(',')]
 assert encode_shots,'No matching skills selected for media export'
 def frame(shot,index):return Image.open(cache/shot['id']/f'{index:03}.jpg').convert('RGB')
 for shot in encode_shots:
  skill=shot['id'];clip=media/(skill+'.mp4')
  stages=EMPTY_LANCE_STAGES if args.empty and skill=='FIR_01' else STAGES[skill]
  video(clip,(frame(shot,i) for i in range(shot['frames'])),(2560,1272))
  with av.open(str(clip)) as movie:assert sum(1 for _ in movie.decode(video=0))==shot['frames']
  contact=Image.new('RGB',(1536,870),'#1d1916');draw=ImageDraw.Draw(contact)
  for n,(i,title) in enumerate(stages):
   i=min(i,shot['frames']-1);x=n%2*768;y=n//2*435
   label(draw,(x+16,y+9),f'{NAMES[skill]}  {i/FPS:.2f}s · {title}',22)
   contact.paste(frame(shot,i).resize((768,382),Image.Resampling.LANCZOS),(x,y+48))
  contact.save(media/(skill+'-stages.jpg'),quality=95,subsampling=0)
  frame(shot,stages[1][0]).save(media/(skill+'.jpg'),quality=95,subsampling=0)
  if args.single and skill=='FIR_01':contact_detail(frame(shot,25)).save(media/'FIR_01-contact-detail.jpg',quality=95,subsampling=0)
 # Keep the three redesigned abilities in the main preview. Regressions remain
 # in the complete per-skill videos. The empty-ground reel is a labelled crop;
 # the normal-hit reel and every per-skill video preserve the whole canvas.
 preview=[s for s in encode_shots if s['id'] in ('FIR_01','FIR_05','FIR_02')]
 make_preview=not args.single and {s['id'] for s in preview}=={'FIR_01','FIR_05','FIR_02'}
 reel_name='fire-three-skills-empty.mp4' if args.empty else 'fire-three-skills-hits.mp4'
 def reel():
  for shot in preview:
   for i in range(shot['frames']):
    canvas=Image.new('RGB',(1280,868 if args.empty else 700),'#1d1916');draw=ImageDraw.Draw(canvas)
    label(draw,(20,16),NAMES[shot['id']]+'  |  '+('实景录制局部 · 原镜头' if args.empty else '真实命中 · 完整画布与 HUD'),25)
    image=frame(shot,i)
    if args.empty:image=image.crop((0,330,1500,1272))
    canvas.paste(image.resize((1280,804 if args.empty else 636),Image.Resampling.LANCZOS),(0,64))
    yield canvas
 if make_preview:video(media/reel_name,reel(),(1280,868 if args.empty else 700))
 # Same crop for every skill, keeping real camera perspective and timings.
 # Clearly labelled details are not a replacement for the full-canvas videos.
 for shot in encode_shots if args.details else []:
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
 result['media']={'primaryReel':reel_name if make_preview else None,
                  'nativePerSkillVideos':[s['id']+'.mp4' for s in encode_shots],
                  'preview':'Actual canvas crop and title only' if args.empty else 'Complete actual canvas without overlay' if args.single else 'Complete actual canvas with title',
                  'optionalDetailWebP':args.details}
 (folder/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 assert result['gameplayUnchanged'] is not False,'Actual gameplay differs from before-r1; inspect recorded hit/cooldown evidence'
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
