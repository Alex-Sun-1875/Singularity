"""Export actual 9-second Cocos meteor casts; technical checks are not art approval."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, math, shutil, sys
import av
from PIL import Image, ImageDraw, ImageFont, ImageOps
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ignition_review
import seal_review
import build_profile_evidence

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];FPS=30
STAGES=[(0,'岩尖触地 · 实际首次冲击帧'),(.05,'冲击开始'),(.25,'火浪前锋外扩'),(.65,'立体翻卷'),(1.25,'爆燃后收势'),(1.65,'收势向余火过渡'),(4.60,'退火结束')]
REFERENCE=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
CROP=(0,0,1550,1272)
COOLING_AGES=[1.2,1.4,1.6,1.8,2.2,2.8,3.5]
IGNITION_AGES=[0,.033,.066,.1,.15,.2,.3,.45,.65]

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
  fade=test['sealFade'];assert 3.6<=fade['beforeAge']<=3.9 and fade['opacityStableWhilePaused'] and fade['resetWhileSealActive']
  assert fade['pausedActiveOpacity'] is None and 0<fade['laterOpacity']<fade['resumedOpacity']<fade['beforeOpacity']<.9
 for switch in report.get('switches',[]):
  assert switch['after']['family']==switch['family'] and not visible(switch['after'])
  if switch['before']['family']=='FIR':assert switch['before']['exercisedActiveSeal']
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

def cooling_stages(shot):
 impact=next(e['time'] for e in shot['events'] if e['type']=='skill_segment' and e.get('skillId')=='FIR_02' and e.get('segment')==0)
 points=[]
 for age in COOLING_AGES:
  metric=min(shot['metrics'],key=lambda m:abs(m['time']-impact-age))
  points.append({'slug':f'cooling-{round(age*1000):04}ms','frame':metric['frame'],'requestedImpactAge':age,'actualImpactAge':metric['time']-impact,'impactInspect':metric['fire'].get('impact',{})})
 window=[m for m in shot['metrics'] if 1.2-1e-8<=m['time']-impact<=2.4+1e-8]
 bodies=[body for m in shot['metrics'] for body in m['meteor']['active'] if body.get('screen')]
 target=bodies[0]['screen']['target'];cx=target['x'];cy=1272-target['y']
 rear_roi=[round(cx-325),round(cy-258),round(cx+325),round(cy+82)]
 return {'requiredImpactAges':COOLING_AGES,'representativeStages':points,'fullWindowFrameRange':[window[0]['frame'],window[-1]['frame']],
         'fullWindowFrames':len(window),'allWindowNativeFramesRetained':True,'rearNativeRoi':rear_roi,
         'qualification':'Review the actual native images and every transition. Active pool records, mesh counts and eventual clearing do not prove an unbroken visible fire surface.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='final');p.add_argument('--rank',type=int,default=1);p.add_argument('--empty',action='store_true');p.add_argument('--verify-only',action='store_true');p.add_argument('--local-candidate',action='store_true');p.add_argument('--seal-provenance',type=Path)
 args=p.parse_args();folder=HERE/f'{args.stage}{"-empty" if args.empty else ""}-r{args.rank}'
 report,shot,cache=load(folder);result=verify(report,shot,cache);points,timing=stages(shot);alignment=target_alignment(shot);cooling=cooling_stages(shot);ignition=ignition_review.evidence(shot);held_seal=seal_review.evidence(shot)
 actual_profile=build_profile_evidence.extract(report,ROOT)
 (folder/'compiled-build-profile-evidence.json').write_text(json.dumps(actual_profile,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 baseline=ROOT/f'source-art/skills/meteor-ignition-glow-v34/final{"-empty" if args.empty else ""}-r{args.rank}'
 # Keep the actual v34 normal-entry capture as the immediately preceding baseline.
 old_report,old_shot,old_cache=load(baseline);old=summary(old_shot)
 fields=['casts','releases','hits','damage','positiveHitEvents','misses','criticalHits','maxCooldown']
 comparison={'baselineDirectory':str(baseline.relative_to(ROOT)),'baselineArtStatus':'v34-before-complete-sigil-and-lifecycle-refinement',
             'baselineCompiledSha256':old_report['gameHash'],'sameIndependentSkillSequence':True,
             'numbersEqual':all(abs(old[k]-result[k])<1e-8 for k in fields),'before':{k:old[k] for k in fields},'after':{k:result[k] for k in fields}}
 comparison['beforeCharacterLevel']=old_report['info']['gameplaySnapshot']['progression']['level']
 comparison['afterCharacterLevel']=report['info']['rangeCharacterLevel']
 comparison['sameCharacterLevel']=comparison['beforeCharacterLevel']==comparison['afterCharacterLevel']
 comparison['sourceHashDifferences']={name:{'before':value,'after':report['sourceHashes'].get(name)} for name,value in old_report['sourceHashes'].items() if report['sourceHashes'].get(name)!=value}
 comparison['sameLevelDifferenceReviewRequired']=comparison['sameCharacterLevel'] and not comparison['numbersEqual']
 comparison['qualification']='Recorded current hit/damage/cooldown events remain authoritative. The actual isolated training maximum differs between these recordings; cross-level damage equality is not claimed.' if not comparison['sameCharacterLevel'] else ('Actual same-level totals differ. Retain the recorded events and concurrent core-source audit; do not alter seed or rules to force equality.' if comparison['sameLevelDifferenceReviewRequired'] else 'Same isolated training level and equal recorded event totals.')
 comparison['sourceHashQualification']='Workspace source hashes sampled at launch are not claimed to prove a compiled rules diff by themselves. The served frozen main/resources and root build/copy provenance identify the actual recording payload.'
 verification={'compiledSha256':report['gameHash'],'sourceHashes':report['sourceHashes'],'buildProvenance':report.get('buildProvenance'),'actualCompiledBuildProfile':actual_profile,'artSourceEvidence':report.get('artSourceEvidence'),'stableBuildDuringCapture':True,
               'shaderAssetEvidence':'shader-asset-evidence.json','emptyGround':args.empty,'nativeCanvas':[2560,1272],
               'frames':270,'seconds':9,'fps':FPS,'defaultCameraAndCompleteHUDInNativeVideo':True,
               'journeyStart':report['journeyStart'],'journeyRestoration':report['journeyRestoration'],
               'temporaryRangeCharacterLevel':report['info']['rangeCharacterLevel'],'runtimeRangeMaxLevel':report['info'].get('rangeMaxLevel'),'progressionContractEvidence':'progression-contract-evidence.json' if (folder/'progression-contract-evidence.json').exists() else None,'actualResults':result,
               'gameplayComparison':comparison,'trajectoryTiming':timing,'targetAlignment':alignment,'representativeStages':points,'coolingContinuityEvidence':cooling,'ignitionPropagationEvidence':ignition,'persistentSealEvidence':held_seal,
               'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],
               'lifecycle':{'pauseResume':len(report.get('lifecycle',[])),'familySwitches':[s['family'] for s in report.get('switches',[])],
                'sealFadeTransitions':[test['sealFade'] for test in report.get('lifecycle',[])],
                'switchesWithActiveSealBefore':[{'fromFamily':switch['before']['family'],'toFamily':switch['family'],'impactAge':switch['before'].get('impactAge'),'ground':switch['before']['ground']} for switch in report.get('switches',[]) if switch['before'].get('exercisedActiveSeal')]},
               'artStatus':'local-native-candidate-user-review-pending' if args.local_candidate else 'pending-native-reference-alignment-review',
               'artStatusNote':'Review complete crisp rear carving, fire-red/orange colour and source brightness variation, then actual post-impact carving retention and gradual fade. Cloud generation, material calculations and native Cocos images are distinct evidence. Preserve fixed-support ignition and unbroken cooling. Inspector alpha and final clearing alone are not art acceptance.',
               'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','mediaEncoded':False}
 def write():(folder/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 write()
 assert not held_seal['missingOpacityFrames'],'Actual active meteorSeal opacity was not exposed by the recorded ground inspector'
 assert held_seal['reportedPresentThrough4p3'] and held_seal['reportedClearedAt4p62'],'Meteor seal did not survive through the requested flame/ember phases and then clear'
 assert held_seal['reportedOpacityNonincreasing'],'Actual post-impact meteor seal opacity increased unexpectedly'
 if args.verify_only:print(json.dumps(verification,ensure_ascii=False));return
 media=folder/'media';media.mkdir(exist_ok=True)
 def raw(index):return Image.open(cache/f'{index:03}.jpg').convert('RGB')
 seal_point=next(point for point in points if point['slug']=='cast-0200ms')
 bodies=[body for metric in shot['metrics'] for body in metric['meteor']['active'] if body.get('screen')]
 target=bodies[0]['screen']['target'];cx=target['x'];cy=1272-target['y']
 cast=next(event for event in shot['events'] if event['type']=='skill_cast' and event.get('skillId')=='FIR_02')
 radius=cast.get('geometry',{}).get('radiusMetres',cast.get('radius',0));ppm=1272/(2*report['info']['cameraHeight'])
 half_width=radius*ppm*1.15;half_height=radius*ppm*report['info']['cameraGroundVerticalFactor']*1.25
 seal_crop=[max(0,round(cx-half_width)),max(0,round(cy-half_height)),min(2560,round(cx+half_width)),min(1272,round(cy+half_height))]
 raw(seal_point['frame']).crop(seal_crop).save(media/'seal-preview-crop.jpg',quality=95,subsampling=0)
 assets=json.loads((folder/'shader-asset-evidence.json').read_text(encoding='utf8'))
 seal_provenance_path=args.seal_provenance.resolve() if args.seal_provenance else ROOT/report['artSourceEvidence']['materialProvenancePath']
 seal_provenance=json.loads(seal_provenance_path.read_text(encoding='utf8'))
 material_resources={item['name']:item for item in seal_provenance['resources']}
 seal_bindings=[binding for binding in assets['assetBindings'] if Path(binding['source']).name in material_resources]
 assert seal_bindings,'No v35 seal asset bindings were recorded'
 seal_resources=[]
 for seal_binding in seal_bindings:
  seal_source_sha=next(file['sha256'] for file in assets['files'] if file['path']==seal_binding['source'])
  seal_candidates=[file for file in seal_binding['servedAssets'] if file.lower().endswith('.png')]
  matching=[file for file in seal_candidates if any(item['path']==file and item['sha256']==seal_source_sha for item in assets['files'])]
  assert len(matching)==1 or len(seal_candidates)==1,'Ambiguous seal PNG versions in served build; retain provenance rather than choosing a stale texture'
  seal_texture=ROOT/(matching[0] if matching else seal_candidates[0]);copied_texture=media/('diagnostic-'+Path(seal_binding['source']).name);shutil.copyfile(seal_texture,copied_texture)
  specification=material_resources.get(Path(seal_binding['source']).name)
  if specification:assert seal_source_sha==specification['sha256'] and sha(copied_texture)==specification['sha256'],'Final seal source/served bytes differ from the approved material resource provenance'
  seal_resources.append({'source':seal_binding['source'],'servedTexture':str(seal_texture.relative_to(ROOT)),'file':copied_texture.name,'sha256':sha(copied_texture),
   'role':specification['role'] if specification else 'Historical/intermediate diagnostic resource; not asserted to be the final seal material.'})
 assert all(any(Path(item['source']).name==name for item in seal_resources) for name in material_resources),'Final colour and light texture pair was not captured from the served snapshot'
 shutil.copyfile(seal_provenance_path,media/'seal-material-provenance.json')
 preview_name=seal_provenance.get('preview');material_preview=seal_provenance_path.parent/preview_name if preview_name else None
 material_preview_output='seal-material-sample-non-native'+material_preview.suffix if material_preview and material_preview.exists() else None
 if material_preview_output:shutil.copyfile(material_preview,media/material_preview_output)
 verification['sealReviewEvidence']={'nativeCropSourceFrame':seal_point['frame'],'actualCastAge':seal_point['castAge'],'nativeCropBounds':seal_crop,
  'nativeCropAlteration':'Crop only from actual default-camera recording; no colour/effect edits.','diagnosticResources':seal_resources,
  'rawResourceAlteration':'Exact copied PNG bytes from the served frozen/live build. Diagnostic data only; do not composite arbitrary raw data channels on a dark background as a final material.',
  'materialProvenance':{'source':str(seal_provenance_path.relative_to(ROOT)),'sha256':sha(seal_provenance_path),'revision':seal_provenance['revision'],'formula':seal_provenance.get('formula',seal_provenance.get('effect',{}).get('formula')),
   'calculatedPreviewFile':material_preview_output,'calculatedPreviewDeclaration':seal_provenance.get('previewDeclaration','Calculated engineering material sample; not native Cocos / TapTap evidence.')},
  'colourJudgement':'Use actual prewarning native crops. Any separately provided shader-math material sample must be labelled as a calculated sample rather than a runtime image.'}
 r3_folder=ROOT/f'source-art/skills/meteor-ignition-glow-v34/final{"-empty" if args.empty else ""}-r{args.rank}'
 if (r3_folder/'capture.json').exists():
  r3_report,r3_shot,r3_cache=load(r3_folder);r3_points,_=stages(r3_shot);r3_point=next(point for point in r3_points if point['slug']=='cast-0200ms')
  r3_body=next(body for metric in r3_shot['metrics'] for body in metric['meteor']['active'] if body.get('screen'));r3_target=r3_body['screen']['target'];r3_cx=r3_target['x'];r3_cy=1272-r3_target['y']
  r3_cast=next(event for event in r3_shot['events'] if event['type']=='skill_cast' and event.get('skillId')=='FIR_02');r3_radius=r3_cast.get('geometry',{}).get('radiusMetres',r3_cast.get('radius',0));r3_ppm=1272/(2*r3_report['info']['cameraHeight'])
  r3_half_width=r3_radius*r3_ppm*1.15;r3_half_height=r3_radius*r3_ppm*r3_report['info']['cameraGroundVerticalFactor']*1.25
  r3_crop=[max(0,round(r3_cx-r3_half_width)),max(0,round(r3_cy-r3_half_height)),min(2560,round(r3_cx+r3_half_width)),min(1272,round(r3_cy+r3_half_height))]
  r3_image=Image.open(r3_cache/f'{r3_point["frame"]:03}.jpg').convert('RGB').crop(r3_crop);r4_image=raw(seal_point['frame']).crop(seal_crop)
  reference_crop=[220,830,590,1000];reference=Image.open(REFERENCE).convert('RGB').crop(reference_crop)
  colour=Image.new('RGB',(1560,440),'#1d1916');colour_draw=ImageDraw.Draw(colour)
  label(colour_draw,(18,16),'原稿图片 · 法阵局部',20);colour.paste(reference,(75,169))
  for x,title,im,centre_y,bounds in [(520,'v34 · 上轮实际截图',r3_image,r3_cy,r3_crop),(1040,'v35 · 当前实际截图',r4_image,cy,seal_crop)]:
   label(colour_draw,(x+18,16),title,20);scale=370/im.width;im=im.resize((370,round(im.height*scale)),Image.Resampling.LANCZOS);colour.paste(im,(x+75,round(250-(centre_y-bounds[1])*scale)))
  label(colour_draw,(18,408),'圈宽接近原稿 · 保留各自透视 · 仅裁切/等比缩放，未改色或亮度',16,color='#cfc3b5')
  colour.save(media/'seal-colour-three-way.jpg',quality=95,subsampling=0)
  verification['sealColourThreeWay']={'referenceSource':str(REFERENCE.relative_to(ROOT)),'referenceCropBounds':reference_crop,
   'oldActualDirectory':str(r3_folder.relative_to(ROOT)),'oldActualCompiledSha256':r3_report['gameHash'],'oldActualFrame':r3_point['frame'],'oldActualCropBounds':r3_crop,
   'finalActualFrame':seal_point['frame'],'finalActualCropBounds':seal_crop,'nativeDisplayCropWidth':370,'processing':'Crop and uniform resize only, with each original perspective preserved. No colour, brightness or effect changes.'}
  rear=raw(seal_point['frame']).crop((seal_crop[0],seal_crop[1],seal_crop[2],round(cy+10)))
  rear.save(media/'seal-rear-preview-crop.jpg',quality=95,subsampling=0)
  old_rear=Image.open(r3_cache/f'{r3_point["frame"]:03}.jpg').convert('RGB').crop((r3_crop[0],r3_crop[1],r3_crop[2],round(r3_cy+10)))
  original_rear=Image.open(REFERENCE).convert('RGB').crop((216,821,578,905))
  rear_board=Image.new('RGB',(1800,510),'#1d1916');rear_draw=ImageDraw.Draw(rear_board)
  for index,(title,image) in enumerate([('原稿后方 · 原有陨石遮挡保留',original_rear),('v34 · 实际后方',old_rear),('v35 · 实际后方',rear)]):
   label(rear_draw,(index*600+16,16),title,22)
   image=ImageOps.contain(image,(570,390),Image.Resampling.LANCZOS);rear_board.paste(image,(index*600+15,70+(390-image.height)//2))
  label(rear_draw,(16,480),'仅裁切/等比缩放 · 各自原透视/原明暗 · 实际纹路是否完整以原生画面判断',18,color='#cfc3b5')
  rear_board.save(media/'seal-rear-three-way.jpg',quality=95,subsampling=0)
  previous_native_comparison=folder/'early/FIR_02-seal-r1-vs-r2-native.jpg'
  if previous_native_comparison.exists():
   shutil.copyfile(previous_native_comparison,media/'seal-r1-vs-r2-native.jpg')
   comparison_proof=folder/'early/FIR_02-seal-r1-vs-r2-native.json'
   verification['sealBeforeR2NativeComparison']=json.loads(comparison_proof.read_text(encoding='utf8'))
   shutil.copyfile(comparison_proof,media/'seal-r1-vs-r2-native.json')
 native=media/'FIR_02-native.mp4';video(native,(raw(i) for i in range(270)),(2560,1272))
 closeup=media/'FIR_02-closeup.mp4';crop_size=(CROP[2]-CROP[0],CROP[3]-CROP[1]);video(closeup,(raw(i).crop(CROP) for i in range(270)),crop_size)
 headers=[]
 for movie,expected_size in ((native,(2560,1272)),(closeup,crop_size)):
  with av.open(str(movie)) as clip:
   stream=clip.streams.video[0];frames=sum(1 for _ in clip.decode(video=0));duration=float(stream.duration*stream.time_base)
   assert frames==270 and stream.average_rate==30 and abs(duration-9)<1e-6
   assert (stream.width,stream.height)==expected_size
   headers.append({'file':movie.name,'sha256':sha(movie),'decodedFrames':frames,'fps':float(stream.average_rate),'seconds':duration,'canvas':[stream.width,stream.height]})
 verification['videoHeaderValidation']=headers
 for point in points:shutil.copyfile(cache/f'{point["frame"]:03}.jpg',media/f'{point["slug"]}.jpg')
 for point in cooling['representativeStages']:shutil.copyfile(cache/f'{point["frame"]:03}.jpg',media/f'{point["slug"]}.jpg')
 ignition_review.render(ignition,cache,media,label)
 ignition_review.render_before_after(ignition,ignition_review.evidence(old_shot),old_cache,cache,media,label)
 seal_review.render(held_seal,cache,media,label,CROP)
 cooling_board=Image.new('RGB',(1800,1440),'#1d1916');cooling_draw=ImageDraw.Draw(cooling_board)
 for index,point in enumerate(cooling['representativeStages']):
  x=index%3*600;y=index//3*480;label(cooling_draw,(x+16,y+14),f"{point['actualImpactAge']:.2f}s · 连续收势 / 余火渐退",23)
  im=ImageOps.contain(raw(point['frame']).crop(CROP),(560,410),Image.Resampling.LANCZOS);cooling_board.paste(im,(x+20,y+65+(410-im.height)//2))
 cooling_board.save(media/'cooling-continuity-stages.jpg',quality=95,subsampling=0)
 first,last=cooling['fullWindowFrameRange'];count=last-first+1
 every_frame=Image.new('RGB',(1920,math.ceil(count/6)*205),'#202824');every_draw=ImageDraw.Draw(every_frame)
 for index,frame in enumerate(range(first,last+1)):
  metric=shot['metrics'][frame];x=index%6*320;y=index//6*205
  label(every_draw,(x+7,y+4),f"F{frame} | {metric['impactAge']:.4f}s",17)
  im=raw(frame).crop(cooling['rearNativeRoi']).resize((320,167),Image.Resampling.LANCZOS);every_frame.paste(im,(x,y+30))
 every_frame.save(media/'cooling-continuity-every-frame.jpg',quality=95,subsampling=0)
 old_cooling=cooling_stages(old_shot);before_point=old_cooling['representativeStages'][2];after_point=cooling['representativeStages'][2]
 cooling_pair=Image.new('RGB',(1600,740),'#1d1916');pair_draw=ImageDraw.Draw(cooling_pair)
 for x,title,im in [(0,'v34 · 修改前实景',Image.open(old_cache/f"{before_point['frame']:03}.jpg").convert('RGB')),
                    (800,'v35 · 1.6秒实际收势',raw(after_point['frame']))]:
  label(pair_draw,(x+16,15),title,25);im=ImageOps.contain(im.crop(CROP),(780,650),Image.Resampling.LANCZOS);cooling_pair.paste(im,(x+10,70))
 cooling_pair.save(media/'cooling-before-vs-after-1p6.jpg',quality=95,subsampling=0)
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
 for x,title,im in [(0,'v34 · 本轮修改前实景',Image.open(old_cache/f'{curl_frame(old_shot):03}.jpg').convert('RGB')),
                    (800,'v35 · 当前实际录制 / 待用户反馈',raw(curl_frame(shot)))]:
  label(draw,(x+16,15),title,25);im=ImageOps.contain(im.crop(CROP),(780,650),Image.Resampling.LANCZOS);pair.paste(im,(x+10,70))
 pair.save(media/'before-vs-after-native-curl.jpg',quality=95,subsampling=0)
 verification['mediaEncoded']=True;verification['media']={'nativeVideo':native.name,'nativeVideoSha256':sha(native),
  'nativeVideoAlteration':'Original complete canvas frames, recorded order and 9-second timing; no overlays.',
  'closeupVideo':closeup.name,'closeupVideoSha256':sha(closeup),'closeupVideoCanvas':crop_size,
  'closeupVideoAlteration':f'Crop only {CROP}, same camera/actors/time; no VFX/text overlays.',
  'referenceSource':str(REFERENCE),'referenceSha256':sha(REFERENCE),'comparisonImages':'Crop/resize/layout only; both v29 original bottom panels retained.'}
 changed=[file['path'] for file in assets['files'] if not (ROOT/file['path']).exists() or sha(ROOT/file['path'])!=file['sha256']]
 changed_served=[file['path'] for file in assets['files'] if file['servedBuildAsset'] and file['path'] in changed]
 assert not changed_served,'Served asset payload changed after capture'
 verification['assetStabilityAtDelivery']={'sampledFiles':len(assets['files']),'servedAssetFiles':sum(bool(file['servedBuildAsset']) for file in assets['files']),
  'changedSourceOrMetadataFiles':[file for file in changed if file not in changed_served],'changedServedFiles':changed_served,
  'qualification':'Frozen served resource bytes are authoritative for the recording. Current source changes, if any, are reported separately and never relabel the served snapshot.'}
 write();print(json.dumps({'compiledSha256':report['gameHash'],'results':result,'comparison':comparison,'timing':timing,'media':str(media),'artStatus':verification['artStatus']},ensure_ascii=False))

if __name__=='__main__':main()
