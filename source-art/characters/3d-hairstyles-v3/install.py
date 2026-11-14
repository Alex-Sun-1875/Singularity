from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
assert (MIRROR/'build/concept-2d-hairstyles-v3/index.html').stat().st_mtime>=(ROOT/'src/cocos/assets/scripts/features/actors/runtime/Actors.ts').stat().st_mtime,'Rebuild the current runtime before installing this appearance package'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=read(BASE/'source-verification.json');ui=read(BASE/'runtime/selection/report.json');art=read(BASE/'art-review.json')
assert source['faceBodyGeometryUVWeightsPreserved']and source['allFaceAndClothingMaterialRecordsPreserved']and source['all14MotionCurvesPreserved']
assert source['runtimeGLBSHA256']==sha(BASE/'raphael-polish.glb')and source['rejectedPrototypeMaterialsAbsent']
assert art['actualEngineViewsReviewed']and art['status']=='installed-candidate-awaiting-user-art-feedback'
assert art['runtimeGLBSHA256']==sha(BASE/'raphael-polish.glb')
assert len(ui['rows'])==4 and ui['persisted']=='nero'and not ui['errors']and not ui['hood']['actual']and ui['mobile']['id']=='dante'
assert all(r['texture']['mipLevels']>1 for r in ui['rows'])
assert (BASE/'runtime/selection/report.json').stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
definitions=read(BASE/'manifest.json')['hairstyles']
assert all(r['actual']==next(s['nodes']for s in definitions if s['id']==r['id'])for r in ui['rows'])
# Selection code, node names and texture import settings are unchanged by the
# final edge-lock adjustment; reuse that completed interaction review.
views=[]
for sid in ['curly','dante','nero','vergil']:
 p=BASE/'runtime/refined'/sid/'report.json';r=read(p)
 assert r['info']['revision']=='hairstyles-v3-refined'and r['info']['validMeshes']==16 and len(r['info']['activeHairs'])==1 and not r['errors']and len(r['info']['clips'])==14
 assert p.stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
 views.append({'id':sid,'views':len(r['records'])})
actor=ROOT/'src/cocos/assets/resources/actors/raphael';staged=MIRROR/'assets/resources/actors/raphael'
for name in ['manifest.json','raphael-polish.glb']:assert sha(BASE/name)==sha(staged/name)
for name in ['manifest.json','raphael-polish.glb','raphael-polish.glb.meta']:shutil.copy2(staged/name,actor/name)
assets=ROOT/'src/cocos/assets/resources/actors';shutil.copytree(MIRROR/'assets/resources/actors/hairstyles-v3',assets/'hairstyles-v3',dirs_exist_ok=True);shutil.copy2(MIRROR/'assets/resources/actors/hairstyles-v3.meta',assets/'hairstyles-v3.meta')
shutil.copytree(MIRROR/'build/concept-2d-hairstyles-v3',ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'sourceVerification':'source-verification.json','selectionReview':'runtime/selection/report.json','artReview':'art-review.json','views':views,'url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=hairstyles-v3-refined'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n');print('Installed reviewed hairstyle candidate in canonical preview',flush=True)
