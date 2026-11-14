"""Quiet the existing v3 body motion; preserve its foot paths with native Blender IK."""
from pathlib import Path
import bpy,json,sys,hashlib,math
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];SOURCE=BASE.parent/'3d-locomotion-v3'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.animation_data.action=None;scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];feet=[o for o in objects if o.get('nativePart')=='feet']
changed=['walk','walk_staff','run','run_staff'];legs=['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
strengths={'pelvis':.20,'spine_01':.22,'spine_02':.22,'spine_03':.22,'neck_01':.25,'Head':.25,'clavicle_l':.45,'clavicle_r':.45}
strengths={n:v for n,v in strengths.items()if n in rig.pose.bones}
def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def mh(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def pose():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}
def restore(v,update=True):
 for n,(l,q,s)in v.items():
  p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.location=l;p.rotation_quaternion=q;p.scale=s
 if update:bpy.context.view_layer.update()
def sample(a,f):
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update();return pose()
def wm(n):return rig.matrix_world@rig.pose.bones[n].matrix
def meanq(qs):
 anchor=qs[0];v=Vector((0,0,0,0))
 for q in qs:
  q=q.copy();q.make_compatible(anchor);v+=Vector(q)
 q=Quaternion(v);q.normalize();return q
def floor():
 low=1e9;deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  e=o.evaluated_get(deps);m=e.to_mesh();low=min(low,min((e.matrix_world@v.co).z for v in m.vertices));e.to_mesh_clear()
 return low
def metrics(rows):
 result={}
 for n in ['pelvis','spine_03','Head']:
  ps=[v[n].translation for v in rows];qs=[v[n].to_quaternion()for v in rows];q=meanq(qs)
  result[n]={'rangeXYZ':[max(p[j]for p in ps)-min(p[j]for p in ps)for j in range(3)],'maxAngleFromMeanDegrees':max(math.degrees(q.rotation_difference(v).angle)for v in qs)}
 return result
before_actions={a.name:ah(a)for a in bpy.data.actions};mesh_hashes={o.name:mh(o)for o in objects};bind=pipeline.skeleton(rig)
samples={};worlds={};source_floors={}
for name in changed:
 a=bpy.data.actions[name];frames=[i*.5 for i in range(int(a.frame_range[1])*2+1)];samples[name]=[];worlds[name]=[];source_floors[name]=[]
 for f in frames:
  samples[name].append(sample(a,f));worlds[name].append({n:wm(n).copy()for n in ['pelvis','spine_03','Head','thigh_l','thigh_r','foot_l','foot_r']});source_floors[name].append(floor())
controls={}
for side in ['l','r']:
 targets=[]
 for kind in ['ankle','knee','rotation']:
  o=bpy.data.objects.new('Stable_'+kind+'_'+side,None);scene.collection.objects.link(o);targets.append(o)
 ankle,pole,rotation=targets;rotation.rotation_mode='QUATERNION'
 ik=rig.pose.bones['calf_'+side].constraints.new('IK');ik.target=ankle;ik.pole_target=pole;ik.pole_angle=-math.pi/2;ik.chain_count=2;ik.use_stretch=False;ik.iterations=150;ik.mute=True
 cr=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');cr.target=rotation;cr.owner_space='WORLD';cr.target_space='WORLD';cr.mix_mode='REPLACE';cr.influence=1;cr.mute=True
 controls[side]=(ankle,pole,rotation,ik,cr)
root=rig.pose.bones['root'];world_to_root=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()
reports=[]
for name in changed:
 frames=[i*.5 for i in range(len(samples[name]))];values_list=samples[name];originals=worlds[name];end=frames[-1]
 means={n:meanq([v[n][1]for v in values_list[:-1]])for n in strengths}
 center=sum((v['pelvis'].translation for v in originals[:-1]),Vector())/(len(originals)-1)
 # Find one constant body height that leaves both original ankle tracks reachable.
 # This is a body-height limit; the maintained native IK performs all leg solving.
 ceilings=[]
 for values,world in zip(values_list,originals):
  restore(values)
  for n,k in strengths.items():rig.pose.bones[n].rotation_quaternion=means[n].slerp(values[n][1],k)
  bpy.context.view_layer.update();current=wm('pelvis').translation;goal=center+(world['pelvis'].translation-center)*Vector((.20,.30,.20))
  for side in controls:
   hip=wm('thigh_'+side).translation+(goal-current);ankle=world['foot_'+side].translation
   reach=(rig.pose.bones['thigh_'+side].length+rig.pose.bones['calf_'+side].length)*rig.matrix_world.to_scale().x*.992
   horizontal=(hip.x-ankle.x)**2+(hip.y-ankle.y)**2
   ceiling=ankle.z+math.sqrt(max(0,reach*reach-horizontal))-(hip.z-goal.z)
   ceilings.append(ceiling-(world['pelvis'].translation.z-center.z)*.20)
 center.z=min(center.z,min(ceilings)-.004)
 baked=[];evaluated=[];ankle_errors=[];floors=[]
 for i,(f,values,world)in enumerate(zip(frames,values_list,originals)):
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  restore(values)
  for n,k in strengths.items():rig.pose.bones[n].rotation_quaternion=means[n].slerp(values[n][1],k)
  bpy.context.view_layer.update();current=wm('pelvis').translation;old_center=sum((v['pelvis'].translation for v in originals[:-1]),Vector())/(len(originals)-1)
  goal=center+(world['pelvis'].translation-old_center)*Vector((.20,.30,.20));root.location+=world_to_root@(goal-current);bpy.context.view_layer.update()
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   m=world['foot_'+side];ankle.location=m.translation;rotation.rotation_quaternion=m.to_quaternion();hip=wm('thigh_'+side).translation
   pole.location=Vector(((hip.x+ankle.location.x)*.5,goal.y-.80,hip.z-.30));ik.mute=False;cr.mute=False
  bpy.context.view_layer.update();solved={n:rig.pose.bones[n].matrix.copy()for n in legs}
  ankle_errors.extend((wm('foot_'+side).translation-world['foot_'+side].translation).length for side in controls)
  for *_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in legs:
   rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  floors.append(floor());evaluated.append({n:wm(n).copy()for n in ['pelvis','spine_03','Head']});baked.append(pose())
 assert max(ankle_errors)<.001,(name,max(ankle_errors));assert min(floors)>-.005,(name,min(floors))
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
 before,after=metrics(originals),metrics(evaluated)
 report={'clip':name,'before':before,'after':after,'pelvisWorldTranslationExcursion':[.20,.30,.20],'localRotationExcursion':strengths,'maxAnklePathErrorMetres':max(ankle_errors),'soleFloorRange': [min(floors),max(floors)],'constantBodyHeightAdjustmentMetres':center.z-old_center.z,'sourceStrideRetained':True,'nativeIK':'Blender two bones, no stretch; source world ankle rotation retained; baked FK only in Cocos'}
 reports.append(report);print('BODY_STABILIZED',json.dumps(report),flush=True)
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
m=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
for r in reports:
 for c in [m['clips'][r['clip']],m['libraryMotion']['clips'][r['clip']]]:c['bodyStabilization']=r
m.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v4',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
(BASE/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'beforeActions':before_actions,'afterActions':after_actions,'changedClips':changed,'unchangedClips':[n for n in before_actions if n not in changed],'meshHashes':mesh_hashes,'bindHash':bind,'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'bodyStabilization':reports},indent=2)+'\n',encoding='utf-8')
