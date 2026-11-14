"""Adapt library hair and sculpt the existing Native65 faces for the v5 cast.

Public integration entry: apply(identity, rig, manifest) -> JSON-ready record.
The loaded native rig/rest/weights/actions are retained. No production asset is
written here. The optional CLI only renders head probes into the temporary stage.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[2]
COMMUNITY = ROOT / 'src/.tools/makehuman-community'
SYSTEM = ROOT / 'src/.tools/makehuman-assets'
PROBES = ROOT / 'src/.tmp/character-redesign-v6/face-probes'
IDS = ['raphael', 'mira', 'lorn', 'nightqi', 'kael', 'evelyn',
       'captain', 'raider', 'raider-shield', 'raider-archer']

# Dimensions are rest-space metres, before the already authored actor scale.
# They adapt the artist's complete low-poly silhouettes, not generated strands.
STYLE = {
    'raphael': dict(asset='elvs_wavy_bob', size=(.209, .214, .171),
                    offset=(0, .012, .027), tint=(.021, .008, .003),
                    cheek=.0026, jaw=-.0012, chin=.0012, nose=.0015,
                    smile=.0036, brow=.0018, asym=.0011, crop='short'),
    'mira': dict(asset='elvs_wavy_bob', size=(.252, .242, .247),
                 offset=(.006, .012, .035), tint=(.68, .39, .13),
                 cheek=.0034, jaw=-.0005, chin=.0005, nose=-.0010,
                 smile=.0044, brow=.0030, asym=.0016, crop='bob'),
    'lorn': dict(asset='culturalibre_hair_05', size=(.192, .208, .133),
                 offset=(0, .014, .025), tint=(.025, .019, .015),
                 cheek=.0024, jaw=.0042, chin=.0021, nose=.0025,
                 smile=.0005, brow=-.0010, asym=.0004, crop='short'),
    'nightqi': dict(asset='ponytail01', size=(.196, .232, .425),
                    offset=(0, .035, .040), tint=(.54, .29, .075),
                    cheek=.0025, jaw=.0003, chin=.0011, nose=.0009,
                    smile=.0011, brow=.0020, asym=-.0007, crop='ponytail'),
    'kael': dict(asset='short02', size=(.192, .211, .158),
                 offset=(0, .013, .025), tint=(.20, .073, .025),
                 cheek=.0032, jaw=-.0015, chin=-.0012, nose=-.0010,
                 smile=.0015, brow=.0013, asym=.0006, crop='short'),
    'evelyn': dict(asset='elvs_keylth_hair', size=(.232, .253, .380),
                   offset=(.002, .032, .030), tint=(.72, .49, .22),
                   cheek=.0022, jaw=.0014, chin=.0014, nose=.0015,
                   smile=.0004, brow=-.0004, asym=.0005, crop='halfup'),
    'captain': dict(asset='culturalibre_hair_05', size=(.196, .216, .138),
                    offset=(0, .016, .024), tint=(.075, .039, .020),
                    cheek=.0018, jaw=.0048, chin=.0028, nose=.0020,
                    smile=-.0010, brow=-.0018, asym=.0010, crop='short'),
    'raider': dict(asset='short04', size=(.189, .203, .134),
                   offset=(0, .013, .022), tint=(.045, .026, .017),
                   cheek=.0012, jaw=.0026, chin=.0010, nose=.0030,
                   smile=-.0012, brow=-.0020, asym=-.0012, crop='short'),
    'raider-shield': dict(asset='culturalibre_hair_05', size=(.202, .214, .142),
                          offset=(0, .016, .027), tint=(.038, .024, .015),
                          cheek=.0020, jaw=.0052, chin=.0030, nose=.0015,
                          smile=-.0005, brow=-.0012, asym=-.0006, crop='short'),
    'raider-archer': dict(asset='short03', size=(.183, .200, .135),
                          offset=(0, .017, .019), tint=(.090, .040, .018),
                          cheek=.0010, jaw=-.0012, chin=.0018, nose=.0025,
                          smile=.0003, brow=.0014, asym=.0010, crop='short'),
}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _bounds(obj):
    points = [v.co for v in obj.data.vertices]
    return ([min(v[i] for v in points) for i in range(3)],
            [max(v[i] for v in points) for i in range(3)])


def _rest_digest(rig):
    return hashlib.sha256(repr([(b.name, b.parent.name if b.parent else None,
                                tuple(tuple(row) for row in b.matrix_local), b.use_deform)
                               for b in rig.data.bones]).encode()).hexdigest()


def _weights_digest(obj):
    return hashlib.sha256(repr([(v.index, [(obj.vertex_groups[g.group].name, g.weight)
                                          for g in v.groups])
                               for v in obj.data.vertices]).encode()).hexdigest()


def _action_digest():
    values = []
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        values.append((action.name, [(fc.data_path, fc.array_index,
                                     [(tuple(k.co), k.interpolation) for k in fc.keyframe_points])
                                    for fc in action.fcurves]))
    return hashlib.sha256(repr(values).encode()).hexdigest()


def _body_digest():
    objects=sorted((o for o in bpy.data.objects if o.type=='MESH' and o.get('nativePart') not in ['head','eyes','brows','lashes','hair']),key=lambda o:o.name)
    data=[(o.name,tuple(tuple(row)for row in o.matrix_world),
           [(tuple(v.co),[(g.group,g.weight)for g in v.groups])for v in o.data.vertices],
           [m.name if m else None for m in o.data.materials])for o in objects]
    return hashlib.sha256(repr(data).encode()).hexdigest()


def _asset(name):
    if (SYSTEM / 'hair' / name).is_dir():
        folder = SYSTEM / 'hair' / name
        metadata = json.loads((SYSTEM / 'packs/makehuman_system_assets.json').read_text())[name]
        metadata['pack'] = 'makehuman_system_assets'
    else:
        folder = COMMUNITY / 'hair' / name
        metadata = None
        for pack in sorted((COMMUNITY / 'packs').glob('hair*.json')):
            data = json.loads(pack.read_text())
            if name in data:
                metadata = dict(data[name], pack=pack.stem)
                break
        if metadata is None:
            raise RuntimeError('Missing verified upstream metadata: ' + name)
    mhclo = folder / (name + '.mhclo')
    text = mhclo.read_text(encoding='utf8', errors='replace')
    obj_name = re.search(r'^obj_file\s+(.+)$', text, re.M).group(1).strip()
    material_name = re.search(r'^material\s+(.+)$', text, re.M).group(1).strip()
    material_path = folder / material_name
    material_text = material_path.read_text(encoding='utf8', errors='replace')
    diffuse = re.search(r'^diffuseTexture\s+(.+)$', material_text, re.M).group(1).strip()
    normal = re.search(r'^normalmapTexture\s+(.+)$', material_text, re.M)
    alpha = bool(re.search(r'^transparent\s+True', material_text, re.M))
    metadata.update(asset=name, folder=str(folder.relative_to(ROOT)).replace('\\', '/'),
                    obj=str((folder / obj_name).relative_to(ROOT)).replace('\\', '/'),
                    texture=str((folder / diffuse).relative_to(ROOT)).replace('\\', '/'),
                    alpha=alpha, objSHA256=_sha(folder / obj_name),
                    textureSHA256=_sha(folder / diffuse),
                    mhcloSHA256=_sha(mhclo), materialSHA256=_sha(material_path))
    metadata['normal'] = str((folder / normal.group(1).strip()).relative_to(ROOT)).replace('\\', '/') if normal else None
    return metadata


def _hair_material(identity, suffix, meta, tint):
    material = bpy.data.materials.new(identity + '_V6_Hair_' + suffix)
    material.use_nodes = True
    material.use_backface_culling = False
    material['v6MaterialRole'] = 'hair'
    material['v6AlbedoPath'] = meta['texture']
    material['v6AlphaMode'] = 'BLEND' if meta['alpha'] else 'OPAQUE'
    material['v6AlphaSource'] = meta['texture'] + ':A' if meta['alpha'] else 'constant 1'
    material['v6Tint'] = list(tint)
    material['v6Roughness'] = .78
    material['v6Metallic'] = 0.0
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    bsdf.inputs['Roughness'].default_value = .78
    bsdf.inputs['Specular IOR Level'].default_value = .20
    texture = nodes.new('ShaderNodeTexImage')
    texture.name = 'V6_SourceAlbedo'
    texture.image = bpy.data.images.load(str(ROOT / meta['texture']), check_existing=False)
    texture.image.name = identity + '_V6_' + suffix + '_SourceAlbedo'
    texture.image.colorspace_settings.name = 'sRGB'
    meta['textureSize'] = list(texture.image.size)
    # Preserve the source's strand detail while permitting dark source hair to
    # become blonde. This is a Blender shader adaptation, not a replacement map.
    grey = nodes.new('ShaderNodeRGBToBW')
    links.new(texture.outputs['Color'], grey.inputs['Color'])
    detail = nodes.new('ShaderNodeMapRange')
    detail.inputs['From Min'].default_value = 0
    detail.inputs['From Max'].default_value = .080 if meta['asset'] == 'elvs_wavy_bob' else .30
    detail.inputs['To Min'].default_value = .48
    detail.inputs['To Max'].default_value = 1.28
    detail.clamp = True
    links.new(grey.outputs[0], detail.inputs['Value'])
    dye = nodes.new('ShaderNodeMixRGB')
    dye.blend_type = 'MULTIPLY'
    dye.inputs[0].default_value = 1
    dye.inputs[2].default_value = (*tint, 1)
    links.new(detail.outputs[0], dye.inputs[1])
    links.new(dye.outputs[0], bsdf.inputs['Base Color'])
    if meta['alpha']:
        links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
        material.surface_render_method = 'DITHERED'
    if meta.get('normal') and 'objnorm' not in meta['normal'].lower():
        normaltex = nodes.new('ShaderNodeTexImage')
        normaltex.image = bpy.data.images.load(str(ROOT / meta['normal']), check_existing=False)
        normaltex.image.name = identity + '_V6_' + suffix + '_SourceNormal'
        normaltex.image.colorspace_settings.name = 'Non-Color'
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = .45
        links.new(normaltex.outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    return material


def _import_hair(meta):
    previous = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(ROOT / meta['obj']),
                          forward_axis='NEGATIVE_Z', up_axis='Y',
                          use_split_objects=False, use_split_groups=False)
    objects = [o for o in set(bpy.data.objects) - previous if o.type == 'MESH']
    assert len(objects) == 1, (meta['asset'], [o.name for o in objects])
    obj = objects[0]
    matrix = obj.matrix_world.copy()
    for vertex in obj.data.vertices:
        vertex.co = matrix @ vertex.co
    obj.matrix_world = Matrix.Identity(4)
    obj.modifiers.clear()
    obj.vertex_groups.clear()
    if meta['asset'] == 'elvs_wavy_bob':
        # This upstream OBJ contains coincident front/back duplicates. Blender's
        # native weld removes those surfaces before smooth subdivision, avoiding
        # the dark coincident edges seen in the first real render probe.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        bpy.context.view_layer.objects.active = obj
        refine = obj.modifiers.new('V6_LibraryCurlRefinement', 'SUBSURF')
        refine.levels = 1
        bpy.ops.object.modifier_apply(modifier=refine.name)
        triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        budget=meta.get('detailBudget',6200)
        if triangles > budget:
            compact = obj.modifiers.new('V6_MobileCurlBudget', 'DECIMATE')
            compact.ratio = budget / triangles
            compact.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=compact.name)
    return obj


def _fit(obj, size, center, top):
    low, high = _bounds(obj)
    for vertex in obj.data.vertices:
        co = vertex.co.copy()
        vertex.co.x = (co.x - (low[0] + high[0]) * .5) / (high[0] - low[0]) * size[0] + center[0]
        vertex.co.y = (co.y - (low[1] + high[1]) * .5) / (high[1] - low[1]) * size[1] + center[1]
        vertex.co.z = (co.z - high[2]) / (high[2] - low[2]) * size[2] + top


def _bind(obj, identity, suffix, rig, material):
    obj.name = identity + '_native_hair_v6_' + suffix
    obj['nativePart'] = 'hair'
    obj['defaultVisible'] = True
    obj['v6MaterialRole'] = 'hair'
    obj.hide_render = False
    obj.hide_set(False)
    obj.parent = rig
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    group = obj.vertex_groups.new(name='Head')
    group.add(range(len(obj.data.vertices)), 1, 'REPLACE')
    armature = obj.modifiers.new('Native65_HeadBinding', 'ARMATURE')
    armature.object = rig
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def _smooth_region(x, y, z, center, radius):
    return math.exp(-sum(((a - b) / r) ** 2 for a, b, r in zip((x, y, z), center, radius)) * 2)


def _sculpt_face(identity, head, eyes, brows, style):
    eye_z = sum(v.co.z for v in eyes.data.vertices) / len(eyes.data.vertices)
    before = [v.co.copy() for v in head.data.vertices]
    weights = _weights_digest(head)
    for v in head.data.vertices:
        x, y, z = v.co
        if y > .025 or z < eye_z - .133:
            continue
        side = 1 if x >= 0 else -1
        cheek = _smooth_region(x, y, z, (side * .045, -.065, eye_z - .037), (.033, .070, .037))
        jaw = _smooth_region(x, y, z, (side * .046, -.035, eye_z - .082), (.039, .080, .037))
        chin = _smooth_region(x, y, z, (0, -.061, eye_z - .102), (.030, .065, .027))
        nose = _smooth_region(x, y, z, (0, -.100, eye_z - .021), (.018, .042, .026))
        mouth = _smooth_region(x, y, z, (side * .023, -.080, eye_z - .067), (.017, .037, .017))
        brow = _smooth_region(x, y, z, (side * .036, -.068, eye_z + .017), (.028, .045, .016))
        v.co.x += side * (style['cheek'] * cheek + style['jaw'] * jaw + .25 * style['chin'] * chin)
        v.co.y -= style['cheek'] * cheek * .50 + style['chin'] * chin * .45 + style['nose'] * nose
        v.co.z += style['smile'] * mouth * (1 if side > 0 else .40) + style['brow'] * brow
        v.co.x += style['asym'] * mouth
        v.co.z += style['chin'] * chin * .25
    # Brows follow the authored brow lift while eyeballs and their original
    # skin weights remain untouched. No facial bones or target topology assumed.
    brow_centers = {side: sum(v.co.z for v in brows.data.vertices if (v.co.x >= 0) == (side > 0)) / sum(1 for v in brows.data.vertices if (v.co.x >= 0) == (side > 0)) for side in [-1, 1]}
    for vertex in brows.data.vertices:
        side = 1 if vertex.co.x >= 0 else -1
        center_z = brow_centers[side]
        brow_scale = 1.0 if head.get('v6NaturalHead') else (.60 if identity in ['mira', 'nightqi', 'evelyn'] else .76)
        vertex.co.z = center_z + (vertex.co.z - center_z) * brow_scale
        vertex.co.x = side * .036 + (vertex.co.x - side * .036) * .93
        vertex.co.z += style['brow'] * (.85 if side > 0 else .55)
        vertex.co.x += style['asym'] * .30
    head.data.update()
    brows.data.update()
    assert _weights_digest(head) == weights
    changed = [(v.co - old).length for v, old in zip(head.data.vertices, before)]
    return {'method': 'Local rest-space mesh editing of cheek, jaw, chin, nose, mouth corners and brow support; neck transition retained',
            'changedVertices': sum(d > 1e-6 for d in changed),
            'maximumDisplacementMetres': max(changed), 'headVertexCount': len(before),
            'eyeHeightRest': eye_z, 'weightsPreserved': True,
            'parameters': {k: style[k] for k in ['cheek', 'jaw', 'chin', 'nose', 'smile', 'brow', 'asym']}}


def _retint_brows(identity, brows, style):
    previous = brows.data.materials[0]
    textures = [n.image for n in previous.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    texture = next((im for im in textures if 'BaseColor' in im.name), textures[0])
    path = Path(bpy.path.abspath(texture.filepath)).resolve()
    meta = {'asset': 'NativeEyebrows', 'texture': str(path.relative_to(ROOT)).replace('\\', '/'),
            'alpha': bool(previous.get('v6AlphaSource')), 'normal': None}
    tint = tuple(c * (.25 if identity in ['mira', 'nightqi', 'evelyn'] else .45)
                 for c in style['tint'])
    material = _hair_material(identity, 'brows', meta, tint)
    material['v6MaterialRole'] = 'brows'
    brows.data.materials.clear()
    brows.data.materials.append(material)


def _stubble(head, eye_z, identity):
    if identity not in ['lorn', 'captain', 'raider-shield']:
        return None
    mesh = head.data
    mask = mesh.color_attributes.new(name='V6_StubbleMask', type='FLOAT_COLOR', domain='CORNER')
    for loop, item in zip(mesh.loops, mask.data):
        x, y, z = mesh.vertices[loop.vertex_index].co
        jaw = math.exp(-((z - (eye_z - .084)) / .036) ** 4)
        front = min(1, max(0, (-y - .015) / .040))
        lip_exclusion = 1 - .94 * _smooth_region(x, y, z, (0, -.083, eye_z - .066), (.034, .050, .015))
        value = jaw * front * lip_exclusion
        item.color = (value, value, value, 1)
    material = mesh.materials[0]
    material['v6FacialHair'] = 'Short dark stubble; Blender noise and vertex-mask shader, baked with head albedo'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    source = bsdf.inputs['Base Color'].links[0].from_socket
    attribute = nodes.new('ShaderNodeVertexColor')
    attribute.layer_name = mask.name
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 1100
    grain.inputs['Detail'].default_value = 1
    factor = nodes.new('ShaderNodeMath')
    factor.operation = 'MULTIPLY'
    links.new(attribute.outputs['Color'], factor.inputs[0])
    links.new(grain.outputs['Fac'], factor.inputs[1])
    dye = nodes.new('ShaderNodeMixRGB')
    dye.blend_type = 'MULTIPLY'
    dye.inputs[2].default_value = (.20, .155, .125, 1)
    links.new(factor.outputs[0], dye.inputs[0])
    links.new(source, dye.inputs[1])
    links.new(dye.outputs[0], bsdf.inputs['Base Color'])
    return {'type': 'short stubble', 'vertexMask': mask.name,
            'source': 'Original light skin albedo with Blender built-in noise modulation',
            'lightBakedIntoAlbedo': False}


def _natural_head(identity, rig):
    """Append mesh IDs only: the old 53-bone Armature is never loaded."""
    source = ROOT / 'source-art/characters/cocos' / (identity + '.blend')
    original_head = next(o for o in bpy.data.objects if o.get('nativePart') == 'head')
    original_eyes = next(o for o in bpy.data.objects if o.get('nativePart') == 'eyes')
    original_brows = next(o for o in bpy.data.objects if o.get('nativePart') == 'brows')
    target_low, target_high = _bounds(original_head)
    target_eye = sum((v.co for v in original_eyes.data.vertices), Vector()) / len(original_eyes.data.vertices)
    old_armatures = set(bpy.data.armatures)
    before_images = set(bpy.data.images)
    lash_mesh = 'eyelashes01' if identity in ['raphael', 'mira', 'evelyn'] else 'eyelashes01.001'
    names = {'head': 'base.001', 'eyes': 'high-poly', 'brows': 'eyebrow001', 'lashes': lash_mesh}
    with bpy.data.libraries.load(str(source), link=False) as (available, loaded):
        assert all(n in available.meshes for n in names.values()), (identity, names)
        loaded.meshes = list(names.values())
    assert set(bpy.data.armatures) == old_armatures, 'Old rig dependency was imported'
    for image in set(bpy.data.images) - before_images:
        if image.source == 'FILE' and image.filepath.startswith('//'):
            resolved=Path(bpy.path.abspath(image.filepath)).resolve()
            if not resolved.is_file():resolved=(source.parent/image.filepath[2:]).resolve()
            assert resolved.is_file(),(identity,resolved)
            image.filepath = str(resolved)
            image.reload()
    parts = {}
    for role, mesh in zip(names, loaded.meshes):
        obj = bpy.data.objects.new(identity + '_native_' + role + '_v6_natural', mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if mesh.shape_keys:
            bpy.context.view_layer.update()
            evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            obj.data=bpy.data.meshes.new_from_object(evaluated,depsgraph=bpy.context.evaluated_depsgraph_get())
        obj.vertex_groups.clear()
        obj.parent = rig; obj.matrix_parent_inverse = Matrix.Identity(4); obj.matrix_basis = Matrix.Identity(4)
        obj['nativePart'] = role; obj['defaultVisible'] = True
        parts[role] = obj
    head, eyes, brows = parts['head'], parts['eyes'], parts['brows']
    source_eye = sum((v.co for v in eyes.data.vertices), Vector()) / len(eyes.data.vertices)
    source_top = _bounds(head)[1][2]
    z_scale = (target_high[2] - target_eye.z) / (source_top - source_eye.z)
    for obj in parts.values():
        for vertex in obj.data.vertices:
            d = vertex.co - source_eye
            vertex.co = Vector((d.x * 1.045, d.y, d.z * z_scale)) + target_eye
    # Continuous original head AND neck keep one photo-skin UV atlas. A native
    # planar bisect and bottom cap lie inside the existing collar, eliminating
    # the cross-atlas bridge that the independent spike rejected visually.
    plane = target_low[2] - .006
    bm = bmesh.new(); bm.from_mesh(head.data)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                          plane_co=(0,0,plane), plane_no=(0,0,1), dist=1e-6,
                          clear_inner=True, clear_outer=False)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    edge_ring = [e for e in bm.edges if e.is_boundary and all(abs(v.co.z-plane)<1e-5 for v in e.verts)]
    assert edge_ring, (identity, 'Missing neck bottom ring')
    cap = bmesh.ops.holes_fill(bm, edges=edge_ring, sides=0)
    neck_open = sum(e.is_boundary and all(abs(v.co.z-plane)<1e-5 for v in e.verts) for e in bm.edges)
    assert neck_open == 0, (identity, 'Open neck bottom', neck_open)
    deform = bm.verts.layers.deform.active
    if deform:
        for vertex in bm.verts: vertex[deform].clear()
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(head.data); bm.free(); head.data.update()
    bpy.ops.object.select_all(action='DESELECT'); head.select_set(True)
    bpy.context.view_layer.objects.active = head
    for bone in rig.data.bones: head.vertex_groups.new(name=bone.name)
    dt = head.modifiers.new('V6_NativeWeightTransfer', 'DATA_TRANSFER')
    dt.object = original_head; dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    arm = head.modifiers.new('Native65_Armature', 'ARMATURE'); arm.object = rig
    for polygon in head.data.polygons: polygon.use_smooth = True
    influence_counts = [sum(g.weight>1e-6 for g in v.groups) for v in head.data.vertices]
    assert min(influence_counts)>0 and max(influence_counts)<=4
    # Directly use the licensed original photo skin, avoiding the old runtime's
    # tinted copies and avoiding the NativeSuperhero palette graph entirely.
    preset = json.loads((ROOT/'tools/model-pipeline/mpfb-appearance-presets.json').read_text())[identity]
    female = identity in ['mira','nightqi','evelyn']
    skin_name = ('young_caucasian_female2' if female else 'young_caucasian_male2') if identity in ['raphael','mira','lorn','nightqi','kael','evelyn','captain'] else preset['skin']
    folder = SYSTEM/'skins'/skin_name
    mhmat = (folder/(skin_name+'.mhmat')).read_text()
    diffuse = re.search(r'^diffuseTexture\s+(.+)$', mhmat, re.M).group(1).strip()
    skin_path = folder/diffuse
    material = head.data.materials[0]
    material.name = identity+'_V6_NaturalSkin'
    material['v6MaterialRole']='skin'; material['v6AlphaSource']='constant 1'; material['v6Roughness']=.72; material['v6Metallic']=0.0
    material['v6AlbedoPath']=str(skin_path.relative_to(ROOT)).replace('\\','/')
    texture = next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    texture.image=bpy.data.images.load(str(skin_path),check_existing=False)
    texture.image.name=identity+'_V6_PhotoSkin'; texture.image.colorspace_settings.name='sRGB'
    bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    material.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value=.72; bsdf.inputs['Metallic'].default_value=0
    for role in ['eyes','brows','lashes']:
        obj=parts[role]
        group=obj.vertex_groups.new(name='Head'); group.add(range(len(obj.data.vertices)),1,'REPLACE')
        arm=obj.modifiers.new('Native65_HeadBinding','ARMATURE'); arm.object=rig
        for m in obj.data.materials:
            m.name=identity+'_V6_Natural_'+role; m['v6MaterialRole']=role
            tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image)
            principal=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            if role=='eyes':
                eye_colour={'raphael':'grey','mira':'brownlight','lorn':'brown','nightqi':'green','kael':'brownlight','evelyn':'bluegreen'}.get(identity,'brown')
                eye_path=SYSTEM/'eyes/materials'/(eye_colour+'_eye.png')
                tex.image=bpy.data.images.load(str(eye_path),check_existing=False)
                tex.image.name=identity+'_V6_PhotoEyes';tex.image.colorspace_settings.name='sRGB'
            m.node_tree.links.new(tex.outputs['Alpha'],principal.inputs['Alpha'])
            m.surface_render_method='DITHERED';m.use_backface_culling=False
            m['v6AlphaMode']='IMAGE';m['v6AlphaSource']=tex.image.filepath+':A'
    for old in [original_head,original_eyes,original_brows]: bpy.data.objects.remove(old,do_unlink=True)
    head['v6NaturalHead']=True
    return head,eyes,brows,{'source':str(source.relative_to(ROOT)).replace('\\','/'),
          'sourceSHA256':_sha(source),'sourceMeshIDs':names,'oldArmatureImported':False,
          'photoSkin':str(skin_path.relative_to(ROOT)).replace('\\','/'),'photoSkinSHA256':_sha(skin_path),
          'assetLicense':'CC0-1.0','sourceFaceTargets':preset['targets'],'sourcePresetSkin':preset['skin'],
          'neckMethod':'Original continuous photo-UV head/neck; Blender native plane bisect and holes_fill bottom cap inside collar',
          'neckBottomPlaneRest':plane,'neckBottomOpenEdges':neck_open,'capFaces':len(cap['faces']),
          'maxDeformInfluences':max(influence_counts),'unweightedVertices':0,
          'weightTool':'Blender DataTransfer nearest-face-interpolated native65 weights; limit4 and normalize',
          'fitScale':[1.045,1,z_scale],'meshVertices':len(head.data.vertices),
          'meshTriangles':sum(len(p.vertices)-2 for p in head.data.polygons),
          'photoUVPreserved':True,'eyeCorneaImageAlphaRestored':True}


def _braid(identity, rig, top, style):
    meta = _asset('braid01')
    braid = _import_hair(meta)
    low, high = _bounds(braid)
    # Retain the author's woven tail only; exclude the supplied scalp cap.
    cutoff = high[2] - (high[2] - low[2]) * .39
    bm = bmesh.new()
    bm.from_mesh(braid.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > cutoff], context='VERTS')
    bm.to_mesh(braid.data)
    bm.free()
    _fit(braid, (.017, .021, .245), (.071, .025), top - .068)
    _bind(braid, identity, 'fine_braid', rig, _hair_material(identity, 'fine_braid', meta, style['tint']))
    return braid, meta


def _lower_waves(identity, rig, top, style):
    """Reuse only the bob artist's side/back curls below the half-up crown."""
    meta = _asset('elvs_wavy_bob')
    waves = _import_hair(meta)
    _fit(waves, (.244, .235, .380), (0, .050), top + .030)
    bm = bmesh.new()
    bm.from_mesh(waves.data)
    # No second scalp: remove the crown band and the central front, retaining
    # the source's curved side locks and lower nape curls as the long waves.
    remove = [v for v in bm.verts if v.co.z > top - .110 or
              (abs(v.co.x) < .073 and v.co.y < .035)]
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(waves.data)
    bm.free()
    for vertex in waves.data.vertices:
        tuck = min(1, max(0, (vertex.co.z - (top - .183)) / .073))
        vertex.co.x *= 1 - .36 * tuck
        vertex.co.y += .044 * tuck
    _bind(waves, identity, 'lower_waves', rig,
          _hair_material(identity, 'lower_waves', meta, style['tint']))
    return waves, meta


