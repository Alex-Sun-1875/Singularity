"""Integrate the existing native65 face, wardrobe, UV/PBR bake and FBX tools.
Only concept-specific tailoring/texture projection is added here.
"""
from pathlib import Path
import bpy,bmesh,json,sys,math
from mathutils import Vector,Matrix
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import v5_face_hair_adapter as face
import v5_wardrobe_adapter as cloth
import cocos_v5_character_redesign as pipeline
pipeline.OUT=BASE/'stage';pipeline.SOURCE=BASE/'sources'
DEST=ROOT/'src/cocos/assets/resources/actors/raphael'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-motion-tempo-v1/compact-jog.blend'))
rig=bpy.data.objects['raphael_Native65'];manifest=json.loads((DEST/'manifest.json').read_text(encoding='utf-8'));scene=bpy.context.scene
action_hash=pipeline.curves();bind_hash=pipeline.skeleton(rig);rig.data.pose_position='REST'
originals=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
for obj in originals:
    for material in obj.data.materials:
        if not material:continue
        record=next((r for r in manifest['materials']if r['runtimeName']==material.name),None)
        if not record:continue
        for node in material.node_tree.nodes:
            if node.type!='TEX_IMAGE'or not node.image:continue
            name=node.image.filepath.lower();kind='normal'if 'normal'in name else'orm'if'orm'in name else'roughness'if'rough'in name else'albedo'
            if kind in record['maps']:node.image=bpy.data.images.load(str((DEST/record['maps'][kind]).resolve()),check_existing=True)
pipeline.prepare_sources(originals,manifest)
face.STYLE['raphael'].update(size=(.222,.214,.194),offset=(0,.012,.033),tint=(.35,.38,.42),smile=0,brow=-.0008,asym=.0001,jaw=.0022,chin=.0034,cheek=.0040,nose=.0020)
import_hair=face._import_hair
def detailed_hair(meta):
    meta['detailBudget']=14000
    return import_hair(meta)
face._import_hair=detailed_hair
face_record=face.apply('raphael',rig,manifest)
hair=next(o for o in bpy.data.objects if o.get('nativePart')=='hair'and 'main'in o.name)
hm=hair.data.materials[0];tree=hm.node_tree
source=next(n for n in tree.nodes if n.type=='TEX_IMAGE'and n.name=='V6_SourceAlbedo');source.image=bpy.data.images.load(str(BASE/'references/silver-curl-detail.png'));source.projection='BOX';source.projection_blend=.3
coord=tree.nodes.new('ShaderNodeTexCoord');tree.links.new(coord.outputs['Generated'],source.inputs['Vector'])
detail=next(n for n in tree.nodes if n.type=='MAP_RANGE');detail.inputs['From Max'].default_value=1;detail.inputs['To Min'].default_value=.42;detail.inputs['To Max'].default_value=1.2
bump=tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0008;tree.links.new(source.outputs['Color'],bump.inputs['Height']);bs=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED');tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
brows=next(o for o in bpy.data.objects if o.get('nativePart')=='brows')
for node in brows.data.materials[0].node_tree.nodes:
    if node.type=='MIX_RGB'and node.blend_type=='MULTIPLY':node.inputs[2].default_value=(.045,.034,.027,1)
