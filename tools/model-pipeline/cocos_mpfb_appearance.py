"""Fit CC0 MPFB face targets and system hair assets onto the existing v5 rigs.

Blender 4.5: --background --factory-startup --python this.py -- [--character ID]
Run after cocos_refine_sources.py, before cocos_optimize_exports.py.
Original files in source-art/characters/*.blend are only read, never saved.
"""
from pathlib import Path
import bpy, bmesh, sys, json, os, hashlib, re
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_bootstrap import ROOT, HumanService, TargetService
import mpfb

SOURCE = ROOT / 'source-art/characters/cocos'
OUT = ROOT / 'src/cocos/assets/resources/actors'
PACK = ROOT / 'src/.tools/makehuman-assets'
PRESETS = json.loads(Path(__file__).with_name('mpfb-appearance-presets.json').read_text())
VERSION = 'mpfb-appearance-1'


def coords(mesh):
    result = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', result.ravel())
    return result


def action_digest(rig):
    data = []
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        curves = [(c.data_path, c.array_index, [(tuple(k.co), k.interpolation) for k in c.keyframe_points]) for c in action.fcurves]
        data.append((action.name, list(action.frame_range), curves))
    return hashlib.sha256(repr(data).encode()).hexdigest()


def image_material(identity, part, source, color=(1, 1, 1), alpha=False, crop=None):
    """Recolor upstream pixels; no generated replacement of the asset's detail."""
    image = bpy.data.images.load(str(source), check_existing=False)
    width, height = image.size
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
    if crop:
        x0, y0, x1, y1 = crop
        pixels = pixels[int(y0*height):int(y1*height), int(x0*width):int(x1*width)].copy()
        height, width = pixels.shape[:2]
    if part in ['hair', 'haircards']:
        lum = np.sum(pixels[:, :, :3] * [0.2126, 0.7152, 0.0722], axis=2)
        # Preserve the source strand contrast while matching the established dye.
        middle = max(.01, float(np.quantile(lum[pixels[:, :, 3] > .8], .6)))
        detail = np.clip(lum / middle, .28, 1.8)
        pixels[:, :, :3] = detail[:, :, None] * np.asarray(color)
    else:
        pixels[:, :, :3] *= np.asarray(color)
    if part == 'hair':
        pixels[:, :, 3] = 1
    if part == 'lashes':
        # The system lash silhouette is designed for a much larger portrait;
        # retain its strands with a softer density at our game camera scale.
        pixels[:, :, 3] *= .55
    result = bpy.data.images.new(identity+'_'+part+'_MPFB', width=width, height=height, alpha=True)
    result.pixels.foreach_set(pixels.ravel())
    destination = SOURCE / 'textures' / identity / (part+'.png')
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.filepath_raw = str(destination); result.file_format = 'PNG'; result.save()
    result.filepath = '//' + os.path.relpath(destination, SOURCE).replace('\\', '/')
    material = bpy.data.materials.get(identity+'_'+part) or bpy.data.materials.new(identity+'_'+part)
    material.use_nodes = True
    material.node_tree.nodes.clear()
    output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    tex = material.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = result
    material.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .77 if part == 'skin' else .88
    bsdf.inputs['Specular IOR Level'].default_value = .25 if part == 'skin' else .06
    if alpha:
        material.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        material.surface_render_method = 'DITHERED'; material.use_backface_culling = False
    material.diffuse_color = (*color, 1)
    material['mpfb_source'] = str(source.relative_to(PACK))
    material['roughness'] = float(bsdf.inputs['Roughness'].default_value)
    material['metallic'] = 0.0
    return material


def connect_components(obj):
    adjacent = [[] for _ in obj.data.vertices]
    for edge in obj.data.edges:
        a,b = edge.vertices; adjacent[a].append(b); adjacent[b].append(a)
    seen = set()
    for vertex in obj.data.vertices:
        if vertex.index in seen: continue
        stack = [vertex.index]; result = []
        while stack:
            index = stack.pop()
            if index in seen: continue
            seen.add(index); result.append(index); stack.extend(adjacent[index])
        yield result


