"""Bake the edited current Native65 actors, without rebuilding their rig/actions.

Blender 4.5.15 --background --factory-startup --python this.py -- --character raphael
Sources remain editable, staged exports are installed only after engine review.
"""
from pathlib import Path
import bpy,sys,json,math,hashlib,shutil,copy,os
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'src/.tmp/character-redesign-v6'
OUT=STAGE/'actors'
SOURCE=ROOT/'source-art/characters/redesign-v6'
OLD=ROOT/'src/.tmp/native-production/source'
PRODUCTION=ROOT/'src/cocos/assets/resources/actors'
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
sys.path.insert(0,str(Path(__file__).parent))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def relative(path):return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
def triangles(obj):return sum(len(p.vertices)-2 for p in obj.data.polygons)
def curves():
    return hashlib.sha256(repr([(a.name,list(a.frame_range),[(c.data_path,c.array_index,[(tuple(k.co),k.interpolation)for k in c.keyframe_points])for c in a.fcurves])for a in sorted(bpy.data.actions,key=lambda a:a.name)]).encode()).hexdigest()
def skeleton(rig):return hashlib.sha256(repr([(b.name,b.parent.name if b.parent else None,[tuple(r)for r in b.matrix_local],b.use_deform)for b in rig.data.bones]).encode()).hexdigest()
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.hide_set(False);obj.hide_render=False;obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
def socket_value(socket):return socket.links[0].from_socket if socket.is_linked else None
def uv_image(tree,path,uv):
    image=bpy.data.images.load(str(path),check_existing=True);node=tree.nodes.new('ShaderNodeTexImage');node.image=image
    coord=tree.nodes.new('ShaderNodeUVMap');coord.uv_map=uv;tree.links.new(coord.outputs['UV'],node.inputs['Vector']);return node

