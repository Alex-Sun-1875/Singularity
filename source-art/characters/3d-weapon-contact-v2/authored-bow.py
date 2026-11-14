"""Restore the complete authored archery pose before adapting prop contact.
Only rigid attachments and native morph data are calibrated; no shifted wrists.
"""
from pathlib import Path
import bpy,json,math,sys
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'src/.tmp/native-production/source/raphael.blend'))
scene=bpy.context.scene;scene.render.fps=30;rig=bpy.data.objects['raphael_Native65']
def assign(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def time(f):scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
def pose():return {p.name:p.matrix_basis.copy() for p in rig.pose.bones}
def set_pose(values):
    for n,m in values.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
def wp(name):return (rig.matrix_world@rig.pose.bones[name].matrix).translation.copy()
original=bpy.data.actions['attack_bow'];canonical=[]
for f in range(50):assign(original);time(f);canonical.append(pose())
# Calibrate the established held-arrow mesh axis from the old full-hold
# attachment contract. This is a prop axis, never a wrist rotation.
assign(original);time(40)
arrow_axis=(rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix).to_3x3().inverted()@(wp('attach_bow_l')-wp('attach_arrow_r')).normalized()
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'),link=False) as (src,dst):
    dst.actions=['RETARGET__Ranged_Bow_Draw','RETARGET__Ranged_Bow_Release']
draw_action,release_action=dst.actions
boots=[o for o in bpy.data.objects if o.type=='MESH' and '_native_feet_' in o.name]
samples=[];rows=[]
timeline=[('draw',f) for f in range(14,41)]+[('release',f) for f in range(1,10)]
for f,(phase,sf) in enumerate(timeline):
    assign(draw_action if phase=='draw' else release_action);time(sf+1)
    values=pose();assign(None)
    # Raw retarget contains the original complete pelvis/shoulder/arm motion.
    # Keep the target's established finger grip and rigid attachment animation.
    for n,m in canonical[sf if phase=='draw' else 40+sf].items():
        # Reuse the established native standing legs. The cross-rig source's
        # lower-body transfer lifts a boot; retain its complete upper-body
        # rotations, with no IK or independently moved arm/hand joints.
        if n in ['root','pelvis'] or n.startswith(('thigh_','calf_','foot_','ball_','index_','middle_','ring_','pinky_','thumb_','attach_')):values[n]=m
    set_pose(values)
    deps=bpy.context.evaluated_depsgraph_get();sole=[]
    for o in boots:
        ev=o.evaluated_get(deps);mesh=ev.to_mesh();sole.extend((ev.matrix_world@v.co).z for v in mesh.vertices);ev.to_mesh_clear()
    root=rig.pose.bones['root'];offset=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,.003-min(sole)))
    root.location+=offset;bpy.context.view_layer.update()
    samples.append((f,pose()));rows.append({'frame':f,'sourcePhase':phase,'sourceFrame':sf,'joints':{n:list(wp(n)) for n in ['upperarm_l','lowerarm_l','hand_l','upperarm_r','lowerarm_r','hand_r','attach_bow_l','attach_arrow_r']}})

original.name='RejectedContactBow'
a=bpy.data.actions.new('attack_bow');a.use_fake_user=True;assign(a);previous={}
for f,values in samples:
    set_pose(values)
    for p in rig.pose.bones:
        p.rotation_mode='QUATERNION';q=p.rotation_quaternion.copy();q.normalize()
        if p.name in previous:q.make_compatible(previous[p.name])
        previous[p.name]=q.copy();p.rotation_quaternion=q
        for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=f)
