import bpy,json
bpy.ops.wm.open_mainfile(filepath='F:/workspace/Singularity/source-art/characters/3d-hairstyles-v1/raphael.blend')
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('nativePart')=='hair':print('HAIRGROUPS',o.name,[(g.index,g.name)for g in o.vertex_groups],[[[g.group,g.weight]for g in v.groups]for v in list(o.data.vertices)[:2]])
