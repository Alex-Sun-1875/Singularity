"""Write final provenance from the two reviewed native meteor recordings."""
from pathlib import Path
import argparse, importlib.util, json

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('meteor_media_v33',HERE/'media.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',default='final');parser.add_argument('--rank',type=int,default=1);args=parser.parse_args()
 recordings=[]
 for empty in (False,True):
  folder=HERE/f'{args.stage}{"-empty" if empty else ""}-r{args.rank}'
  verification=json.loads((folder/'verification.json').read_text(encoding='utf8'));report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
  assert report['stableBuild'] and verification['mediaEncoded'] and verification['artStatus']=='local-native-candidate-user-review-pending'
  assert verification['targetAlignment']['realRockContactRecorded'] and verification['targetAlignment']['maxNoseContactErrorMetres']<.0001
  assert verification['journeyStart']['level']==1 and verification['journeyRestoration']['level']==1
  files=[{'path':str(file.relative_to(ROOT)).replace('\\','/'),'sha256':media.sha(file),'bytes':file.stat().st_size} for file in (folder/'media').iterdir() if file.suffix.lower() in ('.jpg','.png','.mp4')]
  recordings.append({'view':'empty' if empty else 'normal','directory':str(folder.relative_to(ROOT)).replace('\\','/'),
   'compiledSha256':verification['compiledSha256'],'sourceHashes':verification['sourceHashes'],'buildProvenance':verification.get('buildProvenance'),'shaderAssetEvidence':'shader-asset-evidence.json','nativeArtReview':'native-art-review.json',
   'runtimeErrors':verification['runtimeErrors'],'consoleErrors':verification['consoleErrors'],'stableBuildDuringCapture':verification['stableBuildDuringCapture'],'videoHeaderValidation':verification.get('videoHeaderValidation'),'assetStabilityAtDelivery':verification.get('assetStabilityAtDelivery'),
   'actualResults':verification['actualResults'],'targetAlignment':verification['targetAlignment'],
   'coolingContinuityEvidence':verification['coolingContinuityEvidence'],'sealReviewEvidence':verification['sealReviewEvidence'],'sealColourThreeWay':verification.get('sealColourThreeWay'),'gameplayComparison':verification['gameplayComparison'],
   'journeyStart':verification['journeyStart'],'journeyRestoration':verification['journeyRestoration'],'media':files})
 manifest={'artStatus':'local-native-candidate-user-review-pending','requestedRefinements':['Brighter original long curling seal pattern inside regular concentric circular boundaries','Warm orange/amber translucent seal background aligned to the draft','Denser translucent meteor shell with only a faint rock core','Slightly denser ground fire','Continuous whole-surface decay without the former rear gap'],
  'animationMethod':'Cocos registered continuous relief surface, textured rock mesh and animated flame textures.',
  'nativeCaptureMethod':'Actual formal FIR02 ultimate input in the isolated legal-level training range; normal test journey enters and returns at level1. Default camera4.3, complete HUD and visible actors. Each native video is270frames/30fps/9seconds. Closeup is crop only; no VFX/text overlays or retiming.',
  'continuityReviewScope':'Actual1.2/1.4/1.6/1.8/2.2/2.8/3.5s stages plus every frame in the1.2–2.4s transition. Pool counts and final clearing alone do not establish visual continuity.',
  'baseline':'source-art/skills/fire-reference-alignment-v32/contact-final[-empty]-r1','referenceSource':str(media.REFERENCE.relative_to(ROOT)).replace('\\','/'),'referenceSha256':media.sha(media.REFERENCE),
  'mixedCompiledHashes':len({r['compiledSha256'] for r in recordings})>1,'visualLimits':'Real camera projection is retained. User implementation-art feedback remains pending; no exact CG pixel match is claimed.',
  'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','recordings':recordings}
 output=HERE/'delivery';output.mkdir(exist_ok=True);path=output/'manifest.json';path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'manifest':str(path),'recordingDirectories':[r['directory'] for r in recordings],'compiledHashes':[r['compiledSha256'] for r in recordings]},ensure_ascii=False))

if __name__=='__main__':main()