for curve in a.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
for old in [original,draw_action,release_action]:bpy.data.actions.remove(old)
# Inspect the actual bow shape against the untouched authored hand positions.
prior=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(ROOT/'src/.tmp/native-production/props/bow.fbx'))
added=list(set(bpy.data.objects)-prior);bow=next(o for o in added if o.type=='MESH');m=bow.matrix_world.copy()
bow.parent=rig;bow.parent_type='BONE';bow.parent_bone='attach_bow_l';bow.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['attach_bow_l'].length,0));bow.matrix_basis=Matrix.Rotation(math.pi,4,'Z')@m
basis=bow.data.shape_keys.key_blocks[0];draw=next(k for k in bow.data.shape_keys.key_blocks if k.name!='Basis');delta=[(x.co-y.co).length for x,y in zip(draw.data,basis.data)];indices=[i for i,v in enumerate(delta) if v>=max(delta)*.999]
calibrated=[];weights=[];contact=[]
for f,values in samples:
    assign(None);set_pose(values)
    left=wp('attach_bow_l');right=wp('attach_arrow_r');desired=right-left
    basis_nock=bow.matrix_world@(sum((basis.data[i].co for i in indices),Vector())/len(indices))-left
    full_nock=bow.matrix_world@(sum((draw.data[i].co for i in indices),Vector())/len(indices))-left
    if f<=26:
        # Only the existing native Draw morph and rigid prop frame are fitted
        # to the authored hands. Every deforming body bone stays untouched.
        low,high=0,2
        for _ in range(30):
            weight=(low+high)/2
            if basis_nock.lerp(full_nock,weight).length<desired.length:low=weight
            else:high=weight
        weight=(low+high)/2;draw.value=weight
        current=basis_nock.lerp(full_nock,weight)
        delta=current.rotation_difference(desired)
        helper=rig.pose.bones['attach_bow_l'];world=rig.matrix_world@helper.matrix
        helper.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(world.translation,delta@world.to_quaternion(),world.to_scale());bpy.context.view_layer.update()
        hold_delta=helper.rotation_quaternion@values['attach_bow_l'].to_quaternion().inverted()
        held_weight=weight
    else:
        weight=held_weight*max(0,1-(f-26)/3);draw.value=weight
        helper=rig.pose.bones['attach_bow_l'];helper.rotation_quaternion=hold_delta@values['attach_bow_l'].to_quaternion();bpy.context.view_layer.update()
    helper=rig.pose.bones['attach_arrow_r'];world=rig.matrix_world@helper.matrix
    forward=(left-right).normalized();current=world.to_3x3()@arrow_axis
    helper.matrix=rig.matrix_world.inverted()@Matrix.LocRotScale(world.translation,current.rotation_difference(forward)@world.to_quaternion(),world.to_scale());bpy.context.view_layer.update()
    nock=bow.matrix_world@(sum((basis.data[i].co.lerp(draw.data[i].co,weight) for i in indices),Vector())/len(indices))
    weights.append(weight);calibrated.append((f,pose()));contact.append({'frame':f,'morphWeight':weight,'nockGap':(right-nock).length,'forearm':list(wp('hand_l')-wp('lowerarm_l')),'bowUp':list((rig.matrix_world@rig.pose.bones['attach_bow_l'].matrix).to_3x3().col[0].normalized())})
    if f==26:aim_yaw=-math.degrees(math.atan2(forward.x,-forward.y))
assign(a);previous={}
for f,values in calibrated:
    set_pose(values)
    for p in rig.pose.bones:
        p.rotation_mode='QUATERNION';q=p.rotation_quaternion.copy();q.normalize()
        if p.name in previous:q.make_compatible(previous[p.name])
        previous[p.name]=q.copy();p.rotation_quaternion=q
        for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=f)
for curve in a.fcurves:
    for key in curve.keyframe_points:key.interpolation='LINEAR'
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)

