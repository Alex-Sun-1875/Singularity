"""Copy approved imagegen PNGs unchanged and read alpha/anchor metadata only."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import shutil
import statistics
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[3]
RUNTIME = ROOT / 'src/cocos/assets/resources/flat2d/characters'
IDENTITIES = ['raider', 'raider-archer', 'raider-shield', 'captain']
FRAME_W, FRAME_H = 384, 256

def contact_x(cell, bound, fallen=False):
    """Read the two local sole envelopes, not only the lower/front foot."""
    left, top, right, bottom = bound
    height = bottom - top
    support_top = max(top, bottom - max(18, round(height * .12)))
    envelope = {x: max((y for y in range(support_top, bottom) if cell.getpixel((x, y)) >= 128), default=-1)
                for x in range(left, right)}
    runs, current = [], []
    for x in range(left, right):
        if envelope[x] >= support_top:
            current.append(x)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    supports = []
    for run in runs:
        peak = max(envelope[x] for x in run)
        sole = [x for x in run if envelope[x] >= peak - 7]
        if len(sole) >= 5:
            supports.append({'center': round((min(sole) + max(sole)) / 2),
                             'peak': peak, 'range': [min(sole), max(sole)]})
    supports.sort(key=lambda part: (-part['peak'], -(part['range'][1] - part['range'][0])))
    if fallen:
        # Kneeling/fallen figures do not have a standing two-foot base. Read
        # their broad lower-body support span, trimming thin weapon tips.
        pixels = sorted(x for y in range(max(top, bottom - round(height * .55)), bottom)
                        for x in range(left, right) if cell.getpixel((x, y)) >= 128)
        if pixels:
            low, high = pixels[round((len(pixels) - 1) * .05)], pixels[round((len(pixels) - 1) * .95)]
            return round((low + high) / 2), {'method': 'trimmed broad collapse support span', 'range': [low, high]}
    selected = supports[:2]
    center = round(statistics.mean(part['center'] for part in selected)) if selected else round((left + right) / 2)
    return center, {'method': 'two lowest sole-envelope midpoints', 'supports': selected}

def analyze(path, damage=False):
    image = Image.open(path)
    if image.size != (FRAME_W * 4, FRAME_H * 4) or image.mode != 'RGBA':
        raise ValueError(f'{path.name}: expected unchanged RGBA 1536x1024, got {image.mode} {image.size}')
    alpha = image.getchannel('A')
    if alpha.getextrema()[0] != 0:
        raise ValueError(f'{path.name}: no truly transparent background')
    bounds, origins, edges, contact_support = [], [], [], []
    for index in range(16):
        x, y = index % 4 * FRAME_W, index // 4 * FRAME_H
        cell = alpha.crop((x, y, x + FRAME_W, y + FRAME_H))
        mask = cell.point(lambda value: 255 if value >= 24 else 0)
        bound = mask.getbbox()
        if bound is None:
            raise ValueError(f'{path.name}: empty frame {index}')
        left, top, right, bottom = bound
        if left == 0 or top == 0 or right == FRAME_W or bottom == FRAME_H:
            edges.append(index)
        origin_x, support = contact_x(cell, bound, damage and index % 4 >= 2)
        bounds.append(list(bound))
        origins.append([origin_x, bottom])
        contact_support.append(support)
    if edges:
        raise ValueError(f'{path.name}: opaque pixels touch cell edges {edges}; imagegen correction required')
    histogram = alpha.histogram()
    return {'imageSize': list(image.size), 'frameCount': 16, 'alphaBounds': bounds,
            'perFrameOrigins': origins, 'contactSupport': contact_support,
            'transparentFraction': sum(histogram[:8]) / sum(histogram),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def package(identity):
    selected = {}
    for action in ['walk', 'attack', 'hurt']:
        second = SOURCE / f'{identity}-{action}-fitted-v2.png'
        fitted = SOURCE / f'{identity}-{action}-fitted.png'
        selected[action] = second if second.is_file() else fitted if fitted.is_file() else SOURCE / f'{identity}-{action}.png'
        # Both edited captain damage variants introduced background alpha.
        # Keep the original clean, complete drawing and normalize its display
        # scale through the presentation-only action metadata instead.
        if identity == 'captain' and action == 'hurt':
            selected[action] = SOURCE / 'captain-hurt.png'
    reports = {action: analyze(path, action == 'hurt') for action, path in selected.items()}
    standing = reports['walk']['alphaBounds']
    median_height = statistics.median(standing[index][3] - standing[index][1] for index in [0, 4, 8, 12])
    attack = 'attack_bow' if identity == 'raider-archer' else 'attack_sword'
    world_height = 1.9 if identity == 'captain' else 1.72
    def action(image, indices, fps, loop):
        report = reports['walk' if image == 'atlas.png' else 'attack' if image == 'attack.png' else 'hurt']
        # Recovery frames avoid counting raised swords/bow tips as body height.
        sample_columns = [3, 7, 11, 15] if image == 'attack.png' else [0, 4, 8, 12]
        height = statistics.median(report['alphaBounds'][i][3] - report['alphaBounds'][i][1] for i in sample_columns)
        result = {'image': image, 'frames': len(indices), 'frameIndices': indices, 'columns': 4,
                  'fps': fps, 'loop': loop, 'perFrameOrigins': report['perFrameOrigins'],
                  'alphaBounds': report['alphaBounds'], 'worldUnitsPerPixel': world_height / height}
        if image == 'attack.png':
            result['phaseStarts'] = [0, .35, .75, .875] if identity == 'raider-archer' else [0, .18, .28, .6]
        return result
    manifest = {'revision': 'concept-image-2d-enemy-motion-v3-ground-anchors',
                'sourceDesign': 'assets/concepts/captain-detail-reference-v2.png' if identity == 'captain' else 'assets/concepts/raider-detail-reference-v2.png',
                'loaded3DModel': False, 'image': 'atlas.png', 'columns': 4,
                'frameWidth': FRAME_W, 'frameHeight': FRAME_H, 'directions': ['down', 'right', 'up', 'left'],
                'origin': reports['walk']['perFrameOrigins'][0],
                'perFrameOrigins': reports['walk']['perFrameOrigins'], 'alphaBounds': reports['walk']['alphaBounds'],
                'camera': {'worldUnitsPerPixel': world_height / median_height},
                'actions': {'idle': action('atlas.png', [0], 1, True),
                            'walk': action('atlas.png', [1, 2, 3, 2], 7, True),
                            attack: action('attack.png', [0, 1, 2, 3], 9, False),
                            'hit': action('hurt.png', [0], 8, False),
                            'death': action('hurt.png', [1, 2, 3], 4, False)},
                'sourceArtifacts': {key: str(value.relative_to(ROOT)).replace('\\', '/') for key, value in selected.items()},
                'limitations': ['Four drawn directions and low-frame animation; no generated intermediate frames.',
                                'Ground anchors are read from visible sole/contact alpha pixels; runtime foot sliding still needs play review.']}
    output = RUNTIME / identity
    output.mkdir(parents=True, exist_ok=True)
    for key, filename in [('walk', 'atlas.png'), ('attack', 'attack.png'), ('hurt', 'hurt.png')]:
        shutil.copy2(selected[key], output / filename)
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (SOURCE / f'{identity}-atlas-metadata.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    print(json.dumps({'id': identity, 'actions': list(manifest['actions']), 'worldUnitsPerPixel': manifest['camera']['worldUnitsPerPixel'], 'output': str(output)}))

if __name__ == '__main__':
    for identity in sys.argv[1:] or IDENTITIES:
        package(identity)
