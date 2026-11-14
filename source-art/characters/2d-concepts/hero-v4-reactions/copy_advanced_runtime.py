"""Copy accepted advanced run source PNGs without pixel conversion or import."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
DEST=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
path=HERE/'metadata-advanced-runs.json'
meta=json.loads(path.read_text(encoding='utf-8'))
for name,sheet in meta['sheets'].items():
    source=HERE/'advanced-runs'/(name+'.png');dest=DEST/source.name
    shutil.copyfile(source,dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==sheet['sha256']
    sheet['runtimeInstalled']=True
    sheet['runtimePNG']=dest.relative_to(ROOT).as_posix()
meta['runtimeInstalled']=True
meta['status']='RUNTIME_SIBLINGS_COPIED_PENDING_PARENT_IMPORT_NATIVE_QA'
path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'copied':list(meta['sheets']),'actions':list(meta['actions'])}))
