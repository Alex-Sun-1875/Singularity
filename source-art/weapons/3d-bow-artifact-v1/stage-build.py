from pathlib import Path
import shutil,hashlib,json
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent;src=ROOT/'src/cocos';mirror=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109');changed=[];checked=0
for p in (src/'assets').rglob('*'):
 if not p.is_file():continue
 q=mirror/'assets'/p.relative_to(src/'assets');checked+=1
 if not q.is_file()or p.stat().st_size!=q.stat().st_size or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(q.read_bytes()).digest():
  q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);changed.append(p.relative_to(src).as_posix())
for rel in ['Build-Local.ps1','tools/refresh-morph-build-cache.py']:
 q=mirror/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/rel,q)
record={'allCanonicalAssetFilesSynchronized':True,'checkedFiles':checked,'changedFiles':changed,'scriptHashes':{p.relative_to(src/'assets/scripts').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in (src/'assets/scripts').rglob('*.ts')}}
(BASE/'stage-record.json').write_text(json.dumps(record,indent=2)+'\n');print('STAGED_CURRENT_PROJECT',checked,len(changed),changed[:12])
