"""Refine the accepted UAL walk with native Blender FK; preserve character assets.
Only walk/walk_staff change. Reuse the current v3 character and contact helpers.
"""
from pathlib import Path
import bpy,json,sys,hashlib,math
from mathutils import Quaternion,Vector
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
from weapon_carry_calibration import apply_bow_carry_calibration
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-hairstyles-v3/raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];scene=bpy.context.scene;scene.render.fps=30
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
feet=[o for o in objects if o.get('nativePart')=='feet']
assert feet

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices],[m.name for m in o.data.materials])).encode()).hexdigest()
def action_hash(a):
 return hashlib.sha256(repr([(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves]).encode()).hexdigest()
def assign(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def time(f):scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
def pose():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}
def restore(values):
 for n,(l,q,s)in values.items():
  p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.location=l;p.rotation_quaternion=q;p.scale=s

def floor():
 low=1e9;deps=bpy.context.evaluated_depsgraph_get()
 for o in feet:
  e=o.evaluated_get(deps);m=e.to_mesh();low=min(low,min((e.matrix_world@v.co).z for v in m.vertices));e.to_mesh_clear()
 return low

def meanq(values):
 first=values[0];acc=[0.,0.,0.,0.]
 for q in values:
  q=q.copy();q.make_compatible(first)
  for j in range(4):acc[j]+=q[j]
 q=Quaternion(acc);q.normalize();return q
before_mesh={o.name:digest(o)for o in objects};before_actions={a.name:action_hash(a)for a in bpy.data.actions};bind=pipeline.skeleton(rig)
frames=[i/2 for i in range(81)];reports=[]
for name in ['walk','walk_staff']:
 old=bpy.data.actions[name];assign(old);samples=[]
 for f in frames:time(f);samples.append(pose())
 means={n:meanq([v[n][1]for v in samples[:-1]])for n in rig.pose.bones.keys()}
 center=sum((v['pelvis'][0]for v in samples[:-1]),Vector())/(len(samples)-1)
 # Retain connected leg/ankle timing. Quiet the pelvis and shoulder counter-sway.
 strengths={'pelvis':.68,'spine_02':.60,'spine_03':.60,'neck_01':.65,'clavicle_l':.45,'clavicle_r':.45,'upperarm_l':.78,'upperarm_r':.78,'lowerarm_l':.82,'lowerarm_r':.82,'hand_l':.82,'hand_r':.82}
 if name=='walk_staff':
  for n in ['clavicle_r','upperarm_r','lowerarm_r','hand_r']:strengths.pop(n)
 # Relax the empty-hand elbow and wrist angles; retain the staff grip chain.
 for n in ['lowerarm_l','lowerarm_r','hand_l','hand_r']:
  if name=='walk_staff'and n.endswith('_r'):continue
  means[n]=Quaternion().slerp(means[n],.86 if n.startswith('lowerarm')else .72)
 fingers=[n for n in rig.pose.bones.keys()if any(n.startswith(k+'_')for k in ['index','middle','ring','pinky'])and '_04_'not in n and not(name=='walk_staff'and n.endswith('_r'))]
 fingers += [n for n in ['thumb_03_l','thumb_03_r']if not(name=='walk_staff'and n.endswith('_r'))]
 keyed=list(strengths)+fingers
 old.name='SOURCE_'+name;action=old.copy();action.name=name;action.use_fake_user=True;assign(action);previous={};ground=[];points=[]
 root=rig.pose.bones['root'];up=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,1))
 for f,values in zip(frames,samples):
  restore(values)
  for n,k in strengths.items():rig.pose.bones[n].rotation_quaternion=means[n].slerp(values[n][1],k)
  for n in fingers:rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(values[n][1],.48 if n.startswith('thumb')else .46)
  loc=rig.pose.bones['pelvis'].location
  for j,k in enumerate([.65,.80,.65]):loc[j]=center[j]+(loc[j]-center[j])*k
  bpy.context.view_layer.update();root.location+=up*(.003-floor());bpy.context.view_layer.update();ground.append(floor())
  points.append({n:list((rig.matrix_world@rig.pose.bones[n].matrix).translation)for n in ['foot_l','foot_r']})
  for n in keyed:
   p=rig.pose.bones[n];q=p.rotation_quaternion.copy();q.normalize()
   if n in previous:q.make_compatible(previous[n])
   previous[n]=q.copy();p.rotation_quaternion=q;p.keyframe_insert('rotation_quaternion',frame=f)
  rig.pose.bones['pelvis'].keyframe_insert('location',frame=f);root.keyframe_insert('location',frame=f)
 for c in action.fcurves:
  if c.data_path in ['pose.bones["root"].location','pose.bones["pelvis"].location']or any(c.data_path=='pose.bones["'+n+'"].rotation_quaternion'for n in keyed):
   for k in c.keyframe_points:k.interpolation='LINEAR'
 bpy.data.actions.remove(old)
 speeds=[]
 for n in ['foot_l','foot_r']:
  low=min(p[n][2]for p in points)
  for a,b in zip(points,points[1:]):
   if max(a[n][2],b[n][2])<low+.045:speeds.append(math.hypot(b[n][0]-a[n][0],b[n][1]-a[n][1])*60)
 nominal=sorted(speeds)[len(speeds)//2]
 reports.append({'clip':name,'duration':40/30,'nominalSpeed':nominal,'source':'Current accepted UAL1 Walk_Loop with connected FK refinement','rotationalExcursion':strengths,'relaxedEmptyHandFingerBones':fingers,'emptyHandFingerBendFactor':.46,'emptyHandElbowMeanAngleFactor':.86,'emptyHandWristMeanAngleFactor':.72,'pelvisTranslationExcursion':[.65,.8,.65],'soleFloorMin':min(ground),'soleFloorMax':max(ground),'plantedFootSamples':len(speeds),'staffGripLocalChannelsPreserved':name=='walk_staff'})
assert before_mesh=={o.name:digest(o)for o in objects};assert bind==pipeline.skeleton(rig)
after_actions={a.name:action_hash(a)for a in bpy.data.actions};assert all(before_actions[n]==h for n,h in after_actions.items()if n not in ['walk','walk_staff']);assert len(after_actions)==14
assign(bpy.data.actions['idle']);time(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
manifest=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
for r in reports:
 c=manifest['clips'][r['clip']];c['nominalSpeed']=r['nominalSpeed'];manifest['libraryMotion']['clips'][r['clip']]['nominalSpeedMetresPerSecond']=r['nominalSpeed'];manifest['libraryMotion']['clips'][r['clip']]['locomotionRefinement']=r;c['locomotionRefinement']=r;c['floor']={'minFootZ':r['soleFloorMin'],'maxFootMinZ':r['soleFloorMax'],'method':'Evaluated shoes, root-only vertical contact correction'}
manifest.update(source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),locomotionRevision='locomotion-v2',locomotionReview=(BASE/'README.md').relative_to(ROOT).as_posix())
apply_bow_carry_calibration(manifest,ROOT)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
proof={'all16MeshGeometryUVWeightsMaterialsPreserved':True,'allFourHairstylesPreserved':True,'bindPreserved':True,'bindHash':bind,'meshHashes':before_mesh,'beforeActions':before_actions,'afterActions':after_actions,'unchangedClips':[n for n in before_actions if before_actions[n]==after_actions[n]],'changedClips':['walk','walk_staff'],'walk':reports,'runtimeGLBSHA256':hashlib.sha256((BASE/'raphael-polish.glb').read_bytes()).hexdigest()}
(BASE/'source-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('LOCOMOTION_REFINED',json.dumps({'walk':reports,'skins':len(objects),'unchangedClips':proof['unchangedClips']}),flush=True)
