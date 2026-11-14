"""Local-only scabbard extension. No model, network, installation or production write.

The source RGB is flattened against clothing, so its item matte is an estimate.
The terminal cap is NEVER stretched: its RGB/alpha bytes are translated intact.
Only the middle section is axially resampled to bridge the new cap position.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
CASE_ROOT = ROOT.parent.parent
CONFIG = json.loads((ROOT / 'tip-preservation-config.json').read_text(encoding='utf-8'))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frame():
    base = np.array(CONFIG['base_xy'], dtype=float)
    axis = np.array(CONFIG['legacy_tip_xy'], dtype=float) - base
    axis /= np.linalg.norm(axis)
    normal = np.array([axis[1], -axis[0]])
    return base, axis, normal


def polygon_mask(size, points, supersample=8):
    high = Image.new('L', (size[0] * supersample, size[1] * supersample), 0)
    # Pixel centers use integer coordinates. PIL polygon uses pixel corners at
    # this scale; the half-pixel offset makes numerical coordinates consistent.
    poly = [tuple((np.array(p) + .5) * supersample) for p in points]
    ImageDraw.Draw(high).polygon(poly, fill=255)
    return np.asarray(high.resize(size, Image.Resampling.BOX)).copy()


def translate_integer(array, dx, dy):
    out = np.zeros_like(array)
    h, w = array.shape[:2]
    x0, x1 = max(0, -dx), min(w, w - dx)
    y0, y1 = max(0, -dy), min(h, h - dy)
    out[y0 + dy:y1 + dy, x0 + dx:x1 + dx] = array[y0:y1, x0:x1]
    return out


def sample_rgb(array, x, y):
    return np.stack([ndimage.map_coordinates(array[:, :, c], [y, x],
                     order=1, mode='nearest', prefilter=False)
                     for c in range(3)], axis=-1)


def blend(base, foreground, alpha):
    a = alpha.astype(float)[:, :, None] / 255
    return base * (1 - a) + foreground * a


def make_layers(before):
    """Return arrays and metrics; no disk writes. Caller can recompose layers."""
    original = np.asarray(before.convert('RGB')).copy()
    h, w = original.shape[:2]
    base, axis, normal = frame()
    yy, xx = np.indices((h, w), dtype=float)
    s = (xx - base[0]) * axis[0] + (yy - base[1]) * axis[1]
    n = (xx - base[0]) * normal[0] + (yy - base[1]) * normal[1]
    contour_sn = np.array(CONFIG['source_boundary_sn'], dtype=float)
    contour_xy = base + contour_sn[:, :1] * axis + contour_sn[:, 1:] * normal
    source_mask = polygon_mask((w, h), contour_xy)
    source_tip = base + CONFIG['source_tip_sn'][0] * axis + CONFIG['source_tip_sn'][1] * normal
    wanted_delta = np.array(CONFIG['target_tip_xy']) - source_tip
    dx, dy = np.rint(wanted_delta).astype(int)
    delta = np.array([dx, dy])
    ds, dn = float(delta @ axis), float(delta @ normal)
    s0, s1 = CONFIG['middle_start_s'], CONFIG['tip_lock_start_s']

    # Alpha is clipped at the CUT PLANE, not at the old guessed tip coordinate.
    # The complete rounded terminal contour remains inside the translated cap.
    cap_alpha = source_mask.copy()
    cap_alpha[s < s1] = 0
    cap_rgb = translate_integer(original, dx, dy)
    cap_dst_alpha = translate_integer(cap_alpha, dx, dy)
    cap_rgba_source = np.dstack((np.where(cap_alpha[:, :, None] > 0, original, 0), cap_alpha))
    cap_rgba_target = translate_integer(cap_rgba_source, dx, dy)

    # The inverse map varies only on the middle section. Width has unit scale.
    # A 1.5px overlap below the cut avoids a raster sampling pinhole.
    middle_scale = (s1 + ds - s0) / (s1 - s0)
    source_s = s0 + (s - s0) / middle_scale
    phase = np.clip((source_s - s0) / (s1 - s0), 0, 1)
    source_n = n - dn * phase
    sx = base[0] + source_s * axis[0] + source_n * normal[0]
    sy = base[1] + source_s * axis[1] + source_n * normal[1]
    middle_rgb = sample_rgb(original.astype(float), sx, sy)
    middle_alpha = ndimage.map_coordinates(source_mask.astype(float), [sy, sx],
                         order=1, mode='constant', cval=0, prefilter=False)
    middle_alpha[(source_s < s0) | (source_s > s1 + 1.5)] = 0
    middle_alpha = np.rint(middle_alpha).astype('uint8')
    dst_alpha = np.maximum(middle_alpha, cap_dst_alpha)

    # Restore only original item slivers left uncovered by its new silhouette.
    # Hidden background is unknowable; use adjacent ORIGINAL cloth, not guide,
    # raw model, pants patches or moved background. Keep this separate in output.
    remove_alpha = np.rint(source_mask.astype(float) * (1 - dst_alpha / 255)).astype('uint8')
    min_boundary = contour_sn[:17]
    low = np.interp(s.ravel(), min_boundary[:, 0], min_boundary[:, 1]).reshape(h, w)
    # max-side chain includes a tip turn, so evaluate its monotonically ordered
    # shaft-to-tip points separately for stable neighbour sampling.
    right_chain = np.array([[75,10.5],[168,10.5],[175,10.5],[182,10.5],
                           [189,10.2],[193,9.2],[197,8],[200,6.7],
                           [203,5.2],[205,3.7],[206.2,2.4],[206.5,1.2]])
    high = np.interp(s.ravel(), right_chain[:, 0], right_chain[:, 1]).reshape(h, w)
    nl, nr = low - 2, high + 3
    left_rgb = sample_rgb(original.astype(float), base[0] + s * axis[0] + nl * normal[0],
                          base[1] + s * axis[1] + nl * normal[1])
    right_rgb = sample_rgb(original.astype(float), base[0] + s * axis[0] + nr * normal[0],
                           base[1] + s * axis[1] + nr * normal[1])
    amount = np.clip((n - nl) / np.maximum(nr - nl, 1), 0, 1)[:, :, None]
    cloth_fill = left_rgb * (1 - amount) + right_rgb * amount
    cleaned = blend(original.astype(float), cloth_fill, remove_alpha)
    result = blend(cleaned, middle_rgb, middle_alpha)
    result = blend(result, cap_rgb, cap_dst_alpha)
    result = np.rint(np.clip(result, 0, 255)).astype('uint8')
    changed = np.any(result != original, axis=2)
    allowed = (source_mask > 0) | (dst_alpha > 0)
    foreground_inside = cap_alpha == 255
    translated_inside = translate_integer(foreground_inside, dx, dy)
    exact_tip_rgb = np.array_equal(result[translated_inside], cap_rgb[translated_inside])
    target_tip = source_tip + delta
    visible_tip = source_tip - base
    new_visible_tip = target_tip - base
    rows, cols = np.where(cap_alpha > 0)
    metrics = {
        'method': 'pure local geometry; original cap RGBA integer translation; middle-only axial resampling',
        'status': 'prototype, not installed; local visual acceptance pending',
        'base_xy': base.tolist(), 'legacy_tip_xy': CONFIG['legacy_tip_xy'],
        'source_tip_xy': source_tip.tolist(), 'source_tip_uncertainty_px': CONFIG['source_tip_uncertainty_px'],
        'target_tip_xy_requested': CONFIG['target_tip_xy'], 'target_tip_xy_raster': target_tip.tolist(),
        'target_error_xy_px': (target_tip - np.array(CONFIG['target_tip_xy'])).tolist(),
        'translation_xy_integer': delta.tolist(), 'translation_sn': [ds, dn],
        'tip_transform_singular_values': [1.0, 1.0], 'tip_rotation_degrees': 0,
        'tip_rgba_source_vs_translated_equal': bool(np.array_equal(cap_rgba_target, translate_integer(cap_rgba_source, dx, dy))),
        'cap_opaque_rgb_exact_original': bool(exact_tip_rgb),
        'tip_source_alpha_nonzero_pixels': int((cap_alpha > 0).sum()),
        'tip_target_alpha_nonzero_pixels': int((cap_dst_alpha > 0).sum()),
        'tip_source_bbox_xyxy': [int(cols.min()), int(rows.min()), int(cols.max()+1), int(rows.max()+1)],
        'source_tip_pixels_at_or_below_y382': int(((cap_alpha > 0) & (yy >= 382)).sum()),
        'source_background_gray_pixels_inside_cap': int(((cap_alpha > 0) & (np.max(abs(original.astype(float)-228), axis=2)<3)).sum()),
        'tip_source_rgba_sha256_raw': hashlib.sha256(cap_rgba_source.tobytes()).hexdigest(),
        'middle_start_s': s0, 'tip_lock_start_s': s1, 'middle_axial_scale_only': middle_scale,
        'visible_length_ratio_from_actual_tip': float(np.linalg.norm(new_visible_tip)/np.linalg.norm(visible_tip)),
        'changed_pixels': int(changed.sum()), 'changed_outside_item_union': int((changed & ~allowed).sum()),
        'original_pixels_above_y250_equal': bool(np.array_equal(original[:250], result[:250])),
        'exposed_old_item_fill_pixels': int((remove_alpha > 0).sum()),
        'cap_alpha_byte_sum_source': int(cap_alpha.sum()), 'cap_alpha_byte_sum_target': int(cap_dst_alpha.sum()),
        'source_tip_core_rgb_probe_xy': [199,380], 'source_tip_core_rgb_probe': original[380,199].tolist(),
        'quality_boundaries': CONFIG['limits'],
    }
    return {
        'candidate_rgb': result, 'source_sword_alpha': source_mask,
        'source_tip_rgba': cap_rgba_source, 'target_tip_rgba': cap_rgba_target,
        'target_sword_alpha': dst_alpha, 'middle_alpha': middle_alpha,
        'target_tip_alpha': cap_dst_alpha, 'old_tip_cleanup_alpha': remove_alpha,
        'change_mask': (changed * 255).astype('uint8'),
    }, metrics


def build_candidate(before: Image.Image):
    """Caller-facing API: returns RGB candidate and JSON-safe geometry metrics."""
    layers, metrics = make_layers(before)
    return Image.fromarray(layers['candidate_rgb']), metrics


def main():
    inputs = {
        'before': CASE_ROOT / 'guides/sword-back/before.png',
        'guide': CASE_ROOT / 'guides/sword-back/guide.png',
        'v1_candidate': CASE_ROOT / 'results/sword-back/constrained-candidate.png',
    }
    before = Image.open(inputs['before']).convert('RGB')
    layers, metrics = make_layers(before)
    names = {
        'candidate_rgb': 'tip-preserved-candidate.png',
        'source_sword_alpha': 'source-sword-alpha.png',
        'source_tip_rgba': 'source-tip-rgba.png',
        'target_tip_rgba': 'translated-tip-rgba.png',
        'target_sword_alpha': 'target-sword-alpha.png',
        'middle_alpha': 'middle-alpha.png',
        'target_tip_alpha': 'translated-tip-alpha.png',
        'old_tip_cleanup_alpha': 'old-tip-cleanup-alpha.png',
        'change_mask': 'change-mask.png',
    }
    for key, filename in names.items():
        Image.fromarray(layers[key]).save(ROOT / filename)
    original = np.asarray(before)
    # Compare prior stages numerically; do not upload or render any source image.
    prior = {}
    base, axis, normal = frame()
    source_tip = np.array(metrics['source_tip_xy'])
    requested = np.array(CONFIG['target_tip_xy'])
    for name in ('guide', 'v1_candidate'):
        a = np.asarray(Image.open(inputs[name]).convert('RGB'))
        prior[name] = {
            'changed_pixels_total': int(np.any(a != original, axis=2).sum()),
            'cap_terminal_probe_xy': [199,380],
            'terminal_original_rgb': original[380,199].tolist(),
            'terminal_rgb': a[380,199].tolist(),
            'tip_from_legacy_affine_xy': (base + 1.4*(source_tip-base)).tolist(),
            'legacy_affine_tip_misplacement_from_requested': (base + 1.4*(source_tip-base) - requested).tolist(),
        }
    metrics['prior_stage_numeric_audit'] = prior
    # Reproducible numeric evidence for the cap frontier. These are local RGB
    # samples, never a rendered/uploaded image. n is normal to the old axis.
    profiles = ['s,n,x,y,r,g,b,g_minus_b,luma_mean']
    for position_s in range(164, 211):
        for position_n in range(-5, 16):
            point = base + position_s * axis + position_n * normal
            p = sample_rgb(original.astype(float), np.array([[point[0]]]), np.array([[point[1]]]))[0,0]
            profiles.append(','.join(str(round(float(value),4)) for value in
                         [position_s,position_n,*point,*p,p[1]-p[2],p.mean()]))
    (ROOT/'source-tip-line-profiles.csv').write_text('\n'.join(profiles)+'\n', encoding='utf-8')
    metrics['boundary_evidence'] = {
        'line_profiles_csv': 'source-tip-line-profiles.csv',
        's_axis_unit': axis.tolist(), 'n_axis_unit': normal.tolist(),
        'gb_means_g_minus_b': 'Gold/copper cap has positive G-B; burgundy cloth near the cap has near-zero G-B. The cap chroma frontier ends around s205..207, while pants colour starts contaminating the sampled signal after s207.',
        'source_gold_probe_199_380_G_minus_B': int(original[380,199,1])-int(original[380,199,2]),
        'source_next_row_probe_199_381_G_minus_B': int(original[381,199,1])-int(original[381,199,2]),
        'not_a_proof': 'A flattened RGB image does not uniquely identify a material matte. Pixel profiles constrain the cap endpoint, but the boundary is a documented local estimate and needs visual acceptance.',
    }
    metrics['input_sha256'] = {k: {'path': str(v.resolve()), 'sha256': sha256(v)} for k,v in inputs.items()}
    metrics['output_sha256'] = {name: sha256(ROOT/name) for name in names.values()}
    (ROOT / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    assert metrics['cap_opaque_rgb_exact_original']
    assert metrics['changed_outside_item_union'] == 0
    assert metrics['original_pixels_above_y250_equal']
    assert metrics['cap_alpha_byte_sum_source'] == metrics['cap_alpha_byte_sum_target']


if __name__ == '__main__':
    main()
