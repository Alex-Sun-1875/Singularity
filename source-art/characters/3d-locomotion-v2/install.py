from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');BUILD=MIRROR/'build/concept-2d-locomotion-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=read(BASE/'source-verification.json');art=read(BASE/'art-review.json');views=read(BASE/'runtime/poses/report.json');preview=read(BASE/'runtime/preview-review.json');live=read(BASE/'runtime/live-review.json');smoke=read(BASE/'runtime/canonical-smoke.json')
assert p['all16MeshGeometryUVWeightsMaterialsPreserved']and p['allFourHairstylesPreserved']and p['bindPreserved'];assert len(p['unchangedClips'])==12
assert p['runtimeGLBSHA256']==sha(BASE/'raphael-polish.glb')==art['runtimeGLBSHA256'];assert art['actualEngineViewsReviewed'];assert not art['userApproved']
assert len(views['records'])==48 and not views['errors'];assert preview['gifDurationMilliseconds']==2000 and not live['errors'];assert all(not r.get('errors')for r in smoke['rows'])
assert all((BASE/f).stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime for f in ['runtime/poses/report.json','runtime/after/frames.json','runtime/live-review.json','runtime/canonical-smoke.json'])
assert (BUILD/'source-scripts-sha256.json').is_file(),'Rebuild with the full scripts directory before installing; partial mirrors broke arrow emission'
fingerprint=read(BUILD/'source-scripts-sha256.json')['scripts']
assert fingerprint=={p.relative_to(ROOT/'src/cocos/assets/scripts').as_posix():sha(p)for p in (ROOT/'src/cocos/assets/scripts').rglob('*.ts')},'Current source changed; rebuild with complete dependencies before installing'
actor=ROOT/'src/cocos/assets/resources/actors/raphael';staged=MIRROR/'assets/resources/actors/raphael'
for n in ['manifest.json','raphael-polish.glb']:assert sha(BASE/n)==sha(staged/n)
assert (BUILD/'index.html').stat().st_mtime>max((ROOT/'src/cocos/assets/scripts'/p).stat().st_mtime for p in ['runtime/Actors.ts','runtime/ChapterGame.ts','core/GameSession.ts'])
for n in ['manifest.json','raphael-polish.glb','raphael-polish.glb.meta']:shutil.copy2(staged/n,actor/n)
shutil.copytree(BUILD,ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'revision':'locomotion-v2','build':'concept-2d-locomotion-v2','runMetresPerSecond':5.2,'walkMetresPerSecond':1.6,'url':'http://127.0.0.1:7469/?view=2d&player=3d&hair=dante&revision=locomotion-v2'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print('INSTALLED_LOCOMOTION_V2',record['runtimeGLBSHA256'])
