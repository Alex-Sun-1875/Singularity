from pathlib import Path
import bpy,json
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
head=next(o for o in bpy.data.objects if o.get('nativePart')=='head')
hair=next(o for o in bpy.data.objects if o.get('nativePart')=='hair')
tree=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
top=max(v.co.z for v in head.data.vertices);points=[]
for v in hair.data.vertices:
    if v.co.z<top-.025:continue
    p,n,index,dist=tree.find_nearest(v.co)
    if p is not None:points.append({'xyz':list(v.co),'distance':dist,'outside':(v.co-p).dot(n)})
points.sort(key=lambda p:p['distance'])
print(json.dumps({'headTop':top,'hairTop':max(v.co.z for v in hair.data.vertices),
 'headPivot':list(rig.data.bones['Head'].head_local),'crownNearSurface':points[:16]}),flush=True)