def _scalp_underlayer(identity, rig, head, style):
    """Reuse the fitted CC0 head surface beneath the artist's open hair locks.

    The shell has the exact skull shape and photo UVs. This is deliberately an
    opaque, low-detail root layer, so neither alpha cards nor open source locks
    can expose skin-coloured rectangles through the crown.
    """
    top = _bounds(head)[1][2]
    mesh = head.data.copy()
    bm = bmesh.new(); bm.from_mesh(mesh)
    # Bisect the original faces instead of deleting whole polygons: a vertex
    # cutoff leaves a conspicuous staircase across the forehead. The sloping
    # plane raises the front under the forelock and leaves roots at the nape.
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                          plane_co=(0,0,top-.070),plane_no=(0,.75,1),dist=1e-6,
                          clear_inner=True,clear_outer=False)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    deform=bm.verts.layers.deform.active
    if deform:
        for vertex in bm.verts:vertex[deform].clear()
    bm.normal_update()
    for vertex in bm.verts:vertex.co+=vertex.normal*.0007
    bm.to_mesh(mesh);bm.free();mesh.update()
    material=bpy.data.materials.new(identity+'_V6_Hair_OpaqueRoots')
    material.use_nodes=True;material.use_backface_culling=False
    material['v6MaterialRole']='hair';material['v6AlphaMode']='OPAQUE'
    material['v6Roughness']=.83;material['v6Metallic']=0.0
    bsdf=material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(*[c*.52 for c in style['tint']],1)
    bsdf.inputs['Roughness'].default_value=.83
    bsdf.inputs['Specular IOR Level'].default_value=.16
    obj=bpy.data.objects.new(identity+'_V6_FittedScalpRoots',mesh)
    bpy.context.scene.collection.objects.link(obj)
    _bind(obj,identity,'opaque_roots',rig,material)
    obj['v6GeometrySource']='Fitted MakeHuman CC0 skull surface: selected crown, temples and nape; original UV retained'
    return obj,{'tool':'Blender BMesh selection of fitted MakeHuman head surface',
                'source':'face.naturalSource.sourceMeshIDs.head','assetLicense':'CC0-1.0',
                'surfaceOffsetMetres':.0007,'opaqueRootLayer':True,
                'trimPlaneNormal':[0,.75,1],'trimPlaneHeightRest':top-.070,
                'libraryUVRetained':True}


