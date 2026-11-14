"""Fit licensed library surfaces to the frozen v5 game rig.

Blender 4.5.15 + MPFB 2.0.18. -- --character raphael [--draft]
This is an adapter for upstream MHCLO meshes, not generated replacement hair.
"""
from pathlib import Path
import sys, json, re, os, shutil
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_bootstrap import ROOT, HumanService, TargetService

SOURCE = Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT / 'source-art/characters/cocos'))
OUT = Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT / 'src/cocos/assets/resources/actors'))
LIBRARY = ROOT / 'src/.tools/makehuman-community'
PRESETS = json.loads((ROOT / 'tools/model-pipeline/mpfb-appearance-presets.json').read_text())
HAIR = {
    'raphael': 'elvs_wavy_bob',
    'mira': 'elvs_wavy_bob',
    'lorn': 'culturalibre_hair_05',
    'nightqi': 'culturalibre_hair_17',
    'kael': 'culturalibre_hair_06',
    'evelyn': 'elvs_ashley_may_hair',
    'captain': 'culturalibre_hair_05',
    'raider': 'culturalibre_hair_05',
    'raider-shield': 'culturalibre_hair_06',
    'raider-archer': 'culturalibre_hair_05',
}


def bind(asset, rig, name, weights=None):
    asset.parent = rig
    asset.matrix_parent_inverse = Matrix.Identity(4)
    asset.matrix_basis = Matrix.Identity(4)
    asset.modifiers.clear()
    asset.vertex_groups.clear()
    if weights is None:
        group = asset.vertex_groups.new(name='head')
        group.add(range(len(asset.data.vertices)), 1.0, 'REPLACE')
    else:
        tree = KDTree(len(weights.data.vertices))
        for v in weights.data.vertices: tree.insert(v.co, v.index)
        tree.balance()
        for b in rig.data.bones: asset.vertex_groups.new(name=b.name)
        for v in asset.data.vertices:
            _, index, _ = tree.find(v.co)
            entries = sorted([(weights.vertex_groups[g.group].name, g.weight) for g in weights.data.vertices[index].groups if weights.vertex_groups[g.group].name in rig.data.bones], key=lambda x:-x[1])[:4]
            total = sum(w for _, w in entries)
            for name2, weight in entries: asset.vertex_groups[name2].add([v.index], weight / total, 'REPLACE')
    modifier = asset.modifiers.new('Skin', 'ARMATURE'); modifier.object = rig
    asset.name = name
    for p in asset.data.polygons: p.use_smooth = True


