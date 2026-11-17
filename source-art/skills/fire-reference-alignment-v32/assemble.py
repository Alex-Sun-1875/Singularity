"""Assemble verified native recordings; segment build hashes remain distinct."""
from pathlib import Path
import argparse, importlib.util, json

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('meteor_media_v32',HERE/'media.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)

def main():
 p=argparse.ArgumentParser();p.add_argument('--meteor-stage',default='contact-final');p.add_argument('--regression-stage',default='regression');p.add_argument('--combined',action='store_true');args=p.parse_args()
 regression=HERE/f'{args.regression_stage}-r1';normal=HERE/f'{args.meteor_stage}-r1';empty=HERE/f'{args.meteor_stage}-empty-r1'
 reg=json.loads((regression/'regression-verification.json').read_text(encoding='utf8'))
 meteors=[json.loads((folder/'verification.json').read_text(encoding='utf8')) for folder in (normal,empty)]
 assert reg['mediaEncoded'] and all(v['mediaEncoded'] and v['artStatus']=='local-native-candidate-user-review-pending' for v in meteors)
 assert all(v['targetAlignment']['meteorBodyTargetsEqual'] and v['targetAlignment']['eventAndDropBlastCueTargetsEqual'] for v in meteors)
 assert all(v['targetAlignment']['realRockContactRecorded'] and v['targetAlignment']['maxNoseContactErrorMetres']<.0001 for v in meteors)
 output=HERE/'delivery';output.mkdir(exist_ok=True)
 captures=[(regression,'FIR_01',6),(regression,'FIR_05',8),(normal,'FIR_02',9)];segments=[]
 for folder,skill,seconds in captures:
  report=json.loads((folder/'capture.json').read_text(encoding='utf8'));assert report['stableBuild']
  segments.append({'id':skill,'seconds':seconds,'frames':seconds*30,'compiledSha256':report['gameHash'],
                   'sourceHashes':report['sourceHashes'],'recordingDirectory':str(folder.relative_to(ROOT)).replace('\\','/'),
                   'cache':report['cache'],'actualJourneyStartLevel':report['journeyStart']['level'],
                   'temporaryTrainingLevel':report['info']['rangeCharacterLevel'],'journeyRestoration':report['journeyRestoration']})
 def frames():
  for segment in segments:
   cache=ROOT/segment['cache']/segment['id']
   for index in range(segment['frames']):yield media.Image.open(cache/f'{index:03}.jpg').convert('RGB')
 native=output/'fire-three-skills-native.mp4'
 if args.combined:
  media.video(native,frames(),(2560,1272))
  with media.av.open(str(native)) as clip:assert sum(1 for _ in clip.decode(video=0))==sum(s['frames'] for s in segments)
 records=[]
 for folder,verification in [(regression,reg),(normal,meteors[0]),(empty,meteors[1])]:
  files=[{'path':str(file.relative_to(ROOT)).replace('\\','/'),'sha256':media.sha(file),'bytes':file.stat().st_size} for file in (folder/'media').iterdir() if file.suffix.lower() in ('.jpg','.mp4')]
  records.append({'directory':str(folder.relative_to(ROOT)).replace('\\','/'),'compiledSha256':verification['compiledSha256'],
                  'verificationFile':'regression-verification.json' if folder==regression else 'verification.json','media':files})
 manifest={'artStatus':'local-native-candidate-user-review-pending','originalReference':'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png',
           'originalReferenceSha256':media.sha(HERE/'assets/approved-reference.png'),'previousV31Status':'user-rejected-v29-reference-mismatch',
           'mixedBuilds':len({s['compiledSha256'] for s in segments})>1,'segmentBuildPolicy':'FIR01/FIR05 retain their independently verified regression build; final FIR02 uses the later descent-angle build. Do not claim all segments share one compiled hash.',
           'method':'Actual formal training-range inputs, default camera 4.3, complete HUD and visible actors. Each native clip preserves its recorded frame order at 30fps without VFX/text overlays or retiming. Optional combined output uses simple segment cuts.',
           'levelPolicy':'Fresh normal test journey begins at 1. The existing isolated training range now uses legal maximum level 80 from concurrent CampaignProgression changes; original journey is restored unchanged. Cross-level damage equality to historical level40 recordings is not claimed.',
           'visualLimits':'Normal camera projection differs from the CG reference. Preserve the real physical circular footprint; no exact pixel match or user art acceptance is claimed.',
           'animationMethod':'Cocos registered relief surfaces, textured rock mesh and animated flame textures.',
           'finalMeteorValidation':[{'view':'normal' if index==0 else 'empty','compiledSha256':value['compiledSha256'],'actualResults':value['actualResults'],'targetAlignment':value['targetAlignment'],'gameplayComparison':value['gameplayComparison'],'journeyStart':value['journeyStart'],'journeyRestoration':value['journeyRestoration']} for index,value in enumerate(meteors)],
           'regressionActualResults':reg['shots'],
           'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','segments':segments,'recordings':records,
           'combinedNativeVideo':{'path':str(native.relative_to(ROOT)).replace('\\','/'),'sha256':media.sha(native),'frames':690,'seconds':23,'fps':30,'nativeCanvas':[2560,1272]} if args.combined else None}
 (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'combinedNativeVideo':str(native) if args.combined else None,'mixedBuilds':manifest['mixedBuilds'],'manifest':str(output/'manifest.json')},ensure_ascii=False))

if __name__=='__main__':main()
