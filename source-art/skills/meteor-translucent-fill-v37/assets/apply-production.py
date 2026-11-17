"""Publish only v37's two reviewed textures and the two preload names."""
from pathlib import Path
import argparse,hashlib,json,uuid
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
RES=ROOT/'src/cocos/assets/resources/vfx/production';LOCK=ROOT/'src/cocos/temp/taptap-build.lock'
parser=argparse.ArgumentParser();parser.add_argument('--lock-owner',required=True);args=parser.parse_args()
assert LOCK.is_file() and LOCK.read_text(encoding='ascii').strip()==args.lock_owner,'Caller must hold common build lock'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();record=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
for item in record['resources']:assert sha(HERE/item['name'])==item['sha256']
ts=ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts';before=ts.read_bytes();after=before
for old,new in [(b"'fire-meteor-seal-colour-v36'",b"'fire-meteor-seal-colour-v37'"),(b"'fire-meteor-seal-light-v36'",b"'fire-meteor-seal-light-v37'")]:
    assert after.count(old)==1 and after.count(new)==0
    after=after.replace(old,new)
for check in [b'opacity:number',b'opacity:0',b'item.opacity=alpha;',b'opacity:s.opacity',b"'fire-seal-v35r2'",b'radius*2/(460/512),true,.045']:
    assert check in before and check in after
preserve_paths=[RES/n for n in ['fire-ground-jets-v27.png','fire-jet-seal-v27.png','fire-ground-v27.effect','fire-flow-noise-v24.png','fire-seal-v35r2.effect']]
preserve_paths.extend([ts.parent/n for n in ['UnifiedShieldEffects.ts','FireImpactEffects.ts','NativeSkillVfx.ts']])
preserved={str(p.relative_to(ROOT)):sha(p) for p in preserve_paths};checks={}
for item in record['resources']:
    name=item['name'];old_name=name.replace('-v37.png','-v36.png')
    old=np.asarray(Image.open(RES/old_name).convert('RGBA'));new=np.asarray(Image.open(HERE/name).convert('RGBA'))
    assert old.shape==new.shape
    if 'colour' in name:
        assert np.array_equal(old[...,:3],new[...,:3])
        assert np.array_equal(new[...,3],np.uint8(old[...,3].astype(float)*.80+.5))
        checks[name]={'mainRGBByteIdentical':True,'alphaScale080ByteExact':True,'sizeUnchanged':True}
    else:
        y,x=np.mgrid[:512,:512];outside=np.hypot((x-255.5)*2,(y-255.5)*2)>=332.5334167175263
        assert np.array_equal(new[outside],np.uint8(old[outside].astype(float)*.80+.5))
        checks[name]={'outsideInnerDiscAllChannelsScale080Exact':True,'innerFillWithinRadius332533':True,'sizeUnchanged':True}
    (RES/name).write_bytes((HERE/name).read_bytes())
    meta=json.loads((RES/(old_name+'.meta')).read_text(encoding='utf8'));identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+name))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a';sub['displayName']=Path(name).stem
    sub['userData']['imageUuidOrDatabaseUri']=identity;meta['userData']['redirect']=sub['uuid']
    (RES/(name+'.meta')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ts.write_bytes(after);assert all(sha(ROOT/p)==h for p,h in preserved.items())
record['publication']={'productionUpdated':True,'guard':'Common build lock owned for brief publication; no build run.',
 'rendererBeforeSha256':hashlib.sha256(before).hexdigest(),'rendererAfterSha256':hashlib.sha256(after).hexdigest(),
 'rendererDiff':'Exactly two meteor texture paths; effect/lifecycle/opacity/geometry unchanged.',
 'productionFiles':{i['name']:sha(RES/i['name']) for i in record['resources']},'pixelAssertions':checks,'preserved':preserved,
 'slots':{'2':'fire-meteor-seal-colour-v37','4':'fire-meteor-seal-light-v37','0/1/3':'unchanged jets/small-seal/noise'}}
record['review']['production']='Published and frozen; root owns standard build and actual capture.'
record['review']['native']='Pending actual Cocos same-phase capture; material computation not user/device acceptance.'
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record['publication'],ensure_ascii=False))
