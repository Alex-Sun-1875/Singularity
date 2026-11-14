"""Unfold the pelvis/lumbar posture and restore authored body counter-rotation."""
from pathlib import Path
import bpy,json,sys,hashlib,math,statistics,copy
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v8'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];feet=[o for o in objects if o.get('nativePart')=='feet']
changed=['walk','walk_staff','run','run_staff'];leg_bones=['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
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
neutral=sample(bpy.data.actions['idle'],0)
arm_bones=['upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r']
tracked=list(dict.fromkeys(body_bones+leg_bones+arm_bones))
neutral_world={n:wm(n).copy()for n in tracked}
def read(a,f):
 values=sample(a,f);world={n:wm(n).copy()for n in tracked}
 return values,world
def flex(w,side):
 v=w['calf_'+side].translation-w['thigh_'+side].translation
 return math.atan2(-v.y,-v.z)
def lean(w):
 v=w['neck_01'].translation-w['pelvis'].translation
 return math.degrees(math.atan2(-v.y,v.z))
def pitch(q,n='pelvis'):
 d=q@neutral_world[n].to_quaternion().inverted();up=d@Vector((0,0,1))
 return math.degrees(math.atan2(-up.y,up.z))
# Existing native authored walk, and the already-retargeted cached CMU run.
# No new rig, retarget solver, dependency, download or runtime deformation.
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['UAL1__Walk_Loop']
walk_action=dst.actions[0]
with bpy.data.libraries.load(str(SOURCE/'candidates.blend'))as(src,dst):dst.actions=['CMU__16_36']
run_action=dst.actions[0];source_hashes={'walk':ah(walk_action),'runUpperBody':ah(run_action)}
authored={}
for label,a,start,end in [('walk',walk_action,0,40),('run',run_action,2,26)]:
 poses=[]
 for j in range(81):poses.append(sample(a,start+(end-start)*j/80))
 # Reuse the existing mocap adapter's distributed endpoint correction.
 for n in rig.pose.bones.keys():
  l0,q0,s0=poses[0][n];ll,ql,sl=poses[-1][n];delta=ql.inverted()@q0
  if delta.w<0:delta.negate()
  for j,values in enumerate(poses):
   l,q,sc=values[n];t=j/80
   values[n]=(l-(ll-l0)*t,q@Quaternion().slerp(delta,t),sc)
 worlds=[]
 for values in poses:restore(values);worlds.append({n:wm(n).copy()for n in tracked})
 authored[label]={'poses':poses,'worlds':worlds,'means':{n:meanq([v[n][1]for v in poses[:-1]])for n in tracked},'worldMeans':{n:meanq([w[n].to_quaternion()for w in worlds[:-1]])for n in tracked},'meanLean':statistics.mean(lean(w)for w in worlds[:-1])}
for a in [walk_action,run_action]:bpy.data.actions.remove(a)
old_run=[read(bpy.data.actions['run'],j*.25)[1]for j in range(80)]
ref=[flex(w,'l')for w in old_run]
correlations=[]
for shift in range(80):
 candidate=[flex(authored['run']['worlds'][(j+shift)%80],'l')for j in range(80)]
 correlations.append((statistics.correlation(ref,candidate),shift))
correlation,run_shift=max(correlations)
print('BODY_PHASE_ALIGNMENT',run_shift/80,correlation,flush=True)
assert correlation>.65
controls={}
for side in ['l','r']:
 nodes=[]
 for kind in ['ankle','knee','rotation']:
  o=bpy.data.objects.new('Posture_'+kind+'_'+side,None);scene.collection.objects.link(o);nodes.append(o)
 ankle,pole,rotation=nodes;rotation.rotation_mode='QUATERNION'
 ik=rig.pose.bones['calf_'+side].constraints.new('IK');ik.target=ankle;ik.pole_target=pole;ik.pole_angle=-math.pi/2;ik.chain_count=2;ik.use_stretch=False;ik.iterations=150;ik.mute=True
 cr=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');cr.target=rotation;cr.owner_space='WORLD';cr.target_space='WORLD';cr.mix_mode='REPLACE';cr.influence=1;cr.mute=True
 controls[side]=(ankle,pole,rotation,ik,cr)
root=rig.pose.bones['root'];world_to_root=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()
reports=[]
for name in changed:
 running=name.startswith('run');end=20 if running else 40;frames=[j*.25 for j in range(end*4+1)]
 originals=[read(bpy.data.actions[name],f)for f in frames]
 source=authored['run'if running else'walk'];means=source['means'];world_means=source['worldMeans']
 baked=[];rows=[];errors=[]
 for j,(f,(values,w))in enumerate(zip(frames,originals)):
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  restore(values)
  si=(round(f/end*80)+(run_shift if running else 0))%80
  sv=source['poses'][si];sw=source['worlds'][si]
  # Recenter at the native walk's healthy pelvis frame. The old run held
  # 28 degrees of anterior tilt and counter-bent the lumbar spine by ~23.
  base=authored['walk']['worldMeans']['pelvis']
  if running:base=Quaternion((1,0,0),math.radians(3))@base
  deviation=world_means['pelvis'].inverted()@sw['pelvis'].to_quaternion()
  set_world_rotation('pelvis',base@Quaternion().slerp(deviation,.65 if running else 1.0))
  for n,k in [('spine_01',.55 if running else 1.0),('spine_02',.6 if running else 1.0),('spine_03',.7 if running else 1.0),('clavicle_l',.75),('clavicle_r',.75)]:
   base_q=authored['walk']['means'][n]if n.startswith('clavicle')else neutral[n][1]
   rig.pose.bones[n].rotation_quaternion=base_q@Quaternion().slerp(means[n].inverted()@sv[n][1],k)
  bpy.context.view_layer.update()
  source_lean=lean(sw)-source['meanLean'];target_lean=(16 if running else 6)+source_lean*(.55 if running else .7)
  # Spread the small remaining chest inclination through the spine. Do not
  # hinge all the forward lean at the waist or cancel the pelvic turn.
  for _ in range(7):
   current=lean({n:wm(n)for n in ['neck_01','pelvis']});angle=target_lean-current
   if abs(angle)<.02:break
   for n,factor in [('spine_01',.18),('spine_02',.36),('spine_03',.46)]:
    set_world_rotation(n,Quaternion((1,0,0),math.radians(angle*factor))@wm(n).to_quaternion())
  # Keep a responsive, forward gaze instead of world-locking the whole head.
  for n,k in [('neck_01',.45),('Head',.5)]:
   dev=world_means[n].inverted()@sw[n].to_quaternion();base=neutral_world[n].to_quaternion()
   if running and n=='Head':base=Quaternion((1,0,0),math.radians(-4))@base
   set_world_rotation(n,base@Quaternion().slerp(dev,k))
  # Keep the reviewed run's complete UAL shoulder/elbow swing; only walking
  # restores the original native arm trajectory. Fingers/grips stay native.
  for side in ['l','r']:
   if name.endswith('_staff')and side=='r':continue
   upper='upperarm_'+side;lower='lowerarm_'+side;hand='hand_'+side
   arms=w if running else sw
   direction=(arms[lower].translation-arms[upper].translation).normalized();goal=direction.copy();goal.x*=1.0 if running else .6;goal.normalize()
   delta=direction.rotation_difference(goal)
   for n in [upper,lower,hand]:set_world_rotation(n,delta@arms[n].to_quaternion())
  # Preserve the already-reviewed ankle trajectories and heel/toe roll while
  # allowing the hips to turn. Blender solves the connected knee chain.
  max_drop=0
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   ankle.location=w['foot_'+side].translation;rotation.rotation_quaternion=w['foot_'+side].to_quaternion()
   hip=wm('thigh_'+side).translation;reach=(rig.pose.bones['thigh_'+side].length+rig.pose.bones['calf_'+side].length)*rig.matrix_world.to_scale().x*.997
   dx=hip.x-ankle.location.x;dy=hip.y-ankle.location.y
   ceiling=ankle.location.z+math.sqrt(max(.005,reach*reach-dx*dx-dy*dy))
   max_drop=max(max_drop,hip.z-ceiling)
  if max_drop>0:root.location+=world_to_root@Vector((0,0,-max_drop));bpy.context.view_layer.update()
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   hip=wm('thigh_'+side).translation;pole.location=Vector(((hip.x+ankle.location.x)*.5,wm('pelvis').translation.y-.85,hip.z-.2));ik.mute=False;cr.mute=False
  bpy.context.view_layer.update();solved={n:rig.pose.bones[n].matrix.copy()for n in leg_bones}
  errors.extend((wm('foot_'+s).translation-w['foot_'+s].translation).length for s in controls)
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in leg_bones:rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  fl=floors();world={n:wm(n).copy()for n in tracked}
  rows.append({'frame':f,'sourcePhase':si/80,'pelvisPitch':pitch(world['pelvis'].to_quaternion()),'torsoLean':lean(world),'rootHeightDrop':max_drop,'floor':fl,'points':{n:list(m.translation)for n,m in world.items()},'rotations':{n:list(m.to_quaternion())for n,m in world.items()}})
  baked.append(pose())
 assert max(errors)<.001,(name,max(errors))
 assert min(v for r in rows for v in r['floor'].values())>-.006
 baked[-1]={n:tuple(v.copy()for v in x)for n,x in baked[0].items()}
 old=bpy.data.actions[name];old.name='REPLACED_'+name;a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a;previous={}
 for f,values in zip(frames,baked):
  restore(values,False)
  for p in rig.pose.bones:
   q=p.rotation_quaternion.copy();q.normalize()
   if p.name in previous:q.make_compatible(previous[p.name])
   previous[p.name]=q.copy();p.rotation_quaternion=q;p.scale=(1,1,1)
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 for c in a.fcurves:
  for k in c.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None;bpy.data.actions.remove(old)
 report={'clip':name,'bodySource':'Cached CMU 16_36 retarget, frames2..26'if running else'Existing CC0 UAL1 Walk_Loop','sourcePhaseOffset':run_shift/80 if running else 0,'phaseCorrelation':correlation if running else 1,'duration':end/30,'pelvisPitchRange':[min(r['pelvisPitch']for r in rows),max(r['pelvisPitch']for r in rows)],'torsoLeanRange':[min(r['torsoLean']for r in rows),max(r['torsoLean']for r in rows)],'maxAnklePathErrorMetres':max(errors),'maxRootHeightCorrectionMetres':max(r['rootHeightDrop']for r in rows),'floorRange':[min(v for r in rows for v in r['floor'].values()),max(min(r['floor'].values())for r in rows)],'bodyRotationRange':{n:max(math.degrees(Quaternion(a['rotations'][n]).rotation_difference(Quaternion(b['rotations'][n])).angle)for a in rows[::4]for b in rows[::4])for n in ['pelvis','spine_03','Head']}}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':rows},indent=2)+'\n',encoding='utf-8');print('RESPONSIVE_BODY',json.dumps(report),flush=True)
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
cmu_file=ROOT/'source-art/characters/mocap/cmu/16_36.bvh'
cmu_source={'id':'CMU16_36UpperBody','file':cmu_file.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(cmu_file.read_bytes()).hexdigest(),'license':'CMU motion capture database terms; inclusion in commercial products allowed, data must not be sold on its own','termsCopy':'source-art/characters/mocap/cmu/READMEFIRST.txt','url':'https://mocap.cs.cmu.edu/','use':'Running pelvis, spine and head motion, retargeted with existing BVH Retargeter 4.4.0; normalized posture and phase aligned to retained UAL arm/leg cycle'}
manifest['libraryMotion']['sources']=[s for s in manifest['libraryMotion']['sources']if s['id']!=cmu_source['id']]+[cmu_source]
for report in reports:
 for c in [manifest['clips'][report['clip']],manifest['libraryMotion']['clips'][report['clip']]]:
  c['responsiveBody']=report
  c.pop('bodyStabilization',None)
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v9',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':changed,'changedThisRevision':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'sourceUpperBodyActions':source_hashes,'responsiveBody':reports},indent=2)+'\n',encoding='utf-8')
