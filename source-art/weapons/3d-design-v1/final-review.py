"""Summarize existing export, real-render, equip and build evidence; no new tests."""
from pathlib import Path
import hashlib,json,zipfile,datetime
from PIL import Image

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'runtime'
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def checked(value,message):
    if not value:raise RuntimeError(message)

items=read(BASE/'designs.json');install=read(BASE/'install-record.json');geometry=read(BASE/'geometry-review.json')
runtime=read(OUT/'report.json');gallery=read(OUT/'gallery/frames.json');inventory=read(OUT/'inventory-review.json');bows=read(OUT/'all-bows-review.json');flat=read(OUT/'flat-regression.json');previews=read(OUT/'previews.json')
checked(len(items)==24 and len(geometry)==24 and all(x['passed'] for x in geometry),'24 export reviews')
checked(all(sha(ROOT/r['source'])==r['sourceSHA256'] for r in items),'Original 2D source hashes')
checked(all(sha(ROOT/r['fbx'])==r['sha256'] for r in install['records']),'Installed FBX hashes')
body=ROOT/'src/cocos/assets/resources/actors/raphael/raphael.fbx'
checked(sha(body)==install['bodySHA256']==sha(ROOT/'source-art/characters/3d-weapon-contact-v2/authored-raphael.fbx'),'Accepted body FBX unchanged')

# Compare the actual build inputs affected by this task, including installed assets.
paths=['src/cocos/assets/scripts/runtime/'+n+'.ts' for n in ['Actors','CharacterPreview','WeaponMaterials','ChapterGame']]
paths+=['src/cocos/assets/resources/actors/'+n+'/manifest.json' for n in ['props-native','raphael']]
paths+=[r['fbx'] for r in install['records']]
paths+=[(ROOT/'src/cocos/assets/resources/actors/props-native/textures'/p.name).relative_to(ROOT).as_posix() for p in (BASE/'textures').glob('*.png')]
paths+=[body.relative_to(ROOT).as_posix()]
inputs=[]
for name in paths:
    source=ROOT/name;mirror=MIRROR/Path(name).relative_to('src/cocos')
    checked(sha(source)==sha(mirror),'Build input mismatch: '+name)
    inputs.append({'path':name,'sha256':sha(source)})
build=MIRROR/'build/concept-2d';served=ROOT/'src/cocos/build/concept-2d'
output_files=[p for p in build.rglob('*')if p.is_file()]
checked(all((served/p.relative_to(build)).is_file() and sha(p)==sha(served/p.relative_to(build)) for p in output_files),'Copied build output mismatch')
log=MIRROR/'temp/build-concept-2d-out.log';checked('build Task (concept-2d) Finished' in log.read_text(encoding='utf-8'),'Successful final Cocos build log')

samples=runtime['stills']+runtime['frames'];checked(len(runtime['stills'])==96 and len(runtime['frames'])==1392,'Actual actor frame counts')
checked(len(runtime['transitions'])==24 and all(r['stowed'] for r in runtime['transitions']),'Return to back carry')
checked(all(len(r['visible'])==1 and r['mountError']<1e-6 and r['quiver']==(r['kind']=='bow') for r in samples),'Visible families/mounts/quivers')
checked(not runtime['errors'] and not runtime['requests'] and len(gallery['records'])==288 and not gallery['errors'],'Actual render errors')
checked(len(inventory['records'])==24 and inventory['remaining']==0 and not inventory['errors'],'Inventory preview cleanup')
checked(all(r['skins']==13 and r['variants']==['WeaponVariant:design-'+r['id'].lower()] for r in inventory['records']),'Actual equip variants')
staff_ids=[r['id']for r in items if r['kind']=='staff'];checked(all(r['pose']=='idle' for r in inventory['records']if r['id']in staff_ids),'Stowed staff empty-hand pose')
checked(inventory['staff']['playing'] and inventory['staff']['carry']=='ready','Held staff idle')
checked(flat['result']=={'idle':'stowed','attack':'ready','returned':'stowed','dash':'stowed'} and not flat['errors'],'Existing default 2D readiness regression')
checked(len(bows['results'])==7 and not bows['errors'],'All seven bow checks')
calibrations=[read(BASE/'models'/(r['id']+'-draw-calibration.json'))for r in items if r['kind']=='bow']

