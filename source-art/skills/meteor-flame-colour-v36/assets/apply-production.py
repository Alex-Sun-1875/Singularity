"""Publish only the two reviewed colour textures and two preload strings."""
from pathlib import Path
import argparse,hashlib,json,uuid
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
RES=ROOT/'src/cocos/assets/resources/vfx/production';LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
parser=argparse.ArgumentParser();parser.add_argument('--lock-owner',required=True);args=parser.parse_args()
assert LOCK.is_file() and LOCK.read_text(encoding='ascii').strip()==args.lock_owner,'Caller must hold common build lock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
for item in record['resources']:assert sha(HERE/item['name'])==item['sha256'],'Reviewed colour PNG changed'
ts=ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts';before=ts.read_bytes();after=before
for old,new in [(b"'fire-meteor-seal-colour-v35r2'",b"'fire-meteor-seal-colour-v36'"),(b"'fire-meteor-seal-light-v35r2'",b"'fire-meteor-seal-light-v36'")]:
    assert after.count(old)==1 and after.count(new)==0,'Unexpected texture preload source'
    after=after.replace(old,new)
for check in [b'opacity:number',b'opacity:0',b'item.opacity=alpha;',b'opacity:s.opacity',b"'fire-seal-v35r2'",b'radius*2/(460/512),true,.045']:
    assert check in before and check in after
preserve_paths=[RES/n for n in ['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png','fire-seal-v35r2.effect']]
runtime=ts.parent
preserve_paths.extend([runtime/'UnifiedShieldEffects.ts',runtime/'FireImpactEffects.ts',runtime/'NativeSkillVfx.ts'])
preserved={str(p.relative_to(ROOT)):sha(p) for p in preserve_paths}
alpha_checks={}
for item in record['resources']:
    name=item['name'];old_name=name.replace('-v36.png','-v35r2.png')
    old_array=np.asarray(Image.open(RES/old_name).convert('RGBA'));new_array=np.asarray(Image.open(HERE/name).convert('RGBA'))
    assert old_array.shape==new_array.shape and np.array_equal(old_array[:,:,[0,3]],new_array[:,:,[0,3]]),'Red intensity or alpha changed'
    alpha_checks[name]={'redIdentical':True,'alphaIdentical':True,'sizeUnchanged':True,'onlyChangedChannels':['G','B']}
    (RES/name).write_bytes((HERE/name).read_bytes())
    meta=json.loads((RES/(old_name+'.meta')).read_text(encoding='utf8'));identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a';sub['displayName']=Path(name).stem
    sub['userData']['imageUuidOrDatabaseUri']=identity;meta['userData']['redirect']=sub['uuid']
    (RES/(name+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ts.write_bytes(after)
assert all(sha(ROOT/p)==h for p,h in preserved.items())
record['publication']={'productionUpdated':True,'guard':'Acquired common build lock for one brief publication; no build run.',
 'rendererBeforeSha256':hashlib.sha256(before).hexdigest(),'rendererAfterSha256':hashlib.sha256(after).hexdigest(),
 'rendererDiff':'Exactly two texture resource strings; all remaining bytes including effect path, opacity instrumentation and ground geometry unchanged.',
 'productionFiles':{i['name']:sha(RES/i['name']) for i in record['resources']},'pixelAssertions':alpha_checks,
 'slots':{'0':'unchanged v27 jets','1':'unchanged v27 small seal','2':'fire-meteor-seal-colour-v36','3':'unchanged v24 noise','4':'fire-meteor-seal-light-v36'},
 'preserved':preserved}
record['review']['local']='Root and asset agent inspected the one same-native-fire-frame computation: orange light/halo now match the inside flame family; geometry, alpha and red intensity retained. Labels cleaned only; palette unchanged.'
record['review']['production']='Published and frozen. No effect, geometry, impact or lifecycle edits.'
record['review']['native']='Pending root standard test build and same-phase actual capture; source-frame computation is not native acceptance.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record['publication'],ensure_ascii=False))
