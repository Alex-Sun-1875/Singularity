"""Author the current hero from the CC0 MakeHuman basemesh, locally in Blender.

This is a new fitted character. It never opens the rejected blockout/study files.
"""
from pathlib import Path
import sys,math,json
import bpy,bmesh
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_bootstrap import make_body,ROOT,HumanService

PACK=ROOT/'src/.tools/makehuman-assets'
CHARACTER=sys.argv[sys.argv.index('--character')+1] if '--character' in sys.argv else 'raphael'
if CHARACTER not in {'raphael','mira','raider'}: raise ValueError('Unknown character')
SOURCE=ROOT/'source-art/characters'
SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
body,rig=make_body(CHARACTER.title(),gender=0.0 if CHARACTER=='mira' else 1.0)
bpy.context.view_layer.update()
human_height=body.dimensions.z

def material(name,color,rough=.7,metal=0,texture=None,cutout=False):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1)
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Roughness'].default_value=rough; bsdf.inputs['Metallic'].default_value=metal
    m['game_color']=list(color); m['game_roughness']=rough; m['game_metallic']=metal
    m['game_cutout']=cutout
    if texture:
        image=bpy.data.images.load(str(texture),check_existing=True)
        tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=image
        tint=m.node_tree.nodes.new('ShaderNodeMixRGB'); tint.blend_type='MULTIPLY'
        tint.inputs[0].default_value=1; tint.inputs[2].default_value=(*color,1)
        m.node_tree.links.new(tex.outputs['Color'],tint.inputs[1])
        m.node_tree.links.new(tint.outputs[0],bsdf.inputs['Base Color'])
        if cutout: m.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
        m['game_texture']=str(texture)
    return m

skin_folder='young_caucasian_female2' if CHARACTER=='mira' else 'young_caucasian_male2'
import re
skin_dir=PACK/'skins'/skin_folder
skin_texture=re.search(r'^diffuseTexture\s+(.+)$',(skin_dir/(skin_folder+'.mhmat')).read_text(),re.M).group(1).strip()
skin=material('Skin',(.9,.72,.55),.65,texture=skin_dir/skin_texture)
body.data.materials.clear(); body.data.materials.append(skin)

def asset(folder,name,kind):
    obj=HumanService.add_mhclo_asset(str(PACK/folder/name/(name+'.mhclo')),body,asset_type=kind,subdiv_levels=0,material_type='GAMEENGINE')
    obj.name=name
    return obj

eyes=asset('eyes','high-poly','Eyes')
eyes.data.materials.clear(); eyes.data.materials.append(material('BrownEyes',(1,1,1),.18,texture=PACK/'eyes/materials/brown_eye.png'))
brows=asset('eyebrows','eyebrow001','Eyebrows')
brows.data.materials.clear(); brows.data.materials.append(material('Eyebrows',(.17,.08,.035),.85,texture=PACK/'eyebrows/eyebrow001/eyebrow001.png',cutout=True))
hair_name='bob02' if CHARACTER=='mira' else ('short04' if CHARACTER=='raider' else 'short02')
hair=asset('hair',hair_name,'Hair')
hair_color=(1.2,.82,.32) if CHARACTER=='mira' else (.22,.11,.04)
hair.data.materials.clear(); hair.data.materials.append(material('Hair',hair_color,.76,texture=PACK/'hair'/hair_name/(hair_name+'_diffuse.png'),cutout=True))
clothes=asset('clothes','male_casualsuit01','Clothes')
boots=asset('clothes','shoes03','Clothes')
linen=material('UndyedLinen',(.72,.66,.51),.95)
trousers=material('BrownWool',(.16,.105,.065),.93)
leather=material('EmbossedLeather',(.23,.102,.041),.72)
dark=material('DarkLeather',(.095,.047,.022),.76)
teal=material('WeatheredTeal',(.065,.18,.16),.96)
if CHARACTER=='mira':
    leather=material('BurgundyLeather',(.22,.035,.025),.72)
    teal=material('BurgundyMantle',(.13,.02,.015),.95)
elif CHARACTER=='raider':
    leather=material('WornRaiderLeather',(.09,.065,.035),.85)
    linen=material('WeatheredShirt',(.23,.18,.105),.96)
    teal=material('RaiderMantle',(.11,.04,.02),.95)
