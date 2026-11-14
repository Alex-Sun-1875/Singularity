"""Compare complete existing authored running loops on the production rig."""
from pathlib import Path
import bpy,sys,json,math
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_native_motions as motion
bpy.ops.wm.open_mainfile(filepath=str(BASE.parent/'3d-locomotion-v7/raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None
original=set(bpy.data.actions);candidates={'v7':bpy.data.actions['run']}
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend')) as (src,dst):
 dst.actions=['UAL1__Sprint_Loop','UAL1__Jog_Fwd_Loop']
for a in dst.actions:candidates[a.name]=a
motion.retarget_setup()
path=ROOT/'src/.tools/research-animation-kaykit/free-1.1/KayKit_Character_Animations_1.1/Animations/gltf/Rig_Medium/Rig_Medium_MovementBasic.glb'
objects,actions=motion.imported(path);source=next(o for o in objects if o.type=='ARMATURE')
for raw in [a for a in actions if a.name.split('|')[-1] in ['Running_A','Running_B']]:
 work=source.copy();work.data=source.data.copy();bpy.context.collection.objects.link(work)
 a=raw.copy();motion.assign(work,a)
 for c in a.fcurves:
  for k in c.keyframe_points:k.co.x+=1;k.handle_left.x+=1;k.handle_right.x+=1
 motion.reset(rig);rig.animation_data.action=None
 bpy.ops.object.select_all(action='DESELECT');work.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 saved_scale=rig.scale.copy();rig.scale=(1,1,1)
 result=bpy.ops.mcp.retarget_selected_to_active(useAutoSource=False,useAutoTarget=False,useAutoScale=True,useCenterAnimation=False,useAllFrames=False,startFrame=1,endFrame=round(raw.frame_range[1]+1))
 rig.scale=saved_scale
 assert result=={'FINISHED'}
 output=rig.animation_data.action;output.name='KayKit__'+raw.name.split('|')[-1];output.use_fake_user=True;candidates[output.name]=output
 bpy.data.objects.remove(work,do_unlink=True)
for o in objects:bpy.data.objects.remove(o,do_unlink=True)
motion.reset(rig);rig.animation_data.action=None
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
saved_scale=rig.scale.copy();rig.scale=(1,1,1)
result=bpy.ops.mcp.load_and_retarget(filepath=str(ROOT/'source-art/characters/mocap/cmu/16_36.bvh'),useAutoTarget=False,useAutoSource=True,useAutoScale=True,useSimplify=False,useBendPositive=False,useCenterAnimation=False)
rig.scale=saved_scale
assert result=={'FINISHED'}
a=rig.animation_data.action;a.name='CMU__16_36';a.use_fake_user=True;candidates[a.name]=a
rig.animation_data.action=None
names=['pelvis','neck_01','Head','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r','upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r']
report={}
for label,a in candidates.items():
 start,end=a.frame_range
 if label.startswith('KayKit'):start=1
 if label.startswith('CMU'):start,end=2,26
 rows=[]
 for i in range(81):
  motion.reset(rig)
  f=start+(end-start)*i/80
  for c in a.fcurves:
   path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
  bpy.context.view_layer.update()
  rows.append({'frame':f,'bones':{n:list(rig.matrix_world@rig.pose.bones[n].head)for n in names}})
 report[label]={'range':[start,end],'rows':rows}
(BASE/'candidates.json').write_text(json.dumps(report,indent=2))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'candidates.blend'),relative_remap=False)
print('CANDIDATES_READY',[(k,v['range'])for k,v in report.items()],flush=True)
