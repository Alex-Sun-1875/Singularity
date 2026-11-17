"""Export actual 9-second Cocos meteor casts; technical checks are not art approval."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, math
import av
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FPS=30
STAGES=[(.05,'冲击开始'),(.25,'火浪前锋外扩'),(.65,'立体翻卷'),(1.25,'爆燃后收势'),(1.65,'收势向余火过渡'),(4.60,'退火结束')]
REFERENCE=ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
CROP=(0,150,1500,1272)

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
 event=next(e for e in shot['events'] if e['type']=='skill_segment' and e.get('skillId')=='FIR_02' and e.get('segment')==0)
 start=event['time'];out=[]
 for age,title in STAGES:
  metric=min(shot['metrics'],key=lambda m:abs(m['time']-(start+age)))
  out.append({'title':title,'requestedImpactAge':age,'frame':metric['frame'],
              'actualImpactAge':metric['time']-start,'cueImpactAge':metric.get('impactAge'),
              'impactInspect':metric['fire'].get('impact',{}),
              'otherFireInspect':{k:v for k,v in metric['fire'].items() if k not in ('active','impact')}})
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='after');p.add_argument('--baseline-stage',default='before');p.add_argument('--visual-baseline-stage',default='before');p.add_argument('--rank',type=int,default=1);p.add_argument('--empty',action='store_true');p.add_argument('--verify-only',action='store_true');p.add_argument('--local-candidate',action='store_true')
 args=p.parse_args();folder=HERE/f'{args.stage}{"-empty" if args.empty else ""}-r{args.rank}'
 report,shot,cache=load(folder);result=verify(report,shot,cache);points=stages(shot)
 comparison=None;before=HERE/f'{args.baseline_stage}{"-empty" if args.empty else ""}-r{args.rank}'
 if args.stage!='before' and (before/'capture.json').exists():
  old_report,old_shot,old_cache=load(before);old=verify(old_report,old_shot,old_cache)
  fields=['casts','releases','hits','damage','positiveHitEvents','misses','criticalHits','maxCooldown']
  comparison={'baselineStage':args.baseline_stage,'sameIndependentSkillSequence':True,'numbersEqual':all(abs(old[k]-result[k])<1e-8 for k in fields),
              'beforeCompiledSha256':old_report['gameHash'],'before':{k:old[k] for k in fields},'after':{k:result[k] for k in fields}}
 history=None;visual_before=HERE/f'{args.visual_baseline_stage}{"-empty" if args.empty else ""}-r{args.rank}'
 if args.stage!='before' and (visual_before/'capture.json').exists():
  visual_report,visual_shot,visual_cache=load(visual_before);visual_result=verify(visual_report,visual_shot,visual_cache)
  history={'stage':args.visual_baseline_stage,'compiledSha256':visual_report['gameHash'],'actualResults':visual_result,
           'numbersEqual':all(abs(visual_result[k]-result[k])<1e-8 for k in ['casts','releases','hits','damage','misses','criticalHits','maxCooldown']),
           'qualification':'Original rejected v30 visual baseline is separate from the adjacent gameplay baseline. Concurrent core edits and changed critical outcomes prevent claiming exact original gameplay equality; prior seed was not recorded.'}
 verification={'compiledSha256':report['gameHash'],'sourceHashes':report['sourceHashes'],'stableBuildDuringCapture':True,'shaderAssetEvidence':'shader-asset-evidence.json' if (folder/'shader-asset-evidence.json').exists() else None,
               'emptyGround':args.empty,'nativeCanvas':[2560,1272],'frames':270,'seconds':9,'fps':FPS,
               'defaultCameraAndCompleteHUDInNativeVideo':True,'actualResults':result,'gameplayComparison':comparison,'originalVisualBaseline':history,
               'representativeStages':points,'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],
               'lifecycle':{'pauseResume':len(report.get('lifecycle',[])),'familySwitches':[s['family'] for s in report.get('switches',[])]},
               'artStatus':'local-native-candidate-user-review-pending' if args.local_candidate else 'User rejected v30 meteor; this before recording is a rejected baseline.' if args.stage=='before' else 'Pending actual native visual review and user implementation-art feedback; mesh/density counts are not aesthetic approval.',
               'artStatusNote':'Locally reviewed candidate: prior vertical cut faces and rectangular base lines removed; front broad-lobe layering remains visible. Exact v29 appearance and user implementation-art approval are not claimed.' if args.local_candidate else 'Mesh/density counts are not aesthetic approval.',
               'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','mediaEncoded':False}
 def write():
  (folder/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 write()
 assert comparison is None or comparison['numbersEqual'],'Same-sequence actual results changed; inspect hit/cooldown events before claiming presentation-only change'
 if args.verify_only:print(json.dumps(verification,ensure_ascii=False));return
 media=folder/'media';media.mkdir(exist_ok=True)
 def raw(index):return Image.open(cache/f'{index:03}.jpg').convert('RGB')
 native=media/'FIR_02-native.mp4';video(native,(raw(i) for i in range(270)),(2560,1272))
 with av.open(str(native)) as clip:assert sum(1 for _ in clip.decode(video=0))==270
 closeup=media/'FIR_02-closeup.mp4';crop_size=(CROP[2]-CROP[0],CROP[3]-CROP[1])
 video(closeup,(raw(i).crop(CROP) for i in range(270)),crop_size)
 with av.open(str(closeup)) as clip:assert sum(1 for _ in clip.decode(video=0))==270
 refs=HERE/'references';refs.mkdir(exist_ok=True)
 source=Image.open(REFERENCE).convert('RGB');w,h=source.size
 reference=source.crop((round(w*.505),round(h*.65),round(w*.995),round(h*.94)))
 reference.save(refs/'v29-meteor-impact-review.png')
 board=Image.new('RGB',(1800,math.ceil((len(points)+1)/3)*480),'#1d1916');draw=ImageDraw.Draw(board)
 label(draw,(18,14),'v29 静态概念参考',25)
 ref=ImageOps.contain(reference,(560,410),Image.Resampling.LANCZOS);board.paste(ref,(20,65+(410-ref.height)//2))
 label(draw,(18,445),'仅对照风格、外冲与明暗；并非像素相同。',18,color='#cfc3b5')
 for n,point in enumerate(points,1):
  x=n%3*600;y=n//3*480
  label(draw,(x+16,y+14),f"{point['actualImpactAge']:.2f}s · {point['title']}",24)
  image=ImageOps.contain(raw(point['frame']).crop(CROP),(560,410),Image.Resampling.LANCZOS)
  board.paste(image,(x+20,y+65+(410-image.height)//2))
 board.save(media/'reference-vs-native-stages.jpg',quality=95,subsampling=0)
 # Keep one complete-canvas stage sheet alongside the labelled crops.
 full=Image.new('RGB',(1800,1000),'#1d1916');draw=ImageDraw.Draw(full)
 for n,point in enumerate(points):
  x=n%3*600;y=n//3*500
  label(draw,(x+16,y+14),f"{point['actualImpactAge']:.2f}s · {point['title']}",24)
  full.paste(raw(point['frame']).resize((600,298),Image.Resampling.LANCZOS),(x,y+70))
 if len(points)<6:
  label(draw,(1220,550),'完整实际画布 · 默认镜头/HUD',24)
  label(draw,(1220,600),'原生MP4保留9秒完整过程',22,color='#cfc3b5')
 full.save(media/'native-full-canvas-stages.jpg',quality=95,subsampling=0)
 if history:
  old_points=stages(visual_shot);before_point=old_points[2];after_point=points[2]
  pair=Image.new('RGB',(1600,680),'#1d1916');draw=ImageDraw.Draw(pair)
  baseline_title='before · v30用户已否定' if args.visual_baseline_stage=='before' else f'{args.visual_baseline_stage} · 历史候选实景'
  for x,title,image in [(0,baseline_title,Image.open(visual_cache/f"{before_point['frame']:03}.jpg").convert('RGB')),
                        (800,'after · 当前实际画面待反馈',raw(after_point['frame']))]:
   label(draw,(x+16,15),title,26)
   image=ImageOps.contain(image.crop(CROP),(780,600),Image.Resampling.LANCZOS);pair.paste(image,(x+10,65))
  pair.save(media/'before-vs-after-native-curl.jpg',quality=95,subsampling=0)
 verification['mediaEncoded']=True
 verification['media']={'nativeVideo':native.name,'nativeVideoSha256':sha(native),'nativeVideoAlteration':'none; original canvas JPEG frames encoded in recorded order',
                        'closeupVideo':closeup.name,'closeupVideoSha256':sha(closeup),'closeupVideoCanvas':crop_size,'closeupVideoAlteration':f'Native recording crop only, bounds {CROP}; original camera, actors, frame order and 9-second timing; no VFX/text overlays.',
                        'comparisonImages':'crop/resize/layout only; no generated or overlaid effects','referenceSource':str(REFERENCE),'referenceSha256':sha(REFERENCE)}
 write();print(json.dumps({'compiledSha256':report['gameHash'],'results':result,'comparison':comparison,'media':str(media),'nativeFrames':270,'artStatus':verification['artStatus']},ensure_ascii=False))

if __name__=='__main__':main()
