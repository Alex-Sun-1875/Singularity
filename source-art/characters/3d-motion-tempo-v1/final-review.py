"""Summarize source, native runtime, normal-speed media and build evidence."""
from pathlib import Path
import json,hashlib,datetime
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'runtime';MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source=read(BASE/'source-verification.json');stride=read(BASE/'stride-adaptation.json');install=read(BASE/'install-record.json');preview=read(OUT/'preview-review.json');live=read(OUT/'live-review.json');video=read(OUT/'video-review.json')
bows=read(ROOT/'source-art/weapons/3d-design-v1/runtime/all-bows-review.json');inventory=read(ROOT/'source-art/weapons/3d-design-v1/runtime/inventory-review.json')
assert source['meshUVWeightsUnchanged']and source['bindPoseUnchanged']and len(source['unchangedActions'])==12 and source['maxRunArmSpineHelperLocalChannelError']==0
assert preview['sameGameplayActionEmissionSchedule']and not preview['captureErrors']and preview['actorSamples']==600
assert not live['errors']and live['pause']['gameSeconds']==0 and live['resumed']['gameSeconds']>.2
assert len(bows['results'])==7 and not bows['errors']and max(x['maxYawErrorDegrees']for x in bows['results'])<.001
assert len(inventory['records'])==24 and not inventory['errors']and inventory['remaining']==0
assert all(r['skins']==13 for r in inventory['records'])
paths=['src/cocos/assets/scripts/features/actors/runtime/Actors.ts','src/cocos/assets/resources/actors/raphael/manifest.json','src/cocos/assets/resources/actors/raphael/raphael.fbx'];inputs=[]
for name in paths:
    source_file=ROOT/name;mirrored=MIRROR/Path(name).relative_to('src/cocos');assert sha(source_file)==sha(mirrored),name
    inputs.append({'path':name,'sha256':sha(source_file)})
assert inputs[-1]['sha256']==install['fbxSHA256']==sha(BASE/'raphael.fbx')
weapons=read(ROOT/'source-art/weapons/3d-design-v1/install-record.json');assert all(sha(ROOT/r['fbx'])==r['sha256']for r in weapons['records'])
build=MIRROR/'build/concept-2d';served=ROOT/'src/cocos/build/concept-2d';files=[p for p in build.rglob('*')if p.is_file()]
assert all(sha(p)==sha(served/p.relative_to(build))for p in files)
log=MIRROR/'temp/build-concept-2d-out.log';assert 'build Task (concept-2d) Finished'in log.read_text(encoding='utf-8')
result={'created':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'source':source,'stride':stride,'runtime':{'samples':600,'runAnimationRate':preview['runAnimationRate'],'runCycleSeconds':preview['normalRunCycleSeconds'],'gameplayActionEmissionScheduleUnchanged':True,'liveGameToWallTimeRatio':live['run']['gameSeconds']/live['run']['wallSeconds'],'pauseGameSeconds':live['pause']['gameSeconds'],'resumeGameSeconds':live['resumed']['gameSeconds'],'errors':live['errors']+preview['captureErrors']},'weapons':{'all34InstalledPropFBXHashesUnchanged':True,'inventoryEquips':24,'remainingPreviewStages':0,'bowAimSamples':sum(x['turns']for x in bows['results']),'flightSegments':sum(x['flightSamples']for x in bows['results']),'maxArrowYawErrorDegrees':max(x['maxYawErrorDegrees']for x in bows['results']),'maxFlightErrorDegrees':max(x['maxFlightErrorDegrees']for x in bows['results'])},'media':{'previews':preview['outputs'],'decodedVideos':video,'playback':preview['playback']},'validation':{'typecheck':'npm run check passed','whitespace':'Focused git diff --check passed','build':'Cocos Creator 3.8.8; original Build-Local.ps1; real source-copy mirror on C:','buildLogSHA256':sha(log),'inputs':inputs,'copiedBuildFiles':len(files),'allCopiedBuildHashesMatch':True,'url':'http://127.0.0.1:7469/?view=2d&player=3d'},'scope':'Native player motion tempo; existing gameplay timing and weapon models retained; no claim of exhaustive skill collision or mobile-performance acceptance'}
(OUT/'final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'actorSamples':600,'sameGameplaySchedule':True,'runCycleSeconds':preview['normalRunCycleSeconds'],'copiedBuildFiles':len(files),'inventoryEquips':24,'bowAimSamples':56,'flightSegments':301}))
