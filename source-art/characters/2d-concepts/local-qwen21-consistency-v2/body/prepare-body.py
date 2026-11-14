"""Prepare local Qwen body guides with mature SciPy resampling, no model/network calls.
All writes stay inside this body/ directory. Production assets are read-only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PILOT=HERE.parent.parent/'local-qwen21-turbo-pilot-v1'
ORIGINALS=PILOT/'originals-512x768'
W,H=512,768
SPECS={
 'front': {
  'body':[(231,207),(305,207),(317,253),(320,327),(337,372),(337,425),(325,455),(315,502),(304,554),(296,625),(233,625),(233,562),(184,556),(179,493),(180,431),(191,375),(214,334),(221,268)],
  'arms':[
   [(188,204),(231,204),(239,251),(246,275),(279,279),(281,350),(242,364),(210,361),(172,353),(142,339),(130,315),(142,280),(163,242)],
   [(306,202),(345,210),(366,260),(381,318),(387,428),(334,433),(330,368),(317,324),(307,264)]],
  'boots':[
   [(187,547),(236,547),(245,581),(240,616),(225,633),(196,633),(185,609),(185,573)],
   [(230,614),(300,614),(300,724),(226,724)]],
  'weapon_lines': [([(199,124),(226,217)],30), ([(188,188),(236,180)],15)],
  'source_head':[(233,82),(273,83),(291,106),(296,140),(287,163),(281,177),(282,184),(270,194),(241,194),(231,184),(230,174),(221,157),(215,133),(215,111)],
  'old_head':[(247,81),(289,87),(309,119),(311,158),(300,180),(303,207),(232,207),(227,181),(222,143),(226,108)],
  'head_shift':[11,10],
  'source_waist_y':365,
  'belt_axis_x':268,
 },
 'back': {
  'body':[(215,201),(292,200),(310,238),(312,301),(325,344),(338,401),(326,448),(318,511),(324,541),(273,550),(264,636),(198,636),(191,548),(185,465),(181,403),(198,340),(210,279)],
  'arms':[
   [(166,201),(215,201),(220,257),(208,319),(190,374),(186,416),(130,419),(130,346),(141,278),(151,225)],
   [(295,202),(341,212),(365,243),(378,282),(379,321),(353,336),(313,320),(301,298)]],
  'boots':[
   [(267,535),(321,535),(331,572),(326,632),(314,676),(272,676),(263,635),(264,580)],
   [(205,624),(268,624),(274,722),(202,722)]],
  'weapon_lines': [([(311,127),(300,184),(205,421)],27), ([(278,181),(320,203)],15)],
  'source_head':[(229,81),(276,82),(291,104),(293,136),(283,157),(276,170),(278,181),(234,181),(225,168),(219,150),(212,126),(214,104)],
  'old_head':[(223,91),(269,94),(282,123),(282,165),(279,185),(287,206),(211,206),(211,181),(200,154),(199,125)],
  'head_shift':[-11,21],
  'source_waist_y':358,
  'belt_axis_x':258,
 }
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def shape(polygons=(),lines=()):
 im=Image.new('L',(W,H));d=ImageDraw.Draw(im)
 for poly in polygons:d.polygon(poly,fill=255)
 for pts,width in lines:d.line(pts,fill=255,width=width,joint='curve')
 return im

def bbox(a):
 yy,xx=np.nonzero(a)
 return None if len(xx)==0 else [int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1]

def warp(values,sy,order=1):
 yy,xx=np.indices((H,W),dtype=float)
 return ndimage.map_coordinates(values,[sy,xx],order=order,mode='constant',cval=0,prefilter=False)

def remap_rgba(image,source_y):
 a=np.asarray(image).astype(np.float64)/255
 # Premultiplied interpolation prevents transparent black/colour halos.
 p=a.copy();p[...,:3]*=p[...,3:4]
 q=np.stack([warp(p[...,c],source_y) for c in range(4)],axis=-1)
 q[...,:3]/=np.maximum(q[...,3:4],1/255)
 q[q[...,3]==0,:3]=0
 return np.uint8(np.clip(np.rint(q*255),0,255))

def replace_head(original,reference,spec):
 old=np.asarray(shape([spec['old_head']]))>0
 source_mask=shape([spec['source_head']])
 # Standalone approved head pixels retain the original alpha, scale and texture.
 patch=reference.copy()
 pa=np.asarray(patch).copy();pa[np.asarray(source_mask)==0]=0
 patch=Image.fromarray(pa)
 dx,dy=spec['head_shift']
 shifted=Image.new('RGBA',(W,H));shifted.alpha_composite(patch,(dx,dy))
 new=np.asarray(shifted)[:,:,3]>0
 base=np.asarray(original).copy();base[old]=0
 base=Image.alpha_composite(Image.fromarray(base),shifted)
 protection=Image.fromarray(np.uint8((old|new)*255)).filter(ImageFilter.MaxFilter(9))
 return base,protection,shifted

def audit():
 manifest=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/manifest.json'
 runtime=json.loads(manifest.read_text(encoding='utf-8'))
 provenance=json.loads((PILOT/'input-manifest.json').read_text(encoding='utf-8'))
 rows=[]
 for direction,runtime_direction in [('front','down'),('back','up')]:
  for state,key in [('standing','explore_idle_W01'),('run','explore_run_W01')]:
   item=provenance['originals'][f'{state}-{direction}']
   im=Image.open(item['rgba_canvas']['path']).convert('RGBA');a=np.asarray(im)
   bb=bbox(a[...,3]>=16);anybb=bbox(a[...,3]>0)
   act=runtime['actions'][key];upp=act['worldUnitsPerPixel']
   rows.append({'state':state,'direction':direction,'runtime_action':key,'runtime_image':act['image'],
    'runtime_world_units_per_pixel':upp,'source_canvas_scale':item['native_to_canvas_affine'][0],
    'required_canvas_scale_runtime_upp_times_400':upp*400,'alpha16_bounds_canvas':bb,'alpha_any_bounds_canvas':anybb,
    'alpha16_bbox_world_height':(bb[3]-bb[1])/400,'alpha16_crown_above_anchor_world':(712-bb[1])/400,
    'canvas_anchor_xy':[256,712],'source_rgba_sha256':sha(item['rgba_canvas']['path']),
    'runtime_png_sha256':sha(item['runtime_original']['path']),
    'source_original_sha256':sha(item['source_original']['path'])})
 result={'status':'read-only geometry audit; representative p0 body proportion guide, no runtime replacement',
  'conclusion':'Installed idle and run use action-wide UPP calibrated to a similar world height. No direction-specific scale error. Short-legged perception is body/leg projection, coat-hem and bent-leg pose; independently fitting alpha bounds would falsify scale and ground anchoring.',
  'canvas':{'size':[512,768],'pixels_per_world_unit':400,'foot_anchor_xy':[256,712]},
  'runtime_manifest_path':str(manifest),'runtime_manifest_sha256':sha(manifest),'measurements':rows,
  'method_choice':'Existing prepare-inputs.py supplies the world-scale/foot-anchor policy; its old full horizontal strip warp is rejected because it distorts hands/weapons. Installed Pillow/NumPy/SciPy ndimage.map_coordinates perform deterministic body-only premultiplied resampling. No dependencies installed.',
  'mature_components':{'Pillow':'HPND','NumPy':'BSD-3-Clause','SciPy':'BSD-3-Clause'},
  'art_review':'One necessary 880x790 local deterministic coordinate board was viewed through Codex cloud vision. No image generation, model call, server access or external upload by this preparation script. Runtime verification and artistic acceptance remain separate.',
  'production_modified':False}
 (HERE/'geometry-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return result

def prepare(direction):
 spec=SPECS[direction];out=HERE/direction;out.mkdir(parents=True,exist_ok=True)
 op=ORIGINALS/f'run-{direction}-p0-rgba.png';rp=ORIGINALS/f'standing-{direction}-p0-rgba.png'
 shutil.copy2(op,out/'original-rgba.png');shutil.copy2(rp,out/'reference-standing-rgba.png')
 original=Image.open(op).convert('RGBA');reference=Image.open(rp).convert('RGBA')
 headbase,headprotect,headlayer=replace_head(original,reference,spec)
 headlayer.save(out/'approved-head-layer-rgba.png');headprotect.save(out/'head-protection-mask.png')
 arms=shape(spec['arms']);boots=shape(spec['boots']);weapon=shape(lines=spec['weapon_lines'])
 arms.save(out/'arms-hands-protection-mask.png');boots.save(out/'boots-protection-mask.png');weapon.save(out/'weapon-protection-mask.png')
 # Original independently protected equipment/arm foreground wins at occlusions.
 fixed=np.maximum.reduce([np.asarray(x) for x in [arms,boots,weapon]])>0
 hb=np.asarray(headbase).copy();hb[fixed]=np.asarray(original)[fixed];headbase=Image.fromarray(hb)
 protect=np.maximum.reduce([np.asarray(x) for x in [headprotect,arms,boots,weapon]])>0
 # Protect the complete upper head/collar neighborhood and ground contact globally.
 protect[:205]=True;protect[724:]=True
 body=np.asarray(shape([spec['body']]))>0
 owner=body&~protect
 # Waist/belt/coat-hem translate rigidly -22px over the plateau; only torso and
 # cloth-leg transitions resample. No complete row or arm/weapon is stretched.
 sy_knots=np.array([0,210,330,435,618,768],float)
 dy_knots=np.array([0,210,308,413,618,768],float)
 yy,xx=np.indices((H,W),dtype=float)
 source_y=np.interp(yy,dy_knots,sy_knots)
 # Copy nearest valid cloth beneath independent occluders before deforming the
 # body layer. This standard SciPy distance-transform fill prevents transparent
 # holes where an unmoved hand/sword overlaps a shifted torso. The copied pixels
 # are only a provisional seam underlay; Qwen receives these areas in its mask.
 hb=np.asarray(headbase).copy()
 cloth=owner&(hb[...,3]>128)
 _,nearest=ndimage.distance_transform_edt(~cloth,return_indices=True)
 inferred_source=body&protect
 hb[inferred_source]=hb[nearest[0][inferred_source],nearest[1][inferred_source]]
 deformed=remap_rgba(Image.fromarray(hb),source_y)
 dest_owner=warp(body.astype(float),source_y,order=0)>.5
 dest_owner &= ~protect
 changes=owner|dest_owner
 result=np.asarray(headbase).copy();result[changes]=0
 result[dest_owner]=deformed[dest_owner]
 result[protect]=np.asarray(headbase)[protect]
 guide=Image.fromarray(result)
 guide.save(out/'guide-rgba.png')
 np.savez_compressed(out/'geometry-control-points.npz',source_y=sy_knots,destination_y=dy_knots)
 Image.fromarray(np.uint8(changes*255)).save(out/'geometry-change-mask.png')
 Image.fromarray(np.uint8(protect*255)).save(out/'all-protection-mask.png')
 # Qwen may retouch only collar/join, waist/hip and knees. The deterministic
 # changed silhouette already carries the proportion; VAE output never replaces
 # the complete image. Expand by 2 px to include local silhouette seam repair.
 support=ndimage.binary_dilation((result[...,3]>8)|(np.asarray(original)[...,3]>8),iterations=3)
 scope=((yy>=299)&(yy<466))|((yy>=479)&(yy<616))|((yy>=204)&(yy<238))
 allowed=ndimage.binary_dilation(changes,iterations=3)&scope&support&~protect
 inferred_dest=(warp(inferred_source.astype(float),source_y,order=0)>.5)&dest_owner
 allowed|=ndimage.binary_dilation(inferred_dest,iterations=2)&support&~protect
 # Collar seam is independent of the body owner, with a small central envelope.
 collar=(yy>=204)&(yy<232)&(xx>=229 if direction=='front' else xx>=212)&(xx<=310 if direction=='front' else xx<=291)
 allowed|=collar&support&~protect
 softened=ndimage.gaussian_filter(allowed.astype(float),.9)
 softened=np.minimum(softened,allowed.astype(float))
 softened[protect]=0
 mask=Image.fromarray(np.uint8(np.rint(255*softened)))
 mask.save(out/'edit-mask.png')
 orientation='正面向镜头' if direction=='front' else '背面远离镜头'
 prompt=f'''图1是已经用原始像素做好比例引导的{orientation}跑步角色，图2是已验收站姿设计参考。只修补图1遮罩里的领口接缝、上提后的腰带与髋部衣摆连接、裤裆及膝部布料过渡。严格保持图1已经确定的轮廓、跑步相位、前倾和屈腿姿态，腰线已上提约22像素，腿部视觉比例适度修长；不要再增加整体身高或拉满画布。头部已经按图2原像素同尺度复用，不要改变头型、脸、银色短卷发、头大小或位置。完整保留原袖子、双手手指、护腕、剑柄护手剑鞘、包袋与两只靴子的形状和位置；不得重画或拉伸装备。衣服为图2相同的暗酒红、金线刺绣与深灰袖子，裤子同为暗炭灰；保留原布料褶皱和明暗，不要把裤子变成明亮灰白色。只抚平局部接缝，不增删衣饰、不扩大躯干、不改变步态，不复制站姿。保持512×768、原脚部锚点(256,712)、单个完整角色和透明背景，输出RGBA PNG。'''
 (out/'prompt.txt').write_text(prompt+'\n',encoding='utf-8')
 src=np.asarray(original);dst=np.asarray(guide)
 for name,m in [('arms_hands',np.asarray(arms)>0),('boots',np.asarray(boots)>0),('weapon',np.asarray(weapon)>0)]:
  assert np.array_equal(src[m],dst[m]),(direction,name)
 assert not np.any(np.asarray(mask)[protect])
 headsrc=np.asarray(reference)
 hl=np.asarray(headlayer);opaque=hl[...,3]>0
 dx,dy=spec['head_shift'];ys,xs=np.where(opaque)
 assert np.array_equal(hl[ys,xs],headsrc[ys-dy,xs-dx])
 waist=spec['source_waist_y'];target_waist=float(np.interp(waist,sy_knots,dy_knots))
 report={'direction':direction,'status':'single-frame local deterministic guide; requires native masked Qwen seam retouch and final artistic review',
  'paths':{k:str((out/v).resolve()) for k,v in {'original':'original-rgba.png','guide':'guide-rgba.png','mask':'edit-mask.png','reference':'reference-standing-rgba.png','prompt':'prompt.txt'}.items()},
  'source_waist_y':waist,'guide_waist_y':target_waist,'waist_raise_px':waist-target_waist,
  'head':{'method':'Approved standing head pixels 1:1 integer translation, no resampling or regeneration','translation_xy':spec['head_shift'],'scale':1,'source_polygon':spec['source_head'],'nontransparent_head_layer_pixels_exact_reference':True,'running_head_landing_and_forward_body_lean_preserved':True},
  'body_mapping':{'source_y_knots':sy_knots.tolist(),'destination_y_knots':dy_knots.tolist(),'x_coordinates':'unchanged','waist_coat_plateau':'source y330..435 rigid integer translation -22px; complete arms/weapons excluded','waist_to_fixed_ankle_y618_gain_percent':round(100*22/(618-waist),3),'overall_height_target':'unchanged head landing, original ground boots and anchor; no bbox fit'},
  'protection':{'original_arms_hands_pixels_exact':True,'original_boot_pixels_exact':True,'original_weapon_pixels_exact':True,'mask_intersection_protected_pixels':int((np.asarray(mask)[protect]>0).sum()),'head_hands_equipment_independent_masks':True},
  'geometry_changed_pixels':int(np.any(src!=dst,axis=-1).sum()),'qwen_edit_mask_nonzero_pixels':int((np.asarray(mask)>0).sum()),
  'occlusion_underlay':{'method':'SciPy distance_transform_edt nearest valid original cloth pixels under independent original hand/sword/boot layers; Qwen mask includes newly revealed underlay seams','source_pixels':int(inferred_source.sum()),'visible_destination_pixels':int(inferred_dest.sum())},
  'foot_anchor_xy':[256,712],'native_runtime_scale_modified':False,'production_modified':False,'new_model_inference':False,'cloud_generation':False,
  'limitations':['Body-only guide is provisional until final local Qwen output and composite visual review; measured projected garment distance is not anatomical bone length.','Lifted boot stays exactly original; the bent leg therefore keeps phase/foot placement, with larger local knee transition than the grounded leg.','Back-run sword remains original in this body guide; a separate independent sword layer can be integrated afterward.'],
  'sha256':{f:sha(out/f) for f in ['original-rgba.png','reference-standing-rgba.png','guide-rgba.png','edit-mask.png','prompt.txt']}}
 (out/'geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--direction',choices=['front','back','all'],default='all');args=p.parse_args()
 audit()
 for d in ['front','back'] if args.direction=='all' else [args.direction]:
  r=prepare(d);print(json.dumps({'direction':d,**r['paths'],'waist_raise_px':r['waist_raise_px'],'leg_gain_percent':r['body_mapping']['waist_to_fixed_ankle_y618_gain_percent']},ensure_ascii=False),flush=True)
