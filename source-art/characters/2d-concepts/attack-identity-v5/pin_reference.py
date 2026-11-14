"""Keep the accepted model itself immutable while calibrating other poses.

Every idle uses the accepted attack model's original leg pixels/density. The
ready/recovery attack frames reuse exactly that accepted reference, so family
median estimation cannot widen one while narrowing its otherwise equal idle.
"""
from pathlib import Path
import json,hashlib,sys
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent/'local-qwen21-unified-v3'))
import prepare

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

original=HERE.parent/'body-scale-v4/candidate-runtime'
contract=read(HERE/'playback-contract-before.json')
assert sha(original/'manifest.json')==contract['sourceManifestSHA256']
manifest=read(original/'manifest.json');frames=prepare.inventory(manifest)
legjson=HERE/'edits/legs/edits.json';legs=read(legjson)
if isinstance(legs,dict):legs=legs['edits']
merged={}
for row in legs:
    r=dict(row);r['cropPath']=str((legjson.parent/r['cropPath']).resolve());merged[r['image'],r['index']]=r
staticjson=HERE/'edits/static/static.json';static=read(staticjson)
out=HERE/'edits/baseline';out.mkdir(parents=True,exist_ok=True)
pins=[]
for row in static:
    r=dict(row);r['cropPath']=str((staticjson.parent/r['cropPath']).resolve())
    r['referenceModelLock']='Accepted attack-model pants/boots preserved from neutral master; no estimated family warp'
    merged[r['image'],r['index']]=r;pins.append(dict(image=r['image'],index=r['index'],role='neutral model identity'))
for d in prepare.DIRECTIONS:
    source=prepare.find(frames,'attack_sword_W01',d,0)
    x,y,w,h=source['rect'];im=Image.open(original/source['image']).convert('RGBA').crop((x,y,x+w,y+h))
    path=out/f'accepted-attack-{d}.png';im.save(path)
    factor=manifest['frameScaleFactors'][source['image'].removesuffix('.png')][source['index']]
    for phase in (0,3):
        target=prepare.find(frames,'attack_sword_W01',d,phase)
        r=dict(image=target['image'],index=target['index'],cropPath=str(path.resolve()),origin=source['origin'],newFactor=factor,
               referenceModelLock='Exact accepted original attack phase0; recovery returns to the same ready pose')
        merged[r['image'],r['index']]=r;pins.append(dict(image=r['image'],index=r['index'],role='immutable accepted ready/recovery model',sourcePixelSHA256=sha(path)))
write(HERE/'reference-locked-edits.json',list(merged.values()))
write(HERE/'reference-lock-report.json',dict(status='accepted model locked; verify packed runtime separately',sourceManifestSHA256=sha(original/'manifest.json'),physicalFrames=len(merged),pinnedFrames=len(pins),pins=pins,
    reason='Visual runtime comparison exposed a small width divergence because separate family medians also transformed the reference itself. Preserve approved reference pixels and identical idle leg density; all other corrected poses remain unchanged.'))
print({'physicalFrames':len(merged),'pinnedBaselineFrames':len(pins),'otherCorrectedFramesUnchanged':len(merged)-len(pins)})