def _mesh_record(obj):
    low, high = _bounds(obj)
    return {'name': obj.name, 'vertices': len(obj.data.vertices),
            'triangles': sum(len(p.vertices) - 2 for p in obj.data.polygons),
            'dimensionsRestMetres': [b - a for a, b in zip(low, high)],
            'boundsRest': [low, high], 'weightBone': 'Head', 'weight': 1,
            'originalUVRetained': True,
            'materials': [m.name for m in obj.data.materials]}


def apply(identity, rig, manifest):
    """Modify only current native head/brows/hair; retain rig and all Actions."""
    if rig.get('v6FaceHairRecord'):
        previous=json.loads(rig['v6FaceHairRecord'])
        if previous.get('version')=='v5-natural-face-hair-3':return previous
        raise RuntimeError('Reload original native source before upgrading from the first stylized face candidate')
    assert identity in STYLE, identity
    assert len(rig.data.bones) == 67 and 'Head' in rig.data.bones
    rest = _rest_digest(rig)
    actions = _action_digest()
    body = _body_digest()
    transform = rig.matrix_world.copy()
    head,eyes,brows,natural_source = _natural_head(identity,rig)
    old_hair = [o for o in bpy.data.objects if o.get('nativePart') == 'hair']
    old_names = [o.name for o in old_hair]
    style = STYLE[identity]
    face = _sculpt_face(identity, head, eyes, brows, style)
    face['naturalSource']=natural_source
    _retint_brows(identity, brows, style)
    face['facialHair'] = _stubble(head, face['eyeHeightRest'], identity)
    top = _bounds(head)[1][2]
    meta = _asset(style['asset'])
    if identity=='raphael':meta['detailBudget']=2800
    hair = _import_hair(meta)
    offset = style['offset']
    _fit(hair, style['size'], offset[:2], top + offset[2])
    eye_z = face['eyeHeightRest']
    for v in hair.data.vertices:
        if identity=='raphael' and v.co.y < -.025 and abs(v.co.x)<.083:
            # Shorten the artist's broad central forelock into the frontal
            # wave. Keep the original mesh/UV instead of adding tube curls.
            weight=min(1,max(0,(-v.co.y-.025)/.040))
            v.co.z += max(0,top-.025-v.co.z)*weight
            v.co.y += .008*weight
        # Open the eyes while preserving temple curls and the back silhouette.
        if v.co.y < -.035 and v.co.z < eye_z + .038:
            side_weight = math.exp(-((v.co.x / .055) ** 4))
            front_weight = min(1, max(0, (-v.co.y - .035) / .035))
            lift = min(.062, max(0, eye_z + .035 - v.co.z)) * side_weight * front_weight
            v.co.z += lift
            v.co.y += lift * .12
        if style['crop'] == 'bob':
            v.co.z += .009 * (v.co.x / .126)
        elif style['crop'] in ['halfup', 'ponytail']:
            fall = min(1, max(0, (top - .10 - v.co.z) / .20))
            wave = .024 if style['crop'] == 'ponytail' else .016
            v.co.x += wave * math.sin((top - v.co.z) * 38) * fall
            v.co.y += wave * math.sin((top - v.co.z) * 31) * fall
            if style['crop'] == 'ponytail' and v.co.y > .055:
                # Raise the tied-back tail from the source's low tie to a high
                # attachment; the source cap/front hairline remain in place.
                weight = min(1, max(0, (v.co.y - .045) / .05))
                v.co.z += .078 * weight
                v.co.x += .047 * weight
    material = _hair_material(identity, 'main', meta, style['tint'])
    _bind(hair, identity, 'main', rig, material)
    meshes = [hair]
    sources = [meta]
    authored_curls=None
    if identity == 'raphael':
        roots,root_record=_scalp_underlayer(identity,rig,head,style)
        meshes.append(roots)
    elif identity == 'nightqi':
        braid, braid_meta = _braid(identity, rig, top, style)
        meshes.append(braid)
        sources.append(braid_meta)
    elif identity == 'evelyn':
        waves, waves_meta = _lower_waves(identity, rig, top, style)
        meshes.append(waves)
        sources.append(waves_meta)
    for obj in old_hair:
        bpy.data.objects.remove(obj, do_unlink=True)
    assert _rest_digest(rig) == rest, 'Native bind/rest changed'
    assert _action_digest() == actions, 'Native action curves changed'
    assert _body_digest() == body, 'Native body or hand geometry/weights/materials changed'
    assert rig.matrix_world == transform, 'Native actor transform changed'
    record = {'version': 'v5-natural-face-hair-3', 'identity': identity, 'face': face,
              'hair': [_mesh_record(o) for o in meshes], 'removedHair': old_names,
              'sources': sources, 'tintLinear': list(style['tint']),
              'authoredCurls':authored_curls,
              'scalpRoots':root_record if identity=='raphael' else None,
              'restSHA256': rest, 'actionsSHA256': actions,
              'bodyAndHandsSHA256':body,'bodyAndHandsPreserved':True,
              'rigRestPreserved': True, 'rigTransformPreserved': True,
              'actionsPreserved': True, 'deformBones': 65, 'attachmentBones': 2,
              'limitations': ['Hair is rigid to existing Head; no extra physics bones.',
                              'Source artist strand detail and UVs retained; v5 silhouette adaptation is authored mesh editing.',
                              'Natural licensed photo-UV head fitted to native65; final material/neck/curl appearance still requires actual Cocos review.']}
    rig['v6FaceHairRecord'] = json.dumps(record)
    return record


