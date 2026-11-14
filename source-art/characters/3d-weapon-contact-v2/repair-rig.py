"""Adapt the existing hero with Blender's native IK, then bake ordinary FBX clips.
No runtime IK, new model, skin/UV edits, dependencies, or generated imagery.
"""
from pathlib import Path
import bpy,json,math,hashlib,sys
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'src/.tmp/native-production/source/raphael.blend'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
scene.render.fps=30
rig=bpy.data.objects['raphael_Native65']
original={a.name:a for a in bpy.data.actions}
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}

def assign(action):
    rig.animation_data_create();rig.animation_data.action=action
    if action and action.slots:rig.animation_data.action_slot=action.slots[0]
def time(f):scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
def snapshot():return {p.name:p.matrix_basis.copy() for p in rig.pose.bones}
def restore(values):
    for name,matrix in values.items():rig.pose.bones[name].matrix_basis=matrix
    bpy.context.view_layer.update()
def wp(name):return (rig.matrix_world@rig.pose.bones[name].matrix).translation.copy()
assign(original['idle']);time(0)
idle=snapshot()
assign(original['attack_bow'])
samples=[]
for f in range(50):time(f);samples.append(snapshot())

# Load the same final bow export used by Cocos; preserve importer axis transforms.
prior=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'src/.tmp/native-production/props/bow.fbx'))
prop_objects=list(set(bpy.data.objects)-prior)
bow=next(o for o in prop_objects if o.type=='MESH')
matrix=bow.matrix_world.copy();bow.parent=rig;bow.parent_type='BONE';bow.parent_bone='attach_bow_l'
bow.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['attach_bow_l'].length,0))
bow.matrix_basis=Matrix.Rotation(math.pi,4,'Z')@matrix
basis=bow.data.shape_keys.key_blocks[0]
draw=next(k for k in bow.data.shape_keys.key_blocks if k.name!='Basis')
deltas=[(a.co-b.co).length for a,b in zip(draw.data,basis.data)]
nock_indices=[i for i,v in enumerate(deltas) if v>=max(deltas)*.999]
def nock():return bow.matrix_world@(sum((basis.data[i].co.lerp(draw.data[i].co,draw.value) for i in nock_indices),Vector())/len(nock_indices))

controls={}
for side in ['l','r']:
    goal=bpy.data.objects.new('QA_Wrist_'+side,None);pole=bpy.data.objects.new('QA_Elbow_'+side,None);orient=bpy.data.objects.new('QA_Hand_'+side,None)
    for o in [goal,pole,orient]:scene.collection.objects.link(o)
    ik=rig.pose.bones['lowerarm_'+side].constraints.new('IK');ik.name='AuthoredContactIK';ik.target=goal;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=500
    rotation=rig.pose.bones['hand_'+side].constraints.new('COPY_ROTATION');rotation.target=orient;rotation.owner_space='WORLD';rotation.target_space='WORLD';rotation.mix_mode='REPLACE'
    controls[side]=(goal,pole,orient,ik,rotation)
def disable():
    for goal,pole,orient,ik,rotation in controls.values():ik.influence=0;rotation.influence=0

torso=[o for o in bpy.data.objects if o.type=='MESH' and '_native_body_' in o.name]
def body_tree():
    vertices=[];polys=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in torso:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();offset=len(vertices)
        vertices.extend(ev.matrix_world@v.co for v in mesh.vertices)
        polys.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vertices,polys)
def clearance(point,tree):
    nearest,normal,index,distance=tree.find_nearest(point)
    return distance if (point-nearest).dot(normal)>=0 else -distance
def metrics(f):
    tree=body_tree()
    return {'frame':f,'joints':{n:list(wp(n)) for n in ['upperarm_r','lowerarm_r','hand_r','upperarm_l','lowerarm_l','hand_l','attach_arrow_r','attach_bow_l']},'rightWristTorsoClearance':clearance(wp('hand_r'),tree),'leftWristTorsoClearance':clearance(wp('hand_l'),tree),'rightElbowTorsoClearance':clearance(wp('lowerarm_r'),tree),'nockGap':(wp('attach_arrow_r')-nock()).length}

