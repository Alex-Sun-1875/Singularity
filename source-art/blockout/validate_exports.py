from pathlib import Path
import bpy,os,json
from mathutils import Vector
BASE=str(Path(__file__).resolve().parents[2] / 'assets/blockout')
manifest=json.load(open(BASE+'/manifest.json')); results=[]
for a in manifest['assets']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 path=BASE+'/'+a['file'];bpy.ops.import_scene.gltf(filepath=path)
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0;points=[]
 for o in meshes:
  o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
  points += [o.matrix_world@Vector(p) for p in o.bound_box]
 low=[round(min(p[i] for p in points),4) for i in range(3)];high=[round(max(p[i] for p in points),4) for i in range(3)]
 results.append({'id':a['id'],'file_bytes':os.path.getsize(path),'import_success':True,'triangles':tri,'expected_triangles':a['triangles'],'triangle_match':tri==a['triangles'],'mesh_parts':len(meshes),'bounds_blender_xyz_m':[low,high],'materials':len({m.name for o in meshes for m in o.data.materials}),'armatures':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),'animation_actions':len(bpy.data.actions)})
assert all(r['triangle_match'] for r in results)
json.dump({'method':'Blender 4.3.2 glTF exporter, fresh delete and reimport each GLB; triangle parity and bounds checked','passed':True,'results':results},open(BASE+'/validation.json','w'),indent=2)
print('VALIDATION_COMPLETE',len(results))
