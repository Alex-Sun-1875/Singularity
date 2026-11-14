"""Upright running from existing CC0 Sprint_Loop; native Blender IK and FK only."""
from pathlib import Path
import bpy,json,sys,hashlib,math,statistics,copy
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v7'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];feet=[o for o in objects if o.get('nativePart')=='feet']
changed=['run','run_staff'];leg_bones=['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
body_bones=['pelvis','spine_01','spine_02','spine_03','neck_01','Head','clavicle_l','clavicle_r']
def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def mh(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def pose():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}
def restore(v,update=True):
 for n,(l,q,s)in v.items():
  p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.location=l;p.rotation_quaternion=q;p.scale=s
 if update:bpy.context.view_layer.update()
def sample(a,f):
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update();return pose()
def wm(n):return rig.matrix_world@rig.pose.bones[n].matrix
def meanq(qs):
 anchor=qs[0];v=Vector((0,0,0,0))
 for q in qs:q=q.copy();q.make_compatible(anchor);v+=Vector(q)
 q=Quaternion(v);q.normalize();return q
foot_indices={}
for o in feet:
 group_sides={g.index:('l'if g.name.endswith('_l')else'r'if g.name.endswith('_r')else'')for g in o.vertex_groups}
 foot_indices[o.name]={s:[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if group_sides[g.group]==s)>.5]for s in ['l','r']}
def floors():
 result={'l':1e9,'r':1e9};deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  e=o.evaluated_get(deps);m=e.to_mesh()
  for side in result:result[side]=min(result[side],min((e.matrix_world@m.vertices[i].co).z for i in foot_indices[o.name][side]))
  e.to_mesh_clear()
 return result
def set_world_rotation(name,q):
 p=rig.pose.bones[name];m=rig.matrix_world@p.matrix;p.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(m.translation,q,m.to_scale());bpy.context.view_layer.update()
before_actions={a.name:ah(a)for a in bpy.data.actions};mesh_hashes={o.name:mh(o)for o in objects};bind=pipeline.skeleton(rig)
neutral=sample(bpy.data.actions['idle'],0);neutral_world={n:wm(n).copy()for n in body_bones}
old_rows=[]
for i in range(57):
 sample(bpy.data.actions['run'],i*.5);old_rows.append({n:wm(n).translation.copy()for n in ['pelvis','Head','calf_l','calf_r']})
staff_samples=[sample(bpy.data.actions['run_staff'],i*.5*28/20)for i in range(41)]
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['UAL1__Sprint_Loop']
source=dst.actions[0];source_hash=ah(source);frames=[i*.5 for i in range(41)];raw=[];world=[];raw_floor=[]
for f in frames:
 raw.append(sample(source,f));world.append({n:wm(n).copy()for n in ['pelvis','spine_03','neck_01','Head','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r']});raw_floor.append(floors())
bpy.data.actions.remove(source)
means={n:meanq([v[n][1]for v in raw[:-1]])for n in body_bones};center=sum((w['pelvis'].translation for w in world[:-1]),Vector())/(len(world)-1)
base_floor=min(v for r in raw_floor for v in r.values());velocities=[]
for side in ['l','r']:
 for i,(a,b)in enumerate(zip(world,world[1:])):
  speed=(b['foot_'+side].translation.y-a['foot_'+side].translation.y)*60
  if speed>.5 and max(raw_floor[i][side],raw_floor[i+1][side])-base_floor<.08:velocities.append(speed)
raw_speed=statistics.median(velocities);arc_scale=5.2/raw_speed
print('SPRINT_STRIDE',raw_speed,arc_scale,'floor',base_floor,flush=True)
assert .5<arc_scale<1.5,(raw_speed,arc_scale)

(BASE/'raw-contact.json').write_text(json.dumps([{'frame':f,'floor':fl,'feet':{s:list(w['foot_'+s].translation)for s in ['l','r']}}for f,fl,w in zip(frames,raw_floor,world)],indent=2))
