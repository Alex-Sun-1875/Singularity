"""Trace the approved lightning spine from its actual pixels with SciPy."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter1d, map_coordinates
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / 'four-class-vfx-redesign-v1/references/user-selected-first-board-v5.png'
im = Image.open(SOURCE).convert('RGB')
rect = (870, 656, 1150, 830)
roi = im.crop(rect)
rgb = np.asarray(roi, dtype=float)
start = np.array([901., 806.]) - rect[:2]
end = np.array([1125., 688.]) - rect[:2]
axis = end - start
length = np.linalg.norm(axis)
direction = axis / length
normal = np.array([-direction[1], direction[0]])
yy, xx = np.indices(rgb.shape[:2])
q = np.stack([xx - start[0], yy - start[1]], axis=-1)
t = q @ direction / length
side = q @ normal / length
core = (rgb[..., 0] > 210) & (rgb[..., 1] > 220) & (rgb[..., 2] > 245)
distance = distance_transform_edt(core)
domain = (t > -.035) & (t < 1.035) & (abs(side) < .13)
cost = np.where(core, 1 + 5 / (1 + distance), 24 + 45 * (1 - rgb[..., 0] / 255))
def find_route(cost, domain, a, b):
    h, w = cost.shape
    ids = np.full((h, w), -1, dtype=int)
    ids[domain] = np.arange(domain.sum())
    rows, cols, values = [], [], []
    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        sy = slice(max(0, -dy), min(h, h - dy))
        sx = slice(max(0, -dx), min(w, w - dx))
        ty = slice(max(0, dy), min(h, h + dy))
        tx = slice(max(0, dx), min(w, w + dx))
        p, q = ids[sy, sx], ids[ty, tx]
        valid = (p >= 0) & (q >= 0)
        weights = (cost[sy, sx][valid] + cost[ty, tx][valid]) * .5 * np.hypot(dx, dy)
        rows.extend([p[valid], q[valid]])
        cols.extend([q[valid], p[valid]])
        values.extend([weights, weights])
    graph = coo_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(cols))),
                       shape=(domain.sum(), domain.sum())).tocsr()
    source, target = ids[round(a[1]), round(a[0])], ids[round(b[1]), round(b[0])]
    _, predecessors = dijkstra(graph, indices=source, return_predecessors=True)
    route = [target]
    while route[-1] != source:
        previous = int(predecessors[route[-1]])
        assert previous >= 0, 'Reference path is disconnected inside its trace corridor'
        route.append(previous)
    return np.stack([xx[domain], yy[domain]], axis=-1)[route[::-1]]


coordinates = find_route(cost, domain, start, end)
relative = coordinates - start
progress = relative @ direction / length
offset = relative @ normal / length
order = np.argsort(progress)
sample_t = np.linspace(0, 1, 65)
sample_side = np.interp(sample_t, progress[order], offset[order])
sample_side = gaussian_filter1d(sample_side, .65)
sample_side -= sample_side[0] * (1 - sample_t) + sample_side[-1] * sample_t
widths = 2 * distance[coordinates[:, 1], coordinates[:, 0]]
sample_width = np.interp(sample_t, progress[order], widths[order])
median_width = float(np.median(sample_width[5:-5]))
sample_width = gaussian_filter1d(sample_width, .75) / median_width
sample_width = np.clip(sample_width, .52, 1.6)
data = {
    'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
    'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'method': 'SciPy shortest path weighted toward the medial axis of the approved white core',
    'sourceEndpoints': [[901, 806], [1125, 688]],
    'sourceCrop': list(rect),
    'referenceLengthPixels': float(length),
    'medianCoreWidthPixels': median_width,
    'spine': [[round(float(t), 6), round(float(s), 6)] for t, s in zip(sample_t, sample_side)],
    'widths': [round(float(x), 5) for x in sample_width],
}

# Waypoints select the two approved branches; the weighted route follows their
# blue pixels between those guides, without inventing another branch silhouette.
branch_guides = [
    [[976, 737], [990, 704], [1014, 685], [1036, 686], [1054, 673], [1070, 670], [1087, 678], [1105, 687], [1124, 688]],
    [[1006, 734], [1024, 751], [1049, 763], [1067, 763], [1087, 775], [1098, 794], [1114, 806]],
]
branches, branch_pixels = [], []
pixel_grid = np.stack([xx, yy], axis=-1)
blue_signal = np.maximum(rgb[..., 2] - rgb[..., 0] * .55 - rgb[..., 1] * .45,
                          np.clip((rgb[..., 0] - 190) * .5, 0, 35))
branch_cost = 1 + 18 * (1 - np.clip(blue_signal / 100, 0, 1)) ** 2
for guides in branch_guides:
    guides = np.array(guides, dtype=float) - rect[:2]
    proximity = np.full(xx.shape, np.inf)
    for a, b in zip(guides[:-1], guides[1:]):
        delta = b - a
        along = np.clip(((pixel_grid - a) @ delta) / (delta @ delta), 0, 1)
        proximity = np.minimum(proximity, np.linalg.norm(pixel_grid - a - along[..., None] * delta, axis=-1))
    path = find_route(branch_cost + proximity * .05, proximity < 9, guides[0], guides[-1])
    branch_pixels.append(path)
    arc_length = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=-1))])
    samples = np.linspace(0, arc_length[-1], 49)
    points = np.stack([np.interp(samples, arc_length, path[:, i]) for i in range(2)], axis=-1)
    relative = points - start
    local = np.stack([relative @ direction / length, relative @ normal / length], axis=-1)
    # Snap each actual junction onto the extracted main core to keep it connected
    # after remapping the approved drawing into world space.
    local[0, 1] = np.interp(local[0, 0], sample_t, sample_side)
    if len(branches) == 0:
        local[-1, 1] = np.interp(local[-1, 0], sample_t, sample_side)
    branches.append([[round(float(x), 6), round(float(y), 6)] for x, y in local])
data['branches'] = branches
data['branchGuides'] = [[[int(x), int(y)] for x, y in guides] for guides in branch_guides]

# Rectify the actual approved electric light into a ribbon. Estimate the stone
# background away from its core, then preserve the remaining emitted RGB.
u = np.linspace(0, 1, 1024)
spine_side = np.interp(u, sample_t, sample_side)
center = np.array([901., 806.])[None, :] + u[:, None] * axis + spine_side[:, None] * length * normal
width = np.interp(u, sample_t, sample_width) * median_width
cross = np.linspace(-3, 3, 192)
positions = center[None, :, :] + cross[:, None, None] * width[None, :, None] * normal
full = np.asarray(im, dtype=float)
sampled = np.stack([map_coordinates(full[..., c], [positions[..., 1], positions[..., 0]], order=1, mode='nearest') for c in range(3)], axis=-1)
background_offsets = np.concatenate([np.linspace(-58, -36, 12), np.linspace(36, 58, 12)])
background_positions = center[None, :, :] + background_offsets[:, None, None] * normal
background = np.stack([map_coordinates(full[..., c], [background_positions[..., 1], background_positions[..., 0]], order=1, mode='nearest') for c in range(3)], axis=-1)
background = np.median(background, axis=0)
background = gaussian_filter1d(background, 7, axis=0)
emission = np.maximum(0, sampled - background[None, :, :])
white_hot = sampled.min(axis=-1) > 233
emission[white_hot] = np.max(emission[white_hot], axis=-1)[:, None]
is_light = (sampled[..., 2] > sampled[..., 0] + 12) | ((sampled.min(axis=-1) > 210) & (sampled[..., 2] > 242))
emission *= gaussian_filter1d(is_light.astype(float), .6, axis=0)[..., None]
# A zero-energy margin guarantees a transparent soft edge on the 3D ribbon.
margin = np.minimum(1, np.minimum(np.arange(192), np.arange(191, -1, -1)) / 12)
emission *= margin[:, None, None]
rgba = np.dstack([np.clip(emission, 0, 255), np.full(emission.shape[:2], 255)]).astype(np.uint8)
Image.fromarray(rgba).save(HERE / 'approved-thunder-strip.png')
data['ribbonTexture'] = {'file': 'approved-thunder-strip.png', 'size': [1024, 192],
                         'processing': 'Bilinear rectification along approved core, local background subtraction, soft zero-energy margin',
                         'sha256': hashlib.sha256((HERE / 'approved-thunder-strip.png').read_bytes()).hexdigest()}
(HERE / 'reference-profile.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')

panel = im.crop((774, 560, 1518, 958))
draw = ImageDraw.Draw(panel)
line = coordinates + np.array(rect[:2]) - np.array([774, 560])
draw.line([tuple(p) for p in line[::2]], fill=(255, 205, 96), width=2)
for path in branch_pixels:
    local = path + np.array(rect[:2]) - np.array([774, 560])
    draw.line([tuple(p) for p in local], fill=(113, 250, 194), width=1)
for point in [np.array([901, 806]), np.array([1125, 688])]:
    x, y = point - np.array([774, 560])
    draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 205, 96), width=2)
(HERE / 'reference-trace.png').parent.mkdir(exist_ok=True)
panel.save(HERE / 'reference-trace.png')
print(json.dumps({'samples': len(sample_t), 'lengthPixels': float(length),
                  'medianCorePixels': median_width, 'maximumSidePixels': float(abs(sample_side).max() * length)}))
