"""Reference-shaped curl guides using Blender's CC0 Curl Hair Curves asset."""
from pathlib import Path
import bpy,bmesh,math,random,json,sys,hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
SOURCE=BASE.parent/'3d-native-hair-v4';ASSETS=ROOT/'src/.tools/blender-4.5.15-windows-x64/4.5/datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend'

def digest(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()
def bind(o,rig):
    o.parent=rig;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);o.vertex_groups.clear();g=o.vertex_groups.new(name='Head');g.add(range(len(o.data.vertices)),1,'REPLACE');mod=o.modifiers.new('Native head binding','ARMATURE');mod.object=rig
def material(name,color,rough=.7,orm=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;tree=m.node_tree;bs=tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=0
    uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';n=tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(BASE/'textures'/color),check_existing=True);tree.links.new(uv.outputs[0],n.inputs['Vector']);tree.links.new(n.outputs['Color'],bs.inputs['Base Color'])
    if orm:
        n=tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(BASE/'textures'/orm),check_existing=True);n.image.colorspace_settings.name='Non-Color';tree.links.new(uv.outputs[0],n.inputs['Vector']);sep=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(n.outputs[0],sep.inputs[0]);tree.links.new(sep.outputs['Green'],bs.inputs['Roughness']);tree.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    return m

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
original=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];head=next(o for o in original if o.get('nativePart')=='head')
proof={'nonHairMeshHashes':{o.name:digest(o)for o in original if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get());random.seed(817)

# The native head supplies only the hidden scalp, retaining the actual skull fit.
cap=bpy.data.objects.new('CurlRoots',head.data.copy());bpy.context.scene.collection.objects.link(cap)
bm=bmesh.new();bm.from_mesh(cap.data)
def scalp(co):
    front=co.y<-.028
    if abs(co.x)>.080 and 1.635<co.z<1.75 and -.065<co.y<.065:return False
    return co.z>(1.752 if front else 1.642 if abs(co.x)>.055 else 1.612)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not scalp(v.co)],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for v in bm.verts:v.co+=v.normal*.0016
bm.to_mesh(cap.data);bm.free()
for name in [l.name for l in cap.data.uv_layers]:cap.data.uv_layers.remove(cap.data.uv_layers[name])
uv=cap.data.uv_layers.new(name='UVMap')
for p in cap.data.polygons:
    for li in p.loop_indices:
        co=cap.data.vertices[cap.data.loops[li].vertex_index].co;uv.data[li].uv=((math.atan2(co.x,-co.y)+math.pi)/(2*math.pi),.05)
cap.data.materials.clear();cap.data.materials.append(material('Hair2D_Roots','curl-roots.png',.84))
for p in cap.data.polygons:p.material_index=0;p.use_smooth=True
surface=BVHTree.FromObject(cap,bpy.context.evaluated_depsgraph_get())