def library_material(identity, part, source, dye=None, alpha=False, normal=None):
    im = bpy.data.images.load(str(source), check_existing=False)
    pixels = np.asarray(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    if dye:
        lum = pixels[:,:,:3] @ np.array([.2126,.7152,.0722])
        valid = lum[pixels[:,:,3]>.8]
        middle = max(.02, float(np.quantile(valid, .6)))
        detail = np.clip(lum / middle, .16, 2.5)
        pixels[:,:,:3] = np.minimum(1, detail[:,:,None] * np.array(dye))
    result = bpy.data.images.new(identity+'_'+part+'_Library', width=im.size[0], height=im.size[1], alpha=True)
    result.pixels.foreach_set(pixels.ravel())
    dest = SOURCE / 'textures' / identity / (part+'.png')
    dest.parent.mkdir(parents=True, exist_ok=True)
    result.filepath_raw = str(dest); result.file_format='PNG';result.save()
    result.filepath = '//' + os.path.relpath(dest,SOURCE).replace('\\','/')
    mat = bpy.data.materials.get(identity+'_'+part) or bpy.data.materials.new(identity+'_'+part)
    mat.use_nodes=True;mat.node_tree.nodes.clear()
    out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=result
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    mat.node_tree.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    roughness=.88 if part=='haircards' else .90
    bsdf.inputs['Roughness'].default_value=roughness
    bsdf.inputs['Specular IOR Level'].default_value=.08 if part=='haircards' else .15
    if alpha:
        mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
        mat.surface_render_method='DITHERED';mat.use_backface_culling=False
    mat['roughness']=roughness;mat['metallic']=0.0;mat['library_source']=str(source.relative_to(LIBRARY))
    return mat


def remove_vertices(obj, condition):
    bm=bmesh.new();bm.from_mesh(obj.data)
    vertices=[v for v in bm.verts if condition(v.co)]
    bmesh.ops.delete(bm,geom=vertices,context='VERTS');bm.to_mesh(obj.data);bm.free()


def upgrade(identity, draft=False):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/(identity+'.blend')))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig.data.pose_position='REST';bpy.context.view_layer.update()
    old_objects=set(bpy.data.objects);old_actions=set(bpy.data.actions)
    profile=PRESETS[identity]
    with bpy.data.libraries.load(str(ROOT/'source-art/characters'/(profile['base']+'.blend'))) as (available,loaded):
        loaded.objects=[n for n in available.objects if n.endswith('_body')]
    full=loaded.objects[0];bpy.context.collection.objects.link(full)
    full.parent=None;full.matrix_world=Matrix.Identity(4);full.modifiers.clear();TargetService.bake_targets(full)
    manifest=json.loads((OUT/identity/'manifest.json').read_text())
    for name in ['hair_surface','haircards_surface','libraryhair_surface','libraryboots_surface']:
        old=bpy.data.objects.get(identity+'_'+name)
        if old:bpy.data.objects.remove(old,do_unlink=True)
    hairname=HAIR[identity];folder=LIBRARY/'hair'/hairname
    hair=HumanService.add_mhclo_asset(str(folder/(hairname+'.mhclo')),full,asset_type='Hair',subdiv_levels=0,material_type='GAMEENGINE',set_up_rigging=False)
    # Keep the original artist's curl sheets and UVs; the hero has a shorter cut.
    head=rig.data.bones['head'].head_local
    if identity=='raphael' and hairname=='o4saken_curly01':
        # Cut the library's shoulder-length groom at ear height, rather than
        # compressing long curls into flat horizontal clumps.
        remove_vertices(hair,lambda co:co.z<head.z-.035 or (abs(co.x)>.14 and co.z<head.z+.065) or (co.y<-.135 and co.z<head.z+.065))
    elif identity=='mira':
        pass
    if identity=='raphael' and hairname.startswith('elvs_'):
        for v in hair.data.vertices:
            v.co.z=head.z+.17+(v.co.z-head.z-.17)*.72
            v.co.x*=.93
    bind(hair,rig,identity+'_haircards_surface')
    text=next(folder.glob('*.mhmat')).read_text()
    texture=folder/re.search(r'^diffuseTexture\s+(.+)$',text,re.M).group(1).strip()
    dye=manifest['profile']['haircolor']
    if identity=='captain':dye=[.19,.095,.035]
    hair.data.materials.clear();hair.data.materials.append(library_material(identity,'haircards',texture,dye,alpha=True))
    if hairname.startswith('elvs_'):
        bpy.context.view_layer.objects.active=hair
        modifier=hair.modifiers.new('LibrarySurfaceSmoothing','SUBSURF');modifier.levels=2
        bpy.ops.object.modifier_move_up(modifier=modifier.name)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    # A sculpted, UV-authored boot replaces the old seamless tube shin/foot.
    bootname='rehmanpolanski_viking_boots';bf=LIBRARY/'clothes'/bootname
    boots=HumanService.add_mhclo_asset(str(bf/(bootname+'.mhclo')),full,asset_type='Clothes',subdiv_levels=0,material_type='GAMEENGINE',set_up_rigging=False)
    bind(boots,rig,identity+'_libraryboots_surface',full)
    for obj in list(rig.children_recursive):
        if obj.type!='MESH' or obj==boots:continue
        if obj.name=='shoes03' or ('belt_surface' in obj.name):
            # Boots were merged into the dark leather material in the old pass.
            if obj.name=='shoes03':bpy.data.objects.remove(obj,do_unlink=True)
            else:remove_vertices(obj,lambda co:co.z<.53)
    boots.data.materials.clear();boots.data.materials.append(library_material(identity,'boots',bf/'BootsViking.png',(.10,.060,.032)))
    keep={hair,boots}
    garment=None
    if identity in ['raphael','nightqi','captain','raider-archer']:
        for obj in list(rig.children_recursive):
            if obj.name.startswith('ContinuousTealCowl'):
                bpy.data.objects.remove(obj,do_unlink=True)
        garment_name='donitz_monk_robe_hood_off';gf=LIBRARY/'clothes'/garment_name
        garment=HumanService.add_mhclo_asset(str(gf/(garment_name+'.mhclo')),full,asset_type='Clothes',subdiv_levels=0,material_type='GAMEENGINE',set_up_rigging=False)
        bind(garment,rig,identity+'_librarycowl_surface',full)
        gt=next(gf.glob('*.mhmat')).read_text();diffuse=gf/re.search(r'^diffuseTexture\s+(.+)$',gt,re.M).group(1).strip()
        garment.data.materials.clear();garment.data.materials.append(library_material(identity,'cowl',diffuse,manifest['profile']['cape']))
        keep.add(garment)
    equipped=[]
    family=manifest['profile']['weapon']
    kind='sword' if family in ['sword','shield'] else ('bow' if family=='bow' else None)
    if kind:
        side='l' if kind=='bow' else 'r';bone='hand_'+side
        rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['idle'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        pb=rig.pose.bones[bone];inverse=(pb.matrix@pb.bone.matrix_local.inverted()).inverted();palm=pb.head.copy()
        for obj in list(rig.children_recursive):
            if obj.name.startswith('Equipped_') and obj.name.endswith('_'+side):bpy.data.objects.remove(obj,do_unlink=True)
        library=ROOT/'src/.tmp/character-fidelity/weapons/weapons.blend'
        with bpy.data.libraries.load(str(library)) as (available,loaded):loaded.objects=['Library_'+kind]
        gear=loaded.objects[0];bpy.context.collection.objects.link(gear)
        bind(gear,rig,'Equipped_'+family+'_'+side)
        gear.vertex_groups.clear();group=gear.vertex_groups.new(name=bone);group.add(range(len(gear.data.vertices)),1,'REPLACE')
        for v in gear.data.vertices:v.co=inverse@(palm+v.co)
        material=gear.data.materials[0].copy();material.name=identity+'_weapon_'+('steel' if kind=='sword' else kind)
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                dest=SOURCE/'textures'/identity/('gear-'+kind+'.png')
                shutil.copy2(ROOT/'src/.tmp/character-fidelity/weapons/textures'/('library-'+kind+'.png'),dest)
                node.image=bpy.data.images.load(str(dest));node.image.filepath='//'+os.path.relpath(dest,SOURCE).replace('\\','/')
        gear.data.materials.clear();gear.data.materials.append(material);keep.add(gear);equipped.append(kind)
        rig.data.pose_position='REST'
    for obj in set(bpy.data.objects)-old_objects-keep:
        bpy.data.objects.remove(obj,do_unlink=True)
    for action in set(bpy.data.actions)-old_actions:bpy.data.actions.remove(action)
    rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['idle'];bpy.context.scene.frame_set(1)
    manifest['libraryFidelity']={'version':'library-fidelity-1','hair':{'asset':hairname,'license':'CC-BY' if hairname.startswith(('elvs_','culturalibre_hair_17')) else 'CC0-1.0'},'boots':{'asset':bootname,'license':'CC0-1.0'},'removedVolumeLocks':True,'collar':{'asset':'donitz_monk_robe_hood_off','license':'CC0-1.0'} if garment else None,'embeddedWeaponsReplaced':equipped}
    manifest['materials']=[{'name':m.name,'roughness':m.get('roughness',.8),'metallic':m.get('metallic',0)} for m in sorted({m for o in rig.children_recursive if o.type=='MESH' for m in o.data.materials if m},key=lambda m:m.name)]
    for texture in ['boots']+(['cowl'] if garment else []):
        if 'textures/'+texture+'.png' not in manifest['textures']:manifest['textures'].append('textures/'+texture+'.png')
    destination=ROOT/'src/.tmp/character-fidelity'/('draft-'+identity+'.blend') if draft else SOURCE/(identity+'.blend')
    if not draft:(OUT/identity/'manifest.json').write_text(json.dumps(manifest,indent=2))
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),relative_remap=False)
    print('[LIBRARY_FIDELITY]',identity,len(hair.data.vertices),len(boots.data.vertices),destination,flush=True)


if __name__=='__main__':
    selected=sys.argv[sys.argv.index('--character')+1].split(',') if '--character' in sys.argv else list(HAIR)
    if '--hair' in sys.argv:
        for identity in selected:HAIR[identity]=sys.argv[sys.argv.index('--hair')+1]
    for identity in selected:upgrade(identity,'--draft' in sys.argv)
