"""Use Cocos's native glTF importer instead of its crashing FBX converter."""
from pathlib import Path
import bpy,json
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
scene=bpy.context.scene;scene.name='raphael-designed';scene.render.fps=30;scene.render.fps_base=1
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-designed.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False)
print('EXPORTED_RUNTIME_GLB',len(objects))
