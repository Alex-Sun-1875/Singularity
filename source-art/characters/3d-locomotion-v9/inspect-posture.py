"""Read the existing authored body curves before adapting the posture."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(BASE.parent/'3d-locomotion-v8/raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None
names=['root','pelvis','spine_01','spine_02','spine_03','neck_01','Head','thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r','upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r','clavicle_l','clavicle_r']
def sample(a,f):
 for p in rig.pose.bones:p.matrix_basis.identity();p.rotation_mode='QUATERNION'
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update()
 return {n:rig.matrix_world@rig.pose.bones[n].matrix for n in names}
neutral=sample(bpy.data.actions['idle'],0)
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['UAL1__Walk_Loop']
with bpy.data.libraries.load(str(BASE.parent/'3d-locomotion-v8/candidates.blend'))as(src,dst):dst.actions=['CMU__16_36']
out={}
for label,a,start,end in [('walk',bpy.data.actions['walk'],0,40),('run',bpy.data.actions['run'],0,20),('rawWalk',bpy.data.actions['UAL1__Walk_Loop'],0,40),('cmuRun',dst.actions[0],2,26)]:
 rows=[]
 for i in range(81):
  f=start+(end-start)*i/80;m=sample(a,f);angles={}
  for n in names:
   delta=m[n].to_quaternion()@neutral[n].to_quaternion().inverted();up=delta@Vector((0,0,1));front=delta@Vector((0,-1,0))
   angles[n]={'pitch':math.degrees(math.atan2(-up.y,up.z)),'yaw':math.degrees(math.atan2(front.x,-front.y)),'roll':math.degrees(math.atan2(up.x,up.z))}
  rows.append({'frame':f,'points':{n:list(m[n].translation)for n in names},'angles':angles})
 out[label]=rows
 print('POSTURE',label,{n:{c:[round(min(r['angles'][n][c]for r in rows),2),round(max(r['angles'][n][c]for r in rows),2)]for c in ['pitch','yaw','roll']}for n in ['pelvis','spine_01','spine_03','Head']},flush=True)
(BASE/'posture-before.json').write_text(json.dumps(out,indent=2))
