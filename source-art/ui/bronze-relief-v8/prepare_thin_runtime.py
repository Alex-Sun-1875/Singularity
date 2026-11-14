"""Use Pillow mesh resampling to narrow the existing rendered metal rims."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
OUT = PROJECT / 'src/cocos/assets/resources/ui/quiet-bronze'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def narrow(source, target, inner_radius):
    image = Image.open(source).convert('RGBA')
    center = 255.5
    source_inner, outer = 208.0, 256.0

    def inverse(x, y):
        dx, dy = x-center, y-center
        radius = math.hypot(dx, dy)
        if radius < 1e-6:
            return center, center
        mapped = (radius*source_inner/inner_radius if radius <= inner_radius else
                  source_inner+(radius-inner_radius)*(outer-source_inner)/(outer-inner_radius))
        return center+dx*mapped/radius, center+dy*mapped/radius

    # Pillow owns interpolation. Fine inverse-mapped patches keep the original
    # cast bevel/texture while compressing its radial width and enlarging the well.
    mesh = []
    for y in range(0, 512, 8):
        for x in range(0, 512, 8):
            quad = [inverse(x, y), inverse(x, y+8), inverse(x+8, y+8), inverse(x+8, y)]
            mesh.append(((x, y, x+8, y+8), tuple(value for point in quad for value in point)))
    result = image.transform((512, 512), Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)
    result.save(target)
    return result, {'asset': target.relative_to(PROJECT).as_posix(),
                    'source': source.relative_to(PROJECT).as_posix(),
                    'sha256': digest(target), 'sourceInnerRadius': source_inner,
                    'targetInnerRadius': inner_radius, 'outerRadius': outer}


frame, frame_record = narrow(OUT/'compass-frame-v8.png', OUT/'compass-frame-v10.png', 236)
_, button_record = narrow(OUT/'button-medallion-v8.png', OUT/'button-medallion-v10.png', 238)
rail = frame.copy()
alpha = rail.getchannel('A')
mask = Image.new('L', (512, 512))
values = []
for y in range(512):
    for x in range(512):
        angle = math.degrees(math.atan2(255.5-y, x-255.5)) % 360
        fade = max(0, min(1, (angle-220)/4, (320-angle)/4)) if 220 <= angle <= 320 else 0
        values.append(round(alpha.getpixel((x, y))*fade))
mask.putdata(values)
rail.putalpha(mask)
rail_path = OUT/'compass-tool-rail-v10.png'
rail.save(rail_path)
record = {
    'version': 'thin-ornamental-rim-v10', 'date': '2026-11-08',
    'userRevision': 'Border too thick: narrow the metal while keeping brighter material and ornamental curls.',
    'generator': 'No additional generation; deterministic Pillow mesh remap of the retained cloud-generated bright bronze sprites.',
    'generationAndPrompts': 'source-art/ui/bronze-relief-v8/provenance.json',
    'assets': [frame_record, button_record, {'asset': rail_path.relative_to(PROJECT).as_posix(), 'sha256': digest(rail_path)}],
    'nominalMetalWidth': {'mapAt240': 9.375, 'buttonAt86': 3.0234375},
    'artReview': {'runtime': 'Pending desktop/mobile screenshot inspection.', 'userAcceptance': 'Not recorded.'},
}
(ROOT/'thin-rim-provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record['nominalMetalWidth']))
