"""Stage original CC0 Native65 kit characters; production install is separate.

No body/clothing generation or animation solver: this is import, supplied head
selection, head attachment, palette/image adaptation and built-in FBX export.
"""
from pathlib import Path
import re
import bpy,bmesh,json,math,hashlib,shutil,sys,os,copy,struct
import numpy as np
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'src/.tmp/native-production'
OUT=Path(os.environ.get('SINGULARITY_NATIVE_ASSETS',STAGE/'actors'))
SOURCE=Path(os.environ.get('SINGULARITY_NATIVE_SOURCE',STAGE/'source'))
ANIMATION=STAGE/'animation'
KITS=ROOT/'src/.tools/quaternius-ready-kits'
BASE=KITS/'universal-base-characters-standard/Universal Base Characters[Standard]'
FANTASY=KITS/'modular-fantasy-outfits-standard/Modular Character Outfits - Fantasy[Standard]'
GLTF=FANTASY/'Exports/glTF (Godot-Unreal)'
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
CONFIG={
 'raphael':dict(sex='Male',outfit='Ranger',hair='Hair_SimpleParted',hood=False,variant=1,dye=(.045,.10,.095),haircolor=(.085,.035,.014)),
 'mira':dict(sex='Female',outfit='Peasant',hair='Hair_Long',hood=False,variant=1,dye=(.28,.025,.045),haircolor=(.70,.46,.17)),
 'lorn':dict(sex='Male',outfit='Ranger',hair='Hair_Buzzed',hood=False,variant=3,dye=(.075,.11,.17),haircolor=(.025,.018,.014)),
 'nightqi':dict(sex='Female',outfit='Ranger',hair='Hair_Long',hood=False,variant=1,dye=(.13,.17,.12),haircolor=(.59,.36,.12)),
 'kael':dict(sex='Male',outfit='Peasant',hair='Hair_SimpleParted',hood=False,variant=1,dye=(.47,.25,.065),haircolor=(.14,.052,.018)),
 'evelyn':dict(sex='Female',outfit='Ranger',hair='Hair_Long',hood=False,variant=3,dye=(.045,.085,.18),haircolor=(.72,.56,.27)),
 'captain':dict(sex='Male',outfit='Ranger',hair='Hair_SimpleParted',hood=False,variant=3,dye=(.23,.045,.035),haircolor=(.17,.085,.027)),
 'raider':dict(sex='Male',outfit='Peasant',hair='Hair_Buzzed',hood=False,variant=2,dye=(.12,.065,.03),haircolor=(.05,.026,.013)),
 'raider-shield':dict(sex='Male',outfit='Ranger',hair='Hair_Buzzed',hood=False,variant=3,dye=(.14,.075,.035),haircolor=(.035,.018,.010)),
 'raider-archer':dict(sex='Male',outfit='Ranger',hair='Hair_SimpleParted',hood=True,variant=1,dye=(.13,.16,.085),haircolor=(.08,.035,.014)),
}

def relative(p):return str(Path(p).relative_to(ROOT)).replace('\\','/')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
def assign(rig,action):
    rig.animation_data_create();rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
def frame(f):bpy.context.scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
def imported(path):
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));objects=list(set(bpy.data.objects)-old)
    return next(o for o in objects if o.type=='ARMATURE'),sorted([o for o in objects if o.type=='MESH'and any(m.type=='ARMATURE'for m in o.modifiers)],key=lambda o:o.name)
def transfer(obj,rig):
    obj.parent=rig;obj.matrix_parent_inverse.identity();obj.location=(0,0,0);obj.rotation_euler=(0,0,0);obj.scale=(1,1,1)
    for mod in obj.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