head=next(o for o in bpy.data.objects if o.get('nativePart')=='head');hm=head.data.materials[0];bs=next(n for n in hm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.65
old=bs.inputs['Base Color'].links[0].from_socket;hue=hm.node_tree.nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=.80;hm.node_tree.links.new(old,hue.inputs['Color']);hm.node_tree.links.new(hue.outputs[0],bs.inputs['Base Color'])

originals=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
body=next(o for o in originals if o.get('nativePart')=='body'and'belt'not in o.name.lower());arms=next(o for o in originals if o.get('nativePart')=='arms'and'bracer'not in o.name.lower())
sx=abs(rig.data.bones['upperarm_l'].head_local.x)/.1919;sz=rig.data.bones['neck_01'].head_local.z/1.5205;ctx=('raphael',rig,body,sx,sz)
proxies=[]
for source_obj in [body,arms]+[o for o in originals if o.get('nativePart')=='legs']:
    obj=source_obj.copy();obj.data=source_obj.data.copy();scene.collection.objects.link(obj)
    for key in list(obj.keys()):del obj[key]
    obj.name='AppearanceWeightProxy';proxies.append(obj)
pipeline.select(proxies);bpy.ops.object.join();proxy=proxies[0];proxy.hide_render=True;rig['v6WardrobeFitProxy']=proxy.name;rig['v6WardrobeWeightProxy']=proxy.name
for obj in list(originals):
    part=obj.get('nativePart')
    if part=='pauldrons'or part=='arms'and'bracer'in obj.name.lower():bpy.data.objects.remove(obj,do_unlink=True);continue
    if part in ['legs','feet']or part=='body'and'belt'in obj.name.lower():cloth._recolor_native_slots(obj,'raphael','leather'if part!='legs'else'cloth',(.10,.052,.027)if part!='legs'else(.020,.022,.028),.88)
    if part=='feet':
        cloth._tailor_boot_shaft(obj,rig,.18)
        for vertex in obj.data.vertices:
            if vertex.co.z>.15:vertex.co.z=.15+(vertex.co.z-.15)*(.31-.15)/(.52-.15)
    if part=='legs':
        for vertex in obj.data.vertices:
            if vertex.co.z<.55:vertex.co.z=.265+(vertex.co.z-.395)*(.55-.265)/(.55-.395)
    if obj==arms:
        original_materials=list(obj.data.materials);cloth._recolor_native_slots(obj,'raphael','cloth',(.018,.021,.030),.88)
        for index,material in enumerate(original_materials):
            if 'Regular'in material.name:
                obj.data.materials[index]=material;bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');previous=bs.inputs['Base Color'].links[0].from_socket;h=material.node_tree.nodes.new('ShaderNodeHueSaturation');h.inputs['Saturation'].default_value=.65;h.inputs['Value'].default_value=2.1;material.node_tree.links.new(previous,h.inputs['Color']);material.node_tree.links.new(h.outputs[0],bs.inputs['Base Color'])
dark=cloth._material('raphael','cloth',(.018,.021,.030));body.data.materials.clear();body.data.materials.append(dark)
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<1.035*sz or v.co.z>1.515*sz],context='VERTS');bm.to_mesh(body.data);bm.free()
wine=cloth._material('raphael','wine',(.070,.020,.032));linen=cloth._material('raphael','linen',(.68,.61,.48));thread=cloth._material('raphael','thread',(.37,.23,.085));leather=cloth._material('raphael','leather',(.10,.05,.025));brass=cloth._material('raphael','brass',(.30,.19,.065))
rows=[(.87,.210,.153,.14),(1.02,.186,.153,.10),(1.17,.156,.146,.035),(1.34,.184,.152,.055),(1.47,.205,.128,.08),(1.535,.080,.080,.28),(1.60,.072,.074,.30)]
native_mesh=cloth._mesh
def continuous_coat(*args,**kwargs):
    if args[0]=='burgundy_split_embroidered_coat':kwargs['fit_above']=None
    return native_mesh(*args,**kwargs)
cloth._mesh=continuous_coat
made,verts,grid=cloth._surface(ctx,'burgundy_split_embroidered_coat',rows,wine,segments=40,seam=False,hem_wave=.002,neckline=False)
cloth._mesh=native_mesh;coat=made[0];added=list(made)
for vertex in coat.data.vertices:vertex.co.y+=.025*max(0,min(1,(vertex.co.z/sz-1.47)/.065))
verts=[tuple(v.co)for v in list(coat.data.vertices)[:len(verts)]]
insert=[(-.035*sx,-.095,1.55*sz),(0,-.14,1.43*sz),(.035*sx,-.095,1.55*sz)]
added.append(cloth._mesh('ivory_shirt_opening',insert,[(0,1,2)],'raphael',rig,'body',linen,body,.002))
# Gold piping follows the actual modeled opening, hem and collar edge.
for name,indices in [('front_left',[r[0]for r in grid]),('front_right',[r[-1]for r in grid]),('hem',grid[0])]:
    added.append(cloth._seam(ctx,'gold_binding_'+name,[Vector(verts[i])+Vector((0,-.001,0))for i in indices],thread,.0012,fit_target=coat))
added.append(cloth._seam(ctx,'collar_gold_binding',[Vector(verts[i])for i in grid[-1]],thread,.0012))

