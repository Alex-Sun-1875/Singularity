"""Upright running from existing CC0 Sprint_Loop; native Blender IK and FK only."""
from pathlib import Path
import bpy,json,sys,hashlib,math,statistics,copy
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v4'
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
controls={}
for side in ['l','r']:
 nodes=[]
 for kind in ['ankle','knee','rotation']:
  o=bpy.data.objects.new('Run_'+kind+'_'+side,None);scene.collection.objects.link(o);nodes.append(o)
 ankle,pole,rotation=nodes;rotation.rotation_mode='QUATERNION'
 ik=rig.pose.bones['calf_'+side].constraints.new('IK');ik.target=ankle;ik.pole_target=pole;ik.pole_angle=-math.pi/2;ik.chain_count=2;ik.use_stretch=False;ik.iterations=150;ik.mute=True
 cr=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');cr.target=rotation;cr.owner_space='WORLD';cr.target_space='WORLD';cr.mix_mode='REPLACE';cr.influence=1;cr.mute=True
 controls[side]=(ankle,pole,rotation,ik,cr)
root=rig.pose.bones['root'];world_to_root=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()
reports=[]
for name in changed:
 baked=[];records=[];errors=[]
 for i,(f,values,w)in enumerate(zip(frames,raw,world)):
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  restore(values)
  # Replace the sprint's bent-over mean torso with the established upright idle.
  for n in body_bones:
   deviation=means[n].inverted()@values[n][1];rig.pose.bones[n].rotation_quaternion=neutral[n][1]@Quaternion().slerp(deviation,.20 if n not in ['neck_01','Head']else .12)
  rig.pose.bones['pelvis'].rotation_quaternion=means['pelvis']@Quaternion().slerp(means['pelvis'].inverted()@values['pelvis'][1],.15)
  if name=='run_staff':
   for n in rig.pose.bones.keys():
    if n.endswith('_r')and any(n.startswith(prefix)for prefix in ['clavicle','upperarm','lowerarm','hand','thumb','index','middle','ring','pinky']):
     p=rig.pose.bones[n];l,q,s=staff_samples[i][n];p.location=l;p.rotation_quaternion=q;p.scale=s
  bpy.context.view_layer.update()
  for _ in range(4):
   torso=wm('neck_01').translation-wm('pelvis').translation;goal_up=Vector((torso.x*.1,-math.sin(math.radians(9)),math.cos(math.radians(9))))
   delta=torso.normalized().rotation_difference(goal_up.normalized());set_world_rotation('spine_01',delta@wm('spine_01').to_quaternion())
  for n in ['neck_01','Head']:set_world_rotation(n,neutral_world[n].to_quaternion())
  pelvis_goal=Vector(((w['pelvis'].translation.x-center.x)*.20,.045,.950+(w['pelvis'].translation.z-center.z)*.25))
  root.location+=world_to_root@(pelvis_goal-wm('pelvis').translation);bpy.context.view_layer.update()
  # Forward/back arm swing stays on the connected authored shoulder/elbow chain.
  for side in ['l','r']:
   if name=='run_staff'and side=='r':continue
   p=rig.pose.bones['upperarm_'+side];m=p.matrix.copy();direction=m.to_3x3()@Vector((0,1,0));goal=direction.copy();goal.x*=.72
   d=direction.normalized().rotation_difference(goal.normalized());p.matrix=Matrix.LocRotScale(m.translation,d@m.to_quaternion(),m.to_scale());bpy.context.view_layer.update()
  targets={};desired_floors={};common_air=max(0,min(raw_floor[i].values())-base_floor)
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   sign=1 if side=='l'else-1;m=w['foot_'+side];air=max(0,raw_floor[i][side]-base_floor)
   front=max(0,min(1,(center.y-m.translation.y)/.30));other='r'if side=='l'else'l';support=1-max(0,min(1,(raw_floor[i][other]-base_floor-.035)/.12))
   extra_lift=.13*max(0,min(1,(air-.035)/.12))*front*support
   desired_floors[side]=.003+max(0,air-common_air)*1.05+min(.05,common_air*.22)+extra_lift
   target=Vector((sign*.075,.045+(m.translation.y-center.y)*arc_scale,m.translation.z-raw_floor[i][side]+desired_floors[side]))
   ankle.location=target;targets[side]=target.copy();hip=wm('thigh_'+side).translation
   pole.location=Vector(((hip.x+target.x)*.5,pelvis_goal.y-.85,hip.z-.15))
   yaw=math.atan2(m[1][0],m[0][0]);rotation.rotation_quaternion=Quaternion((0,0,1),sign*math.radians(2)-yaw)@m.to_quaternion();ik.mute=False;cr.mute=False
  bpy.context.view_layer.update()
  # Solve shoe contact by adjusting the ankle target, preserving the higher torso.
  for _ in range(3):
   current=floors()
   for side,(ankle,*_)in controls.items():
    ankle.location.z+=desired_floors[side]-current[side]
    hip=wm('thigh_'+side).translation;reach=(rig.pose.bones['thigh_'+side].length+rig.pose.bones['calf_'+side].length)*rig.matrix_world.to_scale().x*.995
    max_y=math.sqrt(max(.005,reach*reach-(hip.z-ankle.location.z)**2-(hip.x-ankle.location.x)**2))
    ankle.location.y=hip.y+max(-max_y,min(max_y,ankle.location.y-hip.y))
   bpy.context.view_layer.update()
  solved={n:rig.pose.bones[n].matrix.copy()for n in leg_bones}
  errors.extend((wm('foot_'+s).translation-controls[s][0].location).length for s in controls)
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in leg_bones:rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  fl=floors();pv=wm('pelvis').translation;neck=wm('neck_01').translation;v=neck-pv
  records.append({'frame':f,'pelvis':list(pv),'head':list(wm('Head').translation),'knees':{s:list(wm('calf_'+s).translation)for s in controls},'ankles':{s:list(wm('foot_'+s).translation)for s in controls},'goals':{s:list(controls[s][0].location)for s in controls},'floor':fl,'torsoLeanDegrees':math.degrees(math.atan2(-v.y,v.z))});baked.append(pose())
 if max(errors)>=.003:print('UNREACHABLE',[(j,errors[j],records[j//2])for j in sorted(range(len(errors)),key=lambda j:errors[j],reverse=True)[:3]],flush=True)
 assert max(errors)<.003,(name,max(errors))
 assert min(v for r in records for v in r['floor'].values())>-.003
 baked[-1]={n:tuple(v.copy()for v in x)for n,x in baked[0].items()}
 old=bpy.data.actions[name];old.name='REPLACED_'+name;a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a;previous={}
 for f,values in zip(frames,baked):
  restore(values,False)
  for p in rig.pose.bones:
   q=p.rotation_quaternion.copy();q.normalize()
   if p.name in previous:q.make_compatible(previous[p.name])
   previous[p.name]=q.copy();p.rotation_quaternion=q
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 for c in a.fcurves:
  for k in c.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None;bpy.data.actions.remove(old)
 measured=[]
 for side in controls:
  for i,(a,b)in enumerate(zip(records,records[1:])):
   speed=(b['ankles'][side][1]-a['ankles'][side][1])*60
   if speed>.5 and max(raw_floor[i][side],raw_floor[i+1][side])-base_floor<.08:measured.append(speed)
 nominal=statistics.median(measured)
 report={'clip':name,'source':'Existing CC0 UAL1 Sprint_Loop, native65, frames0..20','duration':20/30,'nominalSpeed':nominal,'sourceNominalSpeed':raw_speed,'forwardArcScale':arc_scale,'maxIKErrorMetres':max(errors),'torsoLeanRangeDegrees':[min(r['torsoLeanDegrees']for r in records),max(r['torsoLeanDegrees']for r in records)],'meanPelvisHeight':statistics.mean(r['pelvis'][2]for r in records),'pelvisHeightRange':[min(r['pelvis'][2]for r in records),max(r['pelvis'][2]for r in records)],'headHeightRange':[min(r['head'][2]for r in records),max(r['head'][2]for r in records)],'highestKnee':max(p[2]for r in records for p in r['knees'].values()),'highestKneeBefore':max(r[n][2]for r in old_rows for n in ['calf_l','calf_r']),'previousMeanPelvisHeight':statistics.mean(r['pelvis'][2]for r in old_rows),'previousHeadHeightRange':[min(r['Head'][2]for r in old_rows),max(r['Head'][2]for r in old_rows)],'floorRange':[min(v for r in records for v in r['floor'].values()),max(min(r['floor'].values())for r in records)]}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':records},indent=2),encoding='utf-8');print('UPRIGHT_RUN',json.dumps(report),flush=True)
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
 name=report['clip'];c=copy.deepcopy(manifest['clips'][name])
 for key in ['strideAdaptation','locomotionRefinement','bodyStabilization','strideSource','characterFloorAlignment']:c.pop(key,None)
 c.update(name=name,duration=20/30,startFrame=0,endFrame=20,fps=30,loop=True,nominalSpeed=report['nominalSpeed'],nominalSpeedMetresPerSecond=report['nominalSpeed'],sourceSegments=[{'library':'UAL1','clip':'Sprint_Loop','start':0,'end':20}],uprightRun=report,floor={'minFootZ':report['floorRange'][0],'maxFootMinZ':report['floorRange'][1],'method':'Per-foot evaluated shoes, native IK ankle correction; upright torso remains independent'})
 manifest['clips'][name]=copy.deepcopy(c);manifest['libraryMotion']['clips'][name]=copy.deepcopy(c)
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v5',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'sourceSprintActionHash':source_hash,'uprightRun':reports},indent=2)+'\n',encoding='utf-8')