def points(objects):
    values=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();values.extend(ev.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
    return values
def bounds(objects):
    v=points(objects);return min(p.z for p in v),max(p.z for p in v)
def part(name):
    n=name.lower()
    for token,group in [('hood','hood'),('pauldron','pauldrons'),('arms','arms'),('feet','feet'),('legs','legs'),('body','body')]:
        if token in n:return group
    return 'body'

def add_attachments(rig,contract):
    result=copy.deepcopy(contract)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    matrices={}
    for side in ['left','right']:
        data=contract[side];hand=rig.data.bones[data['parent']];suffix='l'if side=='left'else'r'
        matrix=hand.matrix_local@Matrix(data['referenceParentRelativeRest'])
        matrix.translation=(rig.data.bones['index_01_'+suffix].head_local+rig.data.bones['pinky_01_'+suffix].head_local)*.5
        matrices[side]=matrix
    bpy.ops.object.mode_set(mode='EDIT')
    for side,matrix in matrices.items():
        data=contract[side];bone=rig.data.edit_bones.new(data['bone']);bone.parent=rig.data.edit_bones[data['parent']]
        bone.head=matrix.translation;bone.tail=matrix.translation+matrix.to_3x3()@Vector((0,.07,0));bone.matrix=matrix;bone.use_deform=False
    bpy.ops.object.mode_set(mode='OBJECT')
    for side in ['left','right']:
        data=contract[side];helper=rig.data.bones[data['bone']];parent=rig.data.bones[data['parent']]
        rig.pose.bones[data['bone']].rotation_mode='QUATERNION'
        result[side]['targetParentRelativeRest']=[list(row)for row in parent.matrix_local.inverted()@helper.matrix_local]
        result[side]['targetAnchor']='Original target index/pinky head midpoint; helper orientation from reference parent-relative rest'
    return result

def palette_nodes(tree,tex,out,mode,color,hues):
    """Built-in Blender color nodes, shared between editable shader and PNG export."""
    nodes,links=tree.nodes,tree.links;prefix='CompositorNode'if tree.bl_idname=='CompositorNodeTree'else'ShaderNode'
    mix=nodes.new(prefix+'MixRGB');mix.blend_type='MULTIPLY'if mode=='multiply'else'COLOR'
    mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*color,1);links.new(tex.outputs['Color'if'Color'in tex.outputs else'Image'],mix.inputs[1])
    if mode=='color':
        sep=nodes.new(prefix+'SeparateColor');sep.mode='HSV';links.new(tex.outputs['Color'if'Color'in tex.outputs else'Image'],sep.inputs[0])
        sat=nodes.new(prefix+'Math');sat.operation='GREATER_THAN';sat.inputs[1].default_value=.16;links.new(sep.outputs[1],sat.inputs[0])
        low=nodes.new(prefix+'Math');low.operation='GREATER_THAN';low.inputs[1].default_value=hues[0];links.new(sep.outputs[0],low.inputs[0])
        high=nodes.new(prefix+'Math');high.operation='LESS_THAN';high.inputs[1].default_value=hues[1];links.new(sep.outputs[0],high.inputs[0])
        m=nodes.new(prefix+'Math');m.operation='MULTIPLY';links.new(low.outputs[0],m.inputs[0]);links.new(high.outputs[0],m.inputs[1])
        m2=nodes.new(prefix+'Math');m2.operation='MULTIPLY';links.new(m.outputs[0],m2.inputs[0]);links.new(sat.outputs[0],m2.inputs[1]);links.new(m2.outputs[0],mix.inputs[0])
    links.new(mix.outputs[0],out);return mix

def process_image(source_path,kind,limit,palette=None):
    source_path=Path(source_path);key={'sha':digest(source_path),'kind':kind,'limit':limit,'palette':palette}
    token=hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()[:16]
    destination=OUT/'native-shared/textures'/(token+'-'+source_path.name)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        image=bpy.data.images.load(str(source_path),check_existing=False);image.colorspace_settings.name='sRGB'if kind=='albedo'else'Non-Color'
        w,h=image.size;scale=min(1,limit/max(w,h));image.scale(max(1,round(w*scale)),max(1,round(h*scale)))
        if palette:
            scene=bpy.data.scenes.new('NativePaletteExport');scene.render.engine='CYCLES';scene.cycles.samples=1
            scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=image.size[0];scene.render.resolution_y=image.size[1];scene.render.resolution_percentage=100
            scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
            camera=bpy.data.objects.new('PaletteExportCamera',bpy.data.cameras.new('PaletteExportCamera'));scene.collection.objects.link(camera);scene.camera=camera
            scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=100
            scene.use_nodes=True;tree=scene.node_tree;tree.nodes.clear();tex=tree.nodes.new('CompositorNodeImage');tex.image=image
            composite=tree.nodes.new('CompositorNodeComposite');palette_nodes(tree,tex,composite.inputs[0],palette['mode'],palette['color'],palette.get('hues',(.0,1)))
            scene.render.filepath=str(destination);bpy.ops.render.render(write_still=True,scene=scene.name)
            bpy.data.objects.remove(camera,do_unlink=True);bpy.data.scenes.remove(scene)
        else:
            image.filepath_raw=str(destination);image.file_format='PNG';image.save()
        bpy.data.images.remove(image)
    image=bpy.data.images.load(str(destination),check_existing=True);image.colorspace_settings.name='sRGB'if kind=='albedo'else'Non-Color'
    return image,{'runtime':str(destination.relative_to(OUT)).replace('\\','/'),'source':relative(source_path),'sourceSHA256':key['sha'],'runtimeSHA256':digest(destination),'size':list(image.size),'colorSpace':image.colorspace_settings.name,'palette':palette}

