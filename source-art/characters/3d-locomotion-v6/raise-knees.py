"""Explicit forward thigh lift over the existing v5 run. Native Blender FK only.
The body and support-foot curves are retained; only thigh/foot rotations change.
"""
from pathlib import Path
import bpy,json,hashlib,math,sys,copy,statistics
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v5'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];feet=[o for o in objects if o.get('nativePart')=='feet']
changed=['run','run_staff'];edited=['thigh_l','thigh_r','foot_l','foot_r']
def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def mh(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def sample(a,f):
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update()
def wm(n):return rig.matrix_world@rig.pose.bones[n].matrix
def set_rotation(n,q):
 p=rig.pose.bones[n];m=wm(n);p.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(m.translation,q,m.to_scale());bpy.context.view_layer.update()
foot_indices={}
for o in feet:
 sides={g.index:('l'if g.name.endswith('_l')else'r'if g.name.endswith('_r')else'')for g in o.vertex_groups}
 foot_indices[o.name]={s:[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if sides[g.group]==s)>.5]for s in ['l','r']}
def floors():
 out={'l':1e9,'r':1e9};deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  e=o.evaluated_get(deps);m=e.to_mesh()
  for s in out:out[s]=min(out[s],min((e.matrix_world@m.vertices[i].co).z for i in foot_indices[o.name][s]))
  e.to_mesh_clear()
 return out
def smooth(x):
 x=max(0,min(1,x));return x*x*x*(x*(x*6-15)+10)
def lift_weight(frame,side,floor):
 phase=(frame+(10 if side=='r'else 0))%20
 rise=smooth((phase-9.5)/3.0);fall=1-smooth((phase-15.0)/4.0)
 return rise*fall*smooth((floor-.012)/.09)
def flex(side):
 v=wm('calf_'+side).translation-wm('thigh_'+side).translation
 return math.degrees(math.atan2(-v.y,-v.z))
def protected_hash(a):
 paths={'pose.bones["'+n+'"].rotation_quaternion'for n in edited}
 return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves if c.data_path not in paths]).encode()).hexdigest()
before={a.name:ah(a)for a in bpy.data.actions};meshes={o.name:mh(o)for o in objects};bind=pipeline.skeleton(rig);reports=[]
for name in changed:
 old=bpy.data.actions[name];protected=protected_hash(old);frames=[i*.25 for i in range(81)];baked=[];rows=[]
 for f in frames:
  sample(old,f);source_floor=floors();old_head=wm('Head').copy();old_pelvis=wm('pelvis').copy()
  old_flex={s:flex(s)for s in ['l','r']};old_knees={s:list(wm('calf_'+s).translation)for s in ['l','r']}
  foot_q={s:wm('foot_'+s).to_quaternion()for s in ['l','r']};weights={}
  for side in ['l','r']:
   weight=lift_weight(f,side,source_floor[side]);weights[side]=weight
   if weight<1e-8:continue
   thigh=wm('thigh_'+side);direction=wm('calf_'+side).translation-thigh.translation
   target=Vector((0,-math.sin(math.radians(88)),-math.cos(math.radians(88))))
   delta=direction.normalized().rotation_difference(target)
   q=thigh.to_quaternion();set_rotation('thigh_'+side,q.slerp(delta@q,weight))
   # Preserve the native ankle pitch while the connected thigh/calf chain rises.
   set_rotation('foot_'+side,foot_q[side])
  assert (wm('Head').translation-old_head.translation).length<1e-6
  assert (wm('pelvis').translation-old_pelvis.translation).length<1e-6
  floor=floors();row={'frame':f,'weight':weights,'beforeFlex':old_flex,'afterFlex':{s:flex(s)for s in ['l','r']},'beforeKnees':old_knees,'knees':{s:list(wm('calf_'+s).translation)for s in ['l','r']},'hips':{s:list(wm('thigh_'+s).translation)for s in ['l','r']},'ankles':{s:list(wm('foot_'+s).translation)for s in ['l','r']},'beforeFloor':source_floor,'floor':floor}
  rows.append(row);baked.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in edited})
 assert min(v for r in rows for v in r['floor'].values())>-.003
 assert max(r['afterFlex'][s]for r in rows for s in ['l','r'])>86
 old.name='REPLACED_'+name;a=old.copy();a.name=name;a.use_fake_user=True;rig.animation_data.action=a
 paths={'pose.bones["'+n+'"].rotation_quaternion'for n in edited}
 for c in list(a.fcurves):
  if c.data_path in paths:a.fcurves.remove(c)
 previous={}
 for f,values in zip(frames,baked):
  for n,q in values.items():
   q=q.copy();q.normalize()
   if n in previous:q.make_compatible(previous[n])
   previous[n]=q.copy();rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 for c in a.fcurves:
  if c.data_path in paths:
   for k in c.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None;assert protected_hash(a)==protected;bpy.data.actions.remove(old)
 report={'clip':name,'targetThighForwardFlexionDegrees':88,'nativeFK':'Quaternion rotation_difference and slerp on connected original thigh; original calf-local rotation and original world foot orientation retained','overlayFramesLeft':{'rise':[9.5,12.5],'hold':[12.5,15.0],'fall':[15.0,19.0]},'rightLegPhaseOffsetFrames':10,'maxThighFlexBefore':max(r['beforeFlex'][s]for r in rows for s in ['l','r']),'maxThighFlexAfter':max(r['afterFlex'][s]for r in rows for s in ['l','r']),'kneeHeightBefore':max(p[2]for r in rows for p in r['beforeKnees'].values()),'kneeHeightAfter':max(p[2]for r in rows for p in r['knees'].values()),'leftCycleFractionThighAbove70Before':sum(r['beforeFlex']['l']>70 for r in rows[:-1])/80,'leftCycleFractionThighAbove70After':sum(r['afterFlex']['l']>70 for r in rows[:-1])/80,'minShoeFloor':min(v for r in rows for v in r['floor'].values()),'bodyRootArmsCalfAndOtherChannelsPreserved':True,'protectedCurveHash':protected}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':rows},indent=2)+'\n',encoding='utf-8');print('THIGH_LIFT',json.dumps(report),flush=True)
after={a.name:ah(a)for a in bpy.data.actions};assert len(after)==14;assert all(before[n]==v for n,v in after.items()if n not in changed)
assert meshes=={o.name:mh(o)for o in objects};assert bind==pipeline.skeleton(rig)
rig.animation_data.action=bpy.data.actions['idle'];rig.animation_data.action_slot=bpy.data.actions['idle'].slots[0];scene.frame_set(1);scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
m=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
for r in reports:
 for c in [m['clips'][r['clip']],m['libraryMotion']['clips'][r['clip']]]:c['forwardThighLift']=r;c['sourceDuration']=20/30
m.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v6',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before,'afterActions':after,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before if n not in changed],'meshHashes':meshes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'forwardThighLift':reports},indent=2)+'\n',encoding='utf-8')
