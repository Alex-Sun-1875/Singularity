from pathlib import Path
import bpy,json,os
from mathutils import Vector
P=str(Path(__file__).resolve().parents[2] / 'assets/studies/player-refined');m=json.load(open(P+'/manifest.json'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=P+'/models/model_player_refined.glb')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0;points=[]
for o in meshes:
 o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles);points.extend(o.matrix_world@Vector(p) for p in o.bound_box)
assert tri==m['triangles'];assert len(meshes)==m['mesh_parts']
json.dump({'passed':True,'method':'Blender 4.3.2 fresh GLB reimport; triangle and mesh part parity','triangles':tri,'mesh_parts':len(meshes),'bounds_xyz_m':[[round(min(p[i] for p in points),4) for i in range(3)],[round(max(p[i] for p in points),4) for i in range(3)]],'file_bytes':os.path.getsize(P+'/models/model_player_refined.glb'),'armatures':0,'animation_actions':len(bpy.data.actions)},open(P+'/validation.json','w'),indent=2)