def prepare(identity):
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30
    cfg=CONFIG[identity];old=json.loads((ROOT/'src/cocos/assets/resources/actors'/identity/'manifest.json').read_text());profile=copy.deepcopy(old['profile']);profile['haircolor']=cfg['haircolor']
    profile['legacyProceduralWidth']=profile.get('legacyProceduralWidth',profile.get('width',1));profile['width']=1.0
    src=GLTF/'Outfits'/(cfg['sex']+'_'+cfg['outfit']+'.gltf');rig,garments=imported(src);rig.name=identity+'_Native65'
    mesh_sources={o:src for o in garments};groups={o:part(o.name)for o in garments};original_names={o:o.name for o in garments}
    base_path=BASE/'Base Characters/Godot - UE'/('Superhero_'+cfg['sex']+'_FullBody.gltf');base_rig,heads=imported(base_path)
    head_selection=[]
    for obj in heads:
        name=obj.name;before=tris(obj)
        if obj.name.lower().startswith('superhero'):
            indexes={g.index for g in obj.vertex_groups if g.name in ['Head','neck_01']}
            keep={v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in indexes)>=.5}
            bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS');bm.to_mesh(obj.data);bm.free();obj.data.update();group='head'
        else:group='eyes'if'eye'in name.lower()and'brow'not in name.lower()else'brows'
        assert max(abs(rig.data.bones[n].matrix_local[i][j]-base_rig.data.bones[n].matrix_local[i][j])for n in ['Head','neck_01']for i in range(4)for j in range(4))<1e-5
        transfer(obj,rig);mesh_sources[obj]=base_path;groups[obj]=group;original_names[obj]=name;head_selection.append({'mesh':name,'sourceTriangles':before,'selectedTriangles':tris(obj),'method':'Original Head/neck weights >=.5; no new vertices'})
    bpy.data.objects.remove(base_rig,do_unlink=True)
    hair_path=BASE/'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)'/(cfg['hair']+'.gltf');hair_rig,hairs=imported(hair_path)
    correction=rig.data.bones['Head'].matrix_local@hair_rig.data.bones['Head'].matrix_local.inverted()
    for obj in hairs:
        original_names[obj]=obj.name
        for v in obj.data.vertices:v.co=correction@v.co
        transfer(obj,rig);mesh_sources[obj]=hair_path;groups[obj]='hair'
    bpy.data.objects.remove(hair_rig,do_unlink=True);meshes=garments+heads+hairs
    for obj in meshes:obj.name=identity+'_native_'+groups[obj]+'_'+original_names[obj]
    hidden=['hood']if not cfg['hood']else[]
    for obj in meshes:
        if groups[obj]in hidden:obj.hide_render=True
        obj['nativePart']=groups[obj];obj['defaultVisible']=groups[obj]not in hidden
    # Repair two incorrect URIs in the original Standard glTF in memory only.
    for image in bpy.data.images:
        p=Path(bpy.path.abspath(image.filepath))
        if image.source=='FILE'and not p.is_file():
            fixed=p.with_name(p.name.replace('_png.png','.png'))
            if fixed.is_file():image.filepath=str(fixed);image.reload()
    animations=json.loads((ANIMATION/'manifest.json').read_text())
    attachments=add_attachments(rig,animations['attachments'])if'--with-bow'in sys.argv else None
    available=[n for n in animations['availableActions']if n!='attack_bow' or '--with-bow'in sys.argv]
    with bpy.data.libraries.load(str(ANIMATION/'native65-actions.blend'),link=False)as(library_data,dst):dst.actions=list(available)
    actions={name:a for name,a in zip(available,dst.actions) if a}
    assert set(actions)==set(available)
    for a in list(bpy.data.actions):
        if a not in actions.values():bpy.data.actions.remove(a)
    for name,action in actions.items():action.name=name
    assign(rig,actions['idle']);frame(0);visible=[o for o in meshes if groups[o]not in hidden];lo,hi=bounds(visible)
    scale=profile['height']/(hi-lo);rig.scale=(scale,scale,scale);bpy.context.view_layer.update()
    # Source bone proportions define the physical stride, then uniform height scales it.
    stride_scale=rig.data.bones['thigh_l'].length*scale/animations['referenceThighLength']
    clip_records={};feet=[o for o in meshes if groups[o]=='feet']
    for name,action in actions.items():
        assign(rig,action);start,end=map(float,action.frame_range);frames=sorted(set([start,end]+[i*.5 for i in range(math.ceil(start*2),math.floor(end*2)+1)]))
        samples=[];root=rig.pose.bones['root']
        up=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,1))
        for f in frames:
            frame(f);p=points(visible if name in ['dodge','death']else feet);samples.append((f,root.location.copy(),min(v.z for v in p)))
        minimum=min(g for f,p,g in samples)
        for f,original,ground in samples:
            frame(f);desired=.003+(ground-minimum if name=='run'else 0);root.location=original+up*(desired-ground);root.keyframe_insert('location',frame=f)
        record=copy.deepcopy(animations['clips'][name]);record['duration']=(end-start)/30;record['sourceDuration']=record['duration'];record['characterFloorAlignment']={'method':'Built-in root location export offset from evaluated original shoe/body geometry; no pose solving','contact':'body'if name in ['dodge','death']else'sole','sourceMinimum':minimum,'runFlightPreserved':name=='run'}
        if name=='death':
            frame(end);hold=end+math.ceil((end-start)*.3)
            for bone in rig.pose.bones:
                for prop in ['location','rotation_quaternion','scale']:bone.keyframe_insert(prop,frame=hold)
            record['exportFinalPoseHoldSeconds']=(hold-end)/30;record['duration']=(hold-start)/30;record['endFrame']=hold;record['holdFinalPose']=True
        record['nominalSpeedMetresPerSecond']=(.975 if name=='walk'else 5.357142857142857 if name=='run'else 0)*stride_scale
        record['strideSource']='Original UAL1 RM travel / duration scaled by target/reference thigh length and uniform actor height scale'
        for fc in action.fcurves:
            if fc.data_path=='pose.bones["root"].location':
                for k in fc.keyframe_points:k.interpolation='LINEAR'
        clip_records[name]=record;action.use_fake_user=True
    if 'attack_bow'in actions:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from cocos_native_motions import bake_bow_contact_for_rig
        before_contact=actions['attack_bow'].copy();before_contact.name='qa_attack_bow_precontact';before_contact.use_fake_user=True
        baked,contact=bake_bow_contact_for_rig(rig,actions['attack_bow'],output_name='attack_bow')
        actions['attack_bow']=baked;clip_records['attack_bow']['targetContact']=contact
        if contact['fullContactMaxMetres']>=.005:
            (STAGE/('bow-target-'+identity+'.json')).write_text(json.dumps(contact,indent=2)+'\n')
            bpy.ops.wm.save_as_mainfile(filepath=str(STAGE/('bow-target-'+identity+'.blend')),relative_remap=False)
        assert contact['fullContactMaxMetres']<.005,(identity,contact['fullContactMaxMetres'])
        for side in ['left','right']:
            item=attachments[side];helper=rig.data.bones[item['bone']];parent=rig.data.bones[item['parent']]
            item['targetParentRelativeRest']=[list(row)for row in parent.matrix_local.inverted()@helper.matrix_local]
        for action in list(bpy.data.actions):
            if action not in actions.values():bpy.data.actions.remove(action)
    assign(rig,actions['idle']);frame(0)
    material_uses={}
    for obj in meshes:
        for i,material in enumerate(obj.data.materials):
            if not material:continue
            role=groups[obj];palette=None
            if role in ['body','hood']:
                palette={'mode':'color','color':cfg['dye'],'hues':(.16,.48)if cfg['outfit']=='Ranger'and cfg['variant']==1 else((.105,.48)if cfg['outfit']=='Ranger'else(.015,.16))}
            if role in ['hair','brows']:palette={'mode':'multiply','color':tuple(c*(.38 if role=='brows'else 1)for c in cfg['haircolor'])}
            source_variant=cfg['variant']if ('MI_'+cfg['outfit'])in material.name else 1
            key=(material.name,source_variant,json.dumps(palette,sort_keys=True))
            if key not in material_uses:
                clone=material.copy();clone.name='Native_'+material.name.replace('MI_','')+'_'+hashlib.sha256(str(key).encode()).hexdigest()[:8];material_uses[key]={'material':clone,'sourceName':material.name,'palette':palette,'roles':set()}
            use=material_uses[key];use['roles'].add(role);obj.data.materials[i]=use['material']
    texture_records=[];material_records=[];node_exports=[]
    for use in material_uses.values():
        material=use['material'];bsdf=material.node_tree.nodes.get('Principled BSDF');record={'runtimeName':material.name,'sourceName':use['sourceName'],'parts':sorted(use['roles']),'maps':{},'sourcePBR':{'roughness':float(bsdf.inputs['Roughness'].default_value),'metallic':float(bsdf.inputs['Metallic'].default_value),'linked':{'roughness':bsdf.inputs['Roughness'].is_linked,'metallic':bsdf.inputs['Metallic'].is_linked},'effectiveFactors':{'roughness':1 if bsdf.inputs['Roughness'].is_linked else float(bsdf.inputs['Roughness'].default_value),'metallic':1 if bsdf.inputs['Metallic'].is_linked else float(bsdf.inputs['Metallic'].default_value)}},'ormChannels':{'occlusion':'R','roughness':'G','metallic':'B'},'palette':use['palette']}
        # Read actual glTF multipliers: linked Blender inputs can include a
        # multiply-by-zero node (skin metallicFactor0), not an implicit factor1.
        author_path=hair_path if 'hair'in use['roles'] else base_path if set(use['roles'])&{'head','eyes','brows'} else src
        author_name=re.sub(r'\.\d+$','',use['sourceName'])
        author_mat=next(m for m in json.loads(author_path.read_text(encoding='utf8'))['materials']if m.get('name')==author_name)
        author_pbr=author_mat.get('pbrMetallicRoughness',{})
        record['sourcePBR']['effectiveFactors']={'roughness':author_pbr.get('roughnessFactor',1),'metallic':author_pbr.get('metallicFactor',1)}
        record['sourcePBR']['authorGLTF']=relative(author_path);record['sourcePBR']['authorMaterial']=author_name
        for node in list(material.node_tree.nodes):
            if node.type!='TEX_IMAGE'or not node.image:continue
            path=Path(bpy.path.abspath(node.image.filepath));kind='normal'if'normal'in path.name.lower()else'orm'if'_orm'in path.name.lower()else'roughness'if'roughness'in path.name.lower()else'albedo'
            if kind=='albedo'and'Ranger'in path.name and cfg['variant']==3:path=FANTASY/'Textures/Ranger/T_Ranger_3_BaseColor.png'
            if kind=='albedo'and'Peasant'in path.name and cfg['variant']==2:path=FANTASY/'Textures/Peasant/T_Peasant_2_BaseColor.png'
            if kind=='albedo'and'Superhero_'in path.name:path=BASE/'Base Characters/Textures'/('T_Superhero_Female_Light_BaseColor.png'if cfg['sex']=='Female'else'T_Superhero_Male_Ligh.png')
            assert path.is_file(),path
            author=SOURCE/'shared/original'/(digest(path)[:12]+'-'+path.name);author.parent.mkdir(parents=True,exist_ok=True)
            if not author.exists():shutil.copy2(path,author)
            image=bpy.data.images.load(str(author),check_existing=True);image.colorspace_settings.name='sRGB'if kind=='albedo'else'Non-Color';image.filepath='//shared/original/'+author.name;node.image=image
            palette=use['palette']if kind=='albedo'else None
            if palette:palette_nodes(material.node_tree,node,bsdf.inputs['Base Color'],palette['mode'],palette['color'],palette.get('hues',(.0,1)))
            limit=1024 if'head'in use['roles']and identity in ['raphael','mira']and kind=='albedo'else 512
            node_exports.append((node,path,kind,limit,palette,record,bsdf))
        material_records.append(record)
    SOURCE.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(identity+'.blend')),relative_remap=False)
    for node,path,kind,limit,palette,record,bsdf in node_exports:
        image,data=process_image(path,kind,limit,palette);node.image=image
        if kind=='albedo':material=bpy.data.materials[record['runtimeName']];material.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
        record['maps'][kind]='../'+data['runtime'];texture_records.append(data)
    max_influences=0;names={b.name for b in rig.data.bones}
    for obj in meshes:
        for v in obj.data.vertices:
            influences=[g for g in v.groups if obj.vertex_groups[g.group].name in names and g.weight>1e-6];max_influences=max(max_influences,len(influences));assert len(influences)<=4
    folder=OUT/identity;folder.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for obj in meshes:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig;fbx=folder/(identity+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=.5,bake_anim_simplify_factor=.001,path_mode='RELATIVE',embed_textures=False,use_custom_props=True)
    assign(rig,actions['idle']);frame(0)
    idle_lo,idle_hi=bounds(visible);parts={g:{'nodes':[o.name for o in meshes if groups[o]==g],'defaultVisible':g not in hidden}for g in sorted(set(groups.values()))}
    missing=[n for n in animations['canonicalActions']if n not in actions]
    textures=sorted(set('../'+x['runtime']for x in texture_records));provenance={x['source']:x for x in texture_records}
    manifest={'id':identity,'runtimeProfile':'native-kit-v1','reviewStatus':'BOW_PENDING'if missing else'READY_FOR_COCOS_VISUAL_REVIEW','pendingClips':missing,'resource':f'actors/{identity}/{identity}/{identity}','fbx':fbx.name,'source':relative(SOURCE/(identity+'.blend')),'axis':{'forward':'Z','up':'Y','meters':True},'modelYaw':0,'skeletonJointCount':len(rig.data.bones),'skinJointCount':65,'bones':[b.name for b in rig.data.bones],'triangles':sum(tris(o)for o in meshes),'maxInfluences':max_influences,'profile':profile,'nativeKit':cfg,'geometry':{'idleHeightMetres':idle_hi-idle_lo,'measurement':'Visible evaluated original sole-to-hair bounds, scaled to v5 profile height'},'clips':clip_records,'libraryMotion':{'tool':'Original native65 pose Actions; built-in Blender import/export','clips':clip_records,'sources':animations['sources'],'actionLibrarySHA256':digest(ANIMATION/'native65-actions.blend')},'attachments':attachments,'materials':material_records,'parts':parts,'defaultHiddenParts':hidden,'textures':textures,'textureProvenance':list(provenance.values()),'sourceHeadSelection':head_selection,'sourceAssets':[{'file':relative(p),'sha256':digest(p)}for p in [src,base_path,hair_path]],'license':'CC0-1.0','licenseManifest':'source-art/characters/library-kits/sources.json','sockets':{'bones':{'right':'hand_r','left':'hand_l'},'grips':{}},'limitations':['Original free Ranger/Peasant sets are not heavy plate armor or exact v5 costume silhouettes.','Supplied long hair is reused with blonde tint; no new curl/bob/ponytail strand modelling.','Two supplied base faces are reused; bespoke v5 facial sculpting is not claimed.','Weapons and runtime native PBR/default part selection are integrated separately.']}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('[NATIVE_STAGED]',identity,manifest['triangles'],'triangles',manifest['skeletonJointCount'],'bones','pending',missing,flush=True)
    return manifest

