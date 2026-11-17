"""Export actual 9-second Cocos meteor casts; technical checks are not art approval."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, math, shutil
import av
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FPS=30
STAGES=[(0,'岩尖触地 · 实际首次冲击帧'),(.05,'冲击开始'),(.25,'火浪前锋外扩'),(.65,'立体翻卷'),(1.25,'爆燃后收势'),(1.65,'收势向余火过渡'),(4.60,'退火结束')]
REFERENCE=HERE/'assets/approved-reference.png'
CROP=(0,0,1550,1272)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def label(draw,xy,value,size=24,color='#efbb7f'):
 draw.text(xy,value,font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size),fill=color)

def video(path,frames,size):
 with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
  stream=movie.add_stream('libx264',rate=FPS);stream.width,stream.height=size
  stream.pix_fmt='yuv420p';stream.options={'crf':'16','preset':'veryfast'};stream.codec_context.thread_count=3
  for n,image in enumerate(frames):
   frame=av.VideoFrame.from_image(image);frame.pts=n;frame.time_base=Fraction(1,FPS)
   for packet in stream.encode(frame):movie.mux(packet)
  for packet in stream.encode():movie.mux(packet)

def load(folder):
 report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
 shot=json.loads((folder/'FIR_02.json').read_text(encoding='utf8'))
 return report,shot,ROOT/report['cache']/'FIR_02'

def summary(shot):
 metrics=shot['metrics'];last=metrics[-1];events=shot['events']
 hits=[e for e in events if e['type']=='hit' and float(e.get('hpLost',0))>0]
 volumes=[s for m in metrics for s in m['fire'].get('impact',{}).get('active',[]) if s.get('kind')=='meteor']
 return {'casts':sum(e['type']=='skill_cast' and e.get('skillId')=='FIR_02' for e in events),
         'releases':sum(e['type']=='skill_release' and e.get('skillId')=='FIR_02' for e in events),
         'hits':last['hits'],'damage':last['damage'],'positiveHitEvents':len(hits),
         'hitEventDamage':sum(float(e['hpLost']) for e in hits),'misses':last['misses'],'criticalHits':last['criticalHits'],
         'maxCooldown':max(m['cooldowns'].get('FIR_02',0) for m in metrics),
         'peakActiveFireRecords':max(len(m['fire']['active']) for m in metrics),
         'peakReportedImpactHeight':max([s.get('maxHeight',s.get('height',0)) for s in volumes]+[0]),
         'peakReportedImpactVertices':max([s.get('vertices',0) for s in volumes]+[0]),
         'peakReportedFrontRadius':max([s['frontRadius'] for s in volumes if 'frontRadius' in s],default=None),
         'peakReportedLayers':max([s['layers'] for s in volumes if 'layers' in s],default=None),
         'peakReportedLayerHeight':max([s['peakHeight'] for s in volumes if 'peakHeight' in s],default=None),
         'clearedAtEnd':not(last['fire']['active'] or last['ground']['active'] or last['meteor']['active'])}

def visible(snapshot):return bool(snapshot['fire']['active'] or snapshot['ground']['active'] or snapshot['meteor']['active'])
def motion(snapshot):
 return json.dumps({'fire':snapshot['fire']['active'],'ground':snapshot['ground']['active']},sort_keys=True)

def verify(report,shot,cache):
 assert report['stableBuild'] and not report['errors'] and not report['consoleErrors']
 assert report['info']['area']=='TRAINING' and report['info']['viewport']==[2560,1272]
 assert report['journeyStart']['level']==1 and not report['journeyStart']['temporaryMax']
 assert report['info']['rangeSessionIsSeparate']
 expected_max=report['info'].get('rangeMaxLevel')
 if expected_max is None:
  evidence=HERE/f"{report['stage']}{'-empty' if report['emptyGround'] else ''}-r{report['rank']}"/'progression-contract-evidence.json'
  expected_max=json.loads(evidence.read_text(encoding='utf8'))['sourceMaxLevel']
 assert report['info']['rangeCharacterLevel']==expected_max
 restored=report['journeyRestoration']
 assert restored['sessionRestored'] and restored['level']==1 and restored['progressionUnchanged'] and restored['equipmentUnchanged'] and restored['trainingRangeAbsent']
 assert report['info']['cameraHeight']==4.3 and all(m['cameraHeight']==4.3 for m in shot['metrics'])
 assert shot['frames']==270 and len(shot['metrics'])==270
 assert len(list(cache.glob('[0-9][0-9][0-9].jpg')))==270
 result=summary(shot)
 assert result['casts']==1 and result['releases']==1
 assert result['hits']==result['positiveHitEvents'] and abs(result['damage']-result['hitEventDamage'])<1e-6
 assert result['clearedAtEnd']
 if report['emptyGround']:assert result['hits']==0 and result['damage']==0
 else:assert result['hits']>0
 for metric in shot['metrics']:
  assert len(metric['fire']['active'])<=metric['fire']['capacity']
  assert len(metric['ground']['active'])<=metric['ground']['capacity']
 for test in report.get('lifecycle',[]):
  assert test['pauseStable'] and visible(test['before']) and visible(test['resumed'])
  assert not visible(test['paused']) and not visible(test['reset'])
  assert motion(test['reducedMotionFirst'])!=motion(test['reducedMotionSecond'])
 for switch in report.get('switches',[]):
  assert switch['after']['family']==switch['family'] and not visible(switch['after'])
 return result


def stages(shot):
 events=shot['events'];metrics=shot['metrics']
 cast=next(e for e in events if e['type']=='skill_cast' and e.get('skillId')=='FIR_02')
 impact=next(e for e in events if e['type']=='skill_segment' and e.get('skillId')=='FIR_02' and e.get('segment')==0)
 falling=[m for m in metrics if m['time']<impact['time'] and m['meteor']['active']]
 assert falling,'Actual meteor body never became visible before the resolved impact'
 first,last=falling[0],falling[-1];out=[]
 def append(metric,slug,title,kind,**requested):
  out.append({'slug':slug,'title':title,'kind':kind,'frame':metric['frame'],'nativeTime':metric['time'],
              'castAge':metric['time']-cast['time'],'impactAge':metric['time']-impact['time'],
              'meteorInspect':metric['meteor'],'groundInspect':metric['ground'],'impactInspect':metric['fire'].get('impact',{}),**requested})
 for age in [.2,.6]:
  metric=min(metrics,key=lambda m:abs(m['time']-(cast['time']+age)))
  append(metric,f'cast-{round(age*1000):04}ms',f'施法 {age:.2f}s · 真实状态','cast-timing',requestedCastAge=age)
 for progress in [.2,.6]:
  with_progress=[m for m in falling if isinstance(m['meteor']['active'][0].get('progress'),(int,float))]
  if with_progress:
   metric=min(with_progress,key=lambda m:abs(m['meteor']['active'][0]['progress']-progress));basis='Actual meteor.inspect progress'
  else:
   metric=min(falling,key=lambda m:abs(m['time']-(first['time']+(last['time']-first['time'])*progress)));basis='Observed active meteor interval; not an authored trajectory progress or viewport visibility claim'
  append(metric,f'fall-{round(progress*100):02}',f'下落进度 {round(progress*100)}%','fall',requestedFallProgress=progress,selectionBasis=basis)
 append(last,'pre-impact','着陆前 · 最后真实可见帧','pre-impact')
 for age,title in STAGES:
  candidates=[m for m in metrics if m['time']>=impact['time']-1e-8] if age==0 else metrics
  metric=min(candidates,key=lambda m:abs(m['time']-(impact['time']+age)))
  append(metric,f'impact-{round(age*1000):04}ms',f'{metric["time"]-impact["time"]:.2f}s · {title}','impact',requestedImpactAge=age)
 return out,{'castTime':cast['time'],'impactTime':impact['time'],'resolvedWindup':impact['time']-cast['time'],
             'firstActiveMeteorTime':first['time'],'lastActiveMeteorTime':last['time'],
             'observedActiveFallSeconds':last['time']-first['time'],'firstActiveMeteorFrame':first['frame'],'lastActiveMeteorFrame':last['frame']}

def target_alignment(shot):
 relevant=[e for e in shot['events'] if e.get('skillId')=='FIR_02' and (e['type'] in ('skill_cast','skill_release') or e['type']=='skill_segment' and e.get('segment')==0)]
 def point(event):return event.get('at') or event.get('to') or event['from']
 target=point(relevant[0]);assert all(abs(point(e)[axis]-target[axis])<1e-6 for e in relevant for axis in ('x','z'))
 cues=[cue for m in shot['metrics'] for cue in m['native']['cues'] if cue['skillId']=='FIR_02' and cue['kind'] in ('drop','blast')]
 assert all(abs(cue['target'][axis]-target[axis])<1e-6 for cue in cues for axis in ('x','z'))
 bodies=[body for m in shot['metrics'] for body in m['meteor']['active']]
 assert bodies and all(body.get('target') is not None for body in bodies)
 assert all(abs(body['target'][axis]-target[axis])<1e-6 for body in bodies for axis in ('x','z'))
 contact_frames=[m for m in shot['metrics'] if m.get('impactAge') is not None and -1e-8<=m['impactAge']<=.045+1e-8 and any(body.get('progress',0)>=.999 for body in m['meteor']['active']) and any(cue['kind']=='blast' and cue['skillId']=='FIR_02' for cue in m['native']['cues'])]
 contacts=[body for metric in contact_frames for body in metric['meteor']['active'] if body.get('progress',0)>=.999]
 assert contacts,'No real meteor nose contact sample was recorded'
 errors=[math.sqrt(sum((body['nose'][axis]-body['target'][axis])**2 for axis in ('x','y','z'))) for body in contacts]
 assert max(errors)<.0001,'Actual meteor nose did not reach the resolved ground target'
 angles=[body['screen']['projectedDescentAngleDegrees'] for body in bodies if body.get('screen') and body.get('progress',0)<.98]
 return {'eventTarget':target,'eventAndDropBlastCueTargetsEqual':True,'castIds':sorted(set(e['castId'] for e in relevant)),
         'meteorBodyTargetsEqual':True,'meteorLandingHeights':sorted(set(body['target']['y'] for body in bodies)),
         'actualCameraProjectedDescentAnglesDegrees':{'min':min(angles),'max':max(angles)} if angles else None,
         'realRockContactRecorded':True,'contactSamples':contacts,'maxNoseContactErrorMetres':max(errors),
         'contactFrames':[{'frame':m['frame'],'impactAge':m['impactAge'],'meteor':m['meteor'],'blastCues':[c for c in m['native']['cues'] if c['kind']=='blast' and c['skillId']=='FIR_02']} for m in contact_frames],
         'qualification':'This checks actual event/cue anchors. Native stage images must still establish visible rock, flame and seal alignment.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='after');p.add_argument('--rank',type=int,default=1);p.add_argument('--empty',action='store_true');p.add_argument('--verify-only',action='store_true');p.add_argument('--local-candidate',action='store_true')
 args=p.parse_args();folder=HERE/f'{args.stage}{"-empty" if args.empty else ""}-r{args.rank}'
 report,shot,cache=load(folder);result=verify(report,shot,cache);points,timing=stages(shot);alignment=target_alignment(shot)
 baseline=ROOT/f'source-art/skills/meteor-volume-v31/after7{"-empty" if args.empty else ""}-r{args.rank}'
 # v31 has no v32 journey evidence. Its recorded technical result remains historical.
 old_report,old_shot,old_cache=load(baseline);old=summary(old_shot)
 fields=['casts','releases','hits','damage','positiveHitEvents','misses','criticalHits','maxCooldown']
 comparison={'baselineDirectory':str(baseline.relative_to(ROOT)),'baselineArtStatus':'user-rejected-v29-reference-mismatch',
             'baselineCompiledSha256':old_report['gameHash'],'sameIndependentSkillSequence':True,
             'numbersEqual':all(abs(old[k]-result[k])<1e-8 for k in fields),'before':{k:old[k] for k in fields},'after':{k:result[k] for k in fields}}
 comparison['beforeCharacterLevel']=old_report['info']['gameplaySnapshot']['progression']['level']
 comparison['afterCharacterLevel']=report['info']['rangeCharacterLevel']
 comparison['sameCharacterLevel']=comparison['beforeCharacterLevel']==comparison['afterCharacterLevel']
 comparison['qualification']='Recorded current hit/damage/cooldown events remain authoritative. Concurrent CampaignProgression changes moved the isolated training maximum from 40 to 80; cross-level baseline damage equality is not claimed.' if not comparison['sameCharacterLevel'] else 'Same isolated training level; compare actual event totals.'
 verification={'compiledSha256':report['gameHash'],'sourceHashes':report['sourceHashes'],'stableBuildDuringCapture':True,
               'shaderAssetEvidence':'shader-asset-evidence.json','emptyGround':args.empty,'nativeCanvas':[2560,1272],
               'frames':270,'seconds':9,'fps':FPS,'defaultCameraAndCompleteHUDInNativeVideo':True,
               'journeyStart':report['journeyStart'],'journeyRestoration':report['journeyRestoration'],
               'temporaryRangeCharacterLevel':report['info']['rangeCharacterLevel'],'runtimeRangeMaxLevel':report['info'].get('rangeMaxLevel'),'progressionContractEvidence':'progression-contract-evidence.json' if (folder/'progression-contract-evidence.json').exists() else None,'actualResults':result,
               'gameplayComparison':comparison,'trajectoryTiming':timing,'targetAlignment':alignment,'representativeStages':points,
               'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],
               'lifecycle':{'pauseResume':len(report.get('lifecycle',[])),'familySwitches':[s['family'] for s in report.get('switches',[])]},
               'artStatus':'local-native-candidate-user-review-pending' if args.local_candidate else 'pending-native-reference-alignment-review',
               'artStatusNote':'v31 was rejected. Both original v29 bottom panels must be compared with true descent, contact and decay. Runtime success and anchor equality are not art acceptance.',
               'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','mediaEncoded':False}
 def write():(folder/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 write();assert comparison['numbersEqual'] or not comparison['sameCharacterLevel'],'Same-level actual gameplay numbers changed; retain data and inspect core/seed evidence before claiming equality'
 if args.verify_only:print(json.dumps(verification,ensure_ascii=False));return
 media=folder/'media';media.mkdir(exist_ok=True)
 def raw(index):return Image.open(cache/f'{index:03}.jpg').convert('RGB')
 native=media/'FIR_02-native.mp4';video(native,(raw(i) for i in range(270)),(2560,1272))
 closeup=media/'FIR_02-closeup.mp4';crop_size=(CROP[2]-CROP[0],CROP[3]-CROP[1]);video(closeup,(raw(i).crop(CROP) for i in range(270)),crop_size)
 for movie in (native,closeup):
  with av.open(str(movie)) as clip:assert sum(1 for _ in clip.decode(video=0))==270
 for point in points:shutil.copyfile(cache/f'{point["frame"]:03}.jpg',media/f'{point["slug"]}.jpg')
 refs=HERE/'references';refs.mkdir(exist_ok=True);source=Image.open(REFERENCE).convert('RGB');w,h=source.size
 reference_panels=[('v29 · 法阵预警 / 陨石下落',source.crop((round(w*.005),round(h*.64),round(w*.495),round(h*.94)))),
                   ('v29 · 中心冲击 / 余火渐退',source.crop((round(w*.505),round(h*.64),round(w*.995),round(h*.94))))]
 for n,(_,panel) in enumerate(reference_panels):panel.save(refs/f'v29-meteor-{["fall","impact"][n]}.png')
 selected=[point for point in points if point['kind']!='cast-timing']
 board=Image.new('RGB',(1800,math.ceil((len(selected)+2)/3)*480),'#1d1916');draw=ImageDraw.Draw(board)
 for n,(title,reference) in enumerate(reference_panels):
  x=n*600;label(draw,(x+16,14),title,24);im=ImageOps.contain(reference,(560,380),Image.Resampling.LANCZOS);board.paste(im,(x+20,70+(380-im.height)//2));label(draw,(x+16,445),'原稿静态参考 · 不代表已实装/已验收',18,color='#cfc3b5')
 for n,point in enumerate(selected,2):
  x=n%3*600;y=n//3*480;label(draw,(x+16,y+14),point['title'],23)
  im=ImageOps.contain(raw(point['frame']).crop(CROP),(560,410),Image.Resampling.LANCZOS);board.paste(im,(x+20,y+65+(410-im.height)//2))
 board.save(media/'reference-vs-native-stages.jpg',quality=95,subsampling=0)
 full=Image.new('RGB',(1800,math.ceil(len(selected)/3)*430),'#1d1916');draw=ImageDraw.Draw(full)
 for n,point in enumerate(selected):
  x=n%3*600;y=n//3*430;label(draw,(x+16,y+14),point['title'],23);full.paste(raw(point['frame']).resize((600,298),Image.Resampling.LANCZOS),(x,y+65))
 full.save(media/'native-full-canvas-stages.jpg',quality=95,subsampling=0)
 def curl_frame(s):
  impact=next(e['time'] for e in s['events'] if e['type']=='skill_segment' and e.get('skillId')=='FIR_02' and e.get('segment')==0)
  return min(s['metrics'],key=lambda m:abs(m['time']-(impact+.65)))['frame']
 pair=Image.new('RGB',(1600,740),'#1d1916');draw=ImageDraw.Draw(pair)
 for x,title,im in [(0,'v31 · 用户已否定的历史候选',Image.open(old_cache/f'{curl_frame(old_shot):03}.jpg').convert('RGB')),
                    (800,'v32 · 当前实际录制 / 待用户反馈',raw(curl_frame(shot)))]:
  label(draw,(x+16,15),title,25);im=ImageOps.contain(im.crop(CROP),(780,650),Image.Resampling.LANCZOS);pair.paste(im,(x+10,70))
 pair.save(media/'before-vs-after-native-curl.jpg',quality=95,subsampling=0)
 verification['mediaEncoded']=True;verification['media']={'nativeVideo':native.name,'nativeVideoSha256':sha(native),
  'nativeVideoAlteration':'Original complete canvas frames, recorded order and 9-second timing; no overlays.',
  'closeupVideo':closeup.name,'closeupVideoSha256':sha(closeup),'closeupVideoCanvas':crop_size,
  'closeupVideoAlteration':f'Crop only {CROP}, same camera/actors/time; no VFX/text overlays.',
  'referenceSource':str(REFERENCE),'referenceSha256':sha(REFERENCE),'comparisonImages':'Crop/resize/layout only; both v29 original bottom panels retained.'}
 write();print(json.dumps({'compiledSha256':report['gameHash'],'results':result,'comparison':comparison,'timing':timing,'media':str(media),'artStatus':verification['artStatus']},ensure_ascii=False))

if __name__=='__main__':main()
