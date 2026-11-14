import bpy
p=bpy.ops.export_scene.gltf.get_rna_type().properties
for x in p:
    if 'color' in x.identifier:print(x.identifier,x.type,[(y.identifier,y.name)for y in x.enum_items]if x.type=='ENUM'else'')
