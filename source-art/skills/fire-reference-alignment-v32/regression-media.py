"""Encode the two actual normal-range regression casts; no generated effects."""
from pathlib import Path
import argparse, importlib.util, json, shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('meteor_media_v32',HERE/'media.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='regression');p.add_argument('--rank',type=int,default=1);p.add_argument('--verify-only',action='store_true');args=p.parse_args()
 folder=HERE/f'{args.stage}-r{args.rank}';report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
 assert report['stableBuild'] and not report['errors'] and not report['consoleErrors']
 assert report['journeyStart']['level']==1 and not report['journeyStart']['temporaryMax']
 assert report['info']['rangeSessionIsSeparate'] and report['info']['rangeCharacterLevel']==report['info']['rangeMaxLevel']
 restored=report['journeyRestoration'];assert restored['sessionRestored'] and restored['level']==1 and restored['progressionUnchanged'] and restored['equipmentUnchanged']
 assert report['info']['viewport']==[2560,1272] and report['info']['cameraHeight']==4.3
 result={'compiledSha256':report['gameHash'],'sourceHashes':report['sourceHashes'],'shaderAssetEvidence':'shader-asset-evidence.json',
         'journeyStart':report['journeyStart'],'journeyRestoration':restored,'temporaryTrainingLevel':report['info']['rangeCharacterLevel'],
         'runtimeTrainingMaximum':report['info']['rangeMaxLevel'],'stableBuildDuringCapture':True,'nativeCanvas':[2560,1272],
         'artStatus':'actual-native-regression-capture-user-review-pending','qualification':'Actual current-level event totals are recorded; no equality to earlier level-40 gameplay is claimed.',
         'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','mediaEncoded':False,'shots':[]}
 output=folder/'media';output.mkdir(exist_ok=True)
 for skill,seconds in [('FIR_01',6),('FIR_05',8)]:
  shot=json.loads((folder/f'{skill}.json').read_text(encoding='utf8'));metrics=shot['metrics'];events=shot['events'];last=metrics[-1]
  assert shot['frames']==seconds*30 and len(metrics)==seconds*30
  cache=ROOT/report['cache']/skill;assert len(list(cache.glob('[0-9][0-9][0-9].jpg')))==seconds*30
  assert all(m['cameraHeight']==4.3 for m in metrics)
  casts=[e for e in events if e['type']=='skill_cast' and e.get('skillId')==skill];releases=[e for e in events if e['type']=='skill_release' and e.get('skillId')==skill]
  hits=[e for e in events if e['type']=='hit' and float(e.get('hpLost',0))>0]
  assert len(casts)==1 and len(releases)==1 and len(hits)==last['hits'] and sum(e['hpLost'] for e in hits)==last['damage']
  assert not(last['fire']['active'] or last['ground']['active'] or last['meteor']['active'])
  for metric in metrics:
   assert len(metric['fire']['active'])<=metric['fire']['capacity'] and len(metric['ground']['active'])<=metric['ground']['capacity']
  if skill=='FIR_01':
   first_hit=min(e['time'] for e in hits);wanted=[('projectile',(releases[0]['time']+first_hit)*.5),('contact',first_hit+.10)]
  else:wanted=[('field',releases[0]['time']+.80)]
  points=[]
  for name,time in wanted:
   metric=min(metrics,key=lambda m:abs(m['time']-time));points.append({'name':name,'frame':metric['frame'],'actualTime':metric['time'],'secondsAfterRelease':metric['time']-releases[0]['time']})
   if not args.verify_only:shutil.copyfile(cache/f'{metric["frame"]:03}.jpg',output/f'{skill}-{name}-native.jpg')
  entry={'id':skill,'frames':shot['frames'],'seconds':seconds,'fps':30,'casts':1,'releases':1,'hits':last['hits'],'damage':last['damage'],'misses':last['misses'],'criticalHits':last['criticalHits'],
         'actualHitEventDamage':sum(e['hpLost'] for e in hits),'maxCooldown':max(m['cooldowns'].get(skill,0) for m in metrics),'clearedAtEnd':True,'representativeFrames':points}
  if not args.verify_only:
   movie=output/f'{skill}-native.mp4';media.video(movie,(media.Image.open(cache/f'{i:03}.jpg').convert('RGB') for i in range(shot['frames'])),(2560,1272))
   with media.av.open(str(movie)) as clip:assert sum(1 for _ in clip.decode(video=0))==shot['frames']
   entry['nativeVideo']=movie.name;entry['nativeVideoSha256']=media.sha(movie);entry['nativeVideoAlteration']='Original complete HUD/canvas and recorded timing; no overlays or retiming.'
  result['shots'].append(entry)
 result['lifecycle']=[{'id':r['id'],'pauseStable':r['pauseStable'],'activeFireAtSample':media.visible(r['before']),'clearAfterReset':not media.visible(r['reset'])} for r in report['lifecycle']]
 assert all(r['pauseStable'] and r['clearAfterReset'] for r in result['lifecycle'])
 assert all(s['after']['family']==s['family'] and not media.visible(s['after']) for s in report['switches'])
 result['familySwitches']=[s['family'] for s in report['switches']];result['mediaEncoded']=not args.verify_only
 (folder/'regression-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
