"""Publish the one reviewed reference RGB candidate; caller owns common lock."""
from pathlib import Path
import argparse,hashlib,json,uuid
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
RES=ROOT/'src/cocos/assets/resources/vfx/production'
LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
parser=argparse.ArgumentParser();parser.add_argument('--lock-owner',required=True);args=parser.parse_args()
assert LOCK.is_file() and LOCK.read_text(encoding='ascii').strip()==args.lock_owner,'Caller must hold common build lock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
for item in record['resources']:assert sha(HERE/item['name'])==item['sha256'],'Reviewed PNG changed'
ts=ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts'
before=ts.read_bytes();after=before
replacements=[
 (b"'fire-meteor-seal-v34'",b"'fire-meteor-seal-colour-v34r2'"),
 (b"'fire-flow-noise-v24']",b"'fire-flow-noise-v24','fire-meteor-seal-light-v34r2']"),
 (b"'fire-seal-v34'",b"'fire-seal-v34r2'"),
 (b"material.setProperty('mainTexture',texture);",b"material.setProperty('mainTexture',texture);\r\n   if(kind==='meteorSeal')material.setProperty('lightTexture',FireGroundEffects.textures[4]);")
]
for old,new in replacements:
    assert after.count(old)==1 and after.count(new)==0,'Unexpected preload/material source; inspect before writing'
    after=after.replace(old,new)
preserve_names=['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png']
preserved={n:sha(RES/n) for n in preserve_names}
shield=ROOT/'src/cocos/assets/scripts/features/combat/runtime/UnifiedShieldEffects.ts'
if shield.exists():preserved['UnifiedShieldEffects.ts']=sha(shield)
image_template=json.loads((RES/'fire-meteor-seal-v34.png.meta').read_text(encoding='utf8'))
for item in record['resources']:
    name=item['name'];(RES/name).write_bytes((HERE/name).read_bytes())
    meta=json.loads(json.dumps(image_template));identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a'
    sub['displayName']=Path(name).stem;sub['userData']['imageUuidOrDatabaseUri']=identity
    sub['userData']['wrapModeS']='clamp-to-edge';sub['userData']['wrapModeT']='clamp-to-edge'
    meta['userData']['redirect']=sub['uuid'];meta['userData']['fixAlphaTransparencyArtifacts']=False
    (RES/(name+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
effect='fire-seal-v34r2.effect';(RES/effect).write_bytes((HERE/effect).read_bytes())
meta=json.loads((RES/'fire-seal-v34.effect.meta').read_text(encoding='utf8'))
meta['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+effect))
(RES/(effect+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ts.write_bytes(after)
assert all(sha(RES/n)==h for n,h in preserved.items() if n!='UnifiedShieldEffects.ts')
if shield.exists():assert sha(shield)==preserved['UnifiedShieldEffects.ts']
assert b'this.ground(data,p,radius*2/(460/512),true,.045)' in after
record['publication']={
 'productionUpdated':True,'guard':'Caller acquired common build lock for this brief publication only; no build run.',
 'rendererBeforeSha256':hashlib.sha256(before).hexdigest(),'rendererAfterSha256':hashlib.sha256(after).hexdigest(),
 'productionFiles':{n:sha(RES/n) for n in [*[i['name'] for i in record['resources']],effect]},
 'slots':{'0':'unchanged v27 jets','1':'unchanged v27 small seal','2':'fire-meteor-seal-colour-v34r2','3':'unchanged v24 repeating noise','4':'fire-meteor-seal-light-v34r2'},
 'preserved':preserved,'circle':'Original centre/radius/camera-aligned ground UV/+0.045 lift unchanged'}
record['review']['local']='Unique same-ellipse reference reprojection and exact material on dark green-grey ground inspected. Whole meteor silhouette and its substrate detail removed; hidden diffuse light interpolated from valid surrounding original RGB; unknown inner engraving not invented.'
record['review']['production']='Published with dedicated two-sampler effect and meteor-only resource/material wiring.'
record['review']['native']='Pending root standard build and actual Cocos capture. No user/TapTap acceptance claim.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record['publication'],ensure_ascii=False))
