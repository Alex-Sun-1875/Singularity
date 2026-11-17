"""Build the approved slate-blue skins from existing art and shared palette roles."""
from pathlib import Path
from PIL import Image, ImageChops
import json
import re
import uuid
import hashlib

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SKIN=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
SOURCE=OUT.parent/'selection-redesign-v2/compose-review.py'
scope={'__file__':str(SOURCE)}
exec(compile(SOURCE.read_text(encoding='utf-8').split('\noriginals=')[0],str(SOURCE),'exec'),scope)
palette_text=(ROOT/'src/cocos/assets/scripts/shared/ui/FeedbackPalette.ts').read_text(encoding='utf-8')
def role(name):
    color=re.search("'"+re.escape(name)+"':'(#[A-Fa-f0-9]{6})'",palette_text).group(1)
    return tuple(int(color[index:index+2],16) for index in (1,3,5))
palette={'body':role('selection.surface'),'rim':role('selection.edge'),'highlight':role('selection.highlight')}
files=[]
def save(image,name):
    target=SKIN/(name+'.png')
    image.save(target,optimize=True)
    meta_path=target.with_suffix('.png.meta')
    if not meta_path.exists():
        meta=json.loads((SKIN/'prep-socket-v5.png.meta').read_text(encoding='utf-8'))
        old=meta['uuid'];new=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity/'+target.relative_to(ROOT).as_posix()))
        content=json.dumps(meta,ensure_ascii=False,indent=2).replace(old,new).replace('prep-socket-v5',name)
        meta_path.write_text(content+'\n',encoding='utf-8')
    files.append({'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':image.size})

normal=Image.open(SKIN/'prep-skill-row-v5.png').convert('RGBA')
selected=scope['material_inlay'](normal,True,palette)
selected.putalpha(normal.getchannel('A'))
save(selected,'prep-selection-row-v7')

# Texture precedes item art inside the existing rounded clip; alpha matches the sample blend.
base=Image.new('RGBA',(128,64),(0,0,0,0))
inlay=scope['material_inlay'](base,True,palette)
save(inlay,'prep-selection-inlay-v7')
save(scope['muted_smoke'](Image.open(SKIN/'prep-item-sword-v2.png')),'prep-item-common-sword-v7')
save(scope['muted_smoke'](Image.open(SKIN/'prep-inspect-sword-v2.png')),'prep-inspect-common-sword-v7')

record={'date':'2026-11-17','design':'User approved slate-blue for equipment and skill selection.',
        'method':'Deterministic Pillow composition; existing skins and material grain, shared FeedbackPalette roles.',
        'palette':palette,'files':files,'runtimeValidation':'pending','tapTapDevice':'not_validated'}
(OUT/'runtime-assets.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec_path=OUT/'palettes.json'
spec=json.loads(spec_path.read_text(encoding='utf-8'))
spec['status']='slate_blue_approved_for_implementation';spec['selectedPalette']='slate-blue';spec['approvalDate']='2026-11-17'
spec['runtimeIntegration']='in_progress'
spec_path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