def refine_locks(hair):
    """Retain authored curls/waves; replace only the smooth ellipsoid scalp."""
    if not hair.get('mpfb_locks_refined'):
        scalp = [i for part in connect_components(hair) if len(part) == 1408 for i in part]
        if scalp:
            bm = bmesh.new(); bm.from_mesh(hair.data); bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in scalp], context='VERTS')
            bm.to_mesh(hair.data); bm.free()
        # Thinner lock cross sections expose the fitted hair underneath and
        # remove the former oversized rubber-tube highlights.
        hair.data.update()
        for vertex in hair.data.vertices:
            vertex.co -= vertex.normal * .0032
        hair['mpfb_locks_refined'] = True
    # Curve-converted tubes have a native longitudinal UV; the cropped system
    # bob texture provides real strands in place of the previous solid tint.


def bind_head(asset, rig, name):
    asset.parent = rig; asset.matrix_parent_inverse = Matrix.Identity(4)
    asset.matrix_basis = Matrix.Identity(4)
    asset.vertex_groups.clear(); group = asset.vertex_groups.new(name='head')
    group.add(range(len(asset.data.vertices)), 1, 'REPLACE')
    asset.modifiers.clear(); modifier = asset.modifiers.new('Skin', 'ARMATURE'); modifier.object = rig
    asset.name = name
    for polygon in asset.data.polygons: polygon.use_smooth = True


