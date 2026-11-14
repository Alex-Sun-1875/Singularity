"""Install reviewed side-view source actions and the complete Cocos build."""
from pathlib import Path
import json,hashlib,shutil,struct
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');BUILD=MIRROR/'build/concept-2d-locomotion-v10'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=read(BASE/'source-verification.json');saved=read(BASE/'saved-source-review.json');art=read(BASE/'art-review.json');preview=read(BASE/'preview/preview-review.json')
assert not art.get('userRejected'),'User reverted this adjustment; active locomotion is v9'
assert len(proof['changedThisRevision'])==2 and len(proof['unchangedClips'])==12
assert all(proof[k]for k in ['all16MeshGeometryUVWeightsMaterialsPreserved','allFourHairstylesPreserved','bindPreserved'])
assert saved['savedActionsMatch']and proof['runtimeGLBSHA256']==saved['runtimeGLBSHA256']==art['runtimeGLBSHA256']==preview['glbSHA256']==sha(BASE/'raphael-polish.glb')
assert art['sourceLegPosesReviewed']and not art['userApproved']and not art['actualEngineViewsReviewed']
assert preview['view']=='side'and preview['gifDurationMilliseconds']==530
assert all(r['requestedView']=='side'and r['allNonLegChannelsPreserved']and r['footLateralTracksPreserved']for r in proof['sideLegs'])
data=(BASE/'raphael-polish.glb').read_bytes();length=struct.unpack_from('<I',data,12)[0];gltf=json.loads(data[20:20+length])
assert len(gltf['animations'])==14 and {'run','run_staff','walk','walk_staff'}<=set(a['name']for a in gltf['animations'])
scripts=lambda folder:{p.relative_to(folder).as_posix():sha(p)for p in folder.rglob('*.ts')}
source_scripts=scripts(ROOT/'src/cocos/assets/scripts');assert source_scripts==scripts(MIRROR/'assets/scripts'),'Build must contain the complete current script set'
assert 'build Task (concept-2d-locomotion-v10) Finished'in(MIRROR/'temp/build-concept-2d-locomotion-v10-out.log').read_text(encoding='utf-8')
assert (BUILD/'index.html').stat().st_mtime>=(BASE/'raphael-polish.glb').stat().st_mtime
for n in ['manifest.json','raphael-polish.glb']:assert sha(BASE/n)==sha(MIRROR/'assets/resources/actors/raphael'/n)
configs=list((BUILD/'assets/actor-raphael').glob('config.*.json'));assert len(configs)==1
actor=ROOT/'src/cocos/assets/resources/actors/raphael'
assert sha(actor/'raphael-polish.glb')in ['07c1a2797adf46dc401a99f7fb61c48e55b23cd0a338dcd26de99dc64d94ffa8',proof['runtimeGLBSHA256']]
assert read(actor/'manifest.json')['hairstyles']==read(BASE/'manifest.json')['hairstyles']
(BUILD/'source-scripts-sha256.json').write_text(json.dumps({'scripts':source_scripts},indent=2)+'\n',encoding='utf-8')
for n in ['manifest.json','raphael-polish.glb','raphael-polish.glb.meta']:
 source=MIRROR/'assets/resources/actors/raphael'/n;target=actor/n
 if not target.exists()or sha(source)!=sha(target):shutil.copy2(source,target)
shutil.copytree(BUILD,ROOT/'src/cocos/build/concept-2d',dirs_exist_ok=True)
record={'revision':'locomotion-v10','requestedView':'side','runtimeGLBSHA256':sha(actor/'raphael-polish.glb'),'manifestSHA256':sha(actor/'manifest.json'),'sourceScripts':len(source_scripts),'changedThisRevision':proof['changedThisRevision'],'animationClips':len(gltf['animations']),'actorBundleConfig':configs[0].name,'actorBundleConfigSHA256':sha(configs[0]),'build':'concept-2d-locomotion-v10','url':'http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v10','sourcePoseReviewed':True,'actualEngineViewsReviewed':False,'browserAccess':'Disabled in Work settings; no browser UI was controlled','userApproved':False}
(BASE/'install-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('INSTALLED',json.dumps(record))
