"""Extract the approved v29 impact's fire, retaining its connected outline.

Historical experiment retained for reproducibility. Its two output PNGs are
NOT loaded by the current FireImpactEffects, which shares the clean approved
field/lance atlases and contact fan; see README.md and runtime-sources.json.
Deterministic Pillow/NumPy matting only, not an in-game animation claim.
"""
from pathlib import Path
import hashlib
import json
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png'
PRODUCTION = ROOT / 'src/cocos/assets/resources/vfx/production'
SOURCE_META = PRODUCTION / 'fire-ground-jets-v27.png.meta'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(value):
    value = np.clip(value, 0, 1)
    return value * value * (3 - 2 * value)


def blur(channel, radius):
    return np.asarray(Image.fromarray(np.uint8(np.clip(channel, 0, 1) * 255)).filter(
        ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255


def matte(image):
    rgb = np.asarray(image.convert('RGB'), dtype=np.float32) / 255
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Neutral stone grain is correlated with the source's blue channel. Fit
    # that actual local correlation before isolating luminous warm detail;
    # simple saturation-keying retained a thick baked orange floor cloud.
    clean = (red - blue < .115) & (red < .55)
    if np.count_nonzero(clean) >= 16:
        rfit = np.polyfit(blue[clean], red[clean], 1)
        gfit = np.polyfit(blue[clean], green[clean], 1)
        rfit[0] = np.clip(rfit[0], .65, 1.5)
        gfit[0] = np.clip(gfit[0], .65, 1.4)
    else:
        rfit, gfit = np.array([1.12, .02]), np.array([1.05, .01])
    contrast = red - rfit[0] * blue - rfit[1]
    optical_blue = np.full_like(red, .16)
    for _ in range(3):
        body = np.clip(contrast / np.maximum(1-rfit[0]*optical_blue-rfit[1], .2), 0, .95)
        optical_green = (green-gfit[0]*blue-gfit[1]) / np.maximum(body, 1e-5) + gfit[0]*optical_blue+gfit[1]
        optical_blue = np.clip(.045+.59*(optical_green-.37), .035, .34)
    body *= smooth((contrast-.015)/.13)
    # Positive ridges at two small scales retain the approved narrow bright
    # filaments. Low-frequency diffuse fire/floor lighting contributes only
    # 2.5%, avoiding a solid orange cloud and dark baked-stone silhouettes.
    fine = np.maximum(body-blur(body, 1.15), 0)
    medium = np.maximum(body-blur(body, 3.0), 0)
    ridges = np.clip((fine*.85+medium*.70)/.16, 0, 1)
    luminous = smooth((red-.40)/.40) * smooth((green-blue-.075)/.21)
    alpha = np.clip(luminous*(body*ridges*.88 + body**3*.025), 0, .78)
    colour = np.stack([np.ones_like(red), np.clip(optical_green, .37, .80),
                       np.clip(optical_blue, .035, .34)], axis=-1)
    return np.dstack([colour, alpha])


def save(name, pixels):
    path = PRODUCTION / (name + '.png')
    Image.fromarray(np.uint8(np.clip(pixels, 0, 1) * 255), 'RGBA').save(path, optimize=True)
    meta = json.loads(SOURCE_META.read_text(encoding='utf-8'))
    identity = str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity:vfx/production/' + path.name))
    meta['uuid'] = identity
    meta['subMetas']['6c48a']['uuid'] = identity + '@6c48a'
    meta['subMetas']['6c48a']['displayName'] = name
    meta['subMetas']['6c48a']['userData']['imageUuidOrDatabaseUri'] = identity
    meta['userData']['redirect'] = identity + '@6c48a'
    meta['userData']['hasAlpha'] = True
    path.with_suffix('.png.meta').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(path),
            'size': list(Image.open(path).size), 'bytes': path.stat().st_size}


def main():
    source = Image.open(SOURCE).convert('RGB')
    # The lower portion contains the one connected radial impact; the tall
    # central curls are extracted separately for a handful of outward ribbons.
    flow_crop = (903, 791, 1303, 983)
    wisp_crop = (1053, 752, 1169, 874)
    flow = matte(source.crop(flow_crop))
    h, w = flow.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    radial = np.sqrt(((x - w * .5) / (w * .5)) ** 2 +
                     ((y - h * .5) / (h * .5)) ** 2)
    flow[..., 3] *= 1 - smooth((radial - .77) / .25)
    # Eliminate the only foreground soldier fragment at the upper-left edge.
    flow[..., 3] *= smooth((x + y * .65 - 33) / 20)
    flow_image = Image.fromarray(np.uint8(flow * 255), 'RGBA').resize((512, 512), Image.Resampling.LANCZOS)
    flow = np.asarray(flow_image, dtype=np.float32) / 255

    wisp = matte(source.crop(wisp_crop))
    h, w = wisp.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    # Fully feather edges and keep the plume foot at v=.94. The extracted
    # centre is broad soft filaments, never a forced electric-white line.
    envelope = smooth(x / 12) * smooth((w - 1 - x) / 12)
    envelope *= smooth(y / 8) * smooth((h - 1 - y) / 5)
    wisp[..., 3] *= envelope
    wisp_image = Image.fromarray(np.uint8(wisp * 255), 'RGBA').resize((192, 256), Image.Resampling.LANCZOS)
    wisp = np.asarray(wisp_image, dtype=np.float32) / 255
    outputs = [save('fire-impact-flow-v30', flow), save('fire-impact-wisp-v30', wisp)]

    board = Image.new('RGB', (980, 400), '#272e2b')
    board.paste(source.crop((915, 735, 1360, 1010)).resize((445, 275)), (10, 52))
    for pixels, box in [(flow, (470, 54, 744, 328)), (wisp, (766, 54, 958, 310))]:
        rgba = Image.fromarray(np.uint8(pixels * 255), 'RGBA').resize((box[2] - box[0], box[3] - box[1]))
        board.paste(rgba, box[:2], rgba)
    draw = ImageDraw.Draw(board)
    draw.text((12, 18), 'Approved v29 impact / connected radial flow / curved filament matte', fill='#efd6b3')
    draw.text((12, 360), 'Texture extraction only. Runtime geometry, flow and fading require actual Cocos capture.', fill='#d2c5b0')
    board.save(HERE / 'texture-sample.png', optimize=True)
    provenance = {'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'), 'sourceSha256': sha(SOURCE),
                  'method': 'deterministic neutral-channel floor regression, positive small-scale filament ridges, 2.5% low-frequency body, feather and ellipse-to-circle resampling; no image generation',
                  'crops': {'flow': flow_crop, 'wisp': wisp_crop},
                  'textureConvention': 'straight RGBA, display colour; shader outputs premultiplied RGBA',
                  'outputs': outputs, 'review': {'sample': 'pending visual inspection', 'actualCocos': 'pending', 'userArtAcceptance': 'pending'}}
    (HERE / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(outputs))


if __name__ == '__main__':
    main()