def prepare_sources(objects,manifest):
    records={r['runtimeName']:r for r in manifest['materials']}
    for obj in objects:
        if not obj.data.uv_layers:obj.data.uv_layers.new(name='V6_SOURCE_UV')
        obj.data.uv_layers[0].name='V6_SOURCE_UV'
        for slot in obj.material_slots:
            mat=slot.material
            if not mat or not mat.use_nodes:continue
            tree=mat.node_tree;bsdf=next((n for n in tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if not bsdf:continue
            record=records.get(mat.name);factors=(record or {}).get('sourcePBR',{}).get('effectiveFactors',{})
            for field,key in [('Metallic','metallic'),('Roughness','roughness')]:
                if not record or mat.get('v6_factors_applied'):continue
                factor=factors.get(key,1)
                inp=bsdf.inputs[field]
                if inp.is_linked:
                    old=inp.links[0].from_socket;mul=tree.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=factor;tree.links.new(old,mul.inputs[0]);tree.links.new(mul.outputs[0],inp)
                else:inp.default_value=factor
            mat['v6_factors_applied']=True
            for node in tree.nodes:
                if node.type=='TEX_IMAGE'and not node.inputs['Vector'].is_linked:
                    coord=tree.nodes.new('ShaderNodeUVMap');coord.uv_map='V6_SOURCE_UV';tree.links.new(coord.outputs['UV'],node.inputs['Vector'])
                if node.type=='NORMAL_MAP'and not node.uv_map:node.uv_map='V6_SOURCE_UV'

def skin_detail(objects):
    """Use existing licensed art and Blender material nodes, not a UV-image warp."""
    touched=[]
    for obj in objects:
        for slot in obj.material_slots:
            mat=slot.material
            if not mat or mat.get('v6_skin_adapted') or not any(x in mat.name.lower()for x in ['superhero','regular_']):continue
            bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if not bsdf:continue
            tree=mat.node_tree
            # Keep original feature positions and hue variation; desaturate the
            # old orange tan and lift it in linear space to the v5 light skin.
            for node in list(tree.nodes):
                if node.type!='TEX_IMAGE'or not node.image:continue
                name=(node.image.name+' '+node.image.filepath).lower()
                if not ('basecolor'in name or '_ligh'in name):continue
                destinations=[link.to_socket for link in node.outputs['Color'].links]
                hue=tree.nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=.48;hue.inputs['Value'].default_value=1.65 if 'regular_'in mat.name.lower()else 1.5
                tree.links.new(node.outputs['Color'],hue.inputs['Color'])
                for dest in destinations:tree.links.new(hue.outputs['Color'],dest)
            tex=tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=580;tex.inputs['Detail'].default_value=2
            coord=tree.nodes.new('ShaderNodeTexCoord');tree.links.new(coord.outputs['Object'],tex.inputs['Vector'])
            bump=tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00018
            tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
            if bsdf.inputs['Normal'].is_linked:tree.links.new(bsdf.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
            tree.links.new(bump.outputs['Normal'],bsdf.inputs['Normal']);mat['v6_skin_adapted']=True;mat['v6MaterialRole']='skin';touched.append(mat.name)
    return {'method':'Licensed original UV artwork; native Blender HSV/material pore bump, then unlit PBR bake','materials':touched}

def unwrap(objects):
    for obj in objects:
        uv=obj.data.uv_layers.get('V6_BAKE_UV')or obj.data.uv_layers.new(name='V6_BAKE_UV');obj.data.uv_layers.active=uv;uv.active_render=True
    select(objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.1,correct_aspect=True,scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.012,merge_overlap=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def blank(name,size,data=False):
    image=bpy.data.images.new(name,width=size,height=size,alpha=True,float_buffer=False);image.colorspace_settings.name='Non-Color'if data else'sRGB';image.generated_color=(0,0,0,0);return image
def save_image(image,path):
    path.parent.mkdir(parents=True,exist_ok=True);image.filepath_raw=str(path);image.file_format='PNG';image.save();return path
def bake(objects,name,size,channel):
    image=blank(name,size,channel!='Color');mats=list({m for o in objects for m in o.data.materials if m});changes=[]
    for mat in mats:
        tree=mat.node_tree;bsdf=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL')
        target=tree.nodes.new('ShaderNodeTexImage');target.image=image;tree.nodes.active=target;target.select=True
        if channel!='Normal':
            old=socket_value(out.inputs['Surface']);em=tree.nodes.new('ShaderNodeEmission')
            field=bsdf.inputs['Base Color'if channel=='Color'else channel]
            if field.is_linked:tree.links.new(field.links[0].from_socket,em.inputs['Color'])
            else:
                value=field.default_value;em.inputs['Color'].default_value=tuple(value)if channel=='Color'else(value,value,value,1)
            tree.links.new(em.outputs[0],out.inputs['Surface']);changes.append((tree,out,old,em,target))
        else:changes.append((tree,None,None,None,target))
    select(objects);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.bake.use_selected_to_active=False;scene.render.bake.use_clear=True;scene.render.bake.margin=8;scene.render.bake.target='IMAGE_TEXTURES'
    try:
        bpy.ops.object.bake(type='NORMAL'if channel=='Normal'else'EMIT',normal_space='TANGENT',normal_r='POS_X',normal_g='POS_Y',normal_b='POS_Z')
    finally:
        for tree,out,old,em,target in changes:
            if out and old:tree.links.new(old,out.inputs['Surface'])
            if em:tree.nodes.remove(em)
            tree.nodes.remove(target)
    return image

def packed_orm(rough,metal,name):
    size=rough.size[0];r=np.empty(size*size*4,dtype=np.float32);m=np.empty_like(r);rough.pixels.foreach_get(r);metal.pixels.foreach_get(m);r=r.reshape(-1,4);m=m.reshape(-1,4)
    packed=np.ones_like(r);packed[:,1]=r[:,0];packed[:,2]=m[:,0];image=blank(name,size,True);image.pixels.foreach_set(packed.ravel());image.update();return image
def apply_alpha(color,alpha):
    n=color.size[0]*color.size[1]*4;c=np.empty(n,dtype=np.float32);a=np.empty(n,dtype=np.float32);color.pixels.foreach_get(c);alpha.pixels.foreach_get(a);c.reshape(-1,4)[:,3]=a.reshape(-1,4)[:,0];color.pixels.foreach_set(c);color.update()

def group_bake(identity,label,objects,alpha=False):
    if not objects:return None
    high=identity in ['raphael','mira'];sizes={'body':(1024 if high else 512,512,256),'head':(1024 if high else 512,256,128),'hair':(512,256,128),'eyes':(256,128,128),'brows':(256,128,128)}
    color_size,normal_size,pbr_size=sizes[label];prefix='v6-'+identity+'-'+label;folder=OUT/'native-shared/textures'
    print('[V6_BAKE]',identity,label,len(objects),flush=True)
    unwrap(objects)
    color=bake(objects,prefix+'-color',color_size,'Color')
    if alpha:apply_alpha(color,bake(objects,prefix+'-alpha',color_size,'Alpha'))
    normal=bake(objects,prefix+'-normal',normal_size,'Normal');rough=bake(objects,prefix+'-rough',pbr_size,'Roughness');metal=bake(objects,prefix+'-metal',pbr_size,'Metallic');orm=packed_orm(rough,metal,prefix+'-orm')
    paths={key:save_image(image,folder/(prefix+'-'+key+'.png'))for key,image in [('color',color),('normal',normal),('orm',orm)]}
    mat=bpy.data.materials.new('V6_'+identity+'_'+label);mat.use_nodes=True;tree=mat.node_tree;bsdf=tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=1;bsdf.inputs['Metallic'].default_value=1
    color_node=uv_image(tree,paths['color'],'V6_BAKE_UV');tree.links.new(color_node.outputs['Color'],bsdf.inputs['Base Color'])
    if alpha:tree.links.new(color_node.outputs['Alpha'],bsdf.inputs['Alpha']);mat.surface_render_method='DITHERED'
    normal_node=uv_image(tree,paths['normal'],'V6_BAKE_UV');normal_node.image.colorspace_settings.name='Non-Color';n=tree.nodes.new('ShaderNodeNormalMap');n.uv_map='V6_BAKE_UV';tree.links.new(normal_node.outputs['Color'],n.inputs['Color']);tree.links.new(n.outputs[0],bsdf.inputs['Normal'])
    orm_node=uv_image(tree,paths['orm'],'V6_BAKE_UV');orm_node.image.colorspace_settings.name='Non-Color';sep=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(orm_node.outputs['Color'],sep.inputs[0]);tree.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);tree.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    record={'runtimeName':mat.name,'parts':sorted({str(o['nativePart'])for o in objects}),'maps':{'albedo':'../native-shared/textures/'+paths['color'].name,'normal':'../native-shared/textures/'+paths['normal'].name,'orm':'../native-shared/textures/'+paths['orm'].name},'sourcePBR':{'effectiveFactors':{'roughness':1,'metallic':1}},'ormChannels':{'occlusion':'r','roughness':'g','metallic':'b'},'alphaClip':alpha,'doubleSided':alpha,'alphaThreshold':.35,'bake':{'color':'Unlit emission from the editable material graph','normal':'OpenGL tangent +Y','orm':'R=1, G=effective roughness, B=effective metallic','sizes':[color_size,normal_size,pbr_size]}}
    return record,mat,objects

def preserve_images(objects):
    seen=set()
    for obj in objects:
        for mat in obj.data.materials:
            if not mat or not mat.use_nodes:continue
            for node in mat.node_tree.nodes:
                if node.type!='TEX_IMAGE'or not node.image or node.image in seen:continue
                image=node.image;seen.add(image)
                path=Path(bpy.path.abspath(image.filepath))
                if not path.is_file():continue
                dest=SOURCE/'source-textures'/(sha(path)[:12]+'-'+path.name);dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():shutil.copy2(path,dest)
                image.filepath=str(dest)

def visible_height(meshes):
    deps=bpy.context.evaluated_depsgraph_get();low=math.inf;high=-math.inf
    for obj in meshes:
        if not obj.get('defaultVisible',True):continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        for vertex in mesh.vertices:
            z=(evaluated.matrix_world@vertex.co).z;low=min(low,z);high=max(high,z)
        evaluated.to_mesh_clear()
    return high-low

def build(identity,skip=False):
    bpy.ops.wm.open_mainfile(filepath=str(OLD/(identity+'.blend')))
    manifest=json.loads((PRODUCTION/identity/'manifest.json').read_text(encoding='utf-8-sig'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');action_hash=curves();rig_hash=skeleton(rig);rig_transform=[list(r)for r in rig.matrix_world]
    rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
    meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
    prepare_sources(meshes,manifest);skin=skin_detail(meshes)
    changes={}
    if not skip:
        from v5_face_hair_adapter import apply as face
        from v5_wardrobe_adapter import apply as wardrobe
        changes['faceHair']=face(identity,rig,manifest);changes['wardrobe']=wardrobe(identity,rig,manifest)
    meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
    # Added materials receive explicit UV sampling before a new active bake UV.
    prepare_sources(meshes,manifest)
    assert curves()==action_hash and skeleton(rig)==rig_hash and [list(r)for r in rig.matrix_world]==rig_transform,'Appearance adapter altered the rig/actions'
    preserve_images(meshes);SOURCE.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(identity+'.blend')),relative_remap=False)
    groups={name:[]for name in ['body','head','hair','eyes','brows']}
    for obj in meshes:
        part=str(obj['nativePart']);label='brows'if part=='lashes'else part if part in ['head','hair','eyes','brows']else'body';groups[label].append(obj)
    materials=[];baked=[]
    for label,objects in groups.items():
        alpha=any(m and (m.get('v6AlphaMode') in ['CLIP','IMAGE','MASK']or m.get('v6AlphaSource')or any(n.type=='BSDF_PRINCIPLED'and n.inputs['Alpha'].is_linked for n in m.node_tree.nodes))for o in objects for m in o.data.materials)
        result=group_bake(identity,label,objects,alpha)
        if result:materials.append(result[0]);baked.append(result)
    # Finish every bake before replacing source graphs or removing UV layers.
    # RNA layer pointers become stale when CustomData is compacted: reacquire
    # layers by name, never keep a layer wrapper across a remove operation.
    for record,mat,objects in baked:
        for obj in objects:
            obj.data.materials.clear();obj.data.materials.append(mat)
            for poly in obj.data.polygons:poly.material_index=0
            for name in [uv.name for uv in obj.data.uv_layers if uv.name!='V6_BAKE_UV']:
                obj.data.uv_layers.remove(obj.data.uv_layers[name])
            target=obj.data.uv_layers['V6_BAKE_UV'];target.name='UVMap';obj.data.uv_layers.active=target;target.active_render=True
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        for node in mat.node_tree.nodes:
            if node.type=='UVMAP'and node.uv_map=='V6_BAKE_UV':node.uv_map='UVMap'
            if node.type=='NORMAL_MAP'and node.uv_map=='V6_BAKE_UV':node.uv_map='UVMap'
    rig.data.pose_position='POSE';idle=next(a for a in bpy.data.actions if a.name=='idle');rig.animation_data.action=idle
    if idle.slots:rig.animation_data.action_slot=idle.slots[0]
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update();height=visible_height(meshes);select([rig]+meshes);bpy.context.view_layer.objects.active=rig
    folder=OUT/identity;folder.mkdir(parents=True,exist_ok=True);fbx=folder/(identity+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',embed_textures=False,use_custom_props=True)
    assert curves()==action_hash and skeleton(rig)==rig_hash
    parts={}
    for obj in meshes:
        part=str(obj['nativePart']);entry=parts.setdefault(part,{'nodes':[],'defaultVisible':bool(obj.get('defaultVisible',True))});entry['nodes'].append(obj.name)
    manifest.update({'appearanceRevision':'v6','reviewStatus':'AWAITING_ENGINE_APPEARANCE_REVIEW','source':relative(SOURCE/(identity+'.blend')),'materials':materials,'textures':sorted({path for m in materials for path in m['maps'].values()}),'parts':parts,'triangles':sum(triangles(o)for o in meshes),'geometry':{'idleHeightMetres':height,'measurement':'Visible evaluated v6 sole-to-hair bounds; native rig scale retained'},'appearanceChanges':changes,'skinAdaptation':skin,'rigPreservation':{'actionSHA256':action_hash,'bindSHA256':rig_hash,'rigTransform':rig_transform,'unchanged':True},'limitations':changes.get('faceHair',{}).get('limitations',[])})
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('[V6_EXPORTED]',identity,manifest['triangles'],sha(fbx),flush=True)
    return manifest

if __name__=='__main__':
    selected=sys.argv[sys.argv.index('--character')+1].split(',')if'--character'in sys.argv else IDS
    for identity in selected:build(identity,'--skip-adapters'in sys.argv)
