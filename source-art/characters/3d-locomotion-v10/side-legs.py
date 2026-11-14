"""Match the 2D side silhouette: diagonal support and tucked raised calf."""
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
tracked=['pelvis','thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r']
def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
def pole_point(hip,knee,ankle):
 axis=(ankle-hip).normalized();projected=hip+axis*(knee-hip).dot(axis);direction=knee-projected
 if direction.length<.01:direction=Vector((0,-1,0))
 return knee+direction.normalized()*.8
paths={'pose.bones["'+n+'"].'+prop for n in leg_bones for prop in ['location','rotation_quaternion','scale']}
def protected(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves if c.data_path not in paths]).encode()).hexdigest()
def sole_vectors(world):
 result={s:[]for s in ['l','r']};deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  ev=o.evaluated_get(deps);mesh=ev.to_mesh()
  for s in result:
   inv=world['foot_'+s].inverted()
   result[s].extend(inv@(ev.matrix_world@mesh.vertices[i].co)for i in foot_indices[o.name][s])
  ev.to_mesh_clear()
 return result
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
 old=bpy.data.actions[name];protect=protected(old);frames=[i*.25 for i in range(81)];original=[]
 for f in frames:
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  values=sample(old,f);w={n:wm(n).copy()for n in tracked};original.append((values,w,floors(),sole_vectors(w)))
 # Plan a continuous foot-roll curve before solving the legs. The old shoe
 # clearance rises very quickly at toe-off; it must not switch foot pose.
 planned={s:[]for s in ['l','r']}
 for values,w,old_floor,soles in original[:-1]:
  flexes={s:math.degrees(math.atan2(-(w['calf_'+s].translation-w['thigh_'+s].translation).y,-(w['calf_'+s].translation-w['thigh_'+s].translation).z))for s in planned}
  for s in planned:
   other='r'if s=='l'else'l';air=smooth((old_floor[s]-.025)/.115)
   lift=smooth((flexes[s]-25)/40)*air;rear=smooth((flexes[other]-45)/20)*(1-smooth((flexes[s]-15)/20))
   v=w['ball_'+s].translation-w['foot_'+s].translation;pitch=math.atan2(v.z,-v.y);down=15 if lift>rear else 8+122*air
   q=Quaternion((1,0,0),pitch+math.radians(down))@w['foot_'+s].to_quaternion()
   planned[s].append(w['foot_'+s].to_quaternion().slerp(q,max(lift,rear)))
 foot_curves={}
 for s,qs in planned.items():
  curve=[]
  for j in range(80):
   anchor=qs[j];total=Vector((0,0,0,0))
   for offset in range(-6,7):
    q=qs[(j+offset)%80].copy();q.make_compatible(anchor);total+=Vector(q)*(7-abs(offset))
   q=Quaternion(total);q.normalize();curve.append(q)
  foot_curves[s]=curve+[curve[0].copy()]
 baked=[];rows=[];errors=[]
 for frame_index,(f,(values,w,old_floor,soles))in enumerate(zip(frames,original)):
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  restore(values)
  flex={}
  for side in ['l','r']:
   v=w['calf_'+side].translation-w['thigh_'+side].translation;flex[side]=math.degrees(math.atan2(-v.y,-v.z))
  weights={};targets={};goal_rot={};clearance={};limits={}
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   other='r'if side=='l'else'l';hip=w['thigh_'+side].translation;knee=w['calf_'+side].translation;foot=w['foot_'+side].translation
   air=smooth((old_floor[side]-.025)/.115);contact=1-smooth((old_floor[side]-.025)/.10)
   own_drive=smooth((flex[side]-25)/40)*air
   rear_drive=smooth((flex[other]-45)/20)*(1-smooth((flex[side]-15)/20))
   reach_gate=1-smooth(((foot.y-hip.y)-.30)/.20)
   rear_style=rear_drive
   toe=w['ball_'+side].translation-foot;pitch=math.atan2(toe.z,-toe.y)
   def foot_rotation(alpha):
    return w['foot_'+side].to_quaternion().slerp(foot_curves[side][frame_index],alpha)
   L1=(knee-hip).length;L2=(foot-knee).length;reach=(L1+L2)*.997
   # Tuck the lifted calf behind its forward knee, rather than letting the
   # shin hang vertically. The desired thigh remains diagonally raised.
   desired_knee=knee.copy();target=foot.copy()
   F=math.radians(min(67,max(45,flex[side])));sagittal_L1=math.sqrt(max(.001,L1*L1-(knee.x-hip.x)**2))
   raised_knee=Vector((knee.x,hip.y-sagittal_L1*math.sin(F),hip.z-sagittal_L1*math.cos(F)))
   raised_y=hip.y-.05;raised_z=raised_knee.z-math.sqrt(max(.001,L2*L2-(raised_y-raised_knee.y)**2-(foot.x-raised_knee.x)**2))
   target.y=foot.y*(1-own_drive)+raised_y*own_drive
   target.z=foot.z*(1-own_drive)+raised_z*own_drive
   desired_knee=knee.lerp(raised_knee,own_drive)
   shift=.12*rear_drive*contact*reach_gate
   alpha=1.0
   q=foot_rotation(alpha);rot=Matrix.LocRotScale(Vector(),q,w['foot_'+side].to_scale())
   sole_offset=min((rot@v).z for v in soles[side])
   goal=target.copy();goal.y+=shift*alpha
   if own_drive<.01:goal.z=old_floor[side]*(1-.8*rear_drive*air)-sole_offset
   if own_drive>0:goal.z=max(goal.z,.035-sole_offset)
   # Keep the toe-off/flight target inside the native leg reach.
   ceiling=hip.z-math.sqrt(max(.001,reach*reach-(goal.y-hip.y)**2-(goal.x-hip.x)**2))
   goal.z=max(goal.z,ceiling)
   clearance[side]=max(.003,goal.z+sole_offset)if own_drive<.01 else max(.025,goal.z+sole_offset)
   limits[side]=(hip.copy(),reach)
   ankle.location=goal;pole.location=pole_point(hip,desired_knee,goal);rotation.rotation_quaternion=q;ik.mute=False;cr.mute=False
   weights[side]={'lifted':own_drive,'support':rear_style,'feasibility':alpha};targets[side]=goal.copy();goal_rot[side]=q.copy()
  bpy.context.view_layer.update()
  # Correct evaluated shoe clearance after transferring foot roll.
  for _ in range(3):
   fl=floors()
   for side,(ankle,pole,rotation,ik,cr)in controls.items():
    ankle.location.z+=clearance[side]-fl[side]
    hip,reach=limits[side]
    ceiling=hip.z-math.sqrt(max(.001,reach*reach-(ankle.location.y-hip.y)**2-(ankle.location.x-hip.x)**2))
    ankle.location.z=max(ankle.location.z,ceiling)
   bpy.context.view_layer.update()
  solved={n:rig.pose.bones[n].matrix.copy()for n in leg_bones}
  errors.extend((wm('foot_'+s).translation-controls[s][0].location).length for s in controls)
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in leg_bones:rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  world={n:wm(n).copy()for n in tracked};fl=floors()
  assert max(abs(world['foot_'+s].translation.x-w['foot_'+s].translation.x)for s in controls)<.001
  rows.append({'frame':f,'weights':weights,'before':{n:list(m.translation)for n,m in w.items()},'after':{n:list(m.translation)for n,m in world.items()},'floor':fl,'beforeFloor':old_floor})
  baked.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].scale.copy())for n in leg_bones})
 if max(errors)>=.002:print('IK_CONTACT_DETAIL',[(rows[j//2]['frame'],'l'if j%2==0 else'r',e,rows[j//2]['floor'],rows[j//2]['weights'])for j,e in enumerate(errors)if e>=.002],flush=True)
 assert max(errors)<.002,(name,max(errors))
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
 angles={mode:[]for mode in ['before','after']}
 for r in rows:
  for mode in angles:
   v=r[mode];thighs=[];bends=[]
   for s in ['l','r']:
    hip=Vector(v['thigh_'+s]);knee=Vector(v['calf_'+s]);foot=Vector(v['foot_'+s]);u=knee-hip;t=foot-knee
    a1=math.degrees(math.atan2(-u.y,-u.z));a2=math.degrees(math.atan2(-t.y,-t.z));thighs.append(a1);bends.append(abs(a1-a2))
   angles[mode].append({'thighSeparation':abs(thighs[0]-thighs[1]),'thighs':thighs,'kneeBend':bends})
 report={'clip':name,'requestedView':'side','supportFootRearShiftLimitMetres':.12,'raisedThighLimitDegrees':67,'raisedAnkleForwardOffsetFromHip':-.05,'allNonLegChannelsPreserved':True,'protectedUpperBodyAndTimingHash':protect,'maxIKError':max(errors),'footLateralTracksPreserved':True,'beforeSideAngles':angles['before'],'afterSideAngles':angles['after'],'floorRange':[min(v for r in rows for v in r['floor'].values()),max(min(r['floor'].values())for r in rows)]}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':rows},indent=2)+'\n',encoding='utf-8');print('SIDE_LEG_POSE',name,'IK',max(errors),'peak phase side angles',[(j,angles['before'][j],angles['after'][j])for j in [30,60]],flush=True)
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
 for c in [manifest['clips'][report['clip']],manifest['libraryMotion']['clips'][report['clip']]]:c['legSideAngle']=report
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v10',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'sideLegs':reports},indent=2)+'\n',encoding='utf-8')
