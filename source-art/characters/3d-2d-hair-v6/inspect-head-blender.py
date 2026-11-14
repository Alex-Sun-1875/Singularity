import bpy,json
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='F:/workspace/Singularity/source-art/characters/3d-native-hair-v4/raphael.blend')
rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST'
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('nativePart') in ['head','hair']:
  print('BOUNDS',o.name,[min(v.co[i] for v in o.data.vertices) for i in range(3)],[max(v.co[i] for v in o.data.vertices) for i in range(3)])
print('HEAD',list(rig.data.bones['Head'].head_local),list(rig.data.bones['Head'].tail_local))