# Project the existing front/back 2D embroidery, retaining a real curved coat.
atlas=bpy.data.images.load(str(BASE/'references/coat-design-atlas.png'));nt=wine.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='DesignUV';tex=nt.nodes.new('ShaderNodeTexImage');tex.image=atlas;tex.extension='EXTEND';nt.links.new(uv.outputs[0],tex.inputs['Vector']);nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.10;b.inputs['Distance'].default_value=.0005;nt.links.new(tex.outputs['Color'],b.inputs['Height']);nt.links.new(b.outputs[0],bs.inputs['Normal']);bs.inputs['Roughness'].default_value=.67
for obj in [coat]:
    layer=obj.data.uv_layers.new(name='DesignUV')
    for polygon in obj.data.polygons:
        front=polygon.normal.y<0
        for index in polygon.loop_indices:
            co=obj.data.vertices[obj.data.loops[index].vertex_index].co;layer.data[index].uv=((.25+co.x/(.84*sx))if front else(.75-co.x/(.84*sx)),(co.z/sz-.87)/.73)

# Small linen cuffs sit at the wrists, following the original arm weights.
arm_added=[]
for side,suffix in [(1,'l'),(-1,'r')]:
    shoulder=rig.data.bones['upperarm_'+suffix].head_local;vs=[];fs=[];n=24
    for offset,radius in [(-.045,.078),(.005,.080),(.075,.065)]:
        for j in range(n):
            t=math.tau*j/n;vs.append((shoulder.x+side*offset,shoulder.y+radius*math.cos(t),shoulder.z+radius*math.sin(t)))
    for row in range(2):
        for j in range(n):a=row*n+j;c=row*n+(j+1)%n;fs.append((a,c,c+n,a+n))
    arm_added.append(cloth._mesh('tailored_shoulder_sleeve_'+suffix,vs,fs,'raphael',rig,'arms',dark,arms,.002))
for side,suffix in [(1,'l'),(-1,'r')]:
    wrist=rig.data.bones['hand_'+suffix].head_local;vs=[];fs=[];n=20
    for delta,radius in [(-.021,.037),(-.008,.039),(.002,.037)]:
        for j in range(n):t=math.tau*j/n;vs.append((wrist.x+side*delta,wrist.y+radius*math.cos(t),wrist.z+radius*math.sin(t)))
    for row in range(2):
        for j in range(n):a=row*n+j;c=row*n+(j+1)%n;fs.append((a,c,c+n,a+n))
    arm_added.append(cloth._mesh('ivory_wrist_cuff_'+suffix,vs,fs,'raphael',rig,'arms',linen,arms,.0015))

feet=next(o for o in bpy.data.objects if o.get('nativePart')=='feet');laces=[]
from mathutils.bvhtree import BVHTree
boot_tree=BVHTree.FromPolygons([v.co for v in feet.data.vertices],[p.vertices[:]for p in feet.data.polygons])
lace_material=cloth._material('raphael','lace',(.30,.20,.11));feet_ctx=('raphael',rig,feet,sx,sz)
for side,suffix in [(1,'l'),(-1,'r')]:
    centre=rig.data.bones['foot_'+suffix].head_local.x
    for i in range(6):
        z=.16+i*.023
        for sign in [-1,1]:
            points=[]
            for x,height in [(centre+sign*.019,z),(centre-sign*.019,z+.019)]:
                hit=boot_tree.ray_cast(Vector((x,-1,height)),Vector((0,1,0)))[0]
                if hit:points.append(hit+Vector((0,-.002,0)))
            if len(points)==2:laces.append(cloth._seam(feet_ctx,'crossed_boot_lace_'+suffix+str(i)+str(sign),points,lace_material,.0009,part='feet'))

def rounded_box(name,centre,size,material,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1);obj=bpy.context.object;obj.name=name;obj.location=centre;obj.scale=size;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    mod=obj.modifiers.new('Leather rounded edges','BEVEL');mod.width=bevel;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name);cloth._tag(obj,'raphael','body',material);obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4);obj.vertex_groups.clear();obj.vertex_groups.new(name='pelvis').add(range(len(obj.data.vertices)),1,'REPLACE');arm=obj.modifiers.new('Native pelvis binding','ARMATURE');arm.object=rig
    for p in obj.data.polygons:p.use_smooth=True
    return obj
added.append(rounded_box('leather_hip_pouch',(-.186*sx,-.111,1.075*sz),(.115*sx,.066,.128*sz),leather,.012))
added.append(rounded_box('pouch_flap',(-.186*sx,-.149,1.106*sz),(.122*sx,.014,.060*sz),leather,.010))
added.append(rounded_box('pouch_brass_fastener',(-.186*sx,-.161,1.09*sz),(.012,.008,.016),brass,.003))
for centre in [(-.222*sx,-.113,1.155*sz),(-.15*sx,-.113,1.155*sz)]:added.append(rounded_box('pouch_belt_loop',centre,(.014,.014,.043),leather,.003))

