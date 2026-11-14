"""Adapt existing CC0 UAL motion to the approved 2D gait with Blender native IK/FK.
Only four locomotion actions change. No mesh, skin, rest bone or runtime IK edits.
"""
from pathlib import Path
import bpy,json,sys,hashlib,math,statistics
from mathutils import Vector,Quaternion,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
from weapon_carry_calibration import apply_bow_carry_calibration
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-locomotion-v2/raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
feet=[o for o in objects if o.get('nativePart')=='feet']
changed=['walk','walk_staff','run','run_staff']
legs=['thigh_l','calf_l','foot_l','ball_l','thigh_r','calf_r','foot_r','ball_r']

def ah(a):return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def mh(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def pose():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}
def restore(v,update=True):
 for n,(l,q,s)in v.items():
  p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.location=l;p.rotation_quaternion=q;p.scale=s
 if update:bpy.context.view_layer.update()
def sample(a,f):
 rig.animation_data.action=None
 for c in a.fcurves:
  path,attr=c.data_path.rsplit('.',1);getattr(rig.path_resolve(path),attr)[c.array_index]=c.evaluate(f)
 bpy.context.view_layer.update();return pose()
def floor():
 low=1e9;deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  e=o.evaluated_get(deps);m=e.to_mesh();low=min(low,min((e.matrix_world@v.co).z for v in m.vertices));e.to_mesh_clear()
 return low
def whead(n):return rig.matrix_world@rig.pose.bones[n].head
def meanq(qs):
 anchor=qs[0];v=Vector((0,0,0,0))
 for q in qs:
  q=q.copy();q.make_compatible(anchor);v+=Vector(q)
 q=Quaternion(v);q.normalize();return q
before_actions={a.name:ah(a)for a in bpy.data.actions};mesh_hashes={o.name:mh(o)for o in objects};bind=pipeline.skeleton(rig)
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'))as(src,dst):dst.actions=['walk','run']
library=dict(zip(['walk','run'],dst.actions))
source_hash={n:ah(a)for n,a in library.items()}
samples={};raw={};floors={}
for name in changed:
 end=28 if name.startswith('run')else 40;frames=[i*.5 for i in range(end*2+1)]
 samples[name]=[sample(bpy.data.actions[name],f)for f in frames]
 raw[name]=[];floors[name]=[]
 for f in frames:
  values=sample(library['run'if name.startswith('run')else'walk'],f);raw[name].append(values);floors[name].append(floor())
 # Remove inherited end-point drift across the entire cycle, before any IK.
 first,last=samples[name][0],samples[name][-1]
 for i,v in enumerate(samples[name]):
  t=i/(len(frames)-1)
  for n,(l,q,s)in list(v.items()):
   correction=last[n][1].inverted()@first[n][1]
   v[n]=(l-(last[n][0]-first[n][0])*t,q@Quaternion().slerp(correction,t),s)
for a in library.values():bpy.data.actions.remove(a)

controls={}
for side in ['l','r']:
 nodes=[]
 for kind in ['ankle','knee','rotation']:
  o=bpy.data.objects.new('Gait_'+kind+'_'+side,None);scene.collection.objects.link(o);nodes.append(o)
 ankle,pole,rotation=nodes;ik=rig.pose.bones['calf_'+side].constraints.new('IK');ik.target=ankle;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=100
 cr=rig.pose.bones['foot_'+side].constraints.new('COPY_ROTATION');cr.target=rotation;cr.owner_space='WORLD';cr.target_space='WORLD';cr.mix_mode='REPLACE';cr.influence=0
 controls[side]=(ankle,pole,rotation,ik,cr)
