from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');BUILD=MIRROR/'build/concept-2d-arrow-visibility-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
proof=read(BUILD/'source-scripts-sha256.json');src=ROOT/'src/cocos/assets/scripts'
assert all(sha(src/n)==proof['scripts'][n]for n in proof['requiredArrowDependencies']),'Arrow-related source changed after review; rebuild before installing'
assert proof['scripts']=={p.relative_to(MIRROR/'assets/scripts').as_posix():sha(p)for p in (MIRROR/'assets/scripts').rglob('*.ts')}
basic=read(BASE/'runtime/after/report.json');skills=read(BASE/'runtime/after/skills-report.json');bows=read(BASE/'runtime/all-bows-review.json')
assert not basic['errors']and not skills['errors']and not bows['errors'];assert len(skills['rows'])==5 and all(r['projectiles']>0 for r in skills['rows']);assert len(bows['results'])==7 and len(bows['controls'])==3
actor=ROOT/'src/cocos/assets/resources/actors/raphael';assert sha(actor/'raphael-polish.glb')==read(ROOT/'source-art/characters/3d-locomotion-v2/install-record.json')['runtimeGLBSHA256']
shutil.copytree(BUILD,ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'revision':'arrow-visibility-v1','build':'concept-2d-arrow-visibility-v1','runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'sourceScriptFiles':len(proof['scripts']),'url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=arrow-visibility-v1','canonicalRuntimeVerified':False,'concurrentSourceUpdatesPreserved':proof['concurrentSourceUpdatesPreserved']}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n');print('INSTALLED_ARROW_FIX',record['sourceScriptFiles'])
