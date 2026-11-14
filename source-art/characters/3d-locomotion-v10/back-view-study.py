"""Abandoned back-view study; never installed. User requested the side view."""
raise SystemExit("Abandoned study. Use side-legs.py")
"""Refine the running legs' coronal angle with native Blender IK; retain v9 body."""
from pathlib import Path
import bpy,json,sys,hashlib,math,statistics,copy
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v9'
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
tracked=['pelvis','thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
reference=json.loads((BASE.parent/'3d-locomotion-v8/candidates.json').read_text(encoding='utf-8'))['CMU__16_36']['rows']
def ref_x(phase,side,part):
 f=phase*80;i=min(79,int(f));t=f-i
 def relative(j):return reference[j]['bones'][part+'_'+side][0]-reference[j]['bones']['pelvis'][0]
 return relative(i)*(1-t)+relative(i+1)*t-(relative(80)-relative(0))*phase
def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
def pole_point(hip,knee,ankle):
 axis=(ankle-hip).normalized();projected=hip+axis*(knee-hip).dot(axis)
 direction=knee-projected
 if direction.length<.01:direction=Vector((0,-1,0))
 return knee+direction.normalized()*.8
paths={'pose.bones["'+n+'"].'+prop for n in leg_bones for prop in ['location','rotation_quaternion','scale']}
def protected(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves if c.data_path not in paths]).encode()).hexdigest()
controls={}
for side in ['l','r']:
 nodes=[]
 for kind in ['ankle','knee','rotation']:
  o=bpy.data.objects.new('Coronal_'+kind+'_'+side,None);scene.collection.objects.link(o);nodes.append(o)
 ankle,pole,rotation=nodes;rotation.rotation_mode='QUATERNION'
 ik=rig.pose.bones['calf_'+side].constraints.new('IK');ik.target=ankle;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=150;ik.mute=True
 cr=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');cr.target=rotation;cr.owner_space='WORLD';cr.target_space='WORLD';cr.mix_mode='REPLACE';cr.influence=1;cr.mute=True
 controls[side]=(ankle,pole,rotation,ik,cr)
# Reuse the project's native pole-roll calibration on the current saved pose.
sample(bpy.data.actions['run'],0)
for side,(ankle,pole,rotation,ik,cr)in controls.items():
 hip=wm('thigh_'+side).translation;knee=wm('calf_'+side).translation;foot=wm('foot_'+side).translation
 ankle.location=foot;pole.location=pole_point(hip,knee,foot);errors=[];ik.mute=False
 for angle in [0,math.pi/2,-math.pi/2,math.pi]:
  ik.pole_angle=angle;bpy.context.view_layer.update();errors.append(((wm('calf_'+side).translation-knee).length,angle))
 error,best=min(errors)
 # Refine the native constraint's roll calibration; no custom leg solver.
 lo=best-math.pi/4;hi=best+math.pi/4
 def evaluate(angle):
  ik.pole_angle=angle;bpy.context.view_layer.update()
  return (wm('calf_'+side).translation-knee).length
 for _ in range(20):
  a=hi-(hi-lo)/1.61803398875;b=lo+(hi-lo)/1.61803398875
  if evaluate(a)<evaluate(b):hi=b
  else:lo=a
 ik.pole_angle=(lo+hi)*.5;error=evaluate(ik.pole_angle);ik.mute=True
 assert error<.001,(side,error)
