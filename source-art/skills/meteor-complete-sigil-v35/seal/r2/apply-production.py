"""Publish the reviewed v35r2 textures/effect and three meteor preload names."""
from pathlib import Path
import argparse,hashlib,json,uuid
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
RES=ROOT/'src/cocos/assets/resources/vfx/production';LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
parser=argparse.ArgumentParser();parser.add_argument('--lock-owner',required=True);args=parser.parse_args()
assert LOCK.is_file() and LOCK.read_text(encoding='ascii').strip()==args.lock_owner,'Caller must hold common build lock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
for item in record['resources']:assert sha(HERE/item['name'])==item['sha256'],'Reviewed PNG changed'
ts=ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts';before=ts.read_bytes();after=before
for old,new in [(b"'fire-meteor-seal-colour-v35'",b"'fire-meteor-seal-colour-v35r2'"),(b"'fire-meteor-seal-light-v35'",b"'fire-meteor-seal-light-v35r2'"),(b"'fire-seal-v35'",b"'fire-seal-v35r2'")]:
    assert after.count(old)==1 and after.count(new)==0,'Unexpected meteor resource path'
    after=after.replace(old,new)
for check in [b'opacity:number',b'opacity:0',b'item.opacity=alpha;',b'opacity:s.opacity']:
    assert check in before and check in after,'Root opacity instrumentation must remain'
preserve_names=['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png']
preserved={n:sha(RES/n) for n in preserve_names}
shield=ROOT/'src/cocos/assets/scripts/features/combat/runtime/UnifiedShieldEffects.ts';preserved['UnifiedShieldEffects.ts']=sha(shield)
template=json.loads((RES/'fire-meteor-seal-colour-v35.png.meta').read_text(encoding='utf8'))
for item in record['resources']:
    name=item['name'];(RES/name).write_bytes((HERE/name).read_bytes())
    meta=json.loads(json.dumps(template));identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a';sub['displayName']=Path(name).stem
    sub['userData']['imageUuidOrDatabaseUri']=identity;meta['userData']['redirect']=sub['uuid'];meta['userData']['fixAlphaTransparencyArtifacts']=False
    (RES/(name+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
effect='fire-seal-v35r2.effect';(RES/effect).write_bytes((HERE/effect).read_bytes())
meta=json.loads((RES/'fire-seal-v35.effect.meta').read_text(encoding='utf8'));meta['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+effect))
(RES/(effect+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ts.write_bytes(after)
assert all(sha(RES/n)==preserved[n] for n in preserve_names) and sha(shield)==preserved['UnifiedShieldEffects.ts']
assert b'radius*2/(460/512),true,.045' in after
record['publication']={'productionUpdated':True,'guard':'Acquired common build lock for this brief publication only; no build run.',
 'rendererBeforeSha256':hashlib.sha256(before).hexdigest(),'rendererAfterSha256':hashlib.sha256(after).hexdigest(),
 'productionFiles':{n:sha(RES/n) for n in [*[i['name'] for i in record['resources']],effect]},
 'slots':{'0':'unchanged v27 jets','1':'unchanged v27 small seal','2':'fire-meteor-seal-colour-v35r2','3':'unchanged v24 noise','4':'fire-meteor-seal-light-v35r2'},
 'preserved':preserved,'rendererScope':'Exactly three meteor resource strings; all other bytes including root opacity instrumentation remain unchanged.',
 'ground':'Original centre/range/camera UV/+0.045 preserved'}
record['review']['production']='Published and frozen; root owns standard build/capture.'
record['review']['native']='Pending root build and actual Cocos capture; no user or TapTap acceptance claimed.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record['publication'],ensure_ascii=False))
