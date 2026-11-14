"""Local RGBA adapter around the reviewed pure-pixel scabbard module.

No model/server/network use. Only this directory is writable. Model output may
touch the explicitly saved seam mask; final hand/cap locks run afterwards.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import hashlib
import json
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ART = HERE.parent.parent
SOURCE = ART / 'local-qwen21-turbo-pilot-v1/originals-512x768/standing-back-p0-rgba.png'
OLD = ART / 'local-klein-consistency-v1/revision-v2/sword-audit'
HAND_BOXES = [(146, 368, 187, 437), (323, 368, 364, 437)]
SHIFT = (-31, 65)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_legacy():
    spec = importlib.util.spec_from_file_location('local_original_tip_geometry', OLD / 'preserve_tip.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rgba_mix(base, foreground, coverage):
    """Premultiplied interpolation; zero-alpha RGB never bleeds into an edge."""
    w = np.asarray(coverage, float)[..., None] / 255
    ba = base[..., 3:4].astype(float) / 255
    fa = foreground[..., 3:4].astype(float) / 255
    alpha = ba * (1-w) + fa * w
    premul = base[..., :3] * ba * (1-w) + foreground[..., :3] * fa * w
    rgb = np.divide(premul, alpha, out=np.zeros_like(premul), where=alpha > 0)
    result = np.dstack((rgb, alpha[..., 0] * 255))
    result = np.rint(np.clip(result, 0, 255)).astype('uint8')
    result[np.asarray(coverage) == 0] = base[np.asarray(coverage) == 0]
    return result


def sample_rgba(module, source, x, y):
    alpha = source[..., 3].astype(float) / 255
    sa = ndimage.map_coordinates(alpha, [y, x], order=1, mode='constant', cval=0, prefilter=False)
    premul = module.sample_rgb(source[..., :3].astype(float) * alpha[..., None], x, y)
    rgb = np.divide(premul, sa[..., None], out=np.zeros_like(premul), where=sa[..., None] > 1e-8)
    return np.rint(np.clip(np.dstack((rgb, sa*255)), 0, 255)).astype('uint8')


def hand_restore(original, candidate, sword_layer, coverage):
    """Original RGBA hand in front; transparent finger gaps admit the sword.

    No rectangular RGB paste, no gray-matte inverse. Interior pixels >=230
    retain the original bytes. The soft original hand edge is source-over the
    sword layer, using original alpha rather than a skin-colour heuristic.
    """
    out = candidate.copy()
    hand = np.zeros(original.shape[:2], np.uint8)
    for x0, y0, x1, y1 in HAND_BOXES:
        hand[y0:y1, x0:x1] = original[y0:y1, x0:x1, 3]
        active = coverage[y0:y1, x0:x1] > 0
        oa = original[y0:y1, x0:x1, 3:4].astype(float)/255
        sa = sword_layer[y0:y1, x0:x1, 3:4].astype(float)/255
        sa *= coverage[y0:y1, x0:x1, None].astype(float)/255
        oa_rgb = original[y0:y1, x0:x1, :3].astype(float)
        sa_rgb = sword_layer[y0:y1, x0:x1, :3].astype(float)
        alpha = oa + sa*(1-oa)
        premul = oa_rgb*oa + sa_rgb*sa*(1-oa)
        rgb = np.divide(premul, alpha, out=np.zeros_like(premul), where=alpha>0)
        mix = np.rint(np.clip(np.dstack((rgb, alpha[..., 0]*255)), 0, 255)).astype('uint8')
        roi = out[y0:y1, x0:x1]
        roi[active] = mix[active]
        core = original[y0:y1, x0:x1, 3] >= 230
        roi[core] = original[y0:y1, x0:x1][core]
    return out, hand


def geometry():
    module = load_legacy()
    original = np.array(Image.open(SOURCE).convert('RGBA'))
    # This is an actual call into the old implementation, not a reimplementation.
    old_layers, metrics = module.make_layers(Image.fromarray(original))
    base, axis, normal = module.frame()
    yy, xx = np.indices(original.shape[:2], dtype=float)
    s = (xx-base[0])*axis[0] + (yy-base[1])*axis[1]
    n = (xx-base[0])*normal[0] + (yy-base[1])*normal[1]
    dx, dy = metrics['translation_xy_integer']
    assert (dx, dy) == SHIFT
    ds, dn = metrics['translation_sn']
    s0, s1 = module.CONFIG['middle_start_s'], module.CONFIG['tip_lock_start_s']
    scale = metrics['middle_axial_scale_only']
    source_s = s0 + (s-s0)/scale
    phase = np.clip((source_s-s0)/(s1-s0), 0, 1)
    source_n = n-dn*phase
    sx = base[0]+source_s*axis[0]+source_n*normal[0]
    sy = base[1]+source_s*axis[1]+source_n*normal[1]
    middle = sample_rgba(module, original, sx, sy)
    cap = module.translate_integer(original, dx, dy)
    # The old source RGB was flattened on 228 gray. Here both middle and cap
    # sample the true source RGBA; geometry coverage remains the old audited matte.
    middle_mask = old_layers['middle_alpha']
    cap_mask = old_layers['target_tip_alpha']
    coverage = np.maximum(middle_mask, cap_mask)
    source_mask = old_layers['source_sword_alpha']
    cleanup_mask = old_layers['old_tip_cleanup_alpha']

    contour = np.array(module.CONFIG['source_boundary_sn'], float)
    low = np.interp(s.ravel(), contour[:17, 0], contour[:17, 1]).reshape(s.shape)
    right = np.array([[75,10.5],[168,10.5],[175,10.5],[182,10.5],
                      [189,10.2],[193,9.2],[197,8],[200,6.7],
                      [203,5.2],[205,3.7],[206.2,2.4],[206.5,1.2]])
    high = np.interp(s.ravel(), right[:, 0], right[:, 1]).reshape(s.shape)
    nl, nr = low-2, high+3
    left = sample_rgba(module, original, base[0]+s*axis[0]+nl*normal[0], base[1]+s*axis[1]+nl*normal[1])
    right_rgba = sample_rgba(module, original, base[0]+s*axis[0]+nr*normal[0], base[1]+s*axis[1]+nr*normal[1])
    fill_amount = np.clip((n-nl)/np.maximum(nr-nl, 1), 0, 1)*255
    cloth = rgba_mix(left, right_rgba, fill_amount)
    cleaned = rgba_mix(original, cloth, cleanup_mask)
    guide = rgba_mix(cleaned, middle, middle_mask)
    guide = rgba_mix(guide, cap, cap_mask)

    # One effective sword foreground for the original-hand source-over step.
    sword_layer = middle.copy()
    sword_layer = rgba_mix(sword_layer, cap, cap_mask)
    guide, hands = hand_restore(original, guide, sword_layer, coverage)
    guide[:250] = original[:250]

    # Model edits are only narrow joins + uncertain exposed old-tip cloth.
    seams = ((source_s >= s0-1) & (source_s <= s0+10) & (middle_mask > 0))
    seams |= ((source_s >= s1-8) & (source_s <= s1+1.5) & (middle_mask > 0))
    seams |= cleanup_mask > 0
    seams = ndimage.binary_dilation(seams, iterations=2)
    seams[:250] = False
    # Leave the complete translated original cap and hand silhouette read-only.
    cap_protect = ndimage.binary_dilation(cap_mask > 0, iterations=1)
    seams[cap_protect] = False
    seams[hands >= 16] = False
    # Feather inwards only; never expand the model footprint into protected pixels.
    feather = np.asarray(Image.fromarray((seams*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.65)))
    edit = np.where(seams, feather, 0).astype('uint8')
    hand_core = hands >= 230
    changed = np.any(guide != original, axis=2)
    allowed = (source_mask > 0) | (coverage > 0)
    target_cap_rgba = cap.copy()
    target_cap_rgba[..., 3] = np.rint(cap[..., 3].astype(float)*cap_mask/255).astype('uint8')
    target_cap_rgba[target_cap_rgba[..., 3] == 0, :3] = 0
    source_cap_mask = module.translate_integer(cap_mask, -dx, -dy)
    source_cap_rgba = original.copy()
    source_cap_rgba[..., 3] = np.rint(original[..., 3].astype(float)*source_cap_mask/255).astype('uint8')
    source_cap_rgba[source_cap_rgba[..., 3] == 0, :3] = 0
    # A foreground finger can legitimately occlude cap pixels; byte equality
    # is evaluated only on the unobstructed original-cap interior.
    exact_cap_core = (cap_mask == 255) & (hands == 0)
    ys, xs = np.where(edit > 0)
    rgb_matte = np.array(Image.open(ART/'local-klein-consistency-v1/guides/sword-back/before.png').convert('RGB'))
    body = original[..., 3] > 0
    full_length_reference_upper_s = -73.5
    full_ratio = (206.5 - full_length_reference_upper_s + ds)/(206.5-full_length_reference_upper_s)
    report = {
        'status': 'single-frame local geometry guide; model not invoked; artistic acceptance pending',
        'source_path': str(SOURCE), 'source_sha256': sha(SOURCE),
        'reused_geometry_module': str(OLD/'preserve_tip.py'),
        'reused_module_sha256': sha(OLD/'preserve_tip.py'),
        'reused_config_sha256': sha(OLD/'tip-preservation-config.json'),
        'legacy_make_layers_actually_called': True,
        'translation_xy_integer': [dx,dy],
        'shoulder_mount_xy': base.tolist(),
        'source_actual_tip_xy': metrics['source_tip_xy'],
        'target_actual_tip_xy': metrics['target_tip_xy_raster'],
        'shoulder_mount_to_tip_length_ratio': metrics['visible_length_ratio_from_actual_tip'],
        'full_sword_length_ratio_reference': float(full_ratio),
        'full_sword_measurement_limit': 'Approx. 25.7% with upper grip/pommel reference s=-73.5 (~313,125). Overall visual length is approximate; complete sword includes this upper segment, while shoulder-to-tip grows 34.9%.',
        'middle_axial_scale': scale, 'middle_normal_scale': 1.0,
        'terminal_transform': 'complete original cap RGBA, integer translation only; no resampling/rotation/redraw',
        'terminal_source_and_translated_rgba_bytes_equal': bool(np.array_equal(module.translate_integer(source_cap_rgba,dx,dy), target_cap_rgba)),
        'cap_core_equals_source_rgba': bool(np.array_equal(guide[exact_cap_core], cap[exact_cap_core])),
        'hand_core_rgba_byte_exact': bool(np.array_equal(guide[hand_core],original[hand_core])),
        'hand_policy': 'source RGBA foreground over sword; alpha>=230 exact original bytes; alpha=0 finger gaps stay open; no rectangle matte',
        'hand_boxes_xyxy': [list(b) for b in HAND_BOXES],
        'changed_pixels': int(changed.sum()), 'changed_outside_original_and_target_sword_union': int((changed & ~allowed).sum()),
        'head_grip_mount_rgba_exact_above_y250': bool(np.array_equal(guide[:250],original[:250])),
        'feet_exact_from_y650': bool(np.array_equal(guide[650:],original[650:])),
        'model_seam_mask_nonzero_pixels': int((edit>0).sum()),
        'model_seam_mask_bbox_xyxy': [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
        'original_matte_rgb_differs_from_true_rgba_rgb_pixels': int((np.any(rgb_matte!=original[...,:3],axis=2)&body).sum()),
        'gray_background_issue': 'Old RGB before is composited on (228,228,228). Old make_layers discards alpha. This adapter never uses that flattened RGB for composition: original true RGBA + premultiplied interpolation prevent gray/white hand-edge rectangles and transparent-RGB interpolation halos.',
        'alpha_policy': 'True original alpha, premultiplied RGBA interpolation, translated item alpha clipped to source alpha; no opaque review background is introduced. Original alpha exactly preserved outside the edit union.',
        'uncertainties': [
            'Sword is flattened into character; old 8x-supersampled item matte is a manually constrained estimate, not a recovered original item layer. Source cap boundary may contain tiny clothing-colour mixtures.',
            'Exposed old sword/terminal slivers have no recorded hidden cloth. Adjacent original cloth/alpha interpolates an estimate; Qwen is restricted to the saved small seam mask for cleanup. This is not exact hidden-cloth recovery.',
            'Original hand alpha is used as foreground within the audited hand boxes; any source-alpha defects are inherited. Finger-gap locations are retained from the source, not resegmented from skin colour.',
        ],
        'legacy_geometry_metrics': metrics,
        'model_called': False, 'network_used': False, 'cloud_visual_inspection_used': False,
        'production_modified': False,
    }
    assert report['terminal_source_and_translated_rgba_bytes_equal']
    assert report['cap_core_equals_source_rgba']
    assert report['hand_core_rgba_byte_exact']
    assert report['changed_outside_original_and_target_sword_union'] == 0
    layers = {'original': original, 'guide': guide, 'edit': edit, 'hands': hands,
              'cap': cap, 'cap_mask': cap_mask, 'cap_core': exact_cap_core,
              'sword_layer': sword_layer, 'coverage': coverage,
              'source_cap_rgba': source_cap_rgba, 'target_cap_rgba': target_cap_rgba,
              'source_sword_mask': source_mask, 'cleanup_mask': cleanup_mask,
              'middle_mask': middle_mask}
    return layers, report


def finalize(raw_path, output_path=None):
    """Composite a 512x768 Qwen result only through the prepared seam mask.

    Returns (PIL RGBA image, JSON-safe report). Saves candidate/report beside the
    script by default. Raw must remain unchanged. Alpha comes from the guide,
    never from model's opaque or invented background.
    """
    layers, report = geometry()
    raw_path = Path(raw_path).resolve()
    raw_image = Image.open(raw_path)
    if raw_image.size != (512,768):
        raise ValueError(f'Expected Qwen raw 512x768, received {raw_image.size}; no automatic resizing.')
    raw = np.array(raw_image.convert('RGBA'))
    guide = layers['guide']
    proposed = raw.copy()
    proposed[...,3] = guide[...,3]
    candidate = rgba_mix(guide, proposed, layers['edit'])
    # Model cannot change original cap, hands, grip, face/head, costume or feet.
    cap_region = layers['cap_mask'] > 0
    candidate[cap_region] = guide[cap_region]
    hand_core = layers['hands'] >= 230
    candidate[hand_core] = layers['original'][hand_core]
    candidate[:250] = layers['original'][:250]
    candidate[650:] = layers['original'][650:]
    outside = layers['edit'] == 0
    assert np.array_equal(candidate[outside], guide[outside])
    assert np.array_equal(candidate[...,3], guide[...,3])
    assert np.array_equal(candidate[layers['cap_core']], layers['cap'][layers['cap_core']])
    destination = HERE/'candidate-rgba.png' if output_path is None else Path(output_path).resolve()
    if HERE not in destination.parents:
        raise ValueError('Output must remain inside the assigned sword directory.')
    Image.fromarray(candidate).save(destination)
    report.update({'status':'Qwen local seam-composite single-frame candidate; artistic acceptance pending',
                   'raw_path':str(raw_path),'raw_sha256':sha(raw_path),
                   'raw_mode':raw_image.mode,'candidate_path':str(destination),
                   'candidate_sha256':sha(destination),'model_called_by_this_script':False,
                   'model_pixels_used':int((layers['edit']>0).sum()),
                   'model_changed_pixels_outside_seam_mask':0,
                   'model_alpha_discarded_guide_alpha_preserved':True,
                   'final_hand_core_rgba_byte_exact':True,
                   'final_original_cap_core_rgba_byte_exact':True,
                   'final_model_changed_pixels':int(np.any(candidate!=guide,axis=2).sum())})
    (HERE/'final-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return Image.fromarray(candidate), report


def main():
    layers, report = geometry()
    shutil.copy2(SOURCE, HERE/'original-rgba.png')
    outputs = {'guide':'guide-rgba.png', 'edit':'edit-mask.png', 'hands':'hand-protection-alpha.png',
               'source_cap_rgba':'source-cap-rgba.png', 'target_cap_rgba':'translated-cap-rgba.png',
               'source_sword_mask':'source-sword-mask.png','cap_mask':'translated-cap-mask.png',
               'cleanup_mask':'exposed-cloth-cleanup-mask.png','middle_mask':'middle-mask.png'}
    for key, filename in outputs.items():
        Image.fromarray(layers[key]).save(HERE/filename)
    prompt = '''只修复图1中已加长背剑的两处棕色剑鞘中段接缝及原末端移走后少量露出的衣料，位置以白色局部编辑遮罩为准。图1的整把剑已沿原右上至左下轴线加长约26%，新的鞘尖在约(167,445)，不要再改变总长度、角度或鞘宽。保持原金属鞘帽的圆钝轮廓、纹理和颜色，不重画、不压扁、不截断，不改剑柄、护手、肩部固定点。延续原棕皮剑鞘的明暗和材质，让中段接缝连续自然。原手指在剑鞘前面，保留指缝，不画新手，不用矩形覆盖手部。保留银发、头型、脸、暗酒红服装、裤子、腰带、靴子、站姿、人物大小和脚部锚点。保持512×768画布和原透明背景，不添灰底、白底、地面或投影。只输出一个完整背面角色。'''
    (HERE/'prompt.txt').write_text(prompt+'\n',encoding='utf-8')
    report['outputs'] = {name:{'path':str(HERE/name),'sha256':sha(HERE/name)} for name in outputs.values()}
    (HERE/'geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'guide':str(HERE/'guide-rgba.png'),'mask':str(HERE/'edit-mask.png'),
                      'prompt':str(HERE/'prompt.txt'),'translation':SHIFT,
                      'model_edit_pixels':report['model_seam_mask_nonzero_pixels'],
                      'cap_and_hands_locked':True},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    if len(sys.argv)>1:
        _, result = finalize(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
        print(json.dumps({'candidate':result['candidate_path'],'raw':result['raw_path'],
                          'model_pixels_used':result['model_pixels_used']},ensure_ascii=False,indent=2))
    else:
        main()
