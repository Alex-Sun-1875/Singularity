"""Refit the original hair surfaces and project coherent authored view regions.

Unlike the rejected prototypes, this keeps a fitted continuous scalp surface.
Projection uses the broad head region, never the tiny curl surface normals.
"""
from pathlib import Path
import bpy,sys,json,hashlib,math,subprocess
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import interpolate_bezier
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
SOURCE=BASE.parent/'3d-hairstyles-v1'

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

def uv_for(points,v):
 u=(points[:,v['axes'][0]]-v['range'][0][0])/np.ptp(v['range'][0]);t=1-(points[:,v['axes'][1]]-v['range'][1][0])/np.ptp(v['range'][1])
 return np.stack([1-u if v['flip']else u,t],axis=1)

def sample(a,uv):
 x=np.clip(uv[:,0]*(a.shape[1]-1),0,a.shape[1]-1.001);y=np.clip(uv[:,1]*(a.shape[0]-1),0,a.shape[0]-1.001);ix=x.astype(int);iy=y.astype(int);dx=x-ix;dy=y-iy
 return (a[iy,ix]*(1-dx)+a[iy,ix+1]*dx)*(1-dy)+(a[iy+1,ix]*(1-dx)+a[iy+1,ix+1]*dx)*dy

def finish_locks(hair,sid):
 """Short tapered edge locks, seated in the fitted surface, not floating hair."""
 surface=BVHTree.FromObject(hair,bpy.context.evaluated_depsgraph_get());guides=[]
 if sid=='dante':
  for k,phi in enumerate(np.linspace(1.70,4.58,17)):
   x=.075*math.sin(phi);y=.015-.080*math.cos(phi);z=1.579+.018*abs(math.sin(phi));root,n,_,_=surface.find_nearest(Vector((x,y,z)))
   end=Vector((x*1.015,y+.007,root.z-.023-.006*(k%3)));mid=root+Vector((x*.018,.004,-.013));guides.append((root-n*.002,mid,end,.0065,n))
  for side in [-1,1]:
   for k in range(3):
    root,n,_,_=surface.find_nearest(Vector((side*(.073+k*.003),-.063+k*.006,1.706)))
    guides.append((root-n*.002,root+Vector((side*.001,.002,-.011)),root+Vector((-side*.002,.007,-.021-k*.002)),.005,n))
 elif sid=='curly':
  for k,phi in enumerate(np.linspace(.75,5.53,24)):
   approx=Vector((.096*math.sin(phi),.015-.126*math.cos(phi),1.699+.012*abs(math.sin(phi))));root,n,_,_=surface.find_nearest(approx)
   drift=Vector((math.cos(phi)*.005,math.sin(phi)*.005,-.014));guides.append((root-n*.002,root+n*.004+drift*.65,root+drift+n*.001,.0048,n))
  for k,phi in enumerate(np.linspace(1.70,4.58,17)):
   root,n,_,_=surface.find_nearest(Vector((.075*math.sin(phi),.015-.082*math.cos(phi),1.571+.012*abs(math.sin(phi)))))
   drift=Vector((math.cos(phi)*.004,math.sin(phi)*.002,-.020));guides.append((root-n*.002,root+n*.004+drift*.55,root+drift,.006,n))
 else:
  count=23 if sid=='nero'else 19
  for k,phi in enumerate(np.linspace(.60,5.68,count)):
   approx=Vector((.080*math.sin(phi),.015-.096*math.cos(phi),(1.650 if sid=='nero'else 1.639)+.034*abs(math.sin(phi))));root,n,_,_=surface.find_nearest(approx)
   drift=Vector((-.001*math.sin(phi),.005 if sid=='vergil'else .001,-.010-(k%3)*.002));guides.append((root-n*.002,root+drift*.5+n*.0015,root+drift,.0038,n))
  if sid=='nero':
   for k in range(12):
    x=-.064+k*.0115;root,n,_,_=surface.find_nearest(Vector((x,-.080,1.758)));drift=Vector((.003,-.003,-.006-(k%3)*.0015));guides.append((root-n*.002,root+n*.001+drift*.5,root+drift,.0038,n))
 # Sideburns are separate tapered locks: rounded curls / long curtains /
 # cropped tips / backward-combed temples, rather than one shared cutoff.
 for side in [-1,1]:
  for k in range(2):
   root,n,_,_=surface.find_nearest(Vector((side*(.077+k*.003),-.044+k*.007,1.735)))
   length={'curly':.041,'dante':.052,'nero':.015,'vergil':.023}[sid]
   end=root+Vector((-side*.002,.008,-length));q,qn,_,d=scalp.find_nearest(end)
   if q is not None and (end-q).dot(qn)<.002:end=q+qn*.0025
   mid=root+Vector((side*.003,.001,-length*.5));guides.append((root-n*.002,mid,end,.0065 if sid in ['curly','dante']else .0038,n))
 if sid=='dante':
  for side in [-1,1]:
   for k in range(2):
    root,n,_,_=surface.find_nearest(Vector((side*(.018+k*.008),-.080,1.790)))
    guides.append((root-n*.002,root+Vector((side*.010,-.004,-.010)),root+Vector((side*.018,-.005,-.031)),.0045,n))
 verts=[];faces=[]
 for a,b,c,width,outward in guides:
  points=list(interpolate_bezier(a,a+(b-a)*1.2,c+(b-c)*1.2,c,12));off=len(verts)
  for i,p in enumerate(points):
   t=i/(len(points)-1);tan=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();side=tan.cross(outward).normalized();normal=side.cross(tan).normalized();envelope=(1-t**1.6)**.8+.006
   for j in range(8):
    angle=2*math.pi*j/8;v=p+side*(math.cos(angle)*width*.5*envelope)+normal*(math.sin(angle)*.0010*envelope);verts.append(tuple(v))
  for i in range(len(points)-1):
   for j in range(8):
    aa=off+i*8+j;ab=off+i*8+(j+1)%8;faces.append((aa,ab,ab+8,aa+8))
 mesh=bpy.data.meshes.new('Hand finished '+sid+' edge layers');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Fine tapered locks',mesh);bpy.context.scene.collection.objects.link(obj);obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
 for p in mesh.polygons:p.use_smooth=True
 # UVs will be re-unwrapped before projection; combine under one renderer.
 pipeline.select([hair,obj]);bpy.context.view_layer.objects.active=hair;bpy.ops.object.join();g=hair.vertex_groups.get('Head');g.add(range(len(hair.data.vertices)),1,'REPLACE')
 return len(guides)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
