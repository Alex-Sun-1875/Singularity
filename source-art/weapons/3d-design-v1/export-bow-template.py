import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[3];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(root/'src/cocos/assets/resources/actors/props-native/bow/bow.fbx'))
o=next(o for o in bpy.data.objects if o.type=='MESH'and o.data.shape_keys)
r={'positions':[list(o.matrix_world@v.co)for v in o.data.shape_keys.reference_key.data],'draw':[list(o.matrix_world@v.co)for v in o.data.shape_keys.key_blocks['Draw'].data],'faces':[list(p.vertices)for p in o.data.polygons]}
(root/'source-art/weapons/3d-design-v1/stock-bow-template.json').write_text(json.dumps(r,separators=(',',':')))