assign(None);disable();restore(samples[40]);draw.value=1;bpy.context.view_layer.update()
before=metrics(40)
corrected=[];rows=[]
for f,values in enumerate(samples):
    # Retain the author's full-draw stance while drawing the actual morph.
    # The old swing-in and chain-3 contact bake folded the drawing arm across
    # the torso. Here the arrow fingers follow the real moving string instead.
    disable();assign(None);restore(samples[40])
    # Keep the shoulder anchored to the original native idle clavicle. The old
    # chain-3 solve dragged this shoulder behind the chest and folded the elbow in.
    rig.pose.bones['clavicle_r'].matrix_basis=idle['clavicle_r']
    bpy.context.view_layer.update()
    follow=max(0,(f-40)/9)
    draw.value=min(1,f/40) if f<=40 else max(0,1-(f-40)/3)
    goal,pole,orient,ik,rotation=controls['l']
    hand=rig.matrix_world@rig.pose.bones['hand_l'].matrix
    reach=min(1,f/40)
    goal.location=Vector((.16+(.3456886-.16)*reach,-.14+(-.36+.14)*reach,1.70-.025*follow))
    pole.location=Vector((.65,-.14,1.63));orient.matrix_world=Matrix.LocRotScale(hand.translation,hand.to_quaternion(),Vector((1,1,1)))
    ik.pole_angle=0;ik.influence=1;rotation.influence=1;bpy.context.view_layer.update()
    goal,pole,orient,ik,rotation=controls['r']
    hand=rig.matrix_world@rig.pose.bones['hand_r'].matrix
    offset=wp('attach_arrow_r')-hand.translation
    if f<=40:
        goal.location=nock()-offset
        held_goal=goal.location.copy()
    else:goal.location=held_goal+Vector((-.03,.07,.025))*follow
    pole.location=Vector((-.55,.46,1.62));orient.matrix_world=Matrix.LocRotScale(hand.translation,hand.to_quaternion(),Vector((1,1,1)))
    ik.pole_angle=math.pi;ik.influence=1;rotation.influence=1;bpy.context.view_layer.update()
    solved={name:rig.pose.bones[name].matrix.copy() for name in ['upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r']}
    disable();bpy.context.view_layer.update()
    for name,matrix in solved.items():rig.pose.bones[name].matrix=matrix;bpy.context.view_layer.update()
    corrected.append((f,snapshot()));rows.append(metrics(f))

for side,(goal,pole,orient,ik,rotation) in controls.items():
    rig.pose.bones['lowerarm_'+side].constraints.remove(ik);rig.pose.bones['hand_'+side].constraints.remove(rotation)
    for obj in [goal,pole,orient]:bpy.data.objects.remove(obj,do_unlink=True)

old=original['attack_bow'];old.name='Source_attack_bow'
action=bpy.data.actions.new('attack_bow');action.use_fake_user=True;assign(action)
previous={}
for f,values in corrected:
    restore(values)
    for p in rig.pose.bones:
        p.rotation_mode='QUATERNION';q=p.rotation_quaternion.copy();q.normalize()
        if p.name in previous:q.make_compatible(previous[p.name])
        previous[p.name]=q.copy();p.rotation_quaternion=q
        for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=f)
for curve in action.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
bpy.data.actions.remove(old)

for obj in prop_objects:bpy.data.objects.remove(obj,do_unlink=True)