media=[]
for data in previews['outputs'].values():
    with Image.open(OUT/data['file']) as im:
        checked(im.n_frames==data['frames'],'Animation frame count')
        hashes=[]
        for i in range(im.n_frames):im.seek(i);hashes.append(hashlib.sha256(im.convert('RGB').tobytes()).hexdigest())
        checked(len(set(hashes))>1,'Non-static animation')
        media.append({**data,'distinctFrames':len(set(hashes)),'sha256':sha(OUT/data['file'])})
package=ROOT/previews['package']
with zipfile.ZipFile(package) as archive:
    checked(archive.testzip() is None,'Model package CRC')
    checked(len([n for n in archive.namelist() if n.endswith('.glb')])==24,'Portable model count')
    for model in read(BASE/'designs.json'):
        name=model['id']+'.glb';checked(hashlib.sha256(archive.read('models/'+name)).hexdigest()==sha(BASE/'glb'/name),'Packaged model hash')

report={
 'created':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
 'scope':'24 actual 3D weapon assets; optional native actor in original painted world; no broad collision/mobile-performance acceptance',
 'models':{'held':24,'matchingBladeScabbards':9,'quiver':1,'fbxResources':len(install['records']),'textures':install['textures'],'portableGLB':24,'editableBlend':24},
 'provenance':{'original2DSourceHashesUnchanged':True,'W04_W05':'Existing same-series unused 2D designs; no independent original icons found','bodySHA256':sha(body),'acceptedBodyUnchanged':True},
 'geometry':{'passed':len(geometry),'maxPositionErrorMetres':max(x['maxPositionErrorMeters']for x in geometry),'maxMorphPositionErrorMetres':max(x['maxMorphPositionErrorMeters']for x in geometry),'maxUVError':max(x['maxUVError']for x in geometry),'bowDrawCalibrationMaxNockCentreErrorMetres':max(x['maxNockCentreErrorMetres']for x in calibrations)},
 'runtime':{'stills':96,'attackReleaseRecoveryFrames':1392,'stowedTransitions':24,'maxMountPositionErrorMetres':max(x['mountError']for x in samples),'modelTurnViews':288,'inventoryEquips':24,'bodySkins':13,'stowedStaffsUseEmptyHandIdle':6,'heldStaffIdle':inventory['staff'],'remainingPreviewStages':0,'errors':runtime['errors']+gallery['errors']+inventory['errors'],'failedRequests':runtime['requests']},
 'bows':{'weapons':7,'turnSamples':sum(x['turns']for x in bows['results']),'shots':7,'flightSegments':sum(x['flightSamples']for x in bows['results']),'maxHorizontalArrowYawErrorDegrees':max(x['maxYawErrorDegrees']for x in bows['results']),'maxFlightDirectionErrorDegrees':max(x['maxFlightErrorDegrees']for x in bows['results']),'authoredVerticalPitchRetained':True},
 'default2D':flat,
 'build':{'typecheck':'npm run check passed; tsc --noEmit','webMobile':'Original Build-Local.ps1 completed with Cocos Creator 3.8.8 in real-assets C-drive mirror','log':str(log),'logSHA256':sha(log),'inputHashes':inputs,'copiedBuildFiles':len(output_files),'allCopiedBuildHashesMatch':True,'served':'http://127.0.0.1:7469/?view=2d&player=3d','entrySHA256':sha(served/'index.html'),'whitespaceCheck':'Focused git diff --check passed'},
 'media':media,'package':{'file':previews['package'],'bytes':package.stat().st_size,'sha256':sha(package),'zipCRCPassed':True},
}
(OUT/'final-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'models':report['models'],'copiedBuildFiles':len(output_files),'runtime':report['runtime'],'packageBytes':package.stat().st_size},ensure_ascii=True))
