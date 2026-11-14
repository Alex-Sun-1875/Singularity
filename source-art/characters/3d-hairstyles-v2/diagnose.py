from pathlib import Path
import bpy,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
b=Path('F:/workspace/Singularity/source-art/characters/3d-hairstyles-v2');bpy.ops.wm.open_mainfile(filepath=str(b/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.view_layer.update();h=next(o for o in bpy.data.objects if o.get('nativePart')=='head');s=BVHTree.FromObject(h,bpy.context.evaluated_depsgraph_get());c=Vector((0,.015,1.693))
for th in [.3,.8,1.2,1.6]:
 for ph in [0,math.pi/2,math.pi]:
  p=Vector((.079*math.sin(th)*math.sin(ph),.015-.104*math.sin(th)*math.cos(ph),1.693+.118*math.cos(th)));q,n,_,d=s.find_nearest(p);print('NORMAL',th,round(ph,2),[round(x,4)for x in q],[round(x,3)for x in n],round(n.dot((q-c).normalized()),3))
o=next(o for o in bpy.data.objects if 'Curly_Strands'in o.name);print('TRANSFORMS',list(h.matrix_world),list(o.matrix_world));print('GROUPS',[(g.index,g.name)for g in o.vertex_groups])