def _render(identity, rig, output):
    scene = bpy.context.scene
    for obj in list(scene.objects):
        if obj.type in ['LIGHT', 'CAMERA']:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == 'MESH' and not obj.get('nativePart'):
            obj.hide_render = True
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    head = next(o for o in bpy.data.objects if o.get('nativePart') == 'head')
    low, high = _bounds(head)
    target = rig.matrix_world @ Vector((0, -.005, high[2] - .113))
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 20
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 600
    scene.render.resolution_y = 680
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.world = bpy.data.worlds.new('V6_Probe_World')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.15, .17, .20, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    for offset, energy, size in [((1.5, -2, 2.0), 170, 1.5),
                                 ((-2, -1.5, .5), 85, 1.8),
                                 ((.5, 1, 1.5), 130, 1.2)]:
        bpy.ops.object.light_add(type='AREA', location=target + Vector(offset))
        lamp = bpy.context.object
        lamp.data.energy = energy
        lamp.data.shape = 'DISK'
        lamp.data.size = size
        lamp.rotation_euler = (target - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add(location=target + Vector((.65, -2.5, .10)))
    camera = bpy.context.object
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .49 if identity not in ['nightqi', 'evelyn'] else .58
    scene.camera = camera
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument('--characters', default='raphael,mira')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(argv)
    identities = IDS if args.characters == 'all' else args.characters.split(',')
    PROBES.mkdir(parents=True, exist_ok=True)
    summary = PROBES / 'probe-summary.json'
    records = json.loads(summary.read_text(encoding='utf8')) if summary.exists() else {}
    for identity in identities:
        source = ROOT / 'src/.tmp/native-production/source' / (identity + '.blend')
        before = _sha(source)
        bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
        rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        manifest = json.loads((ROOT / 'src/cocos/assets/resources/actors' / identity / 'manifest.json').read_text(encoding='utf-8-sig'))
        record = apply(identity, rig, manifest)
        records[identity] = record
        if args.render:
            _render(identity, rig, PROBES / (identity + '-hair-face.png'))
        assert _sha(source) == before
        (PROBES / (identity + '-record.json')).write_text(json.dumps(record, indent=2), encoding='utf8')
        print('[V6_FACE_HAIR_PROBE]', identity, record['face']['changedVertices'],
              [(h['name'], h['triangles']) for h in record['hair']], flush=True)
    summary.write_text(json.dumps(records, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
