"""Adapt existing native jog stride to the game's 3.6 m/s, preserving arm chains.
Blender native quaternion interpolation, FK, evaluated shoes and FBX exporter.
No IK, new mesh, wrist displacement, new dependencies or animation synthesis.
"""
from pathlib import Path
import bpy,json,math,hashlib,shutil
from mathutils import Vector
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-weapon-contact-v2/authored-bow.blend'))
rig=bpy.data.objects['raphael_Native65'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
def assign(action):
    rig.animation_data.action=action
    if action and action.slots:rig.animation_data.action_slot=action.slots[0]
def time(f):scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
def pose():return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}
def restore(values):
    for name,(loc,q,scale)in values.items():
        p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.location=loc;p.rotation_quaternion=q;p.scale=scale
def shoe_floor():
    deps=bpy.context.evaluated_depsgraph_get();low=1e9
    for obj in feet:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        low=min(low,min((evaluated.matrix_world@v.co).z for v in mesh.vertices));evaluated.to_mesh_clear()
    return low
feet=[o for o in bpy.data.objects if o.type=='MESH'and '_native_feet_'in o.name]
assign(bpy.data.actions['idle']);time(0);neutral=pose()
legs=['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r']
originals={};floors={};frames=[i*.5 for i in range(57)]
for name in ['run','run_staff']:
    action=bpy.data.actions[name];assign(action);originals[name]=[];floors[name]=[]
    for f in frames:time(f);originals[name].append(pose());floors[name].append(shoe_floor())
assign(None)
def stride(amplitude,details=False):
    points=[]
    for values in originals['run'][::2]:
        restore(values)
        for n in legs:rig.pose.bones[n].rotation_quaternion=neutral[n][1].slerp(values[n][1],amplitude)
        bpy.context.view_layer.update();points.append({n:(rig.matrix_world@rig.pose.bones[n].matrix).translation.copy()for n in ['foot_l','foot_r']})
    speeds=[]
    # Use the original contact intervals, excluding aerial and strike frames.
    for n in ['foot_l','foot_r']:
        source_z=[]
        for values in originals['run'][::2]:
            restore(values);bpy.context.view_layer.update();source_z.append((rig.matrix_world@rig.pose.bones[n].matrix).translation.z)
        floor=min(source_z)
        for i,(a,b)in enumerate(zip(points,points[1:])):
            if max(source_z[i:i+2])<floor+.055:speeds.append(Vector((b[n].x-a[n].x,b[n].y-a[n].y)).length*30)
    return sorted(speeds)[len(speeds)//2]
before=stride(1);low,high=.1,1.
for _ in range(16):
    mid=(low+high)/2
    if stride(mid)<3.6:low=mid
    else:high=mid
amplitude=(low+high)/2;after=stride(amplitude);reports=[]
root=rig.pose.bones['root'];up=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,1))
for name in ['run','run_staff']:
    old=bpy.data.actions[name];old.name='SOURCE_'+name;action=old.copy();action.name=name;action.use_fake_user=True;assign(action);previous={};floor_errors=[]
    for f,values,old_floor in zip(frames,originals[name],floors[name]):
        restore(values)
        for n in legs:rig.pose.bones[n].rotation_quaternion=neutral[n][1].slerp(values[n][1],amplitude)
        bpy.context.view_layer.update();desired=.003+max(0,old_floor-.003)*.65;root.location+=up*(desired-shoe_floor());bpy.context.view_layer.update()
        floor_errors.append(abs(shoe_floor()-desired))
        for n in legs:
            p=rig.pose.bones[n]
            q=p.rotation_quaternion.copy();q.normalize()
            if p.name in previous:q.make_compatible(previous[p.name])
            previous[p.name]=q.copy();p.rotation_quaternion=q
            p.keyframe_insert('rotation_quaternion',frame=f)
        root.keyframe_insert('location',frame=f)
    for curve in action.fcurves:
        if curve.data_path=='pose.bones["root"].location'or any(curve.data_path=='pose.bones["'+n+'"].rotation_quaternion'for n in legs):
            for key in curve.keyframe_points:key.interpolation='LINEAR'
    bpy.data.actions.remove(old)
    reports.append({'clip':name,'frames':len(frames),'duration':28/30,'legRotationAmplitude':amplitude,'nominalSpeedMetresPerSecond':after,'maxShoeFloorErrorMetres':max(floor_errors),'unchangedLocalChannels':'All arm, hand, wrist, spine and attachment-helper rotations/translations; mesh, bind pose and weights unchanged','ground':'Root-only vertical sole correction; original air clearance scaled to 0.65'})
assign(bpy.data.actions['idle']);time(0);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'compact-jog.blend'),relative_remap=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'and '_native_'in o.name]
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
for image in bpy.data.images:
    name=Path(bpy.path.abspath(image.filepath)).name
    if (ROOT/'src/cocos/assets/resources/actors/native-shared/textures'/name).is_file():image.filepath=str(BASE.parent/'native-shared/textures'/name)
bpy.ops.export_scene.fbx(filepath=str(BASE/'raphael.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',colors_type='NONE',embed_textures=False,use_custom_props=True)
report={'method':'Existing accepted jog adapted with Blender built-in quaternion.slerp on the connected thigh/calf/foot chain and root-only vertical shoe correction; no IK','originalPlantedFootSpeed':before,'adaptedPlantedFootSpeed':after,'targetSpeed':3.6,'clips':reports,'fbxSHA256':hashlib.sha256((BASE/'raphael.fbx').read_bytes()).hexdigest()}
(BASE/'stride-adaptation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('COMPACT_JOG',json.dumps(report),flush=True)
