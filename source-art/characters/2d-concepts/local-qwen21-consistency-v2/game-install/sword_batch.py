"""Rear exploration scabbards: phase-local extraction and cap-safe extension.

No runtime writes, downloads, model calls or new dependencies. SciPy masked
normalized correlation registers the reference geometry against EACH phase.
Only a mask is registered: cap RGB/alpha always comes from that phase itself
and its output transform is an integer translation, never scaling/rotation.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, signal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RATIO = 1.2635809967340603
_CACHE = {}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resources():
    if 'resources' not in _CACHE:
        tools = _load('batch_rgba_sword_tools', ROOT/'sword/prepare_sword.py')
        back = _load('batch_rear_run_geometry', ROOT/'sword/back-run/prepare_back_run.py')
        layers, _ = back.build_layers()
        original = layers['original']
        mask = layers['source_sword_mask']
        rows, cols = np.where(mask > 128)
        center = np.rint([(cols.min()+cols.max())/2, (rows.min()+rows.max())/2])
        capmask = layers['source_cap'][..., 3]
        rows, cols = np.where(capmask > 128)
        capcenter = np.rint([(cols.min()+cols.max())/2, (rows.min()+rows.max())/2])
        base = np.array(back.CONFIG['base_xy'])
        axis = np.array(back.CONFIG['legacy_tip_xy'])-base
        axis /= np.linalg.norm(axis)
        normal = np.array([axis[1], -axis[0]])
        source_cap_mask = tools.load_legacy().translate_integer(
            layers['cap_mask'], -back.SHIFT[0], -back.SHIFT[1])
        _CACHE['resources'] = dict(tools=tools, back=back, layers=layers,
            original=original, mask=mask, capmask=source_cap_mask,
            center=center, capcenter=capcenter, base=base, axis=axis,
            normal=normal, config=back.CONFIG)
    return _CACHE['resources']


def _rotation(degrees):
    t = np.deg2rad(degrees)
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])


def _template(reference, source_mask, center, matrix, size):
    yy, xx = np.indices((size, size), dtype=float)
    q = np.stack((xx-size//2, yy-size//2)).reshape(2, -1)
    source = center[:, None]+np.linalg.inv(matrix)@q
    x, y = source[0].reshape(size, size), source[1].reshape(size, size)
    w = ndimage.map_coordinates(source_mask.astype(float)/255, [y, x],
        order=1, mode='constant', cval=0, prefilter=False)
    w = (w > .70).astype(float)
    gray = reference[..., :3].astype(float).mean(axis=2)
    values = ndimage.map_coordinates(gray, [y, x], order=1,
        mode='constant', cval=0, prefilter=False)
    count = float(w.sum())
    centered = (values-float((values*w).sum()/count))*w
    return w, count, centered, float((centered*centered).sum())


def _correlation(gray, template):
    w, count, centered, variance = template
    sums = signal.correlate(gray, w, mode='valid', method='fft')
    squares = signal.correlate(gray*gray, w, mode='valid', method='fft')
    cross = signal.correlate(gray, centered, mode='valid', method='fft')
    return cross/np.sqrt(np.maximum((squares-sums*sums/count)*variance, 1e-8))


def _whole_fit(original):
    r = _resources()
    gray = original[..., :3].astype(float).mean(axis=2)[200:500, 130:360]
    best = None
    for angle in range(-12, 13, 2):
        matrix = _rotation(angle)
        key = ('whole-template', angle)
        if key not in _CACHE:
            _CACHE[key] = _template(r['original'], r['mask'], r['center'], matrix, 161)
        scores = _correlation(gray, _CACHE[key])
        iy, ix = np.unravel_index(np.argmax(scores), scores.shape)
        score = float(scores[iy, ix])
        if best is None or score > best['score']:
            best = dict(score=score, angle=float(angle), matrix=matrix,
                center=np.array([ix+130+80, iy+200+80], float))
    return best


def _cap_fit(original, whole):
    r = _resources()
    expected = whole['center']+whole['matrix']@(r['capcenter']-r['center'])
    # A free cap-only search can confuse the gold coat hem with the cap. Search
    # only near the independently located complete lower scabbard.
    radius=18
    left = int(round(expected[0]))-40-radius
    top = int(round(expected[1]))-40-radius
    size=81+2*radius
    gray = original[..., :3].astype(float).mean(axis=2)[top:top+size, left:left+size]
    if gray.shape != (size, size):
        raise ValueError('Rear cap search left the validated canvas window.')
    gy, gx = np.indices((2*radius+1, 2*radius+1))
    centers_x, centers_y = left+gx+40, top+gy+40
    distance2 = (centers_x-expected[0])**2+(centers_y-expected[1])**2
    best = None
    for angle in np.arange(whole['angle']-20, whole['angle']+20.01, 2):
        for scale in (.92, 1., 1.08):
            matrix = _rotation(angle)*scale
            key = ('cap-template', float(angle), scale)
            if key not in _CACHE:
                _CACHE[key] = _template(r['original'], r['capmask'], r['capcenter'], matrix, 81)
            scores = _correlation(gray, _CACHE[key])
            # Mild displacement regularization, only for disambiguation. The
            # reported NCC below is the unpenalized appearance agreement.
            adjusted = scores-.00020*distance2-.03*abs(scale-1)
            iy, ix = np.unravel_index(np.argmax(adjusted), adjusted.shape)
            value = float(adjusted[iy, ix])
            if best is None or value > best['adjusted_score']:
                best = dict(score=float(scores[iy, ix]), adjusted_score=value,
                    angle=float(angle), scale=float(scale), matrix=matrix,
                    center=np.array([left+ix+40, top+iy+40], float), expected=expected)
    return best


def _point(point, registration, reference_center):
    return registration['center']+registration['matrix']@(np.asarray(point)-reference_center)


def _pull_mask(mask, matrix, source_center, target_center):
    yy, xx = np.indices(mask.shape, dtype=float)
    q = np.stack((xx-target_center[0], yy-target_center[1])).reshape(2, -1)
    source = source_center[:, None]+np.linalg.inv(matrix)@q
    return np.rint(np.clip(ndimage.map_coordinates(mask.astype(float),
        [source[1].reshape(mask.shape), source[0].reshape(mask.shape)],
        order=1, mode='constant', cval=0, prefilter=False), 0, 255)).astype('uint8')


def _registration(original, record):
    r = _resources()
    key = ('registration', record['state'], int(record['phase']))
    if key not in _CACHE:
        if record['state'] == 'run' and int(record['phase']) == 0:
            whole = dict(score=1., angle=0., matrix=np.eye(2), center=r['center'].copy())
            cap = dict(score=1., adjusted_score=1., angle=0., scale=1.,
                matrix=np.eye(2), center=r['capcenter'].copy(), expected=r['capcenter'].copy())
        else:
            whole = _whole_fit(original)
            cap = _cap_fit(original, whole)
        displacement = float(np.linalg.norm(cap['center']-cap['expected']))
        # Large phase-specific cap deviations need stronger independent image
        # evidence; never accept a weak nearby coat-trim match merely to pass.
        required_cap_ncc=.90 if displacement>8 else .82
        if whole['score'] < .78 or cap['score'] < required_cap_ncc or displacement > 19.0:
            raise ValueError('Unsafe rear-sword registration: '+json.dumps({
                'state':record['state'], 'phase':record['phase'],
                'shaft_ncc':whole['score'], 'cap_ncc':cap['score'],
                'cap_prediction_error_px':displacement}))
        _CACHE[key] = (whole, cap)
    return _CACHE[key]


def _fallback_hands(original):
    """Conservative separated left-arm silhouette, when no body mask supplied."""
    alpha = original[..., 3]
    output = np.zeros(alpha.shape, np.uint8)
    for y in range(300, 451):
        row = alpha[y, 110:235] >= 24
        labels, count = ndimage.label(row)
        runs = [np.flatnonzero(labels == i)+110 for i in range(1, count+1)]
        runs = [x for x in runs if len(x) >= 4]
        if len(runs) >= 2 and runs[0][-1] < 205 and runs[1][0]-runs[0][-1] >= 4:
            output[y, max(110, runs[0][0]-3):runs[0][-1]+4] = 255
    return ndimage.maximum_filter(output, size=3)


def _hands(original, record):
    value = record.get('hands_protection_mask')
    if value is None:
        return _fallback_hands(original), 'phase-local separated-arm alpha fallback'
    result = np.array(value.convert('L') if isinstance(value, Image.Image) else Image.open(value).convert('L'))
    if result.shape != original.shape[:2]:
        raise ValueError('hands_protection_mask must be 512x768.')
    return result, 'body adapter phase-local hands_protection_mask'


def _protect(record, mask):
    old = record.get('palette_protect_mask')
    if old is not None:
        values = np.array(old.convert('L') if isinstance(old, Image.Image) else Image.open(old).convert('L'))
        mask = np.maximum(mask, values)
    record['palette_protect_mask'] = Image.fromarray(mask)


def weapon_mask(image, record):
    """Phase-local original-weapon protection for the upstream body adapter."""
    r=_resources()
    if record['direction']!='up':
        return Image.new('L',(512,768),0)
    if record['state']=='idle':
        mask=Image.new('L',(512,768),0)
        d=ImageDraw.Draw(mask)
        d.line([(316,120),(283,192),(198,381)],fill=255,width=31)
        d.line([(269,183),(304,199)],fill=255,width=24)
        return mask
    whole,cap=_registration(np.array(image.convert('RGBA')),record)
    m=_pull_mask(r['mask'],whole['matrix'],r['center'],whole['center'])
    m=np.maximum(m,_pull_mask(r['capmask'],cap['matrix'],r['capcenter'],cap['center']))
    result=Image.fromarray((ndimage.binary_dilation(m>0,iterations=3)*255).astype('uint8'))
    d=ImageDraw.Draw(result)
    d.line([tuple(_point(p,whole,r['center'])) for p in [[318,126],[300,185],[258,287]]],fill=255,width=32)
    d.line([tuple(_point(p,whole,r['center'])) for p in [[279,179],[322,203]]],fill=255,width=24)
    return result


def apply_sword(image, record):
    """Return RGBA image and JSON-safe report. Mutates palette mask in record.

    Supported scope: up/idle0, up/walk0..3, up/run0..7 at the shared original
    512x768/400px-per-world-unit canvas. Input may be a body guide as long as
    its original weapon is protected. Non-up directions pass through unchanged.
    The installer may bypass this for approved idle/up0 and run/up0 full images.
    """
    if image.size != (512, 768):
        raise ValueError('Sword adapter requires the established 512x768 canvas.')
    if record['direction'] != 'up':
        return image.convert('RGBA'), {'applied':False, 'reason':'projection-specific rear-only scope'}
    r = _resources()
    tools = r['tools']
    original = np.array(image.convert('RGBA'))
    if record['state'] == 'idle':
        if int(record['phase']) != 0:
            raise ValueError('Only one idle phase is defined.')
        guide, _ = tools.geometry()
        mask = (guide['source_sword_mask'] > 0)|(guide['coverage'] > 0)
        result = original.copy()
        accepted = np.array(Image.open(ROOT/'final/standing-back.png').convert('RGBA'))
        result[mask] = accepted[mask]
        p = Image.new('L', (512,768), 0)
        ImageDraw.Draw(p).line([(316,120),(167,446)], fill=255, width=27)
        _protect(record, np.array(p))
        return Image.fromarray(result), {'applied':True, 'state':'idle','phase':0,
            'method':'approved p0 sword-only RGBA pixels on current canvas',
            'cap_integer_translation_xy':[-31,65], 'cap_rescaled':False,
            'palette_mask_in_record':True, 'production_written':False}

    whole, cap = _registration(original, record)
    cfg = r['config'];base,axis,normal = r['base'],r['axis'],r['normal']
    s0,s1 = cfg['middle_start_s'],cfg['tip_lock_start_s']
    start_ref = base+s0*axis
    join_ref = base+s1*axis
    start = _point(start_ref, whole, r['center'])
    join = _point(join_ref, cap, r['capcenter'])
    vector = join-start
    direction = vector/np.linalg.norm(vector)
    across = whole['matrix']@normal
    across /= np.linalg.norm(across)
    source_tip_ref = base+cfg['source_tip_sn'][0]*axis+cfg['source_tip_sn'][1]*normal
    source_tip = _point(source_tip_ref, cap, r['capcenter'])
    upper = _point([310.,140.], whole, r['center'])
    full_length = float(np.linalg.norm(source_tip-upper))
    delta = np.rint(direction*full_length*(RATIO-1)).astype(int)
    dx,dy = map(int,delta)

    # The source middle polygon adapts to this phase's shaft and independently
    # located cap join. Cap transform only registers an extraction mask.
    contour = np.array(cfg['source_boundary_sn'],float)
    middle_points=[]
    left=contour[:7]  # s110..210
    right=contour[25:][::-1]  # s110..210, high-normal side
    for chain in (left,right[::-1]):
        for s,n in chain:
            t=(s-s0)/(s1-s0)
            point=(1-t)*_point(base+s*axis+n*normal,whole,r['center'])
            point+=t*_point(base+s*axis+n*normal,cap,r['capcenter'])
            middle_points.append(point)
    middle_source_mask=tools.load_legacy().polygon_mask((512,768),middle_points)
    cap_source_mask=_pull_mask(r['capmask'],cap['matrix'],r['capcenter'],cap['center'])
    source_union=np.maximum(middle_source_mask,cap_source_mask)

    yy,xx=np.indices(original.shape[:2],dtype=float)
    dst_basis=np.column_stack((vector+delta,across))
    local=np.linalg.inv(dst_basis)@np.stack((xx-start[0],yy-start[1])).reshape(2,-1)
    t,n=local[0].reshape(xx.shape),local[1].reshape(xx.shape)
    sx=start[0]+t*vector[0]+n*across[0]
    sy=start[1]+t*vector[1]+n*across[1]
    middle=tools.sample_rgba(tools.load_legacy(),original,sx,sy)
    middle_mask=np.rint(ndimage.map_coordinates(middle_source_mask.astype(float),
        [sy,sx],order=1,mode='constant',cval=0,prefilter=False)).astype('uint8')
    # Small overlap is sourced from each phase's own cap start, not cloned p0.
    middle_mask[(t<0)|(t>1.015)]=0
    old=tools.load_legacy()
    translated_cap=old.translate_integer(original,dx,dy)
    target_cap_mask=old.translate_integer(cap_source_mask,dx,dy)
    coverage=np.maximum(middle_mask,target_cap_mask)
    cleanup=np.rint(source_union.astype(float)*(1-coverage/255)).astype('uint8')

    # Hidden cloth is unrecorded. Sample original/current guide neighbours on
    # both normal sides; keep this estimate explicitly counted in the report.
    source_s=(xx-start[0])*direction[0]+(yy-start[1])*direction[1]
    source_n=(xx-start[0])*across[0]+(yy-start[1])*across[1]
    points=np.array(middle_points+[
        _point(base+s*axis+n*normal,cap,r['capcenter']) for s,n in contour[6:26]])
    ps=(points-start)@direction;pn=(points-start)@across
    bins=np.linspace(float(ps.min()),float(ps.max()),80)
    lows=[];highs=[]
    for value in bins:
        close=np.abs(ps-value)<max(3.,float(ps.max()-ps.min())/20)
        if not close.any():close[np.argmin(abs(ps-value))]=True
        lows.append(float(pn[close].min()-3));highs.append(float(pn[close].max()+3))
    nl=np.interp(source_s.ravel(),bins,lows).reshape(xx.shape)
    nr=np.interp(source_s.ravel(),bins,highs).reshape(xx.shape)
    l=tools.sample_rgba(old,original,start[0]+source_s*direction[0]+nl*across[0],start[1]+source_s*direction[1]+nl*across[1])
    rr=tools.sample_rgba(old,original,start[0]+source_s*direction[0]+nr*across[0],start[1]+source_s*direction[1]+nr*across[1])
    cloth=tools.rgba_mix(l,rr,np.clip((source_n-nl)/np.maximum(nr-nl,1),0,1)*255)
    candidate=tools.rgba_mix(original,cloth,cleanup)
    candidate=tools.rgba_mix(candidate,middle,middle_mask)
    candidate=tools.rgba_mix(candidate,translated_cap,target_cap_mask)

    handmask,hand_method=_hands(original,record)
    foreground=(handmask>0)&(coverage>0)
    oa=original[...,3:4].astype(float)/255
    sword=tools.rgba_mix(middle,translated_cap,target_cap_mask)
    sa=sword[...,3:4].astype(float)/255*coverage[...,None]/255
    alpha=oa+sa*(1-oa)
    premul=original[...,:3]*oa+sword[...,:3]*sa*(1-oa)
    rgb=np.divide(premul,alpha,out=np.zeros_like(premul),where=alpha>0)
    occlusion=np.rint(np.clip(np.dstack((rgb,alpha[...,0]*255)),0,255)).astype('uint8')
    candidate[foreground]=occlusion[foreground]
    handcore=(handmask>0)&(original[...,3]>=230)
    candidate[handcore]=original[handcore]

    cap_source_rgba=original.copy()
    cap_source_rgba[...,3]=np.rint(original[...,3].astype(float)*cap_source_mask/255).astype('uint8')
    cap_target_rgba=old.translate_integer(cap_source_rgba,dx,dy)
    core=(target_cap_mask==255)&~foreground
    allowed=(source_union>0)|(coverage>0)
    changed=np.any(candidate!=original,axis=2)
    assert not np.any(changed&~allowed)
    assert np.array_equal(candidate[core],translated_cap[core])
    assert np.array_equal(candidate[handcore],original[handcore])
    palette=(ndimage.binary_dilation(allowed,iterations=2)*255).astype('uint8')
    line=Image.fromarray(palette)
    ImageDraw.Draw(line).line([tuple(_point([318,126],whole,r['center'])),tuple(start)],fill=255,width=31)
    _protect(record,np.array(line))
    report={'applied':True,'state':record['state'],'direction':'up','phase':int(record['phase']),
        'method':'phase-local masked rigid/similarity template registration; own cap integer translation; middle-only axial resampling',
        'shaft_mask_ncc':float(whole['score']),'cap_mask_ncc':float(cap['score']),
        'shaft_angle_degrees':float(whole['angle']),'cap_mask_angle_degrees':float(cap['angle']),
        'cap_mask_scale':float(cap['scale']),
        'cap_prediction_error_px':float(np.linalg.norm(cap['center']-cap['expected'])),
        'cap_registration_policy':'independent mask similarity; NCC>=0.90 when cap differs >8px from whole-shaft rigid prediction, otherwise>=0.82; max19px',
        'registration_grid_resolution_px':1.,'item_matte_uncertainty_px':2.,
        'source_tip_xy':source_tip.tolist(),'target_tip_xy':(source_tip+delta).tolist(),
        'cap_integer_translation_xy':[dx,dy],'cap_rescaled':False,'cap_rotated':False,
        'actual_full_length_ratio':float(np.linalg.norm(source_tip+delta-upper)/full_length),
        'cap_extracted_nonzero_pixels':int((cap_source_mask>0).sum()),
        'cap_integer_translation_preserves_layer_rgba_bytes':bool(np.array_equal(cap_target_rgba,old.translate_integer(cap_source_rgba,dx,dy))),
        'unoccluded_cap_core_rgba_exact':True,'cap_core_check_pixels':int(core.sum()),
        'own_hand_core_rgba_exact':True,'hand_mask_method':hand_method,
        'sword_hand_overlap_pixels':int(foreground.sum()),'hand_skin_core_overlap_pixels':int((handcore&(coverage>0)).sum()),
        'hidden_cloth_estimate_pixels':int((cleanup>0).sum()),'changed_pixels':int(changed.sum()),
        'changed_outside_old_new_sword_union':0,'palette_mask_in_record':True,
        'source_cap_rgba_sha256_raw':hashlib.sha256(cap_source_rgba.tobytes()).hexdigest(),
        'output_cap_core_rgba_sha256_raw':hashlib.sha256(candidate[core].tobytes()).hexdigest(),
        'limitations':['Registered geometry is an estimated item matte, not recovered independent equipment layers.',
            'Each phase retains its own source cap pixels; small original cloth mixtures may remain at its AA fringe.',
            'Cloth hidden by the old sword is estimated only where uncovered by the new shaft.'],
        'model_called':False,'runtime_written':False}
    return Image.fromarray(candidate),report


def validate():
    """Local manual verification, reports + small cap-only comparison sheet."""
    rf=_load('batch_original_runtime_canvas',HERE/'runtime_frames.py')
    manifest=rf.read_manifest();reports=[];tiles=[]
    for state,count in [('idle',1),('walk',4),('run',8)]:
        for phase in range(count):
            image,record=rf.canvas(manifest,state,'up',phase)
            try:
                candidate,report=apply_sword(image,record)
                report['validation_pass']=True
                if state=='idle':
                    source_tip=np.array([198.016,380.206]);target_tip=np.array([167.016,445.206])
                else:
                    source_tip=np.array(report['source_tip_xy']);target_tip=np.array(report['target_tip_xy'])
                pair=Image.new('RGB',(128,86),(235,235,235))
                for col,(im,tip) in enumerate([(image,source_tip),(candidate,target_tip)]):
                    x,y=np.rint(tip).astype(int)
                    crop=im.crop((x-16,y-34,x+16,y+2)).resize((64,72),Image.Resampling.NEAREST)
                    bg=Image.new('RGB',crop.size,(185,185,185));bg.paste(crop,(0,0),crop.getchannel('A'))
                    pair.paste(bg,(col*64,14))
                ImageDraw.Draw(pair).text((2,1),f'{state}{phase} cap own / moved',fill=(20,20,20))
                tiles.append(pair)
            except Exception as error:
                report={'state':state,'phase':phase,'validation_pass':False,'error':str(error)}
            reports.append(report)
    board=Image.new('RGB',(512,4*86),(245,245,245))
    for index,tile in enumerate(tiles):board.paste(tile,((index%4)*128,(index//4)*86))
    board.save(HERE/'sword-batch-cap-local-preview.png')
    result={'scope':'up idle1/walk4/run8 only; validation on original runtime canvases',
        'all_pass':all(x['validation_pass'] for x in reports),'records':reports,
        'preview':str(HERE/'sword-batch-cap-local-preview.png'),
        'preview_policy':'13 tiny cap before/after crops only, source point coordinates in each report; no full frame upload',
        'runtime_written':False,'new_dependencies':False,'model_called':False,'cloud_visual_check_used':False}
    (HERE/'sword-batch-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_pass':result['all_pass'],'records':[{k:v for k,v in row.items() if k in ['state','phase','shaft_mask_ncc','cap_mask_ncc','cap_prediction_error_px','validation_pass','error']} for row in reports],
        'preview':result['preview']},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    validate()