proof={'nonHairMeshHashes':{o.name:digest(o)for o in objects if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'));manifest['materials']=[m for m in manifest['materials']if 'hair'not in m.get('parts',[])]
head=next(o for o in objects if o.get('nativePart')=='head');scalp=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get());textures=BASE/'textures';textures.mkdir(exist_ok=True)
for style in manifest['hairstyles']:
 sid=style['id'];hair=bpy.data.objects[style['nodes'][0]];pipeline.select([hair])
 # Remove the scalloped ledges of the visual hull while retaining the fit.
 sm=hair.modifiers.new('Continuous temple and nape transitions','SMOOTH');sm.factor=.85;sm.iterations=14 if sid=='dante'else 7;bpy.ops.object.modifier_apply(modifier=sm.name)
 referenceCo=np.array([v.co[:]for v in hair.data.vertices]);baseVertexCount=len(hair.data.vertices)
 for v in hair.data.vertices:
  x,y,z=v.co
  if sid=='curly':
   v.co.z=1.745+(z-1.745)*.87 if z>1.745 else z
   if y<-.035 and z<1.73:v.co.x*=.98
  elif sid=='dante':
   # The layered nape follows the skull, instead of horizontal shelf rings.
   low=max(0,min(1,(1.72-z)/.15));v.co.y-=.018*low if y>.055 else 0
   v.co.x*=1-.06*low
  elif sid=='nero':
   side=max(0,min(1,(abs(x)-.045)/.04));v.co.x*=1-.06*side
   if z>1.78:v.co.z=1.78+(z-1.78)*.85
  else:
   side=max(0,min(1,(abs(x)-.045)/.04));v.co.x*=1-.055*side
   if y>.075:v.co.y-=.008*side
   if y>.065 and z<1.71:v.co.y-=.010*max(0,min(1,(1.71-z)/.065))
  # Lower the actual hairline and close the recessed forehead corners without
  # raising the crown or scaling the face. Keep source UV flow on the same verts.
  front=max(0,min(1,(-y-.005)/.060));edge=max(0,min(1,(1.805-z)/.055));corner=max(0,min(1,(abs(x)-.040)/.035))
  amount={'curly':.006,'dante':.007,'nero':.015,'vergil':.018}[sid]
  v.co.z-=amount*front*edge
  temple=max(0,min(1,(.035-y)/.070))*corner*edge
  if sid in ['nero','vergil']:v.co.z-=.0055*temple;v.co.y-=.0025*temple
  rear=max(0,min(1,(y+.005)/.07));low=max(0,min(1,(1.72-z)/.13))
  extension={'curly':.046,'dante':.015,'nero':.027,'vergil':.060}[sid]
  v.co.z-=extension*rear*low;v.co.x*=1-({'curly':.12,'dante':.09,'nero':.02,'vergil':.06}[sid])*rear*low
  if rear>0 and v.co.z<1.71:
   near,n,_,_=scalp.find_nearest(v.co);offset={'curly':.025,'dante':.018,'nero':.004,'vergil':.009}[sid];target=near+n*offset;blend=.70*rear*max(0,min(1,(1.71-v.co.z)/.10));v.co.y+=(target.y-v.co.y)*blend
  if sid=='nero'and y<-.045 and z<1.790:
   v.co.z+=(.0024*math.sin(x*290)+.0016*math.sin(x*470+.4))*max(0,min(1,(1.79-z)/.03))
  near,n,_,distance=scalp.find_nearest(v.co)
  if near is not None and distance<.016 and (v.co-near).dot(n)<.0015 and (v.co.y>.015 or v.co.z>1.705):v.co=near+n*.0015
 hair.data.update()
 locks=finish_locks(hair,sid)
 folder=BASE.parent/('3d-2d-hair-v6'if sid=='curly'else '3d-hairstyles-v1/'+sid)
 views=json.loads((folder/'projection.json').read_text(encoding='utf-8'))
 data=np.load(folder/'hull.npz');co=np.array([v.co[:]for v in hair.data.vertices]);projectCo=co.copy();projectCo[:baseVertexCount]=referenceCo
 # Keep the full source strand flow when extending the actual nape geometry.
 oldBottom={'curly':1.593,'dante':1.567,'nero':1.656,'vergil':1.652}[sid];newBottom={'curly':1.548,'dante':1.552,'nero':1.642,'vergil':1.622}[sid]
 projectCo[baseVertexCount:,2]=np.where(co[baseVertexCount:,2]<1.72,1.72+(co[baseVertexCount:,2]-1.72)*(1.72-oldBottom)/(1.72-newBottom),co[baseVertexCount:,2])
 # Pick coherent view sectors. A surface-normal blend stamped the back curls
 # across the front and made the sides look like melted overlapping layers.
 x=projectCo[:,0]/.10;y=(projectCo[:,1]-.015)/.12
 w=np.stack([np.maximum(-y,0)**8,np.maximum(x,0)**8,np.maximum(y,0)**8,np.maximum(-x,0)**8],axis=1)+1e-7
 names=['front','right','back','left']
 for i,name in enumerate(names):
  uv=uv_for(projectCo,views[name]);w[:,i]*=.01+.99*sample(data[name+'_mask'],uv)
 w/=w.sum(axis=1,keepdims=True)
 for a in list(hair.data.color_attributes):hair.data.color_attributes.remove(a)
 attr=hair.data.color_attributes.new(name='CoherentProjection',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',w.astype(np.float32).ravel())
 core=hair.data.attributes.new(name='OpaqueCore',type='FLOAT',domain='POINT');coreValues=np.clip((co[:,2]-1.765)/.025,0,1).astype(np.float32);coreValues[baseVertexCount:]=1;core.data.foreach_set('value',coreValues)
 mat=bpy.data.materials.new('Hair_Redesigned_'+sid.title()+'_v2');mat.use_nodes=True;tree=mat.node_tree;bs=tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.83;bs.inputs['Metallic'].default_value=0
 vertex=tree.nodes.new('ShaderNodeVertexColor');vertex.layer_name='CoherentProjection';split=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(vertex.outputs['Color'],split.inputs['Color']);sockets=[split.outputs['Red'],split.outputs['Green'],split.outputs['Blue'],vertex.outputs['Alpha']];summed=None;alphaSum=None
 for i,name in enumerate(names):
  uv=uv_for(projectCo,views[name]);uv[:,1]=1-uv[:,1];layer=hair.data.uv_layers.new(name='Redesign_'+name)
  for loop in hair.data.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
  uvn=tree.nodes.new('ShaderNodeUVMap');uvn.uv_map=layer.name;tex=tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(folder/(name+'-extended.png')),check_existing=True);tex.extension='EXTEND';tree.links.new(uvn.outputs[0],tex.inputs['Vector'])
  product=tree.nodes.new('ShaderNodeMixRGB');product.blend_type='MULTIPLY';product.inputs[0].default_value=1;tree.links.new(tex.outputs['Color'],product.inputs[1]);tree.links.new(sockets[i],product.inputs[2])
  if summed is None:summed=product.outputs[0]
  else:
   add=tree.nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;tree.links.new(summed,add.inputs[1]);tree.links.new(product.outputs[0],add.inputs[2]);summed=add.outputs[0]
  raw=tree.nodes.new('ShaderNodeTexImage');raw.image=bpy.data.images.load(str(folder/(name+'.png')),check_existing=True);raw.extension='CLIP';tree.links.new(uvn.outputs[0],raw.inputs['Vector']);mul=tree.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';tree.links.new(raw.outputs['Alpha'],mul.inputs[0]);tree.links.new(sockets[i],mul.inputs[1])
  if alphaSum is None:alphaSum=mul.outputs[0]
  else:
   add=tree.nodes.new('ShaderNodeMath');add.operation='ADD';tree.links.new(alphaSum,add.inputs[0]);tree.links.new(mul.outputs[0],add.inputs[1]);alphaSum=add.outputs[0]
 tree.links.new(summed,bs.inputs['Base Color']);hair.data.materials.clear();hair.data.materials.append(mat)
 # Preserve fine silhouette transparency, but avoid cutting holes at seams.
 lift=tree.nodes.new('ShaderNodeMath');lift.operation='MULTIPLY';lift.inputs[1].default_value=1.8;tree.links.new(alphaSum,lift.inputs[0]);coreNode=tree.nodes.new('ShaderNodeAttribute');coreNode.attribute_name='OpaqueCore';maximum=tree.nodes.new('ShaderNodeMath');maximum.operation='MAXIMUM';tree.links.new(lift.outputs[0],maximum.inputs[0]);tree.links.new(coreNode.outputs['Fac'],maximum.inputs[1]);tree.links.new(maximum.outputs[0],bs.inputs['Alpha'])
 # Reuse the existing baked island layout; only project layers are temporary.
 pipeline.unwrap([hair]);baked=hair.data.uv_layers['V6_BAKE_UV'];baked.active_render=True;hair.data.uv_layers.active=baked
 image=pipeline.bake([hair],'redesigned-'+sid,2048,'Color');path=textures/('redesigned-'+sid+'-color.png');pipeline.save_image(image,path)
 alpha=pipeline.bake([hair],'redesigned-'+sid+'-alpha',2048,'Alpha');pipeline.apply_alpha(image,alpha);pipeline.save_image(image,path)
 subprocess.run(['C:/Python314/python.exe',str(BASE/'pad-redesign.py'),str(path)],check=True);image.reload()
 for n in list(tree.nodes):
  if n!=bs and n.type!='OUTPUT_MATERIAL':tree.nodes.remove(n)
 for name in [layer.name for layer in hair.data.uv_layers if layer.name!='V6_BAKE_UV']:hair.data.uv_layers.remove(hair.data.uv_layers[name])
 hair.data.uv_layers[0].name='UVMap'
 uvn=tree.nodes.new('ShaderNodeUVMap');uvn.uv_map='UVMap';tex=tree.nodes.new('ShaderNodeTexImage');tex.image=image;tree.links.new(uvn.outputs[0],tex.inputs['Vector']);tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);mat.surface_render_method='DITHERED'
 for a in list(hair.data.color_attributes):hair.data.color_attributes.remove(a)
 if hair.data.attributes.get('OpaqueCore'):hair.data.attributes.remove(hair.data.attributes['OpaqueCore'])
 hair.name='raphael_native_hair_'+sid.title()+'_Redesigned';hair['hairstyleId']=sid;style['nodes']=[hair.name];style['triangles']=pipeline.triangles(hair)
 manifest['materials'].append({'runtimeName':mat.name,'parts':['hair'],'maps':{'albedo':'../hairstyles-v2/textures/redesigned-'+sid+'-color.png'},'sourcePBR':{'effectiveFactors':{'roughness':.83,'metallic':0}},'doubleSided':True,'alphaClip':True,'alphaThreshold':.32})
 style['edgeLocks']=locks
 print('REDESIGNED',sid,locks,flush=True)
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']and len(bpy.data.actions)==14
manifest['parts']['hair']['nodes']=[n for s in manifest['hairstyles']for n in s['nodes']];manifest.update(appearanceRevision='hairstyles-v2-redesigned',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),appearanceReview=(BASE/'README.md').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
manifest['hairstyle'].update(method='Refitted native surfaces, coherent four-sector reference projection, separate tapered temple/nape locks and alpha strand edges',reference='source-art/characters/2d-concepts/identity-reference-v1/head-identity-master.png',generation='Reused project-approved curly reference and the three existing cloud-generated v1 sheets; no library hair meshes in the final actor')
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');proof.update(faceBodyUnchanged=True,all14ActionsUnchanged=True)
(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('EXPORTED_REDESIGN',manifest['triangles'],flush=True)