steel=material('BrushedSteel',(.30,.33,.30),.55,.65)
brass=material('AntiqueBrass',(.42,.26,.085),.44,.65)
clothes.data.materials.clear(); clothes.data.materials.append(linen); clothes.data.materials.append(trousers)
waist=rig.data.bones['pelvis'].head_local.z+0.045
for poly in clothes.data.polygons:
    poly.material_index=0 if sum(clothes.data.vertices[i].co.z for i in poly.vertices)/len(poly.vertices)>waist else 1
boots.data.materials.clear(); boots.data.materials.append(dark)

# Fitted additions use the real skinned body as their weight-transfer surface.
names={b.name for b in rig.data.bones}
tree=KDTree(len(body.data.vertices))
for v in body.data.vertices: tree.insert(v.co,v.index)
tree.balance()
def bind(obj,bone=None):
    obj.parent=rig
    for name in names: obj.vertex_groups.new(name=name)
    for v in obj.data.vertices:
        influences={}
        if bone: influences={bone:1}
        else:
            _,index,_=tree.find(v.co)
            for g in body.data.vertices[index].groups:
                name=body.vertex_groups[g.group].name
                if name in names: influences[name]=g.weight
        total=sum(influences.values())
        if total<.001: influences={'spine_02':1}; total=1
        for name,weight in influences.items(): obj.vertex_groups[name].add([v.index],weight/total,'REPLACE')
    mod=obj.modifiers.new('Skin','ARMATURE'); mod.object=rig
    for p in obj.data.polygons: p.use_smooth=True
    return obj
def mesh(name,verts,faces,mat,bone=None,solid=.0):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj); data.materials.append(mat)
    bind(obj,bone)
    if solid:
        mod=obj.modifiers.new('LeatherThickness','SOLIDIFY'); mod.thickness=solid
    return obj
