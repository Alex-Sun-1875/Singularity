"""Remove unused vertex-color sets: Cocos supports only COLOR_0."""
from pathlib import Path
import bpy
BASE=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
for obj in objects:
    for attribute in list(obj.data.color_attributes):obj.data.color_attributes.remove(attribute)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.context.scene.name='raphael-polish'
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
print('EXPORTED_WITHOUT_UNUSED_VERTEX_COLORS')