# The native spell is an empty off-hand cast. Keep the staff hand outside the
# torso, with the author's closed idle fingers and a stable upright palm frame.
assign(original['idle']);time(0)
staff_hand_rotation=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).to_quaternion()
right_fingers={p.name:p.matrix_basis.copy() for p in rig.pose.bones if p.name.endswith('_r') and any(t in p.name for t in ['index_','middle_','ring_','pinky_','thumb_'])}
staff_reports={}
for source_name,result_name in [('idle','idle_staff'),('attack_staff','attack_staff')]:
    source_action=original[source_name];source_rows=[]
    end=source_action.frame_range[1]
    for f in range(math.ceil(end)+1):assign(source_action);time(min(f,end));source_rows.append((min(f,end),snapshot()))
    goal=bpy.data.objects.new('QA_StaffWrist',None);pole=bpy.data.objects.new('QA_StaffElbow',None);orient=bpy.data.objects.new('QA_StaffPalm',None)
    for obj in [goal,pole,orient]:scene.collection.objects.link(obj)
    ik=rig.pose.bones['lowerarm_r'].constraints.new('IK');ik.target=goal;ik.pole_target=pole;ik.chain_count=2;ik.use_stretch=False;ik.iterations=500
    copy=rig.pose.bones['hand_r'].constraints.new('COPY_ROTATION');copy.target=orient;copy.owner_space='WORLD';copy.target_space='WORLD';copy.mix_mode='REPLACE'
    baked=[];checks=[]
    for f,values in source_rows:
        ik.influence=0;copy.influence=0;assign(None);restore(values)
        for name,matrix in right_fingers.items():rig.pose.bones[name].matrix_basis=matrix
        bpy.context.view_layer.update()
        goal.location=Vector((-.39,-.14,1.07+.025*math.sin(f/max(1,end)*math.pi)))
        pole.location=Vector((-.65,.10,1.27));orient.matrix_world=Matrix.LocRotScale(goal.location,staff_hand_rotation,Vector((1,1,1)))
        ik.pole_angle=0;ik.influence=1;copy.influence=1;bpy.context.view_layer.update()
        solved={n:rig.pose.bones[n].matrix.copy() for n in ['upperarm_r','lowerarm_r','hand_r']}
        ik.influence=0;copy.influence=0;bpy.context.view_layer.update()
        for name,matrix in solved.items():rig.pose.bones[name].matrix=matrix;bpy.context.view_layer.update()
        baked.append((f,snapshot()));tree=body_tree();checks.append({'frame':f,'wristClearance':clearance(wp('hand_r'),tree),'elbowClearance':clearance(wp('lowerarm_r'),tree)})
    rig.pose.bones['lowerarm_r'].constraints.remove(ik);rig.pose.bones['hand_r'].constraints.remove(copy)
    for obj in [goal,pole,orient]:bpy.data.objects.remove(obj,do_unlink=True)
    if result_name==source_name:bpy.data.actions.remove(source_action)
    new_action=bpy.data.actions.new(result_name);new_action.use_fake_user=True;assign(new_action);previous={}
    for f,values in baked:
        restore(values)
        for p in rig.pose.bones:
            p.rotation_mode='QUATERNION';q=p.rotation_quaternion.copy();q.normalize()
            if p.name in previous:q.make_compatible(previous[p.name])
            previous[p.name]=q.copy();p.rotation_quaternion=q
            for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=f)
    for curve in new_action.fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
    staff_reports[result_name]=checks

assign(original['idle']);time(0)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'raphael-contact-v2.blend'),relative_remap=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and '_native_' in o.name]
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
target=OUT/'raphael.fbx'
# Keep the same ../native-shared layout after installing this FBX into the
# actor resource folder. Images are already packed/loaded in the source blend.
for image in bpy.data.images:
    name=Path(bpy.path.abspath(image.filepath)).name
    if (ROOT/'src/cocos/assets/resources/actors/native-shared/textures'/name).is_file():
        image.filepath=str(OUT.parent/'native-shared/textures'/name)
bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',colors_type='NONE',embed_textures=False,use_custom_props=True)
assert max(abs(a-b) for n in rest for row,other in zip(rest[n],rig.data.bones[n].matrix_local) for a,b in zip(row,other))<1e-5
report={'tool':'Blender 4.5.15 native two-bone IK with elbow pole targets and CopyRotation, baked; no runtime solver','source':str(SOURCE.relative_to(ROOT)),'beforeHold':before,'afterHold':rows[40],'frames':rows,'staff':staff_reports,'fbxSHA256':hashlib.sha256(target.read_bytes()).hexdigest()}
(OUT/'rig-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('CONTACT_REPORT',json.dumps({k:report[k] for k in ['beforeHold','afterHold','fbxSHA256']}),flush=True)
