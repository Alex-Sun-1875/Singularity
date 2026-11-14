from pathlib import Path
import json,hashlib,sys,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
from weapon_carry_calibration import apply_bow_carry_calibration
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
proof=read(BASE/'preservation.json');views=read(BASE/'runtime/after/report.json');shots=read(BASE/'runtime/all-bows-review.json');controls=read(BASE/'runtime/carry-controls.json');art=read(BASE/'art-review.json');data=read(BASE/'calibration.json')
assert len(views['ids'])==7 and len(views['records'])==78 and not views['errors']
assert all(r['correctParent']and r['backBone']=='spine_02'and r['separateBackSocket']and r['localError']<1e-6 and r['skins']==16 for r in views['records'])
for r in views['records']:
 if r['label']=='returned':assert sum((r['gripModel'][k]-data['items'][r['id']]['position'][i])**2 for i,k in enumerate(['x','y','z']))<1e-10
assert len(shots['results'])==7 and not shots['errors']and all(r['returned']['stowed']and r['returned']['correctParent']and r['maxYawErrorDegrees']<.001 and r['maxFlightErrorDegrees']<.01 for r in shots['results'])
assert len(controls['controls'])==3 and not controls['errors']and art['actualEngineViewsReviewed']
for r in controls['controls']:assert r['before']['legacyBackParent']and not r['held']['stowed']and r['returned']['stowed']
actor=ROOT/'src/cocos/assets/resources/actors/raphael';assert sha(actor/'raphael-polish.glb')==proof['bodyGLBSHA256']
script=ROOT/'src/cocos/assets/scripts/features/actors/runtime/Actors.ts';assert sha(script)==sha(MIRROR/'assets/scripts/features/actors/runtime/Actors.ts')
candidate=read(BASE/'manifest.json');current=read(actor/'manifest.json');apply_bow_carry_calibration(current,ROOT);assert current==candidate
assert sha(BASE/'manifest.json')==sha(MIRROR/'assets/resources/actors/raphael/manifest.json')
write(actor/'manifest.json',current)
source=ROOT/'source-art/characters/3d-hairstyles-v3/manifest.json';sourceActor=read(source);apply_bow_carry_calibration(sourceActor,ROOT);write(source,sourceActor)
shutil.copytree(MIRROR/'build/concept-2d-bow-carry-v2',ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'revision':data['revision'],'bowBone':data['bowBone'],'bows':list(data['items']),'bodyGLBSHA256':proof['bodyGLBSHA256'],'actorScriptSHA256':sha(script),'manifestSHA256':sha(actor/'manifest.json'),'views':len(views['records']),'shots':len(shots['results']),'controls':len(controls['controls']),'url':'http://127.0.0.1:7469/?view=2d&player=3d&hair=dante&revision=bow-carry-v2'};write(BASE/'install-record.json',record);print('Installed corrected bow/quiver mounts and calibrated mid-back socket')
