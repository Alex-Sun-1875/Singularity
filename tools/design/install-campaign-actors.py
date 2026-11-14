"""Install the root-reviewed30 source packs; guard existing12 concept assets."""
from pathlib import Path
import hashlib,json,uuid
from PIL import Image
from enemy_atlas_runtime import install_runtime

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'source-art/encounters/cloud-world-v2'
PRODUCTION=ART/'actor-production-v1'
CHARACTERS=ROOT/'src/cocos/assets/resources/flat2d/characters'
PROTECTED=['raphael','mira','lorn','nightqi','kael','evelyn','raider','raider-shield','raider-archer','captain','mine-worker','mine-crawler']
LEGACY={'R1-1':'raider','R1-2':'raider-shield','R1-3':'raider-archer','BOSS_R1':'captain','R2-1':'mine-worker','R2-3':'mine-crawler'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return str(path.relative_to(ROOT)).replace('\\','/')
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
def protected_hashes():return {rel(path):sha(path)for name in PROTECTED for path in (CHARACTERS/name).rglob('*')if path.is_file()}

def main():
    before=protected_hashes();registry=json.loads((ART/'actor-batch-reference-v1/registry.json').read_text('utf-8'))
    folders={json.loads((d/'processed/processing.json').read_text('utf-8'))['id']:d for d in PRODUCTION.iterdir()if(d/'processed/processing.json').exists()}
    assert len(registry['items'])==len(folders)==30
    mapping=dict(LEGACY);items=[]
    for record in registry['items']:
        identity=record['id'];concept=record['proposedConceptId'];assert concept not in PROTECTED
        folder=folders[identity];pack=folder/'processed';review_path=pack/'review.json'
        review=json.loads(review_path.read_text('utf-8'))if review_path.exists()else{}
        review.update(staticArtReview='passed-for-pilot',rootBatchReview='passed30/30 source-and-packed static contact review; runtime acceptance separate',sourceSha256=sha(ROOT/json.loads((pack/'processing.json').read_text('utf-8'))['source']),atlasSha256=sha(pack/'atlas.png'),manifestSha256=sha(pack/'manifest.json'),runtimeInstalled=False)
        review.setdefault('runtimePlayReview','pending after authorized batch installation');review.setdefault('limitations',['Primary poses only, no independent hit/death/diagonals or new native3D'])
        write(review_path,review)
        _,report=install_runtime(pack,concept)
        target=CHARACTERS/concept;image=Image.open(target/'atlas.png');manifest=json.loads((target/'manifest.json').read_text('utf-8'));assert image.size==(1024,1024)and image.mode=='RGBA'
        assert manifest['frameWidth']==manifest['frameHeight']==256
        if identity=='ELITE_06':assert 'walk'not in manifest['actions']and all('attack_sword_step'+str(i)in manifest['actions']for i in range(3))
        mapping[identity]=concept;items.append(dict(id=identity,conceptId=concept,resource='flat2d/characters/'+concept,sourceFolder=rel(folder),sourceSha256=review['sourceSha256'],atlasSha256=sha(target/'atlas.png'),manifestSha256=sha(target/'manifest.json'),atlasSize=[1024,1024],rgbaBytes=4194304,actions=list(manifest['actions']),runtimeGameReview='pending'))
        review['runtimeInstalled']=True;write(review_path,review)
    assert len(mapping)==36 and before==protected_hashes(),'A protected original concept changed during installation; do not overwrite concurrent work'
    index=dict(version=1,templates=mapping,newRuntimeAssets=items,retainedOriginalTemplates=LEGACY,protectedConcepts=PROTECTED,newAssets=30,totalIdentities=36,newIdentityCountIncludingPilots=32,sourceStaticReview='Root30/30 passed;2 representative pilots already game accepted',runtimeAcceptance='New30 batch pending actual game review; source static approval is separate',native3D='Legacy original four enemy families; no new native3D resource delivered')
    path=CHARACTERS/'campaign-v1-index.json';write(path,index);meta=path.with_name(path.name+'.meta')
    if not meta.exists():write(meta,dict(ver='2.0.1',importer='json',imported=True,uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,rel(path))),files=['.json'],subMetas={},userData={}))
    protected_digest=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
    write(PRODUCTION/'runtime-installation.json',dict(status='installed30-root-reviewed-source-packs-game-review-pending',index=rel(path),indexSha256=sha(path),newAssets=items,templateMap=mapping,protectedConcepts=PROTECTED,protectedFiles=len(before),protectedFilesSha256=protected_digest,protectedFilesUnchanged=True,native3DInstalled=False))
    print('Installed30 x1024 atlases and36-identity index; protected'+str(len(before))+' original files unchanged. Runtime game review pending.')

if __name__=='__main__':main()