# Calibrate the native solver's roll to the existing connected knee plane.
angles={}
for side,(_,_,_,ik,_)in controls.items():ik.mute=True
restore(raw['walk'][10])
reference={s:(whead('thigh_'+s),whead('calf_'+s),whead('foot_'+s))for s in controls}
for side,(ankle,pole,rotation,ik,cr)in controls.items():
 hip,knee,foot=reference[side];axis=(foot-hip).normalized();projection=hip+axis*(knee-hip).dot(axis);pole.location=knee+(knee-projection).normalized()*.8;ankle.location=foot
 errors=[];ik.mute=False
 for angle in [0,math.pi/2,-math.pi/2,math.pi]:
  ik.pole_angle=angle;bpy.context.view_layer.update();errors.append(((whead('calf_'+side)-knee).length,angle))
 ik.pole_angle=min(errors)[1];angles[side]=ik.pole_angle;ik.mute=True

reports=[]
for name in changed:
 running=name.startswith('run');end=28 if running else 40;frames=[i*.5 for i in range(end*2+1)]
 values_list=samples[name];source=raw[name];baked=[];contact=[];positions=[];constraints_error=[]
 pelvis_mean=meanq([v['pelvis'][1]for v in source[:-1]])
 center=sum((v['pelvis'][0]for v in source[:-1]),Vector())/(len(source)-1)
 for i,(f,base,original)in enumerate(zip(frames,values_list,source)):
  for _,_,_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  values={n:(l.copy(),q.copy(),s.copy())for n,(l,q,s)in base.items()}
  for n in ['root','pelvis']+legs:values[n]=tuple(v.copy()for v in original[n])
  l,q,s=values['pelvis'];l=center+(l-center)*Vector((.45,.65,.72));q=pelvis_mean.slerp(q,.62);values['pelvis']=(l,q,s)
  restore(values)
  # Connected shoulder FK: bring the entire arm chain closer to the torso.
  for side in ['l','r']:
   if name.endswith('_staff')and side=='r':continue
   p=rig.pose.bones['upperarm_'+side];m=p.matrix.copy();direction=m.to_3x3()@Vector((0,1,0));goal=direction.copy();goal.x*=.62 if running else .58;goal.normalize()
   delta=direction.normalized().rotation_difference(goal);p.matrix=Matrix.LocRotScale(m.translation,delta@m.to_quaternion(),m.to_scale());bpy.context.view_layer.update()
  # Target the original authored forward/back arc; narrow only the lateral lane.
  pelvis=whead('pelvis');targets={}
  for side,(ankle,pole,rotation,ik,cr)in controls.items():
   sign=1 if side=='l'else-1;hip=whead('thigh_'+side);foot=whead('foot_'+side);target=foot.copy()
   target.x=pelvis.x*.25+sign*(.065 if running else .073)
   target.y=pelvis.y+(foot.y-pelvis.y)*(.66 if running else .90)
   target.z=.105+max(-.025,foot.z-.105)*(.72 if running else .62)
   # Keep the target inside the unchanged two-bone chain's reachable sphere.
   reach=(rig.pose.bones['thigh_'+side].length+rig.pose.bones['calf_'+side].length)*rig.matrix_world.to_scale().x*.997
   delta=target-hip
   if delta.length>reach:target=hip+delta.normalized()*reach
   ankle.location=target;pole.location=Vector(((hip.x+target.x)*.5,pelvis.y-.80,hip.z-.30))
   m=rig.matrix_world@rig.pose.bones['foot_'+side].matrix;e=m.to_quaternion().to_euler('ZXY');e.z=math.radians(-sign*2.0);e.y*=.2
   rotation.rotation_mode='QUATERNION';rotation.rotation_quaternion=e.to_quaternion();targets[side]=target
  for _,_,_,ik,cr in controls.values():ik.mute=False;cr.mute=False
  bpy.context.view_layer.update();solved={n:rig.pose.bones[n].matrix.copy()for n in legs}
  constraints_error.extend((whead('foot_'+s)-target).length for s,target in targets.items())
  for _,_,_,ik,cr in controls.values():ik.mute=True;cr.mute=True
  bpy.context.view_layer.update()
  for n in legs:
   rig.pose.bones[n].matrix=solved[n];bpy.context.view_layer.update()
  desired=.003+(min(.065,max(0,floors[name][i]-min(floors[name]))*.30)if running else 0)
  root=rig.pose.bones['root'];up=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,1));root.location+=up*(desired-floor());bpy.context.view_layer.update()
  contact.append(floor());positions.append({s:{'hip':list(whead('thigh_'+s)),'knee':list(whead('calf_'+s)),'ankle':list(whead('foot_'+s)),'toe':list(whead('ball_'+s))}for s in controls});baked.append(pose())
 # Exact cycle closure on all channels in these four actions.
 baked[-1]={n:tuple(x.copy()for x in v)for n,v in baked[0].items()}
 old=bpy.data.actions[name];old.name='REPLACED_'+name;action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action;previous={}
 for f,values in zip(frames,baked):
  restore(values,False)
  for p in rig.pose.bones:
   q=p.rotation_quaternion.copy();q.normalize()
   if p.name in previous:q.make_compatible(previous[p.name])
   previous[p.name]=q.copy();p.rotation_quaternion=q
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=f)
 for c in action.fcurves:
  for key in c.keyframe_points:key.interpolation='LINEAR'
 bpy.data.actions.remove(old);rig.animation_data.action=None
 velocities=[]
 for side in controls:
  for a,b in zip(positions,positions[1:]):
   if max(a[side]['ankle'][2],b[side]['ankle'][2])<.16:velocities.append(abs(b[side]['ankle'][1]-a[side]['ankle'][1])*60)
 nominal=statistics.median(velocities)
 report={'clip':name,'duration':end/30,'nominalSpeed':nominal,'solver':'Blender native IK, two connected bones, no stretch; world CopyRotation foot; baked FK only in game','kneePoleAngles':angles,'halfAnkleLaneMetres':.065 if running else .073,'forwardArcFactor':.66 if running else .90,'swingHeightFactor':.72 if running else .62,'maxIKTargetError':max(constraints_error),'floorRange':[min(contact),max(contact)],'staffRightArmLocalChannelsPreserved':name.endswith('_staff'),'exactLoopClosure':True}
 reports.append(report);(BASE/(name+'-samples.json')).write_text(json.dumps({'report':report,'frames':positions},indent=2),encoding='utf-8');print('GAIT',json.dumps(report),flush=True)