# Keep the original material/part split and thirteen native renderers.
for target,objects in [(body,added),(arms,arm_added),(feet,laces)]:
    pipeline.select([target]+objects);bpy.context.view_layer.objects.active=target;bpy.ops.object.join()
bpy.data.objects.remove(proxy,do_unlink=True)
for key in ['v6WardrobeFitProxy','v6WardrobeWeightProxy']:del rig[key]
meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(meshes)==13,len(meshes)
pipeline.prepare_sources(meshes,manifest);pipeline.preserve_images(meshes)
assert pipeline.curves()==action_hash and pipeline.skeleton(rig)==bind_hash
pipeline.SOURCE.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(pipeline.SOURCE/'raphael-editable.blend'),relative_remap=False)
(BASE/'authoring-review.json').write_text(json.dumps({'faceHair':face_record,'preservedActionsSHA256':action_hash,'preservedBindSHA256':bind_hash,'meshCount':len(meshes),'rejectedHairPilot':'o4saken_curly01 clipped/decimated cards produced spikes; not installed','design':'Current silver curls, adult face, burgundy gold-embroidered split coat, single standing collar, charcoal sleeves/trousers, ivory cuffs, brown flip-top hip pouch'},indent=2)+'\n',encoding='utf-8')
if '--probe'in sys.argv:
    face._render('raphael',rig,BASE/'appearance-head-probe.png')
    camera=scene.camera;camera.data.ortho_scale=2.12;target=Vector((0,0,.96));camera.location=target+Vector((.9,-4,.25));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.filepath=str(BASE/'appearance-full-probe.png');bpy.ops.render.render(write_still=True)
    sys.exit(0)
groups={name:[]for name in ['body','head','hair','eyes','brows']}
for obj in meshes:
    part=obj['nativePart'];groups['brows'if part=='lashes'else part if part in ['head','hair','eyes','brows']else'body'].append(obj)
baked=[];materials=[]
for label,objects in groups.items():
    result=pipeline.group_bake('raphael',label,objects,label in ['eyes','brows']);baked.append(result);materials.append(result[0])
for record,material,objects in baked:
    for obj in objects:
        obj.data.materials.clear();obj.data.materials.append(material)
        for p in obj.data.polygons:p.material_index=0
        for name in [layer.name for layer in obj.data.uv_layers if layer.name!='V6_BAKE_UV']:obj.data.uv_layers.remove(obj.data.uv_layers[name])
        layer=obj.data.uv_layers['V6_BAKE_UV'];layer.name='UVMap';obj.data.uv_layers.active=layer;layer.active_render=True
    for node in material.node_tree.nodes:
        if node.type in ['UVMAP','NORMAL_MAP']:node.uv_map='UVMap'
    for kind,path in record['maps'].items():record['maps'][kind]='../appearance-v1/textures/'+Path(path).name
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
scene.frame_set(0);scene.render.fps=30;scene.render.fps_base=1;pipeline.select([rig]+meshes);bpy.context.view_layer.objects.active=rig
fbx=BASE/'raphael.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',colors_type='NONE',embed_textures=False,use_custom_props=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
parts={}
for obj in meshes:parts.setdefault(obj['nativePart'],{'nodes':[],'defaultVisible':bool(obj.get('defaultVisible',True))})['nodes'].append(obj.name)
manifest.update(appearanceRevision='2d-design-v1',appearanceReview='source-art/characters/3d-appearance-v1/README.md',source=fbx.with_suffix('.blend').relative_to(ROOT).as_posix(),parts=parts,materials=materials,textures=sorted({p for m in materials for p in m['maps'].values()}),triangles=sum(pipeline.triangles(o)for o in meshes),license='Mixed: Quaternius/MakeHuman CC0; Elvaerwyn elvs_wavy_bob CC-BY; existing project 2D design; see appearance credits',appearancePreservation={'actionsSHA256':action_hash,'bindSHA256':bind_hash,'all14ActionsUnchanged':True,'renderers':13})
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('APPEARANCE_EXPORTED',manifest['triangles'],pipeline.sha(fbx),flush=True)
