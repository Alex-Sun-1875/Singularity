"""Local modular weapon FBX: grip at origin; Blender +Z shaft becomes Cocos +Y."""
from pathlib import Path
import bpy,math,shutil,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'src/cocos/assets/resources/actors/props';SOURCE=ROOT/'source-art/characters/cocos'
OUT.mkdir(parents=True,exist_ok=True);(OUT/'textures').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
def material(name,source,rough,metal):
    origin='lorn' if source=='wood.png' else 'raphael'
    path=OUT/'textures'/f'{name}.png';shutil.copy2(ROOT/f'src/cocos/assets/resources/actors/{origin}/textures'/source,path)
    mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path));mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);return mat
steel=material('steel','steel.png',.58,.72);wood=material('wood','wood.png',.8,0);brass=material('brass','brass.png',.45,.72);leather=material('leather','belt.png',.8,0);linen=material('linen','linen.png',.95,0)
def mesh(name,vertices,faces,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.materials.append(mat);obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    data.uv_layers.new(name='UVMap')
    for loop in data.loops:
        v=data.vertices[loop.vertex_index];data.uv_layers[0].data[loop.index].uv=(v.co.x*4+v.co.y,v.co.z)
    for p in data.polygons:p.use_smooth=True
    return obj
def cylinder(name,z0,z1,radius,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=z1-z0,location=(0,0,(z0+z1)/2));obj=bpy.context.object;obj.name=name;obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    return obj
def tube(name,points,radius,mat):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=2;s=curve.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');obj=bpy.context.object;obj.data.materials.append(mat);return obj
def export(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/f'{name}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',apply_unit_scale=True)
    for obj in objects:obj.hide_render=True;obj.hide_viewport=True
    print('[COCOS_PROP]',name,flush=True)
objects=[]
vertices=[(-.024,0,.08),(.024,0,.08),(.018,0,.64),(0,0,.76),(-.018,0,.64),(0,-.007,.35),(0,.007,.35)]
faces=[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5),(1,0,6),(2,1,6),(3,2,6),(4,3,6),(0,4,6)]
objects.append(mesh('SwordBlade',vertices,faces,steel));objects.append(cylinder('SwordGrip',-.12,.075,.016,leather));objects.append(cylinder('SwordPommel',-.145,-.12,.024,brass));objects.append(tube('SwordGuard',[(-.095,0,.08),(0,0,.09),(.095,0,.08)],.012,brass));export('sword',objects)
objects=[];points=[(0,-.18*math.sin(t*math.pi),-.70+t*1.4) for t in [i/64 for i in range(65)]]
objects.append(tube('Longbow',points,.014,wood));objects.append(tube('BowString',[points[0],(0,0,0),points[-1]],.0015,linen));objects.append(cylinder('BowGrip',-.055,.055,.018,leather));export('bow',objects)
objects=[cylinder('StaffShaft',-.77,.83,.021,wood),cylinder('StaffGrip',-.13,.13,.025,leather),cylinder('StaffFerrule',-.80,-.72,.026,brass)]
for z in [.72,.81]:objects.append(cylinder('StaffBrassCollar',z,z+.03,.034,brass))
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.07,location=(0,0,.92));orb=bpy.context.object;orb.name='StaffCrystal';orb.data.materials.append(steel);objects.append(orb)
for angle in [0,math.pi/2,math.pi,math.pi*1.5]:objects.append(tube('StaffCrystalProng',[(.035*math.cos(angle),.035*math.sin(angle),.8),(.08*math.cos(angle),.08*math.sin(angle),.91),(.03*math.cos(angle),.03*math.sin(angle),.99)],.006,brass))
export('staff',objects)
(OUT/'manifest.json').write_text(json.dumps({'resources':{name:f'actors/props/{name}/{name}' for name in ['sword','bow','staff']},'gripOrigin':[0,0,0],'cocosLongAxis':'+Y','attachmentBones':{'sword':'hand_r','staff':'hand_r','bow':'hand_l'},'rotationNote':'Rotate weapon node to match the hand bone basis; grip origin is at palm, not at mesh bounds center.'},indent=2))
for obj in bpy.data.objects:obj.hide_viewport=False;obj.hide_render=False
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'weapons.blend'))
