"""Install only reviewed sword placements; preserve meshes, actions and other gear."""
from pathlib import Path
from copy import deepcopy
import hashlib, json, math, sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
sys.path.insert(0, str(ROOT / 'tools/model-pipeline'))
from weapon_carry_calibration import apply_sword_carry_calibration

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

actor = ROOT / 'src/cocos/assets/resources/actors/raphael'
current = read(actor / 'manifest.json')
ids = ['W01', 'W02', 'W04', 'W05', 'W06', 'DR3-03', 'DR4-03', 'DE06', 'L01']
assert all(id in current['cocosBinding']['swordBackCarry']['items'] for id in ids)
recipe = next(r for r in read(BASE / 'candidate-placements.json') if r['name'] == 'final')
placement = {key: recipe[key] for key in ['position', 'blade', 'normal']}
data = {'revision': 'sword-back-contact-v2', 'bone': 'spine_03', 'items': {id: deepcopy(placement) for id in ids},
        'basis': {'source': current['source'], 'modelAngleDegrees': math.degrees(math.atan2(placement['blade'][0], -placement['blade'][1])), 'sheathPitchDegrees': math.degrees(math.asin(placement['blade'][2]))}}
write(BASE / 'calibration.json', data)
before = BASE / 'before-bindings.json'
if not before.exists():
    write(before, {'bindings': deepcopy(current['cocosBinding']), 'source': current['source'],
                  'protectedFiles': {name: hashlib.sha256((actor / name).read_bytes()).hexdigest() for name in ['raphael-polish.glb', 'raphael-polish.glb.meta', 'raphael.fbx']}})
for path in [actor / 'manifest.json', ROOT / current['source'].replace('raphael.blend', 'manifest.json'), ROOT / 'source-art/characters/3d-hairstyles-v3/manifest.json']:
    value = read(path)
    original = deepcopy(value)
    apply_sword_carry_calibration(value, ROOT)
    # Reconstruct the original to prove all unrelated data survived.
    check = deepcopy(value)
    for id in ids:
        check['cocosBinding']['swordBackCarry']['items'][id] = original['cocosBinding']['swordBackCarry']['items'][id]
    for kind in ['sword', 'greatsword']:
        check['cocosBinding']['swordBackCarry']['placements'][kind] = original['cocosBinding']['swordBackCarry']['placements'][kind]
    for key in ['swordCarryRevision', 'swordCarryReview']:
        if key in original:
            check[key] = original[key]
        else:
            check.pop(key, None)
    assert check == original, 'Unrelated actor data changed'
    write(path, value)
print('Installed sword-only carry data for', len(ids), 'models')
