from pathlib import Path
import bpy,json
bpy.ops.wm.open_mainfile(filepath='F:/workspace/Singularity/source-art/characters/3d-hairstyles-v1/raphael.blend')
for o in bpy.data.objects:
 if o.type=='MESH'and o.get('nativePart')in['hair','head','body']:
  v=[x.co for x in o.data.vertices if x.co.y>.025]
  if o.get('nativePart')=='body':v=[p for p in v if p.z>1.45]
  if v:print('BOUNDS',o.name,[min(p[i]for p in v)for i in range(3)],[max(p[i]for p in v)for i in range(3)])

