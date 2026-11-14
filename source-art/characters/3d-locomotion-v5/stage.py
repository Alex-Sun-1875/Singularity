from pathlib import Path
import json,shutil,struct
BASE=Path(__file__).resolve().parent
ACTOR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109/assets/resources/actors/raphael')
for name in ['raphael-polish.glb','manifest.json']:shutil.copy2(BASE/name,ACTOR/name)
p=ACTOR/'raphael-polish.glb.meta';meta=json.loads(p.read_text(encoding='utf-8'));duration=struct.unpack('<f',struct.pack('<f',20/30))[0]
for a in meta['userData']['animationImportSettings']:
 if a['name']in ['run','run_staff']:
  a['duration']=duration
  for split in a['splits']:split['from']=0;split['to']=duration
for sub in meta['subMetas'].values():
 if sub.get('name')in ['run.animation','run_staff.animation']:sub['userData']['span']={'from':0,'to':duration}
p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('STAGED_RUN_AND_EXISTING_CLIP_RANGES',duration)