def upgrade(identity):
    profile = PRESETS[identity]
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE / (identity+'.blend')))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    bones = [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]
    actions_before = action_digest(rig); action_set = set(bpy.data.actions)
    old_objects = set(bpy.data.objects)
    with bpy.data.libraries.load(str(ROOT / 'source-art/characters' / (profile['base']+'.blend'))) as (available, loaded):
        loaded.objects = [name for name in available.objects if name.endswith('_body')]
    full = loaded.objects[0]; bpy.context.collection.objects.link(full)
    full.parent = None; full.matrix_world = Matrix.Identity(4); full.modifiers.clear()
    TargetService.bake_targets(full)
    before = coords(full.data)
    targets = [{'target': name, 'value': weight} for name, weight in profile['targets'].items()]
    for target in targets:
        assert TargetService.target_full_path(target['target']), target
    TargetService.bulk_load_targets(full, targets)
    mixed = full.shape_key_add(name='MPFB_final_mix', from_mix=True)
    after = np.asarray([tuple(v.co) for v in mixed.data], dtype=np.float32)
    full.shape_key_remove(mixed)
    delta = after-before
    skin = bpy.data.objects[identity+'_skin_surface']
    if skin.data.shape_keys and 'MPFB_face_refinement' in skin.data.shape_keys.key_blocks:
        skin.shape_key_remove(skin.data.shape_keys.key_blocks['MPFB_face_refinement'])
    tree = KDTree(len(before))
    for i, point in enumerate(before): tree.insert(point, i)
    tree.balance()
    if not skin.data.shape_keys: skin.shape_key_add(name='Basis')
    key = skin.shape_key_add(name='MPFB_face_refinement'); key.value = 1
    changed = 0; maximum = 0
    for vertex, output in zip(skin.data.vertices, key.data):
        _, index, distance = tree.find(vertex.co)
        # Current skin is the same frozen hm08 mesh with hidden torso vertices
        # removed. Facial expression edits cause up to 4mm correspondence drift.
        assert distance < .006, (identity, vertex.index, distance)
        output.co = vertex.co + Vector(delta[index])
        length = float(np.linalg.norm(delta[index])); changed += length > 1e-6; maximum = max(maximum, length)
    skin['mpfb_targets'] = json.dumps(profile['targets'], sort_keys=True)
    manifest_file = OUT / identity / 'manifest.json'
    manifest = json.loads(manifest_file.read_text()); dye = manifest['profile']['haircolor']
    hair = bpy.data.objects[identity+'_hair_surface']; refine_locks(hair)
    strand_source = PACK / 'hair/bob02/bob02_diffuse.png'
    hair.data.materials.clear()
    hair.data.materials.append(image_material(identity, 'hair', strand_source, dye, crop=(.1,.3,.25,.6)))
    for suffix in ['haircards_surface', 'lashes_surface']:
        obj = bpy.data.objects.get(identity+'_'+suffix)
        if obj: bpy.data.objects.remove(obj, do_unlink=True)
    hair_asset = profile['hair']
    cards = HumanService.add_mhclo_asset(str(PACK/'hair'/hair_asset/(hair_asset+'.mhclo')), full,
        asset_type='Hair', subdiv_levels=0, material_type='GAMEENGINE', set_up_rigging=False)
    front_opening_faces = 0
    if hair_asset == 'bob02':
        # The library bob's long fringe covers one eye. The v5 bob/half-up
        # hairstyles expose the face; keep the mature back/temple topology and
        # trim its fringe underneath the existing swept crown waves.
        bm=bmesh.new();bm.from_mesh(cards.data)
        forehead=rig.data.bones['head'].head_local.z+.10
        fringe=[f for f in bm.faces if (lambda c:c.y<-.085 and abs(c.x)<.10 and c.z<forehead)(f.calc_center_median())]
        front_opening_faces=len(fringe)
        bmesh.ops.delete(bm,geom=fringe,context='FACES')
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
        bm.to_mesh(cards.data);bm.free()
    bind_head(cards, rig, identity+'_haircards_surface')
    cards.data.materials.clear()
    cards.data.materials.append(image_material(identity, 'haircards', PACK/'hair'/hair_asset/(hair_asset+'_diffuse.png'), dye, alpha=True))
    lashes = HumanService.add_mhclo_asset(str(PACK/'eyelashes/eyelashes01/eyelashes01.mhclo'), full,
        asset_type='Eyelashes', subdiv_levels=0, material_type='GAMEENGINE', set_up_rigging=False)
    bind_head(lashes, rig, identity+'_lashes_surface')
    lashes.data.materials.clear()
    lashes.data.materials.append(image_material(identity, 'lashes', PACK/'eyelashes/eyelashes01/eyelashes01.png', (.18,.12,.08), alpha=True))
    skin_folder = PACK/'skins'/profile['skin']
    text = (skin_folder/(profile['skin']+'.mhmat')).read_text()
    skin_png = skin_folder/re.search(r'^diffuseTexture\s+(.+)$', text, re.M).group(1).strip()
    skin.data.materials.clear()
    skin.data.materials.append(image_material(identity, 'skin', skin_png, (.96,.91,.86)))
    # Remove the temporary full-resolution body and dependencies it brought in.
    for obj in set(bpy.data.objects)-old_objects-{cards,lashes}:
        bpy.data.objects.remove(obj, do_unlink=True)
    for action in set(bpy.data.actions)-action_set: bpy.data.actions.remove(action)
    assert action_digest(rig) == actions_before, 'Animation curves changed'
    assert bones == [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones], 'Skeleton changed'
    rig.data.pose_position = 'POSE'; rig.animation_data.action = bpy.data.actions['idle']
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    report = {'version': VERSION, 'mpfbVersion': '.'.join(map(str,mpfb.VERSION)), 'targets': profile['targets'],
        'changedSkinVertices': changed, 'maximumTargetDisplacementMeters': maximum,
        'hairAsset': 'hair/'+hair_asset, 'hairCardVertices': len(cards.data.vertices),
        'hairFrontOpeningFacesRemoved':front_opening_faces,
        'eyelashesAsset':'eyelashes/eyelashes01','skinAsset':'skins/'+profile['skin'],
        'skeletonPreserved':True, 'boneCount':len(bones), 'animationCurvesPreserved':True,
        'animationCurvesSha256':actions_before, 'assetLicense':'CC0-1.0',
        'toolLicense':'GPL-3.0-or-later', 'upstream':'https://github.com/makehumancommunity/mpfb2/tree/v2.0.18'}
    manifest['mpfbAppearance'] = report
    current_materials={m for o in rig.children_recursive if o.type=='MESH' for m in o.data.materials if m}
    manifest['materials']=[{'name':m.name,'roughness':m.get('roughness',.8),'metallic':m.get('metallic',0)} for m in sorted(current_materials,key=lambda m:m.name)]
    for part in ['haircards','lashes']:
        relative = 'textures/'+part+'.png'
        if relative not in manifest['textures']: manifest['textures'].append(relative)
    manifest_file.write_text(json.dumps(manifest, indent=2))
    rig['mpfb_appearance'] = json.dumps(report)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(identity+'.blend')), relative_remap=False)
    print('[MPFB_APPEARANCE]', identity, json.dumps(report), flush=True)
    return report


selected = sys.argv[sys.argv.index('--character')+1] if '--character' in sys.argv else None
reports = {identity:upgrade(identity) for identity in (selected.split(',') if selected else PRESETS)}
destination = SOURCE/'mpfb-appearance-report.json'
prior = json.loads(destination.read_text()) if destination.exists() else {}
prior.update(reports); destination.write_text(json.dumps(prior, indent=2))
