"""Match the 2D run's forward torso line while retaining the v6 raised legs."""
from pathlib import Path
import bpy,json,hashlib,math,sys
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v6'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
changed=['run','run_staff'];edited=['spine_01','neck_01','Head'];target_degrees=22
def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def mh(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def sample(a,f):
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update()
def wm(n):return rig.matrix_world@rig.pose.bones[n].matrix
def set_rotation(n,q):
 p=rig.pose.bones[n];m=wm(n);p.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(m.translation,q,m.to_scale());bpy.context.view_layer.update()
def lean():
 v=wm('neck_01').translation-wm('pelvis').translation
 return math.degrees(math.atan2(-v.y,v.z))
def protected_hash(a):
 paths={'pose.bones["'+n+'"].rotation_quaternion'for n in edited}
 return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves if c.data_path not in paths]).encode()).hexdigest()
before={a.name:ah(a)for a in bpy.data.actions};meshes={o.name:mh(o)for o in objects};bind=pipeline.skeleton(rig);reports=[]
for name in changed:
 old=bpy.data.actions[name];protected=protected_hash(old);frames=[i*.25 for i in range(81)];baked=[];rows=[]
 for f in frames:
  sample(old,f);before_lean=lean();neck_q=wm('neck_01').to_quaternion();head_q=wm('Head').to_quaternion();head_goal=Quaternion((1,0,0),math.radians(-8))@head_q
  protected_positions={n:wm(n).translation.copy()for n in ['pelvis','thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']}
  for _ in range(5):
   v=(wm('neck_01').translation-wm('pelvis').translation).normalized();a=math.radians(target_degrees)
   target=Vector((v.x,-math.sin(a),math.cos(a))).normalized();delta=v.rotation_difference(target)
   set_rotation('spine_01',delta@wm('spine_01').to_quaternion())
  # The head travels forward with the chest; the neck keeps the original gaze.
  set_rotation('neck_01',neck_q)
  set_rotation('Head',head_goal)
  errors={n:(wm(n).translation-p).length for n,p in protected_positions.items()}
  angle=math.degrees(head_goal.rotation_difference(wm('Head').to_quaternion()).angle);gaze_error=min(angle,360-angle)
  assert max(errors.values())<1e-6,(name,f,errors);assert gaze_error<.05,(name,f,gaze_error)
  rows.append({'frame':f,'beforeLean':before_lean,'afterLean':lean(),'head':list(wm('Head').translation),'pelvis':list(wm('pelvis').translation),'headGazeRotationErrorDegrees':gaze_error,'legAndRootPositionErrorMetres':max(errors.values())});baked.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in edited})
 assert all(21.8<r['afterLean']<22.2 for r in rows)
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
 report={'clip':name,'targetTorsoLeanDegrees':target_degrees,'headGazeLiftDegrees':8,'beforeLeanRange':[min(r['beforeLean']for r in rows),max(r['beforeLean']for r in rows)],'afterLeanRange':[min(r['afterLean']for r in rows),max(r['afterLean']for r in rows)],'maxHeadGazeRotationErrorDegrees':max(r['headGazeRotationErrorDegrees']for r in rows),'maxLegAndRootPositionErrorMetres':max(r['legAndRootPositionErrorMetres']for r in rows),'allOtherChannelsPreserved':True,'protectedCurveHash':protected,'reference':'Existing approved 2D four-view run design; actual side-view comparison used to tune visible chest lean and forward gaze.'}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':rows},indent=2)+'\n',encoding='utf-8');print('FORWARD_RUN',json.dumps(report),flush=True)
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
 for c in [m['clips'][r['clip']],m['libraryMotion']['clips'][r['clip']]]:c['forwardTorsoLean']=r
m.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v7',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before,'afterActions':after,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before if n not in changed],'meshHashes':meshes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'forwardTorsoLean':reports},indent=2)+'\n',encoding='utf-8')
