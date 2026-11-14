from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];BUILD=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109/build/concept-2d-bow-artifact-v1')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=read(BASE/'runtime/after/report.json');bows=read(BASE/'runtime/all-bows-review.json');proof=read(BASE/'preservation.json');stage=read(BASE/'stage-record.json')
assert not review['errors']and not review['engineErrors']and not bows['errors']and not bows['engineErrors'];assert len(bows['results'])==7 and all(r['valid']for r in bows['morphViews'])
assert proof['characterGLBSHA256']==sha(ROOT/'src/cocos/assets/resources/actors/raphael/raphael-polish.glb')
assert all(sha(ROOT/f'src/cocos/assets/resources/actors/props-native/design-{id.lower()}/design-{id.lower()}.fbx')==h for id,h in proof['allSevenBowFBXSHA256'].items())
assert stage['scriptHashes']=={p.relative_to(ROOT/'src/cocos/assets/scripts').as_posix():sha(p)for p in (ROOT/'src/cocos/assets/scripts').rglob('*.ts')},'Source changed after this build; restage current changes before installing'
assert len(read(BASE/'cache-repair.json')['invalidated'])==14
shutil.copytree(BUILD,ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'revision':'bow-artifact-v1','build':'concept-2d-bow-artifact-v1','characterGLBSHA256':proof['characterGLBSHA256'],'invalidatedMorphCaches':14,'verifiedMorphViews':len(bows['morphViews']),'engineErrors':0,'canonicalRuntimeVerified':False,'url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=bow-artifact-v1'}
(BASE/'install-record.json').write_text(json.dumps(record,indent=2)+'\n');print('INSTALLED_BOW_ARTIFACT_FIX')