def box(name,loc,size,mat,bone='pelvis',bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object; obj.name=name; obj.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    # Store vertices in rig space before assigning skeletal weights.
    for v in obj.data.vertices: v.co+=obj.location
    obj.location=(0,0,0); obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('RoundedEdges','BEVEL'); mod.width=bevel; mod.segments=3
    return bind(obj,bone)
def tube(name,points,radius,mat,bone='spine_02'):
    curve=bpy.data.curves.new(name,'CURVE'); curve.dimensions='3D'; curve.resolution_u=2
    curve.bevel_depth=radius; curve.bevel_resolution=2
    spline=curve.splines.new('POLY'); spline.points.add(len(points)-1)
    for v,co in zip(spline.points,points): v.co=(*co,1)
    obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.convert(target='MESH'); obj=bpy.context.object
    obj.data.materials.append(mat); bind(obj,bone); obj.select_set(False)
    return obj

chest=rig.data.bones['spine_03'].head_local.z
neck=rig.data.bones['neck_01'].head_local.z
hip=rig.data.bones['pelvis'].head_local.z
# Continuous leather vest with neck and arm openings, fitted over the linen.
verts=[]; faces=[]; rings=9; segments=32
for j in range(rings):
    t=j/(rings-1); z=hip-.08+t*(neck-hip-.075)
    rx=.155+.052*math.sin(t*math.pi*.72)
    ry=.11+.025*math.sin(t*math.pi)
    for i in range(segments):
        a=i*math.tau/segments
        verts.append((math.cos(a)*rx,math.sin(a)*ry-.003,z))
for j in range(rings-1):
    for i in range(segments):
        a=(i+.5)*math.tau/segments
        # Open arm holes near the shoulders, keep front and back shoulder panels.
        if j>=rings-3 and abs(math.cos(a))>.72: continue
        faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
vest=clothes.copy(); vest.data=clothes.data.copy(); bpy.context.collection.objects.link(vest)
vest.name='TailoredLeatherVest'; vest.data.materials.clear(); vest.data.materials.append(leather)
bm=bmesh.new(); bm.from_mesh(vest.data)
remove=[]
for face in bm.faces:
    center=face.calc_center_median()
    if not (hip-.065<center.z<neck-.06 and abs(center.x)<.245): remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
for v in bm.verts: v.co+=v.normal*.018
bm.to_mesh(vest.data); bm.free()
for face in vest.data.polygons: face.material_index=0
mod=vest.modifiers.new('LeatherThickness','SOLIDIFY'); mod.thickness=.006
def surface_y(x,z,back=False):
    points=[v.co for v in clothes.data.vertices if (v.co.y>0)==back]
    nearby=sorted(points,key=lambda p:(p.x-x)**2+(p.z-z)**2)[:8]
    return (max(p.y for p in nearby)+.023) if back else (min(p.y for p in nearby)-.023)
for side in [-1,1]:
    points=[]
    for k in range(16):
        z=hip-.055+k*(neck-hip-.07)/15; x=side*.065
        points.append((x,surface_y(x,z)-.003,z))
    tube('VestFrontSeam',points,.0018,brass)
for i in range(5):
    z=hip+.04+i*.075
    box('VestFastener',(0,surface_y(0,z)-.008,z),(.014,.009,.017),brass,'spine_02',.004)
# Belt and diagonal sword belt are geometry, not flat projected concept art.
for z in [hip-.045,hip-.005]:
    tube('WaistBelt',[(math.cos(a)*.177,math.sin(a)*.133,z) for a in [i*math.tau/64 for i in range(65)]],.014,dark,'pelvis')
box('BeltBuckle',(.035,-.152,hip-.022),(.064,.014,.056),brass)
for side in [-1,1]:
    box('BeltPouch',(side*.19,-.045,hip-.13),(.115,.07,.16),leather)
    box('PouchFlap',(side*.19,-.09,hip-.09),(.12,.024,.065),dark)
    box('PouchStud',(side*.19,-.105,hip-.102),(.013,.01,.013),brass)
# Short asymmetric shoulder cloak; drape front/back follows the real upper torso.
for back in [-1,1]:
    vv=[]; ff=[]; cols=10; rows=10
    for row in range(rows):
        t=row/(rows-1)
        for col in range(cols):
            u=col/(cols-1)
            x=-.035+u*.29
            z=neck-.015-t*(.26+.08*(1-u))-.04*u
            y=surface_y(x,z,back>0)+back*(.009*math.sin(u*math.pi*5)*t+.008*t)
            vv.append((x,y,z))
    for j in range(rows-1):
        for i in range(cols-1):
            ff.append((j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i))
    # The drape guide is not used as a render mesh; fit the visible mantle to the
    # authored shirt surface so its skin weights follow the shoulder correctly.
mantle=clothes.copy(); mantle.data=clothes.data.copy(); bpy.context.collection.objects.link(mantle)
mantle.name='FittedTealMantle'; mantle.data.materials.clear(); mantle.data.materials.append(teal)
bm=bmesh.new(); bm.from_mesh(mantle.data)
remove=[]
for face in bm.faces:
    center=face.calc_center_median()
    bottom=neck-.32+.07*max(0,center.x)
    if not (bottom<center.z<neck+.025 and -.045<center.x<.35): remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
for v in bm.verts: v.co+=v.normal*.043
bm.to_mesh(mantle.data); bm.free()
for face in mantle.data.polygons: face.material_index=0
mod=mantle.modifiers.new('ClothHem','SOLIDIFY'); mod.thickness=.006
box('StarClasp',(.08,surface_y(.08,neck-.055)-.017,neck-.055),(.036,.012,.036),brass,'spine_03',.008)
# Anatomically fitted curved shoulder plate, not stacked blockout primitives.
shoulder=rig.data.bones['upperarm_r'].head_local
vv=[]; ff=[]; steps=24; bands=8
for j in range(bands):
    phi=.06+j/(bands-1)*1.4
    for i in range(steps):
        a=i*math.tau/steps
        vv.append((shoulder.x+.13*math.sin(phi)*math.cos(a),shoulder.y+.11*math.sin(phi)*math.sin(a),shoulder.z+.08*math.cos(phi)+.015))
for j in range(bands-1):
    for i in range(steps): ff.append((j*steps+i,j*steps+(i+1)%steps,(j+1)*steps+(i+1)%steps,(j+1)*steps+i))
mesh('SteelPauldron',vv,ff,steel,'upperarm_r',.008)
tube('PauldronRim',vv[-steps:]+[vv[-steps]],.004,brass,'upperarm_r')
# Small authored curls break up the flat hair-card silhouette around the forehead.
head=rig.data.bones['head'].head_local
curl=material('CurlHair',(.035,.013,.005),.78)
for i in range(50 if CHARACTER=='raphael' else 0):
    a=i*2.39996; x=math.cos(a)*(.065+(i%3)*.012); y=-.07+math.sin(a)*.035
    z=head.z+.105+(i%4)*.012
    points=[(x+.012*math.cos(t),y+.012*math.sin(t),z+t*.002) for t in [k*math.pi/10 for k in range(27)]]
    tube('ForeheadCurl',points,.0026,curl,'head')

# Normalize the whole authored hierarchy to the intended 1.85m human scale.
bpy.context.view_layer.update()
rig.scale=((1.72 if CHARACTER=='mira' else 1.85)/human_height,)*3
if CHARACTER=='mira':
    for obj in rig.children_recursive:
        if obj.name.startswith(('SteelPauldron','PauldronRim')): obj.hide_render=True
bpy.context.scene.render.fps=30

def turn(name,angle,axis=(1,0,0)):
    bone=rig.data.bones[name]
    rest=bone.matrix_local.to_quaternion()
    return rest.inverted()@Quaternion(axis,angle)@rest
def pose(kind,t):
    for b in rig.pose.bones: b.rotation_mode='QUATERNION'; b.rotation_quaternion=Quaternion(); b.location=(0,0,0)
    phase=t*math.tau
    for side,sign in [('l',1),('r',-1)]:
        for finger in ['index','middle','ring','pinky']:
            for joint in [1,2,3]:
                name=f'{finger}_{joint:02d}_{side}'
                rig.pose.bones[name].rotation_quaternion=turn(name,sign*(.65 if side=='r' else .18),(0,1,0))
    # Lower the A-pose arms into an actual relaxed standing stance.
    for side,sign in [('l',1),('r',-1)]:
        bone=rig.data.bones['upperarm_'+side]
        direction=bone.tail_local-bone.head_local
        goal=Vector((sign*.10,-.04,-1)).normalized()
        delta=direction.normalized().rotation_difference(goal)
        rest=bone.matrix_local.to_quaternion()
        rig.pose.bones[bone.name].rotation_quaternion=rest.inverted()@delta@rest
    if kind=='run':
        for side,offset in [('l',0),('r',math.pi)]:
            s=math.sin(phase+offset)
            rig.pose.bones['thigh_'+side].rotation_quaternion=turn('thigh_'+side,-s*.68)
            rig.pose.bones['calf_'+side].rotation_quaternion=turn('calf_'+side,max(0,-s)*1.0)
            rig.pose.bones['foot_'+side].rotation_quaternion=turn('foot_'+side,s*.25)
            arm=rig.pose.bones['upperarm_'+side]
            arm.rotation_quaternion=arm.rotation_quaternion@turn(arm.name,s*.38)
        rig.pose.bones['Root'].location.z=.025*(1-math.cos(phase*2))
        rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',-.10)
    elif kind=='attack':
        swing=math.sin(t*math.pi)
        rig.pose.bones['spine_03'].rotation_quaternion=turn('spine_03',-.18*swing,(0,0,1))
        arm=rig.pose.bones['upperarm_r']; arm.rotation_quaternion=arm.rotation_quaternion@turn(arm.name,-1.55*swing)
        rig.pose.bones['lowerarm_r'].rotation_quaternion=turn('lowerarm_r',-.72*swing,(0,0,1))
    elif kind=='hit':
        rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',-.25*math.sin(t*math.pi))
        rig.pose.bones['neck_01'].rotation_quaternion=turn('neck_01',-.12*math.sin(t*math.pi))
    else:
        rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',math.sin(phase)*.018)
    bpy.context.view_layer.update()

for kind,duration in [('idle',2.0),('run',.72),('attack',.65),('hit',.42)]:
    action=bpy.data.actions.new(kind)
    rig.animation_data_create(); rig.animation_data.action=action
    steps=24 if kind=='run' else 16
    for i in range(steps+1):
        pose(kind,i/steps)
        frame=1+i/steps*duration*30
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_quaternion',frame=frame)
            b.keyframe_insert('location',frame=frame)
    action.use_fake_user=True
rig.animation_data.action=bpy.data.actions['idle']; bpy.context.scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(CHARACTER+'.blend')))

if '--export' in sys.argv:
    from export_blender_character import export_character
    export_character(rig,ROOT/'src/assets/model'/CHARACTER,'model/'+CHARACTER)

print('[Raphael] authored meshes',len([o for o in rig.children_recursive if o.type=='MESH']),'bones',len(rig.data.bones))
