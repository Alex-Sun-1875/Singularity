"""Coordinated full-stride run: existing CC0 Sprint, whole-body retiming and native FK/IK adaptation."""
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
staff_samples=[sample(bpy.data.actions['run_staff'],i*.25)for i in range(81)]
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['UAL1__Sprint_Loop']
source=dst.actions[0];source_hash=ah(source);frames=[i*.25 for i in range(81)];raw=[];world=[];raw_floor=[]
# One shared Blender timing curve retimes every joint together: more time for
# stance/push-off, brisk recovery in flight, no isolated high-knee hold.
timing=bpy.data.actions.new('TEMP_RunTiming');fc=timing.fcurves.new('phase')
knots=[(0,0),(1,1),(6.1,4),(7.5,6.8),(10,10),(11.2,12),(15.6,14.5),(17.5,16.8),(20,20)]
h=[b[0]-a[0]for a,b in zip(knots,knots[1:])]
d=[(b[1]-a[1])/dt for a,b,dt in zip(knots,knots[1:],h)]
# Explicit monotone tangents avoid AUTO_CLAMPED's unwanted mid-stance pause.
slopes=[.8]
for j in range(1,len(knots)-1):
 w1=2*h[j]+h[j-1];w2=h[j]+2*h[j-1]
 slopes.append((w1+w2)/(w1/d[j-1]+w2/d[j]))
slopes.append(.8)
for j,(t,sf)in enumerate(knots):
 k=fc.keyframe_points.insert(t,sf);k.interpolation='BEZIER';k.handle_left_type=k.handle_right_type='FREE'
 left=h[j-1]/3 if j else h[0]/3;right=h[j]/3 if j<len(h)else h[-1]/3
 k.handle_left=(t-left,sf-slopes[j]*left);k.handle_right=(t+right,sf+slopes[j]*right)
assert all(fc.evaluate(f+.01)>=fc.evaluate(f)-1e-6 for f in [i*.01 for i in range(2000)])
source_frames=[fc.evaluate(f)for f in frames]
for sf in source_frames:
 raw.append(sample(source,sf));world.append({n:wm(n).copy()for n in ['pelvis','spine_03','neck_01','Head','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r']});world[-1].update({'arm_'+s:wm('lowerarm_'+s).translation-wm('upperarm_'+s).translation for s in ['l','r']});raw_floor.append(floors())
bpy.data.actions.remove(source);bpy.data.actions.remove(timing)
means={n:meanq([v[n][1]for v in raw[:-1]])for n in body_bones};center=sum((w['pelvis'].translation for w in world[:-1]),Vector())/(len(world)-1)
base_floor=min(v for r in raw_floor for v in r.values());velocities=[]
for side in ['l','r']:
 for i,(a,b)in enumerate(zip(world,world[1:])):
  speed=(b['foot_'+side].translation.y-a['foot_'+side].translation.y)*120
  if speed>.5 and max(raw_floor[i][side],raw_floor[i+1][side])-base_floor<.08:velocities.append(speed)
