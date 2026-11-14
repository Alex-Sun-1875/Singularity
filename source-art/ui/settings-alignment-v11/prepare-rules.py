"""Extract reference separators without attenuating already blended gold twice."""
from pathlib import Path
import hashlib
import json
import uuid

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze'
source = ROOT / 'source-art/ui/double-gold-frame-v6/reference-design.png'
reference = Image.open(source).convert('RGB')
specs = [
    ('settings-title-rule-v11', (276, 156, 632, 164), False),
    ('settings-row-rule-v11', (284, 312, 631, 320), False),
    ('settings-footer-rule-v11', (447, 521, 455, 557), True),
]
exports = []
for name, box, vertical in specs:
    pixels = np.array(reference.crop(box)).astype(float)
    work = pixels.transpose(1, 0, 2) if vertical else pixels
    background = np.minimum(work[:2].mean(0), work[-2:].mean(0))
    background = np.array(Image.fromarray(background[None].astype('uint8')).filter(ImageFilter.GaussianBlur(2))).astype(float)
    contrast = (work-background) @ np.array([.299, .587, .114])
    alpha = np.clip((contrast-1.5)/130, 0, 1)
    # Undo the source backdrop before writing alpha, so faded ends stay visible.
    rgb = np.clip((work-background*(1-alpha[..., None]))/np.maximum(.001, alpha[..., None]), 0, 255)
    rgba = np.dstack([rgb, alpha*255]).round().astype('uint8')
    if vertical:
        rgba = rgba.transpose(1, 0, 2)
    output = HERE / (name+'.png')
    Image.fromarray(rgba).save(output)
    data = output.read_bytes()
    (ASSETS / output.name).write_bytes(data)
    meta = ASSETS / (output.name+'.meta')
    if not meta.exists():
        template = json.loads((ASSETS / 'double-gold-stag-v6.png.meta').read_text(encoding='utf-8'))
        text = json.dumps(template, ensure_ascii=False, indent=2).replace(template['uuid'], str(uuid.uuid4())).replace('double-gold-stag-v6', name)
        meta.write_text(text+'\n', encoding='utf-8')
    exports.append({'id':name, 'sourceBox':list(box), 'size':list(Image.open(output).size), 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()})
(HERE / 'rules-provenance.json').write_text(json.dumps({
    'source':str(source.relative_to(ROOT)),
    'method':'Local crop, estimated backdrop removal, unpremultiplied gold RGBA; no image generation.',
    'exports':exports,
    'artReview':'Pending rendered in-game comparison, separate from successful extraction.'
},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(exports))
