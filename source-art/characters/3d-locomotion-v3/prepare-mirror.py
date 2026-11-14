"""Reuse the complete existing Cocos build mirror, including every current script."""
from pathlib import Path
import shutil,json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
MIRROR=Path('C:/Users/Alexa/AppData/Local/Temp/Singularity-weapons-final-20261109')
assert (MIRROR/'package.json').is_file()
count=0
for name in ['assets','settings','build-templates','extensions','tools']:
 for source in (ROOT/'src/cocos'/name).rglob('*'):
  if not source.is_file():continue
  target=MIRROR/source.relative_to(ROOT/'src/cocos');target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists()or target.stat().st_size!=source.stat().st_size or abs(target.stat().st_mtime-source.stat().st_mtime)>.01:
   shutil.copy2(source,target);count+=1
for name in ['Build-Local.ps1','package.json','tsconfig.json','tsconfig.core.json']:
 shutil.copy2(ROOT/'src/cocos'/name,MIRROR/name)
print('COMPLETE_MIRROR_SYNC',count)
