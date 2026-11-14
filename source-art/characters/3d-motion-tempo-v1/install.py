"""Install the verified compact native jog; keep weapon and gameplay settings."""
from pathlib import Path
import json,shutil,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];DEST=ROOT/'src/cocos/assets/resources/actors/raphael'
review=json.loads((BASE/'source-verification.json').read_text(encoding='utf-8'));stride=json.loads((BASE/'stride-adaptation.json').read_text(encoding='utf-8'))
assert review['meshUVWeightsUnchanged']and review['bindPoseUnchanged']and review['maxRunArmSpineHelperLocalChannelError']==0
manifest=DEST/'manifest.json'
if not (BASE/'before-manifest.json').exists():shutil.copyfile(manifest,BASE/'before-manifest.json')
a=json.loads(manifest.read_text(encoding='utf-8'))
for name in ['run','run_staff']:
    for records in [a['clips'],a['libraryMotion']['clips']]:
        records[name]['nominalSpeedMetresPerSecond']=stride['adaptedPlantedFootSpeed']
        records[name]['strideSource']='Accepted native jog compacted with connected leg quaternion interpolation; planted foot travel measured at native 30 fps'
        records[name]['strideAdaptation']={'legRotationAmplitude':stride['clips'][0]['legRotationAmplitude'],'source':'source-art/characters/3d-motion-tempo-v1/compact-jog.blend','targetMetresPerSecond':3.6,'originalNominalMetresPerSecond':5.8702678805688056,'rootSoleCorrection':'Original airborne clearance scaled to .65; no arm/hand channel changes'}
a['motionTempoReview']='source-art/characters/3d-motion-tempo-v1/README.md'
manifest.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');shutil.copyfile(BASE/'raphael.fbx',DEST/'raphael.fbx')
(BASE/'install-record.json').write_text(json.dumps({'fbxSHA256':hashlib.sha256((DEST/'raphael.fbx').read_bytes()).hexdigest(),'manifestSHA256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'review':a['motionTempoReview']},indent=2)+'\n',encoding='utf-8')
print('Installed compact jog for 3D Raphael')
