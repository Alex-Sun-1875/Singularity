from pathlib import Path
import bpy,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-hairstyles-v3/raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='POSE'
axis=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));bones=['spine_01','spine_02','spine_03'];rest={};rows=[]
def pose(name,fraction):
 a=bpy.data.actions[name];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 frame=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*fraction;bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
def surface():
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[]
 for o in bpy.data.objects:
  if o.type!='MESH'or o.get('nativePart')!='body':continue
  e=o.evaluated_get(dg);m=e.to_mesh();offset=len(vs);vs.extend(tuple((axis@o.matrix_world)@v.co)for v in m.vertices);fs.extend(tuple(offset+i for i in p.vertices)for p in m.polygons);e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs)
pose('idle',0)
for b in bones:rest[b]=(axis@rig.matrix_world@rig.pose.bones[b].matrix).inverted()@Vector((.13,1.2,-.155))
for name,fraction in [('idle',0),('walk',.25),('walk',.75),('run',.25),('run',.75)]:
 pose(name,fraction);bvh=surface();samples=[]
 for b in bones:
  p=(axis@rig.matrix_world@rig.pose.bones[b].matrix)@rest[b];q,n,_,d=bvh.find_nearest(p);samples.append({'bone':b,'grip':list(p),'surfaceDistance':d,'signedGripRadiusGap':d*(1 if(p-q).dot(n)>0 else-1)-.018})
 rows.append({'clip':name,'fraction':fraction,'samples':samples})
(BASE/'anchor-measurements.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(rows),flush=True)
