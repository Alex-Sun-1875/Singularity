import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(root/'src/cocos/assets/resources/actors/props-native/bow/bow.fbx'))
o=next(o for o in bpy.data.objects if o.type=='MESH'and o.data.shape_keys)
print('WORLD',o.matrix_world)
print('KEYS',[(k.name,len(k.data))for k in o.data.shape_keys.key_blocks])
for k in o.data.shape_keys.key_blocks:
 p=[o.matrix_world@v.co for v in k.data];print('KEY',k.name,'min',[min(v[i]for v in p)for i in range(3)],'max',[max(v[i]for v in p)for i in range(3)])

from mathutils import Matrix
world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Identity(4);o.data.transform(world,shape_keys=True)
print('TRANSFORM')
for k in o.data.shape_keys.key_blocks:
 p=[v.co for v in k.data];print(k.name,'min',[min(v[i]for v in p)for i in range(3)],'max',[max(v[i]for v in p)for i in range(3)])
print('STRINGCOORDS',[(list(v.co),i)for i,v in enumerate(o.data.shape_keys.reference_key.data)if v.co.x<-.244][:8])

r=o.data.shape_keys.reference_key.data;d=o.data.shape_keys.key_blocks['Draw'].data
faces=[p for p in o.data.polygons if min(d[i].co.x for i in p.vertices)<-.55]
print('NOCKFACES',len(faces))
for p in faces[:8]:print([list(r[i].co)for i in p.vertices],[list(d[i].co)for i in p.vertices])
