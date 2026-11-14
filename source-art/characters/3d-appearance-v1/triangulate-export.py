"""Use Blender's native triangulation for the editor's FBX converter."""
from pathlib import Path
import bpy,bmesh,json,sys
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
for obj in meshes:
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(BASE/'raphael.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',colors_type='NONE',embed_textures=False,use_custom_props=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
print('TRIANGULATED',sum(len(o.data.polygons)for o in meshes))
