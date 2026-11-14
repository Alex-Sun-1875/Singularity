"""Offline visual review of the exact converted meshes and packed source maps."""
import bpy,json,pathlib,math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'assets/resources/environment'
data=json.loads((ROOT/'temp/environment-source/library-unpacked.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
materials={}
for key,definition in data['materials'].items():
 mat=bpy.data.materials.new(key);mat.use_nodes=True;n=mat.node_tree.nodes;links=mat.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.82
 image=n.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(BASE/(definition['color']+'.png')));links.new(image.outputs['Color'],p.inputs['Base Color'])
 if definition['cutout']:links.new(image.outputs['Alpha'],p.inputs['Alpha']);mat.surface_render_method='DITHERED'
 if definition.get('normal'):
  normal=n.new('ShaderNodeTexImage');normal.image=bpy.data.images.load(str(BASE/(definition['normal']+'.png')),check_existing=True);normal.image.colorspace_settings.name='Non-Color';mapnode=n.new('ShaderNodeNormalMap');links.new(normal.outputs['Color'],mapnode.inputs['Color']);links.new(mapnode.outputs['Normal'],p.inputs['Normal'])
 materials[key]=mat
def put(key,x,y,width=None,height=None,depth=None,yaw=0):
 model=data['models'][key];dims=model['dimensions'];factor=height/dims[1] if height else width/dims[0] if width else depth/dims[2] if depth else 1;size=[width or dims[0]*factor,height or dims[1]*factor,depth or dims[2]*factor]
 for part in model['parts']:
  pos=part['positions'];verts=[(pos[i]*size[0]/dims[0],-pos[i+2]*size[2]/dims[2],pos[i+1]*size[1]/dims[1]) for i in range(0,len(pos),3)];indices=part['indices'];faces=[indices[i:i+3] for i in range(0,len(indices),3)]
  mesh=bpy.data.meshes.new(key);mesh.from_pydata(verts,[],faces);mesh.materials.append(materials[part['material']]);mesh.update();uv=mesh.uv_layers.new()
  for polygon in mesh.polygons:
   polygon.use_smooth=True
   for li in polygon.loop_indices:
    vi=mesh.loops[li].vertex_index;uv.data[li].uv=(part['uvs'][vi*2],1-part['uvs'][vi*2+1])
  obj=bpy.data.objects.new(key,mesh);bpy.context.collection.objects.link(obj);obj.location=(x,y,0);obj.rotation_euler.z=math.radians(yaw)
put('tree',5,3,height=5)
put('rocks-0',5,-.5,width=2.5,height=1.4,depth=2.2)
put('fern-1',6,-3,height=1);put('grass-2',4,-3,height=.7);put('stump',7,-1.9,height=.7)
put('shelf',-5,3,width=2.4,height=2.6,depth=.8)
put('chair',-2,3,height=2);put('barrel',0,3,height=1.4)
put('table',-4,-.6,width=3.4,height=1,depth=1.65)
put('chest',0,-.6,width=1.8,height=1.1,depth=1.2)
put('crate',-4,-3.8,width=1.5,height=.9,depth=1.1)
put('firepit',-1,-3.8,width=1.7,height=.55,depth=1.7)
put('lantern',1,-3.5,height=1.1)
put('stool',2,3,height=.7)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.035));ground=bpy.context.object;m=bpy.data.materials.new('warm grey');m.diffuse_color=(.19,.175,.14,1);ground.data.materials.append(m)
world=bpy.data.worlds.new('Studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.34,.40,.43,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.light_add(type='AREA',location=(-5,-7,14));bpy.context.object.data.energy=2200;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.ops.object.camera_add(location=(12,-16,15));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=19;bpy.context.scene.camera=camera
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'temp/environment-source/environment-asset-sheet.png');bpy.ops.render.render(write_still=True)
