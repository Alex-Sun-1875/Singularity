from pathlib import Path
import bpy,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-locomotion-v2/raphael.blend'))
r=bpy.data.objects['raphael_Native65'];r.animation_data.action=None
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):
 print('LIBRARY_ACTIONS',src.actions);dst.actions=[n for n in src.actions if n in ['walk','run']]
for a in dst.actions:
 print('LIB',a.name,list(a.frame_range))
 for f in [0,a.frame_range[1]/2,a.frame_range[1]]:
  for c in a.fcurves:
   path,attr=c.data_path.rsplit('.',1);getattr(r.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
  bpy.context.view_layer.update()
  print('FRAME',f,{n:[round(x,4)for x in r.matrix_world@r.pose.bones[n].head]for n in ['root','pelvis','calf_l','foot_l','foot_r']})