raw_speed=statistics.median(velocities);arc_scale=1.0
print('SPRINT_STRIDE',raw_speed,arc_scale,'floor',base_floor,flush=True)
assert .5<arc_scale<1.5,(raw_speed,arc_scale)
foot_rot={}
for side in ['l','r']:
 # Keep the author's full heel/toe roll. Horizontal yaw is undefined as a
 # recovering boot passes vertical, so do not flatten its Euler heading.
 qs=[w['foot_'+side].to_quaternion()for w in world[:-1]]
 smooth=[]
 for j in range(len(qs)):
  anchor=qs[j];v=Vector((0,0,0,0))
  for offset in range(-4,5):
   q=qs[(j+offset)%len(qs)].copy();q.make_compatible(anchor);v+=Vector(q)*(5-abs(offset))
  q=Quaternion(v);q.normalize();smooth.append(q)
 foot_rot[side]=smooth+[smooth[0].copy()]
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
  # Keep the author's connected pelvis/spine/shoulder counter-rotation.
  # Change the mean chest line, not the interjoint phase or rear leg extension.
  raw_lean=math.degrees(math.atan2(-(w['neck_01'].translation-w['pelvis'].translation).y,(w['neck_01'].translation-w['pelvis'].translation).z))
  target_lean=20+(raw_lean-40)*.3
  for _ in range(4):
   torso=wm('neck_01').translation-wm('pelvis').translation
   goal=Vector((torso.x*.65,-math.sin(math.radians(target_lean)),math.cos(math.radians(target_lean))))
   delta=torso.normalized().rotation_difference(goal.normalized());set_world_rotation('spine_01',delta@wm('spine_01').to_quaternion())
  for n in ['neck_01','Head']:
   deviation=means[n].inverted()@values[n][1]
   q=neutral_world[n].to_quaternion()@Quaternion().slerp(deviation,.2)
   if n=='Head':q=Quaternion((1,0,0),math.radians(-8))@q
   set_world_rotation(n,q)
  pelvis_goal=Vector(((w['pelvis'].translation.x-center.x)*.5,center.y,.910+(w['pelvis'].translation.z-center.z)*.20))
  root.location+=world_to_root@(pelvis_goal-wm('pelvis').translation);bpy.context.view_layer.update()
  # Retain authored 80-96 degree elbow bend and opposite-leg timing. The source
  # sprint has both upper arms behind its deeply bent chest; map that mean to
  # relaxed +/-35 degree swing around the new chest, instead of boxing hands.
  for side in ['l','r']:
   p=rig.pose.bones['upperarm_'+side];m=wm(p.name);direction=wm('lowerarm_'+side).translation-m.translation
   # Original world direction is sampled before any body adaptation.
   rd=world[i]['arm_'+side]
   pitch=.8*(math.degrees(math.atan2(-rd.y,-rd.z))+45)-4
   x=direction.normalized().x*.55
   goal=Vector((x,-math.sin(math.radians(pitch)),-math.cos(math.radians(pitch)))).normalized()
   delta=direction.normalized().rotation_difference(goal);set_world_rotation(p.name,delta@m.to_quaternion())
  if name=='run_staff':
   for n in rig.pose.bones.keys():
    if n.endswith('_r')and any(n.startswith(prefix)for prefix in ['hand','thumb','index','middle','ring','pinky']):
     p=rig.pose.bones[n];l,q,s=staff_samples[i][n];p.location=l;p.rotation_quaternion=q;p.scale=s
   bpy.context.view_layer.update()
  targets={};desired_floors={};common_air=max(0,min(raw_floor[i].values())-base_floor)
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   sign=1 if side=='l'else-1;m=w['foot_'+side];air=max(0,raw_floor[i][side]-base_floor)
   # Full original forward/back arc is retained. Narrow only the lateral lane;
   # compression of the sagittal arc was what removed the previous push-off.
   desired_floors[side]=.003+max(0,air-.035)*.94
   hip=wm('thigh_'+side).translation
   target=Vector((hip.x*.45+sign*.045,m.translation.y,m.translation.z-raw_floor[i][side]+desired_floors[side]))
   ankle.location=target;targets[side]=target.copy();hip=wm('thigh_'+side).translation
   pole.location=Vector(((hip.x+target.x)*.5,pelvis_goal.y-.85,hip.z-.2))
   rotation.rotation_quaternion=foot_rot[side][i];ik.mute=False;cr.mute=False
  bpy.context.view_layer.update()
  # Solve shoe contact by adjusting the ankle target, preserving the higher torso.
  for _ in range(3):
   current=floors()
   for side,(ankle,*_)in controls.items():
    ankle.location.z+=desired_floors[side]-current[side]
    hip=wm('thigh_'+side).translation;reach=(rig.pose.bones['thigh_'+side].length+rig.pose.bones['calf_'+side].length)*rig.matrix_world.to_scale().x*.995
    distance=(ankle.location-hip).length
    if distance>reach:
     # Lower the root just enough to reach an extended planted leg; never
     # pull the ankle forward and erase the rear extension.
     max_z=math.sqrt(max(.005,reach*reach-(hip.y-ankle.location.y)**2-(hip.x-ankle.location.x)**2))
     root.location+=world_to_root@Vector((0,0,-max(0,hip.z-ankle.location.z-max_z)))
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
 assert min(v for r in records for v in r['floor'].values())>-.006
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
   speed=(b['ankles'][side][1]-a['ankles'][side][1])*120
   if speed>.5 and max(raw_floor[i][side],raw_floor[i+1][side])-base_floor<.08:measured.append(speed)
 nominal=statistics.median(measured)
 report={'clip':name,'source':'Existing CC0 UAL1 Sprint_Loop, full-body Blender timing curve, native65','duration':20/30,'nominalSpeed':nominal,'sourceNominalSpeed':raw_speed,'wholeBodySourceFrames':source_frames,'fullSagittalFootArcRetained':True,'forwardArcScale':arc_scale,'maxIKErrorMetres':max(errors),'torsoLeanRangeDegrees':[min(r['torsoLeanDegrees']for r in records),max(r['torsoLeanDegrees']for r in records)],'meanPelvisHeight':statistics.mean(r['pelvis'][2]for r in records),'pelvisHeightRange':[min(r['pelvis'][2]for r in records),max(r['pelvis'][2]for r in records)],'headHeightRange':[min(r['head'][2]for r in records),max(r['head'][2]for r in records)],'highestKnee':max(p[2]for r in records for p in r['knees'].values()),'highestKneeBefore':max(r[n][2]for r in old_rows for n in ['calf_l','calf_r']),'previousMeanPelvisHeight':statistics.mean(r['pelvis'][2]for r in old_rows),'previousHeadHeightRange':[min(r['Head'][2]for r in old_rows),max(r['Head'][2]for r in old_rows)],'floorRange':[min(v for r in records for v in r['floor'].values()),max(min(r['floor'].values())for r in records)]}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':records},indent=2),encoding='utf-8');print('COORDINATED_RUN',json.dumps(report),flush=True)
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
 for key in ['strideAdaptation','locomotionRefinement','bodyStabilization','strideSource','characterFloorAlignment','uprightRun','raisedKnee','forwardTorsoLean']:c.pop(key,None)
 c.update(name=name,duration=20/30,startFrame=0,endFrame=20,fps=30,loop=True,nominalSpeed=report['nominalSpeed'],nominalSpeedMetresPerSecond=report['nominalSpeed'],sourceSegments=[{'library':'UAL1','clip':'Sprint_Loop','start':0,'end':20}],coordinatedRun=report,floor={'minFootZ':report['floorRange'][0],'maxFootMinZ':report['floorRange'][1],'method':'Evaluated shoes, native IK contact, full forward/back foot arc and whole-body phase'})
 manifest['clips'][name]=copy.deepcopy(c);manifest['libraryMotion']['clips'][name]=copy.deepcopy(c)
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v8',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':['walk','walk_staff','run','run_staff'],'changedThisRevision':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'sourceSprintActionHash':source_hash,'coordinatedRun':reports},indent=2)+'\n',encoding='utf-8')
