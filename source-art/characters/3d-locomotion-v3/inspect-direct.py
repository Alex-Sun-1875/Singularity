from pathlib import Path
import bpy,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-locomotion-v2/raphael.blend'))
r=bpy.data.objects['raphael_Native65'];s=bpy.context.scene
names=['root','pelvis','spine_01','spine_02','spine_03','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r','upperarm_l','lowerarm_l','hand_l']
out={'world':list(map(list,r.matrix_world)),'bones':{},'clips':{}}
for n in names:
 b=r.data.bones.get(n)
 if b:out['bones'][n]={'head':list(b.head_local),'tail':list(b.tail_local),'matrix':list(map(list,b.matrix_local)),'parent':b.parent.name if b.parent else None,'length':b.length}
for name in ['idle','walk','run','walk_staff','run_staff']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out['clips'][name]=[]
 for i in range(9):
  f=float(a.frame_range[1])*i/8;r.animation_data.action=None
  for c in a.fcurves:
   prop=c.data_path.rsplit('.',1);target=r.path_resolve(prop[0]);getattr(target,prop[1])[c.array_index]=c.evaluate(f)
  bpy.context.view_layer.update()
  out['clips'][name].append({'frame':f,'bones':{n:{'head':list(r.matrix_world@r.pose.bones[n].head),'tail':list(r.matrix_world@r.pose.bones[n].tail),'q':list(r.pose.bones[n].rotation_quaternion),'loc':list(r.pose.bones[n].location)}for n in names if n in r.pose.bones}})
(BASE/'rig-direct.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('DIRECT',[(n,[(x['frame'],x['bones']['foot_l']['head'])for x in a[::4]])for n,a in out['clips'].items()])