if __name__=='__main__':
    selected=sys.argv[sys.argv.index('--character')+1].split(',')if'--character'in sys.argv else IDS
    records={identity:prepare(identity)for identity in selected}
    report=OUT/'native-integration-report.json';previous=json.loads(report.read_text())if report.exists()else{}
    previous.update({k:{'triangles':v['triangles'],'skeletonJointCount':v['skeletonJointCount'],'pendingClips':v['pendingClips'],'fbxSHA256':digest(OUT/k/(k+'.fbx'))}for k,v in records.items()});report.write_text(json.dumps(previous,indent=2)+'\n')
    shared=OUT/'native-shared/textures';referenced=set()
    for manifest_path in OUT.glob('*/manifest.json'):
        data=json.loads(manifest_path.read_text())
        if data.get('runtimeProfile')=='native-kit-v1':referenced.update((manifest_path.parent/p).resolve()for p in data['textures'])
    for path in shared.glob('*.png'):
        if path.resolve()not in referenced:
            assert path.resolve().is_relative_to(shared.resolve());path.unlink()
    maps=list(shared.glob('*.png'));base=mip=0
    for path in maps:
        w,h=struct.unpack_from('>II',path.read_bytes(),16);base+=w*h*4
        while True:
            mip+=w*h*4
            if w==1 and h==1:break
            w=max(1,w//2);h=max(1,h//2)
    budget={'scope':'Shared native PNGs; uncompressed RGBA8 estimate, not measured device residency/frame rate','count':len(maps),'pngBytes':sum(p.stat().st_size for p in maps),'rgbaBaseBytes':base,'rgbaFullMipChainBytes':mip,'limits':{'pngBytes':16000000,'rgbaBaseBytes':64*1024*1024,'rgbaFullMipChainBytes':86*1024*1024}}
    (OUT.parent/'texture-budget.json').write_text(json.dumps(budget,indent=2)+'\n')
    assert budget['pngBytes']<=16000000 and base<=64*1024*1024 and mip<=86*1024*1024,budget