# Guides follow the reference zones: crown swept across the forehead, loose
# temple curls and descending nape curls. Actual curl deformation/profile are
# Blender's bundled mature Geometry Nodes assets, not a custom curl solver.
curve=bpy.data.curves.new('Reference curl guides','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.twist_mode='MINIMUM'
obj=bpy.data.objects.new('ReferenceCurlGuides',curve);bpy.context.scene.collection.objects.link(obj)
centers=[]
for ring,theta in enumerate([.22,.48,.75,1.00,1.22,1.45,1.68,1.86]):
    count=8 if ring<2 else 13 if ring<5 else 15
    for k in range(count):
        phi=2*math.pi*(k+.47*(ring%2))/count
        approx=Vector((.083*math.sin(theta)*math.sin(phi),.012-.086*math.sin(theta)*math.cos(phi),1.689+.121*math.cos(theta)))
        if approx.y<-.028 and approx.z<1.748:continue
        if approx.z<1.635 and abs(approx.x)>.055:continue
        near,n,_,dist=surface.find_nearest(approx)
        if near is None or near.z<1.60:continue
        root=near+n*.002
        if theta<.85:direction=Vector((-.028,.043,.008));lift=.042
        elif math.cos(phi)>.42:direction=Vector((-.035,.008,-.019));lift=.034
        else:direction=Vector((math.copysign(.007,root.x),.018,-.052 if theta<1.5 else-.061));lift=.026
        centers.append((root,n,direction,lift,phi))
for index,(root,n,direction,lift,phase) in enumerate(centers):
    tangent=n.cross(Vector((0,0,1)))
    if tangent.length<.1:tangent=Vector((1,0,0))
    tangent.normalize();other=n.cross(tangent).normalized()
    for child in range(7):
        ang=child*2.39996+index;spread=.0048*math.sqrt((child+.3)/7);offset=(tangent*math.cos(ang)+other*math.sin(ang))*spread
        start=root+offset;near,nn,_,_=surface.find_nearest(start);start=near+nn*.002
        spline=curve.splines.new('POLY');spline.points.add(23)
        for i,p in enumerate(spline.points):
            t=i/23;position=start+direction*t+n*(lift*math.sin(t*math.pi*.85))
            position+=offset*(.65*math.sin(math.pi*t))
            p.co=(*position,1)

with bpy.data.libraries.load(str(ASSETS),link=False)as(src,dst):dst.node_groups=['Curl Hair Curves','Set Hair Curve Profile']
group=bpy.data.node_groups.new('2D reference curl groom','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
nodes,links=group.nodes,group.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
store=nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='strand_t';param=nodes.new('GeometryNodeSplineParameter');links.new(param.outputs['Factor'],store.inputs['Value']);links.new(inp.outputs[0],store.inputs['Geometry'])
curl=nodes.new('GeometryNodeGroup');curl.node_tree=bpy.data.node_groups['Curl Hair Curves'];curl.inputs['Existing Guide Map'].default_value=False;curl.inputs['Guide Distance'].default_value=.014;curl.inputs['Radius'].default_value=.010;curl.inputs['Frequency'].default_value=1.15;curl.inputs['Curl Start'].default_value=.06;curl.inputs['Subdivision'].default_value=0;curl.inputs['Factor Start'].default_value=.55;curl.inputs['Factor End'].default_value=1.;curl.inputs['Random Offset'].default_value=.12;curl.inputs['Seed'].default_value=83;links.new(store.outputs['Geometry'],curl.inputs['Geometry'])
profile=nodes.new('GeometryNodeGroup');profile.node_tree=bpy.data.node_groups['Set Hair Curve Profile'];profile.inputs['Radius'].default_value=.0045;profile.inputs['Factor Min'].default_value=.15;profile.inputs['Factor Max'].default_value=1.;profile.inputs['Shape'].default_value=.3;links.new(curl.outputs['Geometry'],profile.inputs['Geometry'])
circle=nodes.new('GeometryNodeCurvePrimitiveCircle');circle.inputs['Resolution'].default_value=4;circle.inputs['Radius'].default_value=1
flatten=nodes.new('GeometryNodeTransform');flatten.inputs['Scale'].default_value=(1,.35,1);links.new(circle.outputs['Curve'],flatten.inputs['Geometry'])
resample=nodes.new('GeometryNodeResampleCurve');resample.mode='COUNT';resample.inputs['Count'].default_value=24;links.new(profile.outputs['Geometry'],resample.inputs['Curve'])
to_mesh=nodes.new('GeometryNodeCurveToMesh');links.new(resample.outputs['Curve'],to_mesh.inputs['Curve']);links.new(flatten.outputs['Geometry'],to_mesh.inputs['Profile Curve']);to_mesh.inputs['Fill Caps'].default_value=True
radius=nodes.new('GeometryNodeInputRadius');links.new(radius.outputs['Radius'],to_mesh.inputs['Scale']);links.new(to_mesh.outputs['Mesh'],out.inputs[0])
mod=obj.modifiers.new('Blender native curl groom','NODES');mod.node_group=group;pipeline.select([obj]);bpy.ops.object.convert(target='MESH');hair=bpy.context.object
assert len(hair.data.vertices)>1000
bounds=[[min(v.co[i]for v in hair.data.vertices)for i in range(3)],[max(v.co[i]for v in hair.data.vertices)for i in range(3)]]
assert max(bounds[1][i]-bounds[0][i]for i in range(3))<.45,bounds
attribute=hair.data.attributes.get('strand_t');uv=hair.data.uv_layers.new(name='UVMap')
for p in hair.data.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        vi=hair.data.loops[li].vertex_index;uv.data[li].uv=((vi%4)/4,attribute.data[vi].value if attribute else .5)
hair.data.materials.clear();hair.data.materials.append(material('Hair2D_SilverFibres','curl-fibres.png',.7,'curl-orm.png'))
pipeline.select([hair,cap]);bpy.context.view_layer.objects.active=hair;bpy.ops.object.join();hair=bpy.context.object
for old in original:
    if old.get('nativePart')=='hair':bpy.data.objects.remove(old,do_unlink=True)
hair.name='raphael_native_hair_2D_Curls';hair['nativePart']='hair';hair['defaultVisible']=True;bind(hair,rig)
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'));manifest['materials']=[r for r in manifest['materials']if 'hair'not in r.get('parts',[])]+[
 {'runtimeName':'Hair2D_Roots','parts':['hair'],'maps':{'albedo':'../hair-2d-v5/textures/curl-roots.png'},'sourcePBR':{'effectiveFactors':{'roughness':.84,'metallic':0}}},
 {'runtimeName':'Hair2D_SilverFibres','parts':['hair'],'maps':{'albedo':'../hair-2d-v5/textures/curl-fibres.png','orm':'../hair-2d-v5/textures/curl-orm.png'},'sourcePBR':{'effectiveFactors':{'roughness':1,'metallic':1}},'ormChannels':{'occlusion':'r','roughness':'g','metallic':'b'}}]
manifest['parts']['hair']['nodes']=[hair.name];manifest.update(appearanceRevision='reference-2d-curls-v5',prefabRoot='raphael-polish',appearanceReview='source-art/characters/3d-2d-hair-v5/README.md',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
manifest['hairstyle']={'asset':'Project 2D-reference curl groom','method':'Blender bundled CC0 Curl Hair Curves and Set Hair Curve Profile; reference-oriented guides','reference':'source-art/characters/2d-concepts/identity-reference-v1/head-identity-master.png','guides':len(centers),'fibres':len(centers)*7,'physics':'Head-bound mesh; no simulated hair physics'}
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
proof.update(faceBodyUnchanged=True,all14ActionsUnchanged=True,bindPoseUnchanged=True,guides=len(centers),fibres=len(centers)*7,hairTriangles=pipeline.triangles(hair),triangles=manifest['triangles'],method='Blender bundled CC0 Curl Hair Curves + Set Hair Curve Profile, zoned reference guides; no downloaded models')
(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print('CURL_GROOM_EXPORTED',json.dumps(proof),flush=True)
