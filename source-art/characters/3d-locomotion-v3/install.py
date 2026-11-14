"""Install only the reviewed candidate and its complete-source local build."""
from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');BUILD=MIRROR/'build/concept-2d-locomotion-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=read(BASE/'source-verification.json');saved=read(BASE/'saved-source-review.json');art=read(BASE/'art-review.json')
assert len(proof['changedClips'])==4 and len(proof['unchangedClips'])==10
assert proof['all16MeshGeometryUVWeightsMaterialsPreserved']and proof['allFourHairstylesPreserved']and proof['bindPreserved']
assert saved['savedActionsMatch']and proof['runtimeGLBSHA256']==saved['runtimeGLBSHA256']==art['runtimeGLBSHA256']==sha(BASE/'raphael-polish.glb')
assert art['actualEngineViewsReviewed']and not art['userApproved']
assert len(read(BASE/'runtime/after/report.json')['records'])==96
assert len(read(BASE/'runtime/after-motion/report.json')['records'])==240
assert not read(BASE/'runtime/live-review.json')['errors']
assert all(not r.get('errors')for r in read(BASE/'runtime/canonical-smoke.json')['rows'])
assert read(BASE/'runtime/preview-review.json')['gifDurationMilliseconds']==2000
scripts=lambda folder:{p.relative_to(folder).as_posix():sha(p)for p in folder.rglob('*.ts')}
source_scripts=scripts(ROOT/'src/cocos/assets/scripts');assert source_scripts==scripts(MIRROR/'assets/scripts'),'Build mirror must contain the complete current script set'
assert 'build Task (concept-2d-locomotion-v3) Finished' in (MIRROR/'temp/build-concept-2d-locomotion-v3-out.log').read_text(encoding='utf-8')
assert (BUILD/'index.html').stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
for name in ['manifest.json','raphael-polish.glb']:assert sha(BASE/name)==sha(MIRROR/'assets/resources/actors/raphael'/name)
(BUILD/'source-scripts-sha256.json').write_text(json.dumps({'scripts':source_scripts},indent=2)+'\n',encoding='utf-8')
actor=ROOT/'src/cocos/assets/resources/actors/raphael'
for name in ['manifest.json','raphael-polish.glb','raphael-polish.glb.meta']:shutil.copy2(MIRROR/'assets/resources/actors/raphael'/name,actor/name)
shutil.copytree(BUILD,ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'revision':'locomotion-v3','runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'manifestSHA256':sha(actor/'manifest.json'),'sourceScripts':len(source_scripts),'changedClips':proof['changedClips'],'build':'concept-2d-locomotion-v3','url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v3','userApproved':False}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('INSTALLED',json.dumps(record))
