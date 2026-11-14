"""Apply reviewed carry-only data without overwriting character appearance."""
from pathlib import Path
from copy import deepcopy
import json

def apply_sword_carry_calibration(actor,root):
 path=Path(root)/'source-art/weapons/3d-sword-carry-v2/calibration.json'
 if not path.exists():return False
 data=json.loads(path.read_text(encoding='utf-8'));carry=actor['cocosBinding']['swordBackCarry']
 assert carry['bone']==data['bone']
 for id,placement in data['items'].items():
  assert id in carry['items']
  carry['items'][id]=deepcopy(placement)
 for kind,id in [('sword','W01'),('greatsword','L01')]:
  carry['placements'][kind]=deepcopy(data['items'][id])
 actor['swordCarryRevision']=data['revision'];actor['swordCarryReview']='source-art/weapons/3d-sword-carry-v2/README.md'
 return True

def apply_bow_carry_calibration(actor,root):
 # Existing exporters call this entry point; retain both reviewed calibrations.
 sword_applied=apply_sword_carry_calibration(actor,root)
 path=Path(root)/'source-art/weapons/3d-bow-carry-v2/calibration.json'
 if not path.exists():return sword_applied
 data=json.loads(path.read_text(encoding='utf-8'));carry=actor['cocosBinding']['swordBackCarry']
 assert carry['bone']==data['bone']
 carry['bowBone']=data['bowBone']
 for id,placement in data['items'].items():
  assert id in carry['items']
  carry['items'][id]=deepcopy(placement)
 carry['placements']['bow']=deepcopy(data['items']['W07'])
 for id,placement in data['quiverPlacements'].items():
  assert id in carry['quiver']['placements']
  carry['quiver']['placements'][id]=deepcopy(placement)
 actor['bowCarryRevision']=data['revision'];actor['bowCarryReview']='source-art/weapons/3d-bow-carry-v2/README.md'
 return True