for side,(ankle,pole,rotation,ik,cr)in controls.items():
 rig.pose.bones['calf_'+side].constraints.remove(ik);rig.pose.bones['foot_'+side].constraints.remove(cr)
 for o in [ankle,pole,rotation]:bpy.data.objects.remove(o,do_unlink=True)
after_actions={a.name:ah(a)for a in bpy.data.actions}
assert len(after_actions)==14;assert all(before_actions[n]==h for n,h in after_actions.items()if n not in changed)
assert mesh_hashes=={o.name:mh(o)for o in objects};assert bind==pipeline.skeleton(rig)
rig.animation_data.action=bpy.data.actions['idle'];rig.animation_data.action_slot=bpy.data.actions['idle'].slots[0];scene.frame_set(1);scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
manifest=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
for report in reports:
 name=report['clip']
 for c in [manifest['clips'][name],manifest['libraryMotion']['clips'][name]]:
  c['nominalSpeedMetresPerSecond']=report['nominalSpeed'];c['nominalSpeed']=report['nominalSpeed'];c['locomotionRefinement']=report;c['floor']={'minFootZ':report['floorRange'][0],'maxFootMinZ':report['floorRange'][1],'method':'Evaluated shoes, root-only vertical contact correction; original air interval retained at reduced clearance'}
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v3',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
apply_bow_carry_calibration(manifest,ROOT)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(BASE/'source-verification.json').write_text(json.dumps({'meshHashes':mesh_hashes,'bindHash':bind,'beforeActions':before_actions,'afterActions':after_actions,'changedClips':changed,'unchangedClips':[n for n in before_actions if n not in changed],'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'nativeLibraryActionHashes':source_hash,'reference2D':['source-art/characters/2d-concepts/locomotion-repair-v3/shared-body-walk.jpg','source-art/characters/2d-concepts/locomotion-repair-v3/shared-body-run.jpg'],'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest(),'gaits':reports},indent=2)+'\n',encoding='utf-8')
