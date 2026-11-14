from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((BASE/'source-verification.json').read_text());views=json.loads((BASE/'runtime/after/report.json').read_text());motion=json.loads((BASE/'runtime/after/frames.json').read_text())
assert source['faceBodyGeometryUVWeightsPreserved']and source['allFaceAndClothingMaterialRecordsPreserved']and source['all14MotionCurvesPreserved']
assert views['info']['revision']=='native-short-fine-v4'and views['info']['validMeshes']==13 and len(views['info']['clips'])==14 and not views['errors']
assert len(motion['rows'])==180 and not motion['errors']
actor=ROOT/'src/cocos/assets/resources/actors/raphael';staged=MIRROR/'assets/resources/actors/raphael'
for name in ['raphael-polish.glb','manifest.json']:assert sha(BASE/name)==sha(staged/name)
for name in ['raphael-polish.glb','manifest.json']:shutil.copy2(BASE/name,actor/name)
if (staged/'raphael-polish.glb.meta').exists():shutil.copy2(staged/'raphael-polish.glb.meta',actor/'raphael-polish.glb.meta')
assets=ROOT/'src/cocos/assets/resources/actors';folder=assets/'native-hair-v4'
shutil.copytree(MIRROR/'assets/resources/actors/native-hair-v4',folder,dirs_exist_ok=True)
shutil.copy2(MIRROR/'assets/resources/actors/native-hair-v4.meta',assets/'native-hair-v4.meta')
shutil.copytree(MIRROR/'build/concept-2d',ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'manifestSHA256':sha(actor/'manifest.json'),'textures':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in sorted((folder/'textures').glob('*.png'))],'source':source,'runtimeViews':len(views['records']),'motionFrames':len(motion['rows']),'url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=native-short-fine-v4'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('Installed native short hair fine-detail revision; canonical preview updated')
