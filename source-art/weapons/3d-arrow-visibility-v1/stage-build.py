from pathlib import Path
import json,hashlib,shutil
base=Path('source-art/weapons/3d-arrow-visibility-v1');root=Path.cwd();mirror=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
source=root/'src/cocos/assets/scripts';target=mirror/'assets/scripts';changes=[]
for p in source.rglob('*'):
 if p.is_file():
  q=target/p.relative_to(source)
  if not q.exists()or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(q.read_bytes()).digest():changes.append(p.relative_to(source).as_posix())
shutil.copytree(source,target,dirs_exist_ok=True)
for p in source.rglob('*'):
 if p.is_file():assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((target/p.relative_to(source)).read_bytes()).digest()
for n in ['raphael-polish.glb','manifest.json']:
 assert hashlib.sha256((root/'src/cocos/assets/resources/actors/raphael'/n).read_bytes()).digest()==hashlib.sha256((mirror/'assets/resources/actors/raphael'/n).read_bytes()).digest()
(base/'stage-record.json').write_text(json.dumps({'allScriptFilesSynchronized':True,'changedFiles':changes,'characterMatchesCanonical':True,'scriptHashes':{p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in source.rglob('*.ts')}},indent=2)+'\n')
print('SYNCHRONIZED',changes)
