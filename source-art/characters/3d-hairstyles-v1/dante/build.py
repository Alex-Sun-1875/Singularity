from pathlib import Path
import bpy,bmesh,json,hashlib,sys,math,subprocess
import numpy as np
from mathutils import Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
SOURCE=BASE.parent.parent/'3d-native-hair-v4'

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
original=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
proof={'nonHairMeshHashes':{o.name:digest(o)for o in original if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
data=np.load(BASE/'hull.npz');mesh=bpy.data.meshes.new('Reference hair silhouette');mesh.from_pydata(data['vertices'],[],data['faces']);mesh.update()
hair=bpy.data.objects.new('Reference hair hull',mesh);bpy.context.scene.collection.objects.link(hair);pipeline.select([hair])
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0002);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
remesh=hair.modifiers.new('Native OpenVDB silhouette reconstruction','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0026;remesh.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=hair.modifiers.new('Soft curl volume','SMOOTH');smooth.factor=.75;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
views=json.loads((BASE/'projection.json').read_text());views['top']={'axes':[0,1],'range':[views['back']['range'][0],views['right']['range'][0]],'flip':False};co=np.array([v.co[:]for v in hair.data.vertices]);n=len(co)

def uv_for(points,v):
 u=(points[:,v['axes'][0]]-v['range'][0][0])/np.ptp(v['range'][0]);t=1-(points[:,v['axes'][1]]-v['range'][1][0])/np.ptp(v['range'][1])
 return np.stack([1-u if v['flip']else u,t],axis=1)
def sample(a,uv):
 x=np.clip(uv[:,0]*(a.shape[1]-1),0,a.shape[1]-1.001);y=np.clip(uv[:,1]*(a.shape[0]-1),0,a.shape[0]-1.001);ix=x.astype(int);iy=y.astype(int);dx=x-ix;dy=y-iy
 if a.ndim==3:dx=dx[:,None];dy=dy[:,None]
 return (a[iy,ix]*(1-dx)+a[iy,ix+1]*dx)*(1-dy)+(a[iy+1,ix]*(1-dx)+a[iy+1,ix+1]*dx)*dy
def weights(points):
 x=points[:,0]/.105;y=(points[:,1]-.014)/.125
 w=np.stack([np.maximum(-y,0)**3,np.maximum(x,0)**3,np.maximum(y,0)**3,np.maximum(-x,0)**3],axis=1)+.0001
 return w/w.sum(axis=1,keepdims=True)
names=['front','right','back','left'];w=weights(co);relief=np.zeros(n)
for i,name in enumerate(names):relief+=w[:,i]*sample(data[name+'_relief'],uv_for(co,views[name]))
# Millimetre relief follows the actual painted curls rather than random noise.
normal=np.array([v.normal[:]for v in hair.data.vertices]);co+=normal*np.clip(relief*.008,-.0009,.0009)[:,None]
hair.data.vertices.foreach_set('co',co.ravel());hair.data.update()
dec=hair.modifiers.new('Runtime hair surface budget','DECIMATE');dec.ratio=min(1,8000/max(1,len(hair.data.polygons)));bpy.ops.object.modifier_apply(modifier=dec.name)
for p in hair.data.polygons:p.use_smooth=True
co=np.array([v.co[:]for v in hair.data.vertices]);norm=np.array([v.normal[:]for v in hair.data.vertices]);nx,ny,nz=norm.T
w=np.stack([np.maximum(-ny,0)**3,np.maximum(nx,0)**3+.12*np.maximum(-nx,0)**3,np.maximum(ny,0)**3,np.maximum(-nx,0)**3+.12*np.maximum(nx,0)**3,np.maximum(nz,0)**3*1.6],axis=1)+.0001
for i,name in enumerate(names):
 projected=uv_for(co,views[name]);valid=np.all((projected>=0)&(projected<=1),axis=1);w[:,i]*=.0001+.9999*sample(data[name+'_mask'],projected)*valid
w/=w.sum(axis=1,keepdims=True)
color=hair.data.color_attributes.new(name='ReferenceWeights',type='FLOAT_COLOR',domain='POINT');color.data.foreach_set('color',w[:,:4].astype(np.float32).ravel())
top=hair.data.attributes.new('TopWeight','FLOAT','POINT');top.data.foreach_set('value',w[:,4].astype(np.float32))
mat=bpy.data.materials.new('Hair_Style_Dante');mat.use_nodes=True;tree=mat.node_tree;bs=tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8;bs.inputs['Metallic'].default_value=0
attr=tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='ReferenceWeights';separate=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(attr.outputs['Color'],separate.inputs['Color']);weightsockets=[separate.outputs['Red'],separate.outputs['Green'],separate.outputs['Blue'],attr.outputs['Alpha']]
topattr=tree.nodes.new('ShaderNodeAttribute');topattr.attribute_name='TopWeight';weightsockets.append(topattr.outputs['Fac']);names=names+['top']
summed=None
for i,name in enumerate(names):
 projected=uv_for(co,views[name]);projected[:,1]=1-projected[:,1]
 layer=hair.data.uv_layers.new(name='Project_'+name)
 for loop in hair.data.loops:layer.data[loop.index].uv=projected[loop.vertex_index]
 uvnode=tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=layer.name;node=tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(BASE/(('back'if name=='top'else name)+'-extended.png')),check_existing=True);node.extension='EXTEND';tree.links.new(uvnode.outputs['UV'],node.inputs['Vector'])
 product=tree.nodes.new('ShaderNodeMixRGB');product.blend_type='MULTIPLY';product.inputs[0].default_value=1;tree.links.new(node.outputs['Color'],product.inputs[1]);tree.links.new(weightsockets[i],product.inputs[2])
 if summed is None:summed=product.outputs[0]
 else:
  add=tree.nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;tree.links.new(summed,add.inputs[1]);tree.links.new(product.outputs[0],add.inputs[2]);summed=add.outputs[0]
tree.links.new(summed,bs.inputs['Base Color']);hair.data.materials.clear();hair.data.materials.append(mat)
pipeline.unwrap([hair]);hair.data.uv_layers['V6_BAKE_UV'].active_render=True
image=pipeline.bake([hair],'style-dante',2048,'Color');pipeline.save_image(image,BASE/'textures/hair-dante-color.png')
subprocess.run(['C:/Python314/python.exe',str(BASE/'finish-padding.py')],check=True);image.reload()
# Baked color carries the reference's detailed strands. A restrained tangent
# normal follows the same atlas, prepared separately by the local image step.
for node in list(tree.nodes):
 if node!=bs and node.type!='OUTPUT_MATERIAL':tree.nodes.remove(node)
for name in [layer.name for layer in hair.data.uv_layers if layer.name!='V6_BAKE_UV']:hair.data.uv_layers.remove(hair.data.uv_layers[name])
hair.data.uv_layers[0].name='UVMap';uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';tex=tree.nodes.new('ShaderNodeTexImage');tex.image=image;tree.links.new(uv.outputs[0],tex.inputs['Vector']);tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
for attribute in list(hair.data.color_attributes):hair.data.color_attributes.remove(attribute)
for old in original:
 if old.get('nativePart')=='hair':bpy.data.objects.remove(old,do_unlink=True)
hair.name='raphael_native_hair_Dante';hair['nativePart']='hair';hair['defaultVisible']=True
hair.parent=rig;hair.matrix_parent_inverse=Matrix.Identity(4);hair.matrix_basis=Matrix.Identity(4);g=hair.vertex_groups.new(name='Head');g.add(range(len(hair.data.vertices)),1,'REPLACE');mod=hair.modifiers.new('Native head binding','ARMATURE');mod.object=rig
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
manifest=json.loads((SOURCE/'manifest.json').read_text());manifest['materials']=[r for r in manifest['materials']if 'hair'not in r.get('parts',[])]+[{'runtimeName':mat.name,'parts':['hair'],'maps':{'albedo':'../hairstyles-v1/textures/hair-dante-color.png'},'sourcePBR':{'effectiveFactors':{'roughness':.8,'metallic':0}},'doubleSided':True}]
manifest['parts']['hair']['nodes']=[hair.name];manifest.update(appearanceRevision='hairstyle-dante-v1',prefabRoot='raphael-polish',appearanceReview='source-art/characters/3d-hairstyles-v1/README.md',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
manifest['hairstyle']={'meshData':hair.data.name,'asset':'Accepted 2D silver curl reconstruction','method':'Four-view silhouette visual hull; Blender native voxel remesh; multi-view reference projection and fine curl relief','reference':'source-art/characters/2d-concepts/identity-reference-v1/head-identity-master.png','physics':'Original Head-bound mesh, no simulated hair physics','atlasSize':2048}
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
# Shared-rig export is performed once by combine.py.
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
proof.update(faceBodyUnchanged=True,all14ActionsUnchanged=True,bindPoseUnchanged=True,hairTriangles=pipeline.triangles(hair),triangles=manifest['triangles'],finishedHairMeshHash=digest(hair))
(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print('REFERENCE_HAIR_EXPORTED',manifest['triangles'],flush=True)
