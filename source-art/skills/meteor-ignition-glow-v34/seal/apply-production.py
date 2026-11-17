"""Publish the one inspected v34 candidate under the common build lock."""
from pathlib import Path
import argparse,hashlib,json,uuid

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
parser=argparse.ArgumentParser();parser.add_argument('--lock-owner',required=True);args=parser.parse_args()
assert LOCK.is_file() and LOCK.read_text(encoding='ascii').strip()==args.lock_owner,'Caller must hold its own common build lock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
assert sha(HERE/'fire-meteor-seal-v34.png')==record['asset']['sha256'],'Frozen mask changed after material review'
ts=ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts'
before=ts.read_bytes()
replacements=[(b"'fire-meteor-seal-v33'",b"'fire-meteor-seal-v34'"),(b"'fire-seal-v33'",b"'fire-seal-v34'")]
after=before
for old,new in replacements:
    assert after.count(old)==1 and after.count(new)==0,'Unexpected meteor preload path; inspect before changing'
    after=after.replace(old,new)
preserved={n:sha(RES/n) for n in ['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png']}
for name in ['fire-meteor-seal-v34.png','fire-seal-v34.effect']:
    (RES/name).write_bytes((HERE/name).read_bytes())
imageMeta=json.loads((RES/'fire-meteor-seal-v33.png.meta').read_text(encoding='utf8'))
identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/fire-meteor-seal-v34.png'))
imageMeta['uuid']=identity;sub=imageMeta['subMetas']['6c48a']
sub['uuid']=identity+'@6c48a';sub['displayName']='fire-meteor-seal-v34';sub['userData']['imageUuidOrDatabaseUri']=identity
sub['userData']['wrapModeS']='clamp-to-edge';sub['userData']['wrapModeT']='clamp-to-edge'
imageMeta['userData']['redirect']=sub['uuid'];imageMeta['userData']['fixAlphaTransparencyArtifacts']=False
(RES/'fire-meteor-seal-v34.png.meta').write_text(json.dumps(imageMeta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
effectMeta=json.loads((RES/'fire-seal-v33.effect.meta').read_text(encoding='utf8'))
effectMeta['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/fire-seal-v34.effect'))
(RES/'fire-seal-v34.effect.meta').write_text(json.dumps(effectMeta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ts.write_bytes(after)
assert all(sha(RES/n)==h for n,h in preserved.items()),'Approved v27 assets changed'
assert b'this.ground(data,p,radius*2/(460/512),true,.045)' in after,'Circle/radius/height/UV changed unexpectedly'
record['productionUpdated']=True
record['publication']=dict(guard='Caller acquired common taptap-build.lock for the brief publication window; no Cocos build was run.',preloadChanges='Exactly meteor texture and meteor effect resource names; remaining FireGroundEffects bytes unchanged.',
    rendererBeforeSha256=hashlib.sha256(before).hexdigest(),rendererAfterSha256=hashlib.sha256(after).hexdigest(),
    productionMaskSha256=sha(RES/'fire-meteor-seal-v34.png'),productionEffectSha256=sha(RES/'fire-seal-v34.effect'),preservedV27=preserved)
record['review']['local']='Root and asset agent inspected the unique exact-shader preview: brighter warm complete disk, visible stroke-local halo, transmitted terrain and retained warm ink. Raw data mask is not a colour preview.'
record['review']['native']='Pending root standard build and actual Cocos capture; no claim of user or TapTap acceptance.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record['publication'],ensure_ascii=False))
