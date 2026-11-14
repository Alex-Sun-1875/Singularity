"""Pose-specific cap-safe back-run adapter; local pixels, no model/network."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
import shutil
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent
SWORD = HERE.parent
ART = SWORD.parent.parent
SOURCE = ART/'local-qwen21-turbo-pilot-v1/originals-512x768/run-back-p0-rgba.png'
spec = importlib.util.spec_from_file_location('standing_sword_rgba_tools',SWORD/'prepare_sword.py')
TOOLS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(TOOLS)
SHIFT = (-28,68)
HAND_BOX = (133,350,184,411)
CONFIG = {
    'base_xy':[300.,185.], 'legacy_tip_xy':[206.,413.],
    'source_tip_sn':[233.6,-6.8], 'middle_start_s':110., 'tip_lock_start_s':210.,
    'source_tip_uncertainty_px':1.5,
    # Left edge from shaft to real cap; right edge returns to shaft. Gold coat
    # trim at s235..244 is intentionally excluded: it is not the sword tip.
    'source_boundary_sn':[
        [110,-15],[135,-15],[160,-15],[180,-15],[195,-15],[205,-15],
        [210,-14.8],[214,-14.5],[218,-13.8],[220,-13.2],[224,-12.5],
        [227,-11.8],[229,-10.8],[231,-9.5],[232,-8.7],[233,-7.5],[233.6,-6.8],
        [233.3,-6.0],[232.6,-4.8],[231,-3.3],[229,-1.7],[226,0],
        [222,1.8],[218,2.8],[214,3.3],[210,4],[205,5],[195,5.8],
        [180,7],[160,7.5],[135,7.5],[110,7.5]],
    'limits':['Pose-specific estimated item matte; source cap contains baked-in clothing mixture at AA fringe.',
              'One necessary 420x440 crop inspected; x125..264 y300..439, 3x nearest.',
              'Actual cap ends around (205,398); gold trim near (206,413) is coat hem and remains fixed.']}


def build_layers():
    old = TOOLS.load_legacy()
    old.CONFIG = dict(CONFIG)
    base,axis,normal = old.frame()
    tip = base+CONFIG['source_tip_sn'][0]*axis+CONFIG['source_tip_sn'][1]*normal
    old.CONFIG['target_tip_xy'] = (tip+SHIFT).tolist()
    original = np.array(Image.open(SOURCE).convert('RGBA'))
    layers, legacy = old.make_layers(Image.fromarray(original))
    yy,xx = np.indices(original.shape[:2],dtype=float)
    s = (xx-base[0])*axis[0]+(yy-base[1])*axis[1]
    n = (xx-base[0])*normal[0]+(yy-base[1])*normal[1]
    ds,dn = np.array(SHIFT)@axis,np.array(SHIFT)@normal
    s0,s1=CONFIG['middle_start_s'],CONFIG['tip_lock_start_s']
    scale=(s1+ds-s0)/(s1-s0)
    ss=s0+(s-s0)/scale
    nn=n-dn*np.clip((ss-s0)/(s1-s0),0,1)
    middle=TOOLS.sample_rgba(old,original,base[0]+ss*axis[0]+nn*normal[0],base[1]+ss*axis[1]+nn*normal[1])
    cap=old.translate_integer(original,*SHIFT)
    sm=layers['source_sword_alpha'];mm=layers['middle_alpha'];cm=layers['target_tip_alpha']
    coverage=np.maximum(mm,cm)
    cleanup=np.rint(sm.astype(float)*(1-coverage/255)).astype('uint8')

    boundary=np.array(CONFIG['source_boundary_sn'],float)
    left=boundary[:17]
    right=boundary[16:][::-1]
    # The closure repeats the tip once; np.interp tolerates that endpoint.
    nl=np.interp(s.ravel(),left[:,0],left[:,1]).reshape(s.shape)-3
    nr=np.interp(s.ravel(),right[:,0],right[:,1]).reshape(s.shape)+3
    left_rgba=TOOLS.sample_rgba(old,original,base[0]+s*axis[0]+nl*normal[0],base[1]+s*axis[1]+nl*normal[1])
    right_rgba=TOOLS.sample_rgba(old,original,base[0]+s*axis[0]+nr*normal[0],base[1]+s*axis[1]+nr*normal[1])
    cloth=TOOLS.rgba_mix(left_rgba,right_rgba,np.clip((n-nl)/np.maximum(nr-nl,1),0,1)*255)

    source_cap_mask=old.translate_integer(cm,-SHIFT[0],-SHIFT[1])
    source_cap=original.copy();source_cap[:,:,3]=np.rint(original[:,:,3].astype(float)*source_cap_mask/255).astype('uint8')
    source_cap[source_cap[:,:,3]==0,:3]=0
    target_cap=old.translate_integer(source_cap,*SHIFT)
    hand=np.zeros(original.shape[:2],np.uint8);x0,y0,x1,y1=HAND_BOX
    hand[y0:y1,x0:x1]=original[y0:y1,x0:x1,3]
    assert not np.any((coverage>0)&(hand>0)), 'Unexpected sword/hand crossing needs occlusion review.'
    seams=(((ss>=s0-1)&(ss<=s0+9))|((ss>=s1-8)&(ss<=s1+1.5)))&(mm>0)
    seams|=cleanup>0
    seams=ndimage.binary_dilation(seams,iterations=2)
    seams[ndimage.binary_dilation(cm>0,iterations=1)]=False
    seams[hand>0]=False
    seams[:250]=False
    soft=np.array(Image.fromarray((seams*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.65)))
    edit=np.where(seams,soft,0).astype('uint8')
    report={
        'status':'pose-specific local single-frame extension, artistic acceptance pending',
        'source_path':str(SOURCE),'source_sha256':TOOLS.sha(SOURCE),
        'original_geometry_reused':str(TOOLS.OLD/'preserve_tip.py'),
        'original_make_layers_actually_called_with_pose_specific_config':True,
        'local_visual_inspection':{'cloud_visual_check_used':True,'crop_xyxy':[125,300,265,440],
            'uploaded_thumbnail_size':[420,440],'uploads':1,'whole_frame_uploaded':False,
            'finding':'Independent gold metal cap ends around (205,398). Diagonal coat gold trim below it is a separate feature, excluded from item matte.'},
        'source_tip_xy':tip.tolist(),'target_tip_xy':(tip+SHIFT).tolist(),
        'translation_xy_integer':list(SHIFT),'translation_along_axis_px':float(ds),
        'source_cap_start_s':s1,'source_cap_end_s':CONFIG['source_tip_sn'][0],
        'middle_start_s':s0,'middle_axial_scale':float(scale),'middle_normal_scale':1.,
        'full_sword_length_ratio_approx':float(1+ds/(233.6+45.4)),
        'full_sword_reference':'Upper grip approx (310,140); shoulder frame (300,185). Reference total axis length approx279px; target+26.4%.',
        'source_cap_rgba_translated_byte_exact':bool(np.array_equal(old.translate_integer(source_cap,*SHIFT),target_cap)),
        'hand_overlap_pixels':0,'old_sword_exposed_cleanup_pixels':int((cleanup>0).sum()),
        'seam_mask_pixels':int((edit>0).sum()),
        'cap_source_mask_nonzero_pixels':int((source_cap_mask>0).sum()),
        'uncertainties':CONFIG['limits']+['Hidden old sword cloth is unknown. Any exposed sliver is a premultiplied original-neighbour estimate with a separate cleanup mask.',
                  'Visual review established cap versus coat semantic separation, but the manually estimated AA item matte still needs final artistic review.'],
        'model_invoked_by_this_script':False,'network_generation_used':False,'production_modified':False}
    assert report['source_cap_rgba_translated_byte_exact']
    return {'original':original,'middle':middle,'middle_mask':mm,'cap':cap,'cap_mask':cm,
            'source_cap':source_cap,'target_cap':target_cap,'source_sword_mask':sm,
            'coverage':coverage,'cleanup_mask':cleanup,'cloth':cloth,'edit':edit,'hand':hand},report


def extend_sword_rgba(image, source_pose='back-run'):
    """Return (RGBA guide, seam L mask, report) over an existing body guide."""
    if source_pose!='back-run':
        raise ValueError('This checked source matte is only for back-run.')
    if image.size!=(512,768):
        raise ValueError('Expected exact 512x768 RGBA canvas, no fit or resize.')
    layers,report=build_layers()
    base=np.array(image.convert('RGBA'))
    result=TOOLS.rgba_mix(base,layers['cloth'],layers['cleanup_mask'])
    result=TOOLS.rgba_mix(result,layers['middle'],layers['middle_mask'])
    result=TOOLS.rgba_mix(result,layers['cap'],layers['cap_mask'])
    handcore=layers['hand']>=230
    result[handcore]=layers['original'][handcore]
    allowed=(layers['source_sword_mask']>0)|(layers['coverage']>0)
    assert np.array_equal(result[~allowed],base[~allowed])
    capcore=layers['cap_mask']==255
    assert np.array_equal(result[capcore],layers['cap'][capcore])
    report['input_body_rgba_sha256_raw']=__import__('hashlib').sha256(base.tobytes()).hexdigest()
    report['changed_outside_source_and_extended_sword_union']=0
    report['cap_core_matches_original_rgba']=True
    report['source_and_destination_cap_source_opacity_retained']=True
    return Image.fromarray(result),Image.fromarray(layers['edit']),report


def merge_back_run(body_guide_path,body_edit_mask_path):
    body=Image.open(body_guide_path).convert('RGBA')
    guide,seam,report=extend_sword_rgba(body)
    layers,_=build_layers()
    bodymask=np.array(Image.open(body_edit_mask_path).convert('L'))
    if bodymask.shape!=(768,512):
        raise ValueError('Body mask dimensions must match the guide.')
    union=np.maximum(bodymask,np.array(seam))
    # Keep the whole sword deterministic. Only seam/cleanup pixels may use raw.
    sword=ndimage.binary_dilation(layers['coverage']>0,iterations=1)
    union[sword]=np.array(seam)[sword]
    union[layers['cap_mask']>0]=0
    union[layers['hand']>0]=0
    body_folder=Path(body_guide_path).resolve().parent
    immutable=np.zeros(union.shape,np.uint8)
    for name in ('head-protection-mask.png','arms-hands-protection-mask.png','boots-protection-mask.png'):
        immutable=np.maximum(immutable,np.array(Image.open(body_folder/name).convert('L')))
    union[immutable>0]=0
    immutable=np.maximum(immutable,layers['cap_mask'])
    palette_protect=np.array(Image.open(body_folder/'all-protection-mask.png').convert('L'))
    palette_protect=np.maximum(palette_protect,ndimage.binary_dilation(
        (layers['coverage']>0)|(layers['source_sword_mask']>0),iterations=2).astype('uint8')*255)
    guide.save(HERE/'merged-guide-rgba.png')
    Image.fromarray(union).save(HERE/'merged-edit-mask.png')
    Image.fromarray(immutable).save(HERE/'merged-immutable-mask.png')
    Image.fromarray(palette_protect).save(HERE/'palette-protection-mask.png')
    Image.fromarray(layers['edit']).save(HERE/'sword-seam-edit-mask.png')
    report['body_guide_path']=str(Path(body_guide_path).resolve())
    report['body_guide_sha256']=TOOLS.sha(body_guide_path)
    report['body_edit_mask_path']=str(Path(body_edit_mask_path).resolve())
    report['merged_guide_path']=str(HERE/'merged-guide-rgba.png')
    report['merged_mask_path']=str(HERE/'merged-edit-mask.png')
    report['merged_immutable_mask_path']=str(HERE/'merged-immutable-mask.png')
    report['palette_protection_mask_path']=str(HERE/'palette-protection-mask.png')
    report['merged_edit_pixels']=int((union>0).sum())
    (HERE/'merged-geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return guide,Image.fromarray(union),report


def finalize_back_run(raw_path,body_candidate_path=None):
    """Raw contributes RGB only through merged-edit-mask; merged guide owns alpha.

    Head, hands, boots and translated cap are copied from the prepared merged
    guide last. The optional second argument is rejected: passing a body-only
    candidate would reinstate the old sword and break the merged-mask contract.
    """
    if body_candidate_path is not None:
        raise ValueError('Finalize directly on merged guide; no body-only candidate is accepted.')
    guide=Image.open(HERE/'merged-guide-rgba.png').convert('RGBA')
    mask=np.array(Image.open(HERE/'merged-edit-mask.png').convert('L'))
    immutable=np.array(Image.open(HERE/'merged-immutable-mask.png').convert('L'))>0
    report=json.loads((HERE/'merged-geometry-report.json').read_text(encoding='utf-8'))
    raw=Image.open(raw_path).convert('RGBA')
    if raw.size!=guide.size:
        raise ValueError('Raw and body candidate must be 512x768.')
    a=np.array(guide);proposed=np.array(raw);proposed[:,:,3]=a[:,:,3]
    effective=np.where(a[:,:,3]>0,mask,0).astype('uint8')
    result=TOOLS.rgba_mix(a,proposed,effective)
    layers,_=build_layers();cap=layers['cap_mask']>0
    result[cap]=a[cap]
    result[immutable]=a[immutable]
    outside=effective==0
    assert np.array_equal(result[outside],a[outside])
    assert np.array_equal(result[:,:,3],a[:,:,3])
    assert np.array_equal(result[layers['cap_mask']==255],layers['cap'][layers['cap_mask']==255])
    Image.fromarray(result).save(HERE/'candidate-rgba.png')
    report.update({'raw_path':str(Path(raw_path).resolve()),'raw_sha256':TOOLS.sha(raw_path),
        'base_guide_path':str(HERE/'merged-guide-rgba.png'),
        'candidate_path':str(HERE/'candidate-rgba.png'),'candidate_sha256':TOOLS.sha(HERE/'candidate-rgba.png'),
        'merged_model_pixels_used':int((effective>0).sum()),'model_alpha_discarded':True,
        'final_cap_core_original_rgba_exact':True,'final_hand_core_original_rgba_exact':True,
        'model_changed_pixels_outside_merged_edit_mask':0,
        'final_head_hands_boots_guide_rgba_exact':bool(np.array_equal(result[immutable],a[immutable])),
        'status':'combined body palette/proportion and cap-safe sword extension candidate; artistic acceptance pending'})
    (HERE/'final-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return Image.fromarray(result),report


def main():
    layers,report=build_layers()
    shutil.copy2(SOURCE,HERE/'original-rgba.png')
    guide,edit,guide_report=extend_sword_rgba(Image.open(SOURCE))
    guide.save(HERE/'guide-rgba.png');edit.save(HERE/'edit-mask.png')
    for key,name in {'source_cap':'source-cap-rgba.png','target_cap':'translated-cap-rgba.png',
                     'source_sword_mask':'source-sword-mask.png','middle_mask':'middle-mask.png',
                     'cap_mask':'translated-cap-mask.png','cleanup_mask':'exposed-cloth-cleanup-mask.png'}.items():
        Image.fromarray(layers[key]).save(HERE/name)
    (HERE/'pose-specific-cap-config.json').write_text(json.dumps(CONFIG,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'geometry-report.json').write_text(json.dumps(guide_report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'guide':str(HERE/'guide-rgba.png'),'mask':str(HERE/'edit-mask.png'),
                      'source_tip':report['source_tip_xy'],'target_tip':report['target_tip_xy'],
                      'shift':SHIFT,'cap_nonzero_pixels':report['cap_source_mask_nonzero_pixels'],
                      'cleanup_pixels':report['old_sword_exposed_cleanup_pixels']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='finalize':
        _,report=finalize_back_run(sys.argv[2]);print(json.dumps({'candidate':report['candidate_path'],'mask_pixels':report['merged_model_pixels_used']},ensure_ascii=False,indent=2))
    elif len(sys.argv)==3:
        _,_,report=merge_back_run(sys.argv[1],sys.argv[2]);print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        main()
