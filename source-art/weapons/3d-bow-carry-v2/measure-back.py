"""Use the existing native Blender rig and BVH to measure the idle clothing."""
from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-hairstyles-v3/raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='POSE';action=bpy.data.actions['idle'];rig.animation_data.action=action
if action.slots:rig.animation_data.action_slot=action.slots[0]
bpy.context.scene.frame_set(0);dg=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
for o in bpy.data.objects:
 if o.type!='MESH'or o.get('nativePart')not in ['body','arms']:continue
 evaluated=o.evaluated_get(dg);mesh=evaluated.to_mesh();offset=len(verts)
 for v in mesh.vertices:
  p=o.matrix_world@v.co;verts.append((p.x,p.z,-p.y))
 faces.extend(tuple(offset+i for i in p.vertices)for p in mesh.polygons);evaluated.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,faces);samples=[]
for y in [1.20,1.27]:
 for x in [-.18,-.15,-.13,-.12,-.11,-.09,.09,.11,.12,.13,.15,.18]:
  p,n,_,distance=bvh.ray_cast(Vector((x,y,-1)),Vector((0,0,1)),2)
  if p:samples.append({'x':x,'y':y,'surface':list(p),'normal':list(n),'bowGripZ':p.z-.024,'quiverCenterZ':p.z-.067})
record={'space':'Cocos model Y-up; native idle frame 0, evaluated clothes; glTF axis conversion applied','samples':samples,'rigWorld':list(map(list,rig.matrix_world))}
(BASE/'back-surface.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(samples,ensure_ascii=False),flush=True)
