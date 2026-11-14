"""Deterministic export of approved chrome; button labels remain live Cocos UI."""
from pathlib import Path
import json
import uuid
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / 'src/cocos/assets/resources/ui/quiet-bronze'
image = Image.open(HERE / 'centered-menu-proposal-v8.png').convert('RGB')

def save(name, asset):
    path = HERE / (name+'.png')
    asset.save(path)
    data = path.read_bytes()
    (OUT / path.name).write_bytes(data)
    meta = OUT / (path.name+'.meta')
    if not meta.exists():
        template = (OUT / 'unified-gold-panel-v13.png.meta').read_text(encoding='utf-8')
        old_id = json.loads(template)['uuid']
        meta.write_text(template.replace(old_id, str(uuid.uuid4())).replace('unified-gold-panel-v13', name), encoding='utf-8')
    return {'id': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

exports = []
for name, box in [('start-menu-title-v8', (786, 77, 1058, 174)), ('start-menu-subtitle-v8', (823, 178, 1023, 232)), ('start-menu-rule-v8', (784, 249, 1060, 272))]:
    rgb = np.array(image.crop(box)).astype(float)
    light = rgb @ np.array([.299, .587, .114])
    warmth = (rgb[:,:,0]-rgb[:,:,2])/np.maximum(rgb[:,:,0], 1)
    alpha = np.clip((light-82)/96, 0, 1)*np.clip((warmth-.15)/.13, 0, 1)
    asset = Image.fromarray(np.dstack([rgb, np.round(alpha*255)]).astype('uint8'))
    exports.append(save(name, asset))

for name, box in [('start-menu-primary-v8', (706, 294, 1140, 376)), ('start-menu-secondary-v8', (706, 402, 1140, 484))]:
    button = np.array(image.crop(box)).astype(float)
    h,w = button.shape[:2]
    # Unlettered strips on both sides preserve the native vertical material
    # profile. Interpolate only the caption area, retaining all original rims.
    left = np.median(button[:, 70:90], axis=1)
    right = np.median(button[:, w-90:w-70], axis=1)
    for x in range(96, w-96):
        t = (x-96)/(w-193)
        blend_x = min(1, (x-96)/32, (w-97-x)/32)
        blend_y = np.minimum(1, np.minimum(np.arange(58)/4, np.arange(57,-1,-1)/4))[:,None]
        blend = blend_x*blend_y
        material = left[12:70]*(1-t)+right[12:70]*t
        button[12:70, x] = button[12:70, x]*(1-blend)+material*blend
    mask = Image.new('L', (w*4,h*4))
    points = [(28,5),(w-28,5),(w-5,40),(w-23,77),(24,77),(5,40)]
    ImageDraw.Draw(mask).polygon([(x*4,y*4) for x,y in points], fill=255)
    mask = mask.resize((w,h), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.35))
    asset = Image.fromarray(np.dstack([button, np.array(mask)]).astype('uint8'))
    exports.append(save(name, asset))

(HERE / 'exports.json').write_text(json.dumps({'source':'centered-menu-proposal-v8.png','method':'Local Pillow/NumPy crop, alpha extraction and caption-area material interpolation; no new image generation.','buttonSourceSize':[434,82],'nineSliceInsets':[54,54,12,12],'exports':exports,'exportBytes':sum(x['bytes'] for x in exports)},indent=2)+'\n',encoding='utf-8')