reports=[]
for name in changed:
 old=bpy.data.actions[name];protect=protected(old);frames=[i*.25 for i in range(81)]
 original=[]
 for f in frames:
  values=sample(old,f);original.append((values,{n:wm(n).copy()for n in tracked},floors()))
 center=statistics.mean(w['pelvis'].translation.x for _,w,_ in original[:-1]);baked=[];rows=[];errors=[]
 for f,(values,w,old_floor)in zip(frames,original):
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  restore(values);phase=(f/20+.8875)%1
  targets={};knees={};weights={}
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   sign=1 if side=='l'else-1;air=smooth((old_floor[side]-.025)/.115);weights[side]=air
   ref_foot=sign*ref_x(phase,side,'foot');swing_lane=max(.020,min(.036,.027+.10*(ref_foot-.060)))
   half_lane=.047*(1-air)+swing_lane*air
   target=w['foot_'+side].translation.copy();target.x=center+sign*half_lane;targets[side]=target.copy()
   knee=w['calf_'+side].translation.copy();hip=wm('thigh_'+side).translation
   knee.x=hip.x+.4*(ref_x(phase,side,'calf')-ref_x(phase,side,'thigh'));knees[side]=knee
   ankle.location=target;pole.location=pole_point(hip,knee,target);rotation.rotation_quaternion=w['foot_'+side].to_quaternion();ik.mute=False;cr.mute=False
  bpy.context.view_layer.update();solved={n:rig.pose.bones[n].matrix.copy()for n in leg_bones}
  errors.extend((wm('foot_'+s).translation-targets[s]).length for s in controls)
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in leg_bones:rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  world={n:wm(n).copy()for n in tracked};fl=floors();yz_error=max(abs(world['foot_'+s].translation[j]-w['foot_'+s].translation[j])for s in controls for j in [1,2])
  # Same ankle path in the sagittal plane, same foot orientation and body pose.
  upper_error=max((world['pelvis'].translation-w['pelvis'].translation).length,abs(world['pelvis'].to_quaternion().dot(w['pelvis'].to_quaternion())-1))
  assert yz_error<.001 and upper_error<1e-5,(name,f,yz_error,upper_error)
  rows.append({'frame':f,'airWeight':weights,'before':{n:list(m.translation)for n,m in w.items()},'after':{n:list(m.translation)for n,m in world.items()},'floor':fl,'beforeFloor':old_floor,'sagittalAnkleError':yz_error})
  baked.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].scale.copy())for n in leg_bones})
 assert max(errors)<.001,(name,max(errors))
 assert min(v for r in rows for v in r['floor'].values())>-.006
 baked[-1]={n:tuple(v.copy()for v in x)for n,x in baked[0].items()}
 old.name='REPLACED_'+name;a=old.copy();a.name=name;a.use_fake_user=True;rig.animation_data.action=a
 for c in list(a.fcurves):
  if c.data_path in paths:a.fcurves.remove(c)
 previous={}
 for f,values in zip(frames,baked):
  for n,(l,q,sc)in values.items():
   p=rig.pose.bones[n];q=q.copy();q.normalize()
   if n in previous:q.make_compatible(previous[n])
   previous[n]=q.copy();p.location=l;p.rotation_quaternion=q;p.scale=(1,1,1)
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 for c in a.fcurves:
  if c.data_path in paths:
   for k in c.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None;assert protected(a)==protect;bpy.data.actions.remove(old)
 projected={'before':[],'after':[]}
 for r in rows:
  for mode in projected:
   angles=[]
   for side in ['l','r']:
    # Rear camera at the same 27.5 degree downward angle as the Cocos review.
    knee=Vector(r[mode]['calf_'+side]);ankle=Vector(r[mode]['foot_'+side]);v=ankle-knee
    down=-(v.z*math.cos(math.radians(27.5))-v.y*math.sin(math.radians(27.5)))
    angles.append(math.degrees(math.atan2(v.x,max(.03,down))))
   projected[mode].append(abs(angles[0]-angles[1]))
 report={'clip':name,'supportHalfLaneMetres':.047,'swingHalfLaneMetres':[.020,.036],'kneeFrontalSource':'Existing CMU 16_36 phase, 40% of authored coronal offset','sourcePhaseOffset':.8875,'maxIKError':max(errors),'maxSagittalAnkleError':max(r['sagittalAnkleError']for r in rows),'protectedUpperBodyAndTimingHash':protect,'allNonLegChannelsPreserved':True,'rearProjectedShinAngleSeparationBefore':[min(projected['before']),max(projected['before'])],'rearProjectedShinAngleSeparationAfter':[min(projected['after']),max(projected['after'])],'floorRange':[min(v for r in rows for v in r['floor'].values()),max(min(r['floor'].values())for r in rows)]}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':rows},indent=2)+'\n',encoding='utf-8');print('CORONAL_RUN',json.dumps(report),flush=True)
for side,(ankle,pole,rotation,ik,cr)in controls.items():
 rig.pose.bones['calf_'+side].constraints.remove(ik);rig.pose.bones['foot_'+side].constraints.remove(cr)
 for o in [ankle,pole,rotation]:bpy.data.objects.remove(o,do_unlink=True)
after_actions={a.name:ah(a)for a in bpy.data.actions};assert len(after_actions)==14;assert all(before_actions[n]==v for n,v in after_actions.items()if n not in changed)
assert mesh_hashes=={o.name:mh(o)for o in objects};assert bind==pipeline.skeleton(rig)
rig.animation_data.action=bpy.data.actions['idle'];rig.animation_data.action_slot=bpy.data.actions['idle'].slots[0];scene.frame_set(1);scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)


manifest=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
for report in reports:
 for c in [manifest['clips'][report['clip']],manifest['libraryMotion']['clips'][report['clip']]]:c['legFrontalAngle']=report
for entry in manifest['libraryMotion']['sources']:
 if entry['id']=='CMU16_36UpperBody':entry['use']+='; v10 also adapts the same captured coronal knee/ankle recovery pattern'
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v10',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'coronalLegs':reports},indent=2)+'\n',encoding='utf-8')
