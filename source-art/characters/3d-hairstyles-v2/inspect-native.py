from pathlib import Path
import bpy,sys
from mathutils import Vector
b=Path('F:/workspace/Singularity');sys.path.insert(0,str(b/'tools/model-pipeline'));import cocos_native_characters as native
bpy.ops.wm.open_mainfile(filepath=str(b/'source-art/characters/3d-native-hair-v4/raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST'
p=b/'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Buzzed.gltf'
sr,meshes=native.imported(p);correction=rig.data.bones['Head'].matrix_local@sr.data.bones['Head'].matrix_local.inverted()
for o in meshes:
 co=[correction@v.co for v in o.data.vertices];print('BUZZED',len(co),[min(v[i]for v in co)for i in range(3)],[max(v[i]for v in co)for i in range(3)])
 for m in o.data.materials:
  print('MAT',m.name,[(n.image.filepath,n.image.name)for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image])
