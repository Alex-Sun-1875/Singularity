"""Composite a local Qwen raw retouch into a prepared RGBA body guide.

Import composite_local_raw(direction, raw_path, output_path=None), or use CLI.
No model/server/network call. All generated artifacts remain under this body/.
The guide owns geometry/alpha; raw contributes only RGB inside the prepared mask.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def composite_local_raw(direction,raw_path,output_path=None):
 if direction not in ('front','back'):raise ValueError('direction must be front or back')
 folder=HERE/direction
 raw_path=Path(raw_path).resolve()
 output=Path(output_path).resolve() if output_path else folder/'candidate-rgba.png'
 if not output.is_relative_to(HERE):raise ValueError('All composite outputs must stay inside body/')
 if output==raw_path:raise ValueError('The actual raw output must never be overwritten')
 for reserved in ['guide-rgba.png','original-rgba.png','reference-standing-rgba.png','edit-mask.png','all-protection-mask.png']:
  if output==(folder/reserved).resolve():raise ValueError('Do not overwrite prepared inputs')
 raw_sha=sha(raw_path)
 with Image.open(raw_path) as raw_im:
  if raw_im.size!=(512,768):raise ValueError('Raw output must be exact 512x768; no per-bbox resizing')
  raw_mode=raw_im.mode
  raw=np.asarray(raw_im.convert('RGB')).astype(np.float64)
 guide=np.asarray(Image.open(folder/'guide-rgba.png').convert('RGBA'))
 mask=np.asarray(Image.open(folder/'edit-mask.png').convert('L')).astype(np.float64)/255
 protected=np.asarray(Image.open(folder/'all-protection-mask.png').convert('L'))>0
 if np.any(mask[protected]):raise ValueError('Prepared mask intersects a protected region')
 # Raw alpha is intentionally ignored: deterministic guide geometry/alpha is
 # already reviewed separately. This also supports native Qwen RGB VAE output.
 weight=mask*(guide[...,3]>0)
 candidate=guide.copy()
 candidate[...,:3]=np.uint8(np.clip(np.rint(guide[...,:3]*(1-weight[...,None])+raw*weight[...,None]),0,255))
 candidate[protected]=guide[protected]
 # At fully transparent pixels leave original RGB bytes exactly as prepared.
 outside=weight==0
 assert np.array_equal(candidate[outside],guide[outside])
 assert np.array_equal(candidate[protected],guide[protected])
 assert np.array_equal(candidate[...,3],guide[...,3])
 output.parent.mkdir(parents=True,exist_ok=True)
 Image.fromarray(candidate).save(output)
 assert sha(raw_path)==raw_sha
 original=np.asarray(Image.open(folder/'original-rgba.png').convert('RGBA'))
 locks={}
 for label,name in [('arms_hands','arms-hands-protection-mask.png'),('boots','boots-protection-mask.png'),('weapon','weapon-protection-mask.png')]:
  roi=np.asarray(Image.open(folder/name).convert('L'))>0
  locks[label]=bool(np.array_equal(candidate[roi],original[roi]))
  assert locks[label]
 report={'direction':direction,'raw_model_path':str(raw_path),'raw_model_sha256':raw_sha,'raw_mode':raw_mode,
  'output_path':str(output),'output_sha256':sha(output),'new_model_inference':False,'cloud_generation':False,'production_modified':False,
  'composition':'Local RGB feathered composite only inside prepared edit-mask; alpha and world geometry owned entirely by deterministic RGBA guide; all independent protected parts copied from guide last',
  'guide_rgba_sha256':sha(folder/'guide-rgba.png'),'mask_sha256':sha(folder/'edit-mask.png'),
  'raw_file_unchanged':True,'guide_alpha_exact':True,'outside_mask_guide_rgba_exact':True,
  'protected_guide_rgba_exact':True,'protected_original_rgba_exact':locks,
  'model_blend_pixels':int((weight>0).sum()),'actual_changed_rgba_pixels':int(np.any(candidate!=guide,axis=-1).sum()),
  'foot_anchor_xy':[256,712],'status':'provisional composite; visual artistic review required before approval, no runtime installation'}
 output.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--direction',choices=['front','back'],required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path)
 a=p.parse_args();print(json.dumps(composite_local_raw(a.direction,a.raw,a.output),ensure_ascii=False,indent=2))
