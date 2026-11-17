"""Write final provenance from the two reviewed native meteor recordings."""
from pathlib import Path
import argparse, importlib.util, json, shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('meteor_media_v37',HERE/'media.py')
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
  assert len(verification['videoHeaderValidation'])==2 and all(header['decodedFrames']==270 and header['fps']==30 and header['seconds']==9 for header in verification['videoHeaderValidation'])
  material_provenance=ROOT/verification['sealReviewEvidence']['materialProvenance']['source']
  shutil.copyfile(material_provenance,folder/'media/seal-material-provenance.json')
  verification['sealReviewEvidence']['materialProvenance']['sha256']=media.sha(material_provenance)
  verification['sealReviewEvidence']['materialProvenance']['metadataResampledAfterRootReview']=True
  (folder/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  capture_review={'artStatus':'local-native-candidate-user-review-pending','scope':'Read actual recorded frames; technical support diagnostics are not substituted for visual review.',
   'earlyFrames':verification['ignitionPropagationEvidence']['actualFrameRange'],'earlyFrameCount':verification['ignitionPropagationEvidence']['actualFrameCount'],
   'earlyNativeObservation':'The paired empty-ground consecutive frames retain centre-out fire positions. Normal frames retain actor occlusion. Geometry is preserved; V37 intentionally changes sigil texture coverage/alpha and is not tested for byte-identical alpha against V36.',
   'coolingFrames':verification['coolingContinuityEvidence']['fullWindowFrameRange'],'coolingFrameCount':verification['coolingContinuityEvidence']['fullWindowFrames'],
   'coolingNativeObservation':'Paired empty-ground1.2–2.4s consecutive frames retain continuous rear settling. All normal transition frames are retained; renderer opacity/timing and geometry are distinct from the intentionally changed texture alpha.',
   'persistentSealStages':verification['persistentSealEvidence']['requestedImpactAges'],
   'persistentSealNativeObservation':'Actual prewarning rear carving is continuous and crisp. Empty-ground stages show the outer/rear seal remaining visible under fire through3.5s, faint at4.3167s and absent at4.6167s. Normal actor/screen occlusion remains visible and is not removed in postproduction.',
   'sameFrameColourStages':verification['sameFrameColourEvidence']['stages'],
   'sameFrameColourNativeObservation':'Review actual prewarning and .65/2.8/3.5s frames for faint orange coverage in the formerly dark centre, greater whole-sigil translucency and visible ground. This is native visual assessment, not pixel-colour equality or unchanged-alpha acceptance.',
   'evidence':['media/sigil-flame-v36-vs-v37-native.jpg','media/seal-v36-vs-v37-native.jpg','media/ignition-every-frame.jpg','media/ignition-before-vs-after.jpg','media/cooling-continuity-every-frame.jpg','media/seal-colour-three-way.jpg','media/seal-rear-three-way.jpg','media/seal-after-impact-stages.jpg'],
   'qualifications':['Normal view retains actor occlusion; the empty-ground recording provides the unobstructed silhouette.','Material reprojection is explicitly non-native and is not used as runtime proof.','Cocos textured relief is not fluid simulation. User art feedback and TapTap device validation remain pending.']}
  (folder/'capture-native-review.json').write_text(json.dumps(capture_review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  files=[{'path':str(file.relative_to(ROOT)).replace('\\','/'),'sha256':media.sha(file),'bytes':file.stat().st_size} for file in (folder/'media').iterdir() if file.suffix.lower() in ('.jpg','.png','.mp4')]
  recordings.append({'view':'empty' if empty else 'normal','directory':str(folder.relative_to(ROOT)).replace('\\','/'),
   'compiledSha256':verification['compiledSha256'],'sourceHashes':verification['sourceHashes'],'buildProvenance':verification.get('buildProvenance'),'actualCompiledBuildProfile':verification['actualCompiledBuildProfile'],'artSourceEvidence':verification.get('artSourceEvidence'),'shaderAssetEvidence':'shader-asset-evidence.json','nativeArtReview':'capture-native-review.json',
   'runtimeErrors':verification['runtimeErrors'],'consoleErrors':verification['consoleErrors'],'lifecycle':verification['lifecycle'],'stableBuildDuringCapture':verification['stableBuildDuringCapture'],'videoHeaderValidation':verification.get('videoHeaderValidation'),'assetStabilityAtDelivery':verification.get('assetStabilityAtDelivery'),
   'actualResults':verification['actualResults'],'targetAlignment':verification['targetAlignment'],
   'coolingContinuityEvidence':verification['coolingContinuityEvidence'],'ignitionPropagationEvidence':verification['ignitionPropagationEvidence'],'persistentSealEvidence':verification['persistentSealEvidence'],'sameFrameColourEvidence':verification['sameFrameColourEvidence'],'sealReviewEvidence':verification['sealReviewEvidence'],'sealColourThreeWay':verification.get('sealColourThreeWay'),'sealBeforeColourNativeComparison':verification.get('sealBeforeColourNativeComparison'),'gameplayComparison':verification['gameplayComparison'],
   'journeyStart':verification['journeyStart'],'journeyRestoration':verification['journeyRestoration'],'media':files})
 manifest={'artStatus':'local-native-candidate-user-review-pending','requestedRefinements':['Fill the formerly dark centre with a faint continuous flame-orange layer','Make the whole sigil more translucent while preserving concentric circles, complete carving, colour family, geometry and timing','Texture alpha changes intentionally; preserve existing renderer opacity curve and reuse the V35 cloud source without a new model run'],
  'artEvidenceCategories':{'cloudDesignSource':'source-art/skills/meteor-complete-sigil-v35/seal/cloud-complete-fire-sigil.png; reused historical cloud RGBA source, not generated again and not a runtime image','materialSample':'Calculated colour/light material sample labelled non-native','nativeCapture':'Actual Cocos canvas pixels captured from the frozen standard test build'},
  'animationMethod':'Cocos registered relief surface with spatial ignition reveal, textured rock mesh and animated flame textures; not fluid simulation.',
  'nativeCaptureMethod':'Actual formal FIR02 ultimate input in the isolated legal-level training range; normal test journey enters and returns at level1. Default camera4.3, complete HUD and visible actors. Each native video is270frames/30fps/9seconds. Closeup is crop only; no VFX/text overlays or retiming.',
  'nativeCaptureBuildScope':'FIR02 VFX only. Both recordings bind their actual gameHash to the one VFX frozen snapshot; any separate workshop-UI build/validation is excluded from these native video claims.',
  'continuityReviewScope':'Actual1.2/1.4/1.6/1.8/2.2/2.8/3.5s stages plus every frame in the1.2–2.4s transition. Pool counts and final clearing alone do not establish visual continuity.',
  'ignitionReviewScope':'Requested0/.033/.066/.1/.15/.2/.3/.45/.65s stages select real30fps samples with explicit actual ages, including duplicate selections. Consecutive early native frames and separate support/front inspector fields are retained; fixed reported support alone is not art acceptance.',
  'persistentSealReviewScope':'Actual post-impact.25/.65/1.2/1.6/2.2/2.8/3.5/4.3/4.62s native stages and meteorSeal.opacity series. Active/opacity alone does not establish visible carving retention.',
  'baseline':'source-art/skills/meteor-flame-colour-v36/final[-empty]-r1','referenceSource':str(media.REFERENCE.relative_to(ROOT)).replace('\\','/'),'referenceSha256':media.sha(media.REFERENCE),
  'historicalBeforeRecordings':[{'directory':f'source-art/skills/meteor-flame-colour-v36/final{suffix}-r{args.rank}','status':'v36-before-translucent-fill-refinement','notFinalDelivery':True} for suffix in ('','-empty')],
  'mixedCompiledHashes':len({r['compiledSha256'] for r in recordings})>1,'visualLimits':'Real camera projection is retained. User implementation-art feedback remains pending; no exact CG pixel match is claimed.',
  'taptapDeviceValidation':'Pending; browser capture is not device acceptance.','recordings':recordings,
  'finalDesignProvenance':[{'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':media.sha(path)} for path in (material_provenance,ROOT/'source-art/skills/meteor-complete-sigil-v35/seal/cloud-generation.json',ROOT/'source-art/skills/meteor-complete-sigil-v35/seal/cloud-refinement-prompt.txt',ROOT/'source-art/skills/meteor-complete-sigil-v35/seal/cloud-complete-fire-sigil.png',HERE/'preserved-assets-check.json',HERE/'root-native-review.json',HERE/'root-build-review.json') if path.exists()]}
 output=HERE/'delivery';output.mkdir(exist_ok=True);path=output/'manifest.json';path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 normal=HERE/f'{args.stage}-r{args.rank}'/'media';empty=HERE/f'{args.stage}-empty-r{args.rank}'/'media'
 actual=recordings[0]['actualResults'];numbers_note='与v36同序实录相同' if recordings[0]['gameplayComparison']['numbersEqual'] else '与v36差异已记录，未调整规则或seed'
 readme=f'''# v37 淡橙填色/透明原生候选\n\n[空地近景录像]({(empty/'FIR_02-closeup.mp4').as_posix()}) · [真实命中完整HUD录像]({(normal/'FIR_02-native.mp4').as_posix()})\n\n[预警填色/透地前后]({(empty/'seal-v36-vs-v37-native.jpg').as_posix()}) · [同帧法阵/中央火焰 · v36/v37对照]({(empty/'sigil-flame-v36-vs-v37-native.jpg').as_posix()}) · [落地后法阵9阶段]({(empty/'seal-after-impact-stages.jpg').as_posix()})\n\n两段各9秒、30fps、270帧；完整原片保留默认镜头、角色与HUD，近景只固定裁切。正常{actual['hits']}次命中、{actual['damage']}伤害，空地0，{numbers_note}。每次从1级test旅程进入独立合法满级训练会话，退出恢复原旅程不变。原生错误0、served资产稳定、真实触地误差低于0.0001m。\n\n本轮确定性淡橙内底填充与贴图透明度调整，没有新生图。draw opacity与贴图alpha分别记录，不要求与v36像素alpha不变。本地候选，用户美术反馈及TapTap真机验收待定。来源、逐段SHA、实际年龄和验证见[manifest]({path.as_posix()})。\n'''
 (output/'README.md').write_text(readme,encoding='utf8')
 print(json.dumps({'manifest':str(path),'recordingDirectories':[r['directory'] for r in recordings],'compiledHashes':[r['compiledSha256'] for r in recordings]},ensure_ascii=False))

if __name__=='__main__':main()
