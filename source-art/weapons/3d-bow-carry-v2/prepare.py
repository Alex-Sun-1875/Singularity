from pathlib import Path
import json,sys,copy,hashlib,shutil
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
from weapon_carry_calibration import apply_bow_carry_calibration
path=ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json';actor=json.loads(path.read_text(encoding='utf-8'));original=copy.deepcopy(actor)
ids=['W07','W08','W09','W10','DU2-04','DE02','L02'];carry=actor['cocosBinding']['swordBackCarry']
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
if not(BASE/'before-bindings.json').exists():write(BASE/'before-bindings.json',{'items':{id:carry['items'][id]for id in ids},'quiverPlacements':{id:carry['quiver']['placements'][id]for id in ids}})
data={'revision':'bow-back-contact-v2','bone':carry['bone'],'bowBone':'spine_02','reference':'back-surface.json','space':'Cocos model space; native idle frame zero','items':{},'quiverPlacements':{}}
for id in ids:
 right=id in ['W08','DU2-04'];p=copy.deepcopy(carry['items'][id]);p['position']=[-.13 if right else .13,1.20,-.165 if right else -.155];data['items'][id]=p
 q=copy.deepcopy(carry['quiver']['placements'][id]);q['position']=[.13 if right else -.13,1.27,-.20 if right else -.21];data['quiverPlacements'][id]=q
if not(BASE/'calibration.json').exists():write(BASE/'calibration.json',data)
data=json.loads((BASE/'calibration.json').read_text(encoding='utf-8'));apply_bow_carry_calibration(actor,ROOT)
# Only back-bow/quiver placements and their provenance may change.
check=copy.deepcopy(actor);expected=copy.deepcopy(original)
for key in ['bowCarryRevision','bowCarryReview']:check.pop(key,None);expected.pop(key,None)
for id in ids:
 check['cocosBinding']['swordBackCarry']['items'][id]=copy.deepcopy(original['cocosBinding']['swordBackCarry']['items'][id]);check['cocosBinding']['swordBackCarry']['quiver']['placements'][id]=copy.deepcopy(original['cocosBinding']['swordBackCarry']['quiver']['placements'][id])
check['cocosBinding']['swordBackCarry']['placements']['bow']=copy.deepcopy(original['cocosBinding']['swordBackCarry']['placements']['bow'])
if 'bowBone' in original['cocosBinding']['swordBackCarry']:check['cocosBinding']['swordBackCarry']['bowBone']=original['cocosBinding']['swordBackCarry']['bowBone']
else:check['cocosBinding']['swordBackCarry'].pop('bowBone',None)
assert check==expected
for id in ids:
 assert data['items'][id]['blade']==original['cocosBinding']['swordBackCarry']['items'][id]['blade']and data['items'][id]['normal']==original['cocosBinding']['swordBackCarry']['items'][id]['normal']
write(BASE/'manifest.json',actor)
body=ROOT/'src/cocos/assets/resources/actors/raphael/raphael-polish.glb';proof={'bodyGLBSHA256':hashlib.sha256(body.read_bytes()).hexdigest(),'appearanceRevision':actor['appearanceRevision'],'nonCarryManifestDataUnchanged':True,'handAndArrowCalibrationUnchanged':actor['cocosBinding']['bowEuler']==original['cocosBinding']['bowEuler']and actor['cocosBinding']['arrowPosition']==original['cocosBinding']['arrowPosition'],'items':ids}
write(BASE/'preservation.json',proof)
mirror=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');assert hashlib.sha256((mirror/'assets/resources/actors/raphael/raphael-polish.glb').read_bytes()).hexdigest()==proof['bodyGLBSHA256'];shutil.copy2(BASE/'manifest.json',mirror/'assets/resources/actors/raphael/manifest.json')
print('Staged seven bow and quiver carry placements; body/held/arrow data preserved')
