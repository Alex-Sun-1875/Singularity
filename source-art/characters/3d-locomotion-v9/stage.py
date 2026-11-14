from pathlib import Path
import json,shutil,struct
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
ACTOR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109/assets/resources/actors/raphael')
MIRROR=ACTOR.parents[3]
# The current release helper expects the repository's two-level directory
# layout. Keep the established cache mirror and read its version from the
# real repository, while all generated files still belong to the mirror.
shutil.copytree(ROOT/'src/cocos/release',MIRROR/'release',dirs_exist_ok=True)
shutil.copy2(ROOT/'src/cocos/package-lock.json',MIRROR/'package-lock.json')
helper=MIRROR/'tools/taptap-config.cjs'
s=(ROOT/'src/cocos/tools/taptap-config.cjs').read_text(encoding='utf-8')
anchor="root=path.resolve(project,'../..')"
assert anchor in s
s=s.replace(anchor,"root="+json.dumps(ROOT.as_posix()),1)
helper.write_text(s,encoding='utf-8')
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