# Reuse the author's upright torch arm for a held staff. Mirror the complete
# left clavicle-to-fingers pose with Blender's own pose operation; no wrist IK.
with bpy.data.libraries.load(str(ROOT/'src/.tmp/native-production/animation/native65-actions.blend'),link=False) as (src,dst):dst.actions=['UAL1__Idle_Torch_Loop']
torch=dst.actions[0];assign(torch);time(0);assign(None)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.select_all(action='DESELECT')
for p in rig.pose.bones:
    if p.name.endswith('_l') and p.name.startswith(('clavicle_','upperarm_','lowerarm_','hand_','index_','middle_','ring_','pinky_','thumb_')):p.bone.select=True
bpy.ops.pose.copy();bpy.ops.pose.paste(flipped=True);bpy.ops.object.mode_set(mode='OBJECT')
staff_arm={p.name:p.matrix_basis.copy() for p in rig.pose.bones if p.name.endswith('_r') and p.name.startswith(('clavicle_','upperarm_','lowerarm_','hand_','index_','middle_','ring_','pinky_','thumb_'))}
staff_sources={}
for source_name,target_name in [('idle','idle_staff'),('walk','walk_staff'),('run','run_staff'),('attack_staff','attack_staff')]:
    source_action=bpy.data.actions[source_name];frames=[]
    for frame in range(math.floor(source_action.frame_range[1])+1):
        assign(source_action);time(frame);values=pose();values.update(staff_arm);frames.append((frame,values))
    assign(None)
    if source_name==target_name:bpy.data.actions.remove(source_action)
    result=bpy.data.actions.new(target_name);result.use_fake_user=True;assign(result);previous={}
    for frame,values in frames:
        set_pose(values)
        for p in rig.pose.bones:
            p.rotation_mode='QUATERNION';q=p.rotation_quaternion.copy();q.normalize()
            if p.name in previous:q.make_compatible(previous[p.name])
            previous[p.name]=q.copy();p.rotation_quaternion=q
            for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=frame)
    for curve in result.fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
    staff_sources[target_name]={'body':source_name,'rightArm':'Original UAL1 Idle_Torch_Loop left clavicle-to-fingers mirrored with Blender pose.paste(flipped=True)'}
bpy.data.actions.remove(torch)
scene.render.fps=30;scene.render.fps_base=1.0
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'authored-bow.blend'),relative_remap=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and '_native_' in o.name]
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
for image in bpy.data.images:
    name=Path(bpy.path.abspath(image.filepath)).name
    if (ROOT/'src/cocos/assets/resources/actors/native-shared/textures'/name).is_file():image.filepath=str(OUT.parent/'native-shared/textures'/name)
bpy.ops.export_scene.fbx(filepath=str(OUT/'authored-raphael.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',colors_type='NONE',embed_textures=False,use_custom_props=True)
report={'source':'Complete BVH-Retargeter KayKit Draw frames14..40 / Release1..9 upper-body rotations with established native standing lower-body mask and finger grip; rigid helper/morph contact calibration without any wrist IK','holdFrame':26,'endFrame':35,'drawWeights':weights,'bowAimYawCorrectionDegrees':aim_yaw,'fullHold':rows[26],'contact':contact,'frames':rows,'staffSources':staff_sources}
(OUT/'authored-pose-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('AUTHORED_POSE',json.dumps({k:report[k] for k in ['fullHold','holdFrame','endFrame','bowAimYawCorrectionDegrees']}),flush=True)

if '--render' in sys.argv:
    assign(a);time(26)
    for o in bpy.data.objects:
        if o.type=='MESH' and '_hood_'in o.name:o.hide_render=True
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=600;scene.render.resolution_y=700;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('QAWorld');scene.world.color=(.25,.25,.25)
    def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    for location in [(3,-4,5),(-3,2,4)]:
        bpy.ops.object.light_add(type='AREA',location=location);bpy.context.object.data.energy=600;bpy.context.object.data.size=4;aim(bpy.context.object,(0,0,1))
    bpy.ops.object.camera_add(location=(3,-5,2.8));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.3;aim(cam,(0,0,1));scene.camera=cam
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'authored-hold-review.png');bpy.ops.render.render(write_still=True)
