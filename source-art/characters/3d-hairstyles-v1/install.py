from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=read(BASE/'source-verification.json');ui=read(BASE/'runtime/selection/report.json')
assert source['originalCurlyDesignRetained']and source['faceBodyGeometryUVWeightsPreserved']and source['allFaceAndClothingMaterialRecordsPreserved']and source['all14MotionCurvesPreserved']
assert len(ui['rows'])==4 and ui['persisted']=='nero'and not ui['errors']and not ui['hood']['actual']and ui['mobile']['id']=='dante'
assert (BASE/'runtime/selection/report.json').stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
views=[]
for style in ['curly','dante','nero','vergil']:
 report=read(BASE/'runtime/after'/style/'report.json');assert report['info']['revision']=='hairstyles-v1'and report['info']['validMeshes']==16 and len(report['info']['activeHairs'])==1 and not report['errors'];assert len(report['info']['clips'])==14
 assert (BASE/'runtime/after'/style/'report.json').stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
 views.append({'id':style,'count':len(report['records'])})
actor=ROOT/'src/cocos/assets/resources/actors/raphael';staged=MIRROR/'assets/resources/actors/raphael'
for name in ['manifest.json','raphael-polish.glb']:assert sha(BASE/name)==sha(staged/name)
for script in ['Actors.ts','Hairstyles.ts','Hud.ts','CharacterPanel.ts','CharacterPreview.ts','ChapterGame.ts']:
 assert (ROOT/'src/cocos/assets/scripts/runtime'/script).read_text(encoding='utf-8')==(MIRROR/'assets/scripts/runtime'/script).read_text(encoding='utf-8')
for name in ['manifest.json','raphael-polish.glb','raphael-polish.glb.meta']:shutil.copy2(staged/name,actor/name)
assets=ROOT/'src/cocos/assets/resources/actors';shutil.copytree(MIRROR/'assets/resources/actors/hairstyles-v1',assets/'hairstyles-v1',dirs_exist_ok=True);shutil.copy2(MIRROR/'assets/resources/actors/hairstyles-v1.meta',assets/'hairstyles-v1.meta')
for script in ['Hairstyles.ts.meta']:
 shutil.copy2(MIRROR/'assets/scripts/runtime'/script,ROOT/'src/cocos/assets/scripts/runtime'/script)
shutil.copytree(MIRROR/'build/concept-2d',ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'sourceVerification':'source-verification.json','selectionReview':'runtime/selection/report.json','views':views,'url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=hairstyles-v1'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n');print('Installed four hairstyles and selector in canonical preview',flush=True)
