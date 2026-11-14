"""Copy accepted reaction sibling bytes after parent lifts runtime import freeze."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
path=HERE/'metadata-readable.json'
meta=json.loads(path.read_text(encoding='utf-8'))
runtime=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
runtime.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
copied=[]
for key,sheet in meta['sheets'].items():
    source=HERE/Path(sheet['image']).name
    target=runtime/source.name
    shutil.copyfile(source,target)
    assert sha(source)==sha(target)==sheet['sha256']
    sheet['runtimeFile']=str(target.relative_to(ROOT)).replace('\\','/')
    sheet['runtimeInstalled']=True
    copied.append({'file':sheet['runtimeFile'],'sha256':sha(target),'dimensions':sheet['size']})
meta['runtimeInstalled']=True
meta['status']='RUNTIME_SIBLINGS_COPIED_PENDING_PARENT_IMPORT_NATIVE_QA'
meta['limits']=[v for v in meta['limits'] if 'import freeze' not in v]
meta['limits'].append('PNG siblings copied after parent lifted import freeze. Engine import/build and native pose acceptance remain parent-owned; game manifest/code unchanged.')
meta['sheets']['hero-v4-hit-death-readable']['rectIsolation']={'foregroundComponents':16,'perRow':4,'foreignBodyPixelsInsideAllRects':0,'minimumGlobalColumnBodyGapPixels':13,'note':'Native perFrameRects are independent integer crops. Nominal1254/4 grid lines can intersect a body; do not replace measured rects by equal-cell crops.'}
path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'installed':copied,'upps':{k:v['worldUnitsPerPixel'] for k,v in meta['actions'].items()},'indices':{k:v['frameIndices'] for k,v in meta['actions'].items()}},ensure_ascii=False))
