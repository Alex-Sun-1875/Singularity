"""Repair the isolated pasted-head/neck seam using original local pixels.

Frozen guides, actual Qwen raw files and root final/ are read-only. All repair
layers, masks and previews are written beside this module under neck-repair/.
Import apply_neck_repair(image, direction): image is a PIL Image or local path;
returns (repaired PIL RGBA image, report) without writing or mutating the input.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent

SPECS={
 'front':{
  'polygon':[(234,181),(300,181),(307,190),(315,202),(315,212),(305,223),(293,242),(251,242),(237,224),(226,210),(225,199)],
  'start_y':185,'full_y':191,'fade_y':228,'end_y':243,
  'neck_translation_y':0,
 },
 'back':{
  'polygon':[(215,175),(278,175),(287,187),(295,203),(296,219),(280,234),(220,234),(204,220),(202,202),(208,187)],
  'start_y':178,'full_y':184,'fade_y':219,'end_y':235,
  'neck_translation_y':7,
 }
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def polygon(points,size=(512,768)):
 image=Image.new('L',size);ImageDraw.Draw(image).polygon(points,fill=255)
 return np.asarray(image)>0

def prepare_repair(direction):
 if direction not in SPECS:raise ValueError('direction must be front or back')
 spec=SPECS[direction];folder=HERE/direction;out=HERE/'neck-repair'/direction
 out.mkdir(parents=True,exist_ok=True)
 original=Image.open(folder/'original-rgba.png').convert('RGBA')
 guide=Image.open(folder/'guide-rgba.png').convert('RGBA')
 layer=np.asarray(original).copy();yy,xx=np.indices(layer.shape[:2])
 approved_head=np.asarray(Image.open(folder/'approved-head-layer-rgba.png').convert('RGBA'))
 if direction=='front':
  # Keep all copied hair/face/jaw pixels through y185 exactly. Only the copied
  # standing collar below the jaw is replaced by the original running neck.
  core=(approved_head[...,3]>0)&(yy<=185)
 else:
  # The rear run head lands lower than standing; move the original run collar
  # rigidly 7px down to sit beneath the copied nape, then feather into unmoved
  # original shoulders. This retains the original narrow gold collar shape.
  dy=spec['neck_translation_y'];translated=Image.new('RGBA',original.size)
  translated.alpha_composite(original,(0,dy))
  collar=polygon([(220,175),(274,175),(283,185),(282,203),(272,212),(220,212),(211,201),(212,185)])
  inward=np.minimum(ndimage.distance_transform_edt(collar)/3,1)
  blend=inward*np.clip((yy-177)/5,0,1)*np.clip((214-yy)/7,0,1)
  base=np.asarray(original).astype(float);moved=np.asarray(translated).astype(float)
  # The unmoved original shoulder layer under the shifted collar fills sides;
  # do not replace shoulder coverage with transparent background from the crop.
  blend*=moved[...,3]/255
  layer=np.uint8(np.clip(np.rint(base*(1-blend[...,None])+moved*blend[...,None]),0,255))
  # Shifted collar AA must not punch translucent pinholes into the opaque
  # original shoulder underlay.
  layer[...,3]=np.maximum(layer[...,3],np.asarray(original)[...,3])
  rgb=approved_head[...,:3].astype(int)
  neutral=(rgb.max(axis=-1)-rgb.min(axis=-1)<45)&(rgb.max(axis=-1)>35)
  core=(approved_head[...,3]>0)&((yy<=178)|((yy<=183)&neutral))
 allowed=polygon(spec['polygon'])
 feather=np.minimum(ndimage.distance_transform_edt(allowed)/2,1)
 feather*=np.clip((yy-spec['start_y'])/(spec['full_y']-spec['start_y']),0,1)
 feather*=np.clip((spec['end_y']-yy)/(spec['end_y']-spec['fade_y']),0,1)
 fixed=np.zeros((768,512),bool)
 for name in ['arms-hands-protection-mask.png','boots-protection-mask.png','weapon-protection-mask.png']:
  fixed|=np.asarray(Image.open(folder/name).convert('L'))>0
 fixed|=core
 feather[fixed]=0
 mask=np.uint8(np.rint(255*feather))
 Image.fromarray(layer).save(out/'repair-layer-rgba.png')
 Image.fromarray(mask).save(out/'repair-mask.png')
 Image.fromarray(np.uint8(core*255)).save(out/'head-hair-face-core-mask.png')
 Image.fromarray(np.uint8(fixed*255)).save(out/'repair-protection-mask.png')
 # Diagnostic: frozen guide had transparent rectangular sides below the pasted
 # head. The source run layer provides continuous neck/shoulder coverage there.
 before=np.asarray(guide)
 old_holes=(before[...,3]<64)&(layer[...,3]>220)&(mask>0)
 report={'direction':direction,'method':'Local original running neck/collar/shoulder pixels with a narrow inward feathered polygon; no generation, no model calls; copied standing hair/face core untouched',
  'source_original_sha256':sha(folder/'original-rgba.png'),'frozen_guide_sha256':sha(folder/'guide-rgba.png'),
  'layer_sha256':sha(out/'repair-layer-rgba.png'),'mask_sha256':sha(out/'repair-mask.png'),
  'repair_mask_bounds_xyxy':None,'neck_collar_translation_y':spec['neck_translation_y'],
  'potential_original_opaque_coverage_hole_pixels':int(old_holes.sum()),'protected_intersection_pixels':int((mask[fixed]>0).sum()),
  'preserve':'Exact current candidate pixels in approved standing hair/face core, hands/arms, boots, weapon; waist and legs lie entirely outside repair mask',
  'production_modified':False,'new_model_inference':False,'cloud_generation':False,'status':'Local neck seam repair only; frozen guide and raw remain unchanged'}
 ys,xs=np.where(mask>0);report['repair_mask_bounds_xyxy']=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
 (out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return out

def apply_neck_repair(image,direction):
 """Return (repaired RGBA PIL Image, report); never mutate/write the input."""
 folder=HERE/'neck-repair'/direction
 if not (folder/'repair-layer-rgba.png').exists():prepare_repair(direction)
 before=Image.open(image).convert('RGBA') if isinstance(image,(str,Path)) else image.convert('RGBA').copy()
 if before.size!=(512,768):raise ValueError('Expected exact512x768 candidate; no resize')
 patch=Image.open(folder/'repair-layer-rgba.png').convert('RGBA')
 mask=Image.open(folder/'repair-mask.png').convert('L')
 # RGBA crossfade is deliberate: the repair source supplies actual original
 # opaque neck/shoulders where the old head removal left transparency.
 repaired=Image.composite(patch,before,mask)
 a=np.asarray(before);b=np.asarray(repaired);m=np.asarray(mask)
 fixed=np.asarray(Image.open(folder/'repair-protection-mask.png').convert('L'))>0
 assert np.array_equal(a[m==0],b[m==0])
 assert np.array_equal(a[fixed],b[fixed])
 assert np.array_equal(a[300:],b[300:])
 report=json.loads((folder/'repair-report.json').read_text(encoding='utf-8'))
 report.update({'changed_pixels':int(np.any(a!=b,axis=-1).sum()),
  'outside_repair_mask_rgba_exact':True,'protected_hair_face_hands_boots_weapon_rgba_exact':True,
  'waist_legs_rgba_exact':True,'guide_modified':False,'raw_modified':False})
 return repaired,report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--direction',choices=['front','back','all'],default='all');p.add_argument('--input',type=Path);a=p.parse_args()
 for direction in ['front','back'] if a.direction=='all' else [a.direction]:
  out=prepare_repair(direction)
  source=a.input if a.input else HERE.parent/'final'/f'run-{direction}.png'
  before=sha(source)
  result,report=apply_neck_repair(source,direction);result.save(out/'repaired-preview.png')
  (out/'applied-preview-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  assert before==sha(source)
  old=np.asarray(Image.open(source).convert('RGBA'));new=np.asarray(result)
  print(json.dumps({'direction':direction,'layer':str(out/'repair-layer-rgba.png'),'mask':str(out/'repair-mask.png'),'preview':str(out/'repaired-preview.png'),'changed_pixels':int(np.any(old!=new,axis=-1).sum()),'input_unchanged':True},ensure_ascii=False))
