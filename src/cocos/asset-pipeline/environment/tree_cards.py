"""Project authored Poly Haven leaf clusters to conventional two-triangle LOD cards.

Keeps the source GeometryNodes instance placements, source UV atlas and alpha map.
The source cluster's principal plane bounds approximate its curved silhouette;
it does not invent leaf placement or hand-model a replacement tree.
"""
import bpy,numpy as np
from mathutils import Vector

def tree_cards(scene):
 source=bpy.data.objects['tree_small_02_geometry_nodes'];scene.collection.objects.link(source)
 modifier=source.modifiers[0];modifier['Input_32']=bpy.data.collections['tree_small_02_leaves_LOD1']
 for node in modifier.node_group.nodes:
  if node.bl_idname=='GeometryNodeRealizeInstances':node.mute=True
 source.update_tag();basis=bpy.data.objects['tree_small_02_LOD1'].matrix_world@source.matrix_world.inverted();graph=bpy.context.evaluated_depsgraph_get();cache={};positions=[];faces=[];uvs=[];count=0
 for instance in graph.object_instances:
  obj=instance.object
  if not instance.is_instance or obj.type!='MESH' or len([m for m in obj.data.materials if m])!=1 or not any(m and m.name=='tree_small_02_leaves' for m in obj.data.materials):continue
  mesh=obj.data;identity=mesh.as_pointer()
  if identity not in cache:
   layer=mesh.uv_layers.active
   if not layer:continue
   source_uv=np.array([layer.data[i].uv[:] for i in range(len(mesh.loops))]);source_positions=np.array([mesh.vertices[loop.vertex_index].co[:] for loop in mesh.loops])
   coefficients=np.linalg.lstsq(np.column_stack([source_uv,np.ones(len(source_uv))]),source_positions,rcond=None)[0]
   low=source_uv.min(axis=0);high=source_uv.max(axis=0);corners=[(low[0],low[1]),(high[0],low[1]),(high[0],high[1]),(low[0],high[1])]
   center=source_positions.mean(axis=0);_,_,axes=np.linalg.svd(source_positions-center,full_matrices=False);axis_u=axes[0];axis_v=axes[1]
   if np.dot(axis_u,coefficients[0])<0:axis_u=-axis_u
   if np.dot(axis_v,coefficients[1])<0:axis_v=-axis_v
   plane=np.column_stack([(source_positions-center)@axis_u,(source_positions-center)@axis_v]);lo=plane.min(axis=0);hi=plane.max(axis=0);xy=[(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]
   points=[Vector(tuple(center+axis_u*x+axis_v*y)) for x,y in xy]
   cache[identity]=(points,corners)
  points,corners=cache[identity];start=len(positions)
  positions.extend([tuple(basis@instance.matrix_world@point) for point in points]);faces.extend([(start,start+1,start+2),(start,start+2,start+3)]);uvs.extend(corners);count+=1
 scene.collection.objects.unlink(source)
 mesh=bpy.data.meshes.new('AuthoredLeafClusterCards');mesh.from_pydata(positions,[],faces);mesh.materials.append(bpy.data.materials['tree_small_02_leaves']);mesh.update();layer=mesh.uv_layers.new()
 for polygon in mesh.polygons:
  for loop_index in polygon.loop_indices:layer.data[loop_index].uv=uvs[mesh.loops[loop_index].vertex_index]
 obj=bpy.data.objects.new('AuthorPlacementLeafCards',mesh);scene.collection.objects.link(obj)
 print('Projected authored leaf clusters:',count,'cards,',len(faces),'triangles',flush=True)
 return obj
