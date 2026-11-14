from pathlib import Path
import bpy,json,math
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(BASE.parent/'3d-locomotion-v4/raphael.blend'))
r=bpy.data.objects['raphael_Native65'];r.animation_data.action=None
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['UAL1__Sprint_Loop','UAL1__Jog_Fwd_Loop']
actions=[bpy.data.actions['idle'],bpy.data.actions['run']]+dst.actions
out={}
for a in actions:
 rows=[]
 for i in range(17):
  f=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/16
  for c in a.fcurves:
   path,attr=c.data_path.rsplit('.',1);getattr(r.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
  bpy.context.view_layer.update()
  names=['pelvis','spine_01','spine_02','spine_03','neck_01','Head','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r','upperarm_l','lowerarm_l','hand_l']
  rows.append({'frame':f,'bones':{n:{'head':list(r.matrix_world@r.pose.bones[n].head),'tail':list(r.matrix_world@r.pose.bones[n].tail),'matrix':list(map(list,r.matrix_world@r.pose.bones[n].matrix)),'q':list(r.pose.bones[n].rotation_quaternion)}for n in names}})
 out[a.name]=rows
 print('MOTION',a.name,list(a.frame_range),[(round(row['frame'],2),{n:[round(v,3)for v in row['bones'][n]['head']]for n in ['pelvis','Head','calf_l','foot_l']})for row in rows[::4]],flush=True)
(BASE/'motion-inspection.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
