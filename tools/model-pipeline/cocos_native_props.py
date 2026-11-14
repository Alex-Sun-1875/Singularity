"""Adapt official CC0 KayKit Adventurers props; never generate weapon geometry.

Run with the project's Blender 4.5 LTS, e.g. blender --background --python
tools/model-pipeline/cocos_native_props.py. Outputs are review candidates only.
Source triangles, UVs, normals, and the author's Bow Draw shape are retained.
"""
from pathlib import Path
import bpy
import hashlib
import json
import math
import shutil
import sys
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'src/.tools/research-animation-kaykit/adventurers-free-2.0/KayKit_Adventurers_2.0_FREE'
LIBRARY = PACKAGE / 'Assets/gltf'
OUT = ROOT / 'src/.tmp/native-production/props'
SOURCE = ROOT / 'src/.tmp/native-production/source/props'
ENGINE = Path('C:/ProgramData/cocos/editors/Creator/3.8.8/resources/resources/3d/engine')
PROFILES = {
    'sword': ('sword_1handed', 1.05, 'Y', 'hand_r'),
    'greatsword': ('sword_2handed', 1.30, 'Y', 'hand_r'),
    'staff': ('staff', 1.75, 'Y', 'hand_r'),
    'wand': ('wand', .60, 'Y', 'hand_r'),
    'bow': ('bow_withString', 1.40, 'Z', 'hand_l'),
    'arrow': ('arrow_bow', .70, 'Z', 'hand_r'),
    'dagger': ('dagger', .48, 'Y', 'hand_r'),
    'shield': ('shield_round', .70, 'Y', 'hand_l'),
}
# glTF->Blender import is Rx(+90); FBX Y-up export is Rx(-90).
BLENDER_TO_COCOS = Matrix.Rotation(-math.pi / 2, 4, 'X')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def bounds(points):
    low = [min(p[i] for p in points) for i in range(3)]
    high = [max(p[i] for p in points) for i in range(3)]
    return {'min': low, 'max': high, 'dimensions': [b-a for a, b in zip(low, high)]}


def matrix_rows(matrix):
    return [list(row) for row in matrix]


def snapshot(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    keys = mesh.shape_keys
    return {
        'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles),
        'polygons': len(mesh.polygons), 'uvLoops': len(mesh.uv_layers.active.data),
        'uv': [tuple(item.uv) for item in mesh.uv_layers.active.data],
        'points': [obj.matrix_world @ vertex.co for vertex in mesh.vertices],
        'shapeNames': [key.name for key in keys.key_blocks][1:] if keys else [],
        'shapes': {key.name: [obj.matrix_world @ v.co for v in key.data]
                   for key in keys.key_blocks[1:]} if keys else {},
    }


def compare_roundtrip(before, after):
    # FBX may split/weld coincident normal/UV vertices; compare geometry instead
    # of relying on mutable vertex indices. Morph matching also uses base points.
    assert before['triangles'] == after['triangles'], 'Triangle count changed'
    assert before['uvLoops'] == after['uvLoops'], 'UV corner count changed'
    assert before['shapeNames'] == after['shapeNames'], 'Morph names changed'
    tree = KDTree(len(after['points']))
    for i, point in enumerate(after['points']):
        tree.insert(point, i)
    tree.balance()
    position_error = 0.0
    morph_error = 0.0
    for i, point in enumerate(before['points']):
        nearest, index, error = tree.find(point)
        position_error = max(position_error, error)
        for name in before['shapeNames']:
            # Coincident split vertices share the authored morph displacement.
            morph_error = max(morph_error, (before['shapes'][name][i] - after['shapes'][name][index]).length)
    uv_before = sorted(before['uv'])
    uv_after = sorted(after['uv'])
    uv_error = max(abs(a-b) for p, q in zip(uv_before, uv_after) for a, b in zip(p, q))
    assert position_error < 2e-5, f'FBX position drift {position_error}'
    assert morph_error < 2e-5, f'FBX morph drift {morph_error}'
    assert uv_error < 2e-5, f'FBX UV drift {uv_error}'
    return {'passed': True, 'trianglesBefore': before['triangles'],
            'trianglesAfter': after['triangles'], 'uvCornerCount': before['uvLoops'],
            'maxPositionErrorMeters': position_error, 'maxMorphPositionErrorMeters': morph_error,
            'maxUVError': uv_error, 'shapeNamesAfterFBXImport': after['shapeNames']}


def import_mesh(path):
    previous = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in previous and obj.type == 'MESH']
    assert len(imported) == 1, f'Expected one official prop mesh: {path}'
    return imported[0]


def wood_grip_evidence(scale):
    # The official bow.gltf is the same wooden bow without string. Intersect
    # actual wooden triangle edges at the author z=0 plane, never a PCA band.
    obj = import_mesh(LIBRARY / 'bow.gltf')
    points = [v.co.copy() for v in obj.data.vertices]
    hits = []
    # Source glTF Z corresponds to Blender -Y before our export adaptation.
    for edge in obj.data.edges:
        a, b = [points[i] for i in edge.vertices]
        if a.y * b.y <= 0 and abs(a.y-b.y) > 1e-9:
            hits.append(a.lerp(b, -a.y/(b.y-a.y)))
    assert hits, 'No author-origin wooden grip cross-section'
    section = bounds(hits)
    # Author origin must pass through the wooden handle cross-section.
    assert section['min'][0] < 0 < section['max'][0]
    assert section['min'][2] < 0 < section['max'][2]
    center = [(a+b)/2 for a, b in zip(section['min'], section['max'])]
    bpy.data.objects.remove(obj, do_unlink=True)
    return {'method': 'Author origin retained. Intersect official stringless bow.gltf wooden edges at original glTF z=0; origin lies inside wooden cross-section in both transverse axes.',
            'source': relative(LIBRARY / 'bow.gltf'), 'sourceSHA256': digest(LIBRARY / 'bow.gltf'),
            'woodEdgeIntersections': len(hits), 'crossSectionBoundsBlenderSourceUnits': section,
            'crossSectionCenterDistanceFromAuthorOriginMeters': Vector(center).length * scale,
            'pivotTranslation': [0, 0, 0]}


def mobile_materials(obj, source_record):
    textures = []
    for material in obj.data.materials:
        if not material or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.type != 'TEX_IMAGE' or not node.image:
                continue
            source_name = Path(bpy.path.abspath(node.image.filepath)).name
            original = LIBRARY / source_name
            destination = OUT / 'textures' / source_name
            image = node.image
            original_size = list(image.size)
            if max(image.size) > 256:
                factor = 256 / max(image.size)
                image.scale(round(image.size[0]*factor), round(image.size[1]*factor))
            image.filepath_raw = str(destination)
            image.file_format = 'PNG'
            image.save()
            textures.append({'path': relative(destination), 'sha256': digest(destination),
                             'dimensions': list(image.size), 'sourceDimensions': original_size,
                             'source': relative(original), 'sourceSHA256': digest(original)})
    source_record['textures'] = textures


def save_source_dependencies(asset, document):
    assets = [LIBRARY / (asset+'.gltf')]
    assets += [LIBRARY / item['uri'] for item in document['buffers']]
    assets += [LIBRARY / item['uri'] for item in document.get('images', [])]
    records = []
    for path in assets:
        destination = SOURCE / 'original' / path.name
        shutil.copy2(path, destination)
        records.append({'path': relative(path), 'sha256': digest(path), 'archived': relative(destination)})
    return records


def build():
    selected = set(sys.argv[sys.argv.index('--props')+1].split(',')) if '--props' in sys.argv else None
    if selected and (SOURCE/'native-props.blend').exists():
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'native-props.blend'))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    (OUT / 'textures').mkdir(parents=True, exist_ok=True)
    (SOURCE / 'original').mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGE / 'License.txt', SOURCE / 'License-KayKit-Adventurers.txt')
    objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    records = json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['props'] if selected and (OUT/'manifest.json').exists() else {}
    for name, (asset, length, author_axis, hand) in PROFILES.items():
        if selected and name not in selected:
            continue
        existing = bpy.data.objects.get('KayKit_'+name)
        if existing:
            if existing in objects: objects.remove(existing)
            bpy.data.objects.remove(existing, do_unlink=True)
        document = json.loads((LIBRARY / (asset+'.gltf')).read_text())
        obj = import_mesh(LIBRARY / (asset+'.gltf'))
        obj.name = 'KayKit_' + name
        original = snapshot(obj)
        extent = max(original['points'][i][{'Y': 2, 'Z': 1}[author_axis]] for i in range(len(original['points']))) - min(p[{'Y': 2, 'Z': 1}[author_axis]] for p in original['points'])
        scale = length / extent
        rotation = Matrix.Rotation(-math.pi/2, 4, 'X') if author_axis == 'Z' else Matrix.Identity(4)
        transform = Matrix.Scale(scale, 4) @ rotation
        # Blender's native operation updates mesh.vertices AND every shape key.
        # Editing Basis key points alone leaves the exported base mesh stale.
        obj.data.transform(transform, shape_keys=True)
        obj.data.update()
        record = {'asset': asset, 'creator': 'Kay Lousberg / KayKit', 'license': 'CC0-1.0',
                  'officialPackage': 'KayKit Adventurers Free 2.0',
                  'officialURL': 'https://kaylousberg.itch.io/kaykit-adventurers',
                  'sourceFiles': save_source_dependencies(asset, document),
                  'fbx': relative(OUT / (name+'.fbx')), 'suggestedResource': 'actors/props/'+name+'/'+name,
                  'meshObject': obj.name, 'authorGripOrigin': [0,0,0], 'exportGripOrigin': [0,0,0],
                  'authorLongAxis': '+'+author_axis, 'cocosLongAxis': '+Y',
                  'units': 'metres', 'lengthMeters': length, 'unitScale': scale,
                  'authorToExport': matrix_rows(transform), 'exportToAuthor': matrix_rows(transform.inverted()),
                  'authorToExportRotation': matrix_rows(rotation), 'socketPropRotation': matrix_rows(rotation.inverted()),
                  'socketPropRotationNote': 'For an animated helper in the author handslot frame apply rotation inverse only. FBX already contains the intended metre size; do not cancel unitScale.',
                  'attachmentHand': hand, 'topology': {'sourceTriangles': original['triangles'], 'sourceVertices': original['vertices'],
                      'sourceUVLoops': original['uvLoops'], 'geometryOperation': 'uniform scale + rigid rotation only; no remesh, simplification, modifiers or UV edits'}}
        mobile_materials(obj, record)
        current = snapshot(obj)
        points_cocos = [BLENDER_TO_COCOS @ p for p in current['points']]
        record['boundsCocosMeters'] = bounds(points_cocos)
        assert abs(record['boundsCocosMeters']['dimensions'][1] - length) < 1e-5, 'Cocos +Y length mismatch'
        record['morph'] = None
        if name == 'bow':
            record['woodGripValidation'] = wood_grip_evidence(scale)
            shape = current['shapes']['Draw']
            record['morph'] = {'shapeName': 'Draw', 'shapeIndex': 0, 'subMeshIndex': 0,
                               'defaultWeight': 0, 'range': [0,1], 'source': 'official author target',
                               'boundsAtWeight1CocosMeters': bounds([BLENDER_TO_COCOS @ p for p in shape]),
                               'maxVertexDisplacementMeters': max((a-b).length for a,b in zip(current['points'], shape)),
                               'cocosAPI': 'renderer.setWeight(draw01, subMeshIndex, shapeIndex)',
                               'cocosTargetLookup': 'renderer.mesh.struct.morph.targetNames.indexOf("Draw")'}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')), use_selection=True, object_types={'MESH'},
                                 axis_forward='Z', axis_up='Y', bake_space_transform=True,
                                 add_leaf_bones=False, bake_anim=False, use_mesh_modifiers=False,
                                 path_mode='RELATIVE', apply_unit_scale=True, mesh_smooth_type='OFF')
        record['exportSHA256'] = digest(OUT/(name+'.fbx'))
        previous = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(OUT/(name+'.fbx')))
        roundtrip = [o for o in bpy.data.objects if o not in previous and o.type == 'MESH']
        assert len(roundtrip) == 1
        record['fbxRoundtrip'] = compare_roundtrip(current, snapshot(roundtrip[0]))
        for imported in [o for o in bpy.data.objects if o not in previous]:
            bpy.data.objects.remove(imported, do_unlink=True)
        records[name] = record
        objects.append(obj)
        print('[NATIVE_PROP_READY]', name, json.dumps({'fbx': record['fbx'], 'bounds': record['boundsCocosMeters'], 'morph': record['morph'], 'roundtrip': record['fbxRoundtrip']}), flush=True)
    for image in bpy.data.images:
        if image.source == 'FILE' and Path(bpy.path.abspath(image.filepath)).exists():
            image.pack()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'native-props.blend'))
    manifest = {'status': 'candidate-not-installed', 'pipeline': relative(Path(__file__).resolve()),
                'blender': bpy.app.version_string, 'license': 'CC0-1.0',
                'scope': 'Official game-ready meshes; adapters only. Source origin, topology, UVs, normals and Bow Draw target retained.',
                'fbxAxes': {'forward': '+Z', 'up': '+Y', 'bakeSpaceTransform': True},
                'recommendedEquipmentResources': {'W01': 'sword', 'W02': 'sword', 'L01': 'greatsword',
                    'W07': 'bow', 'W08': 'bow', 'L02': 'bow', 'W11': 'staff'},
                'equipmentNote': 'W01/W02 share official sword mesh; W07/W08/L02 share official drawn bow mesh. Distinct rarity is game metadata. No invented official variants/palettes.',
                'recommendedProfileWeapons': {'mira': 'dagger', 'lorn': 'shield', 'raider-shield': 'shield', 'captain': 'greatsword', 'nightqi': 'bow', 'evelyn': None, 'kael': None},
                'profileLimitations': 'Captain uses the official greatsword until a licensed matching hammer is available. Evelyn/Kael carry no weapon; their lantern/maps are not approximated by swords.',
                'cocosMorphSource': {'meshRenderer': str(ENGINE/'cocos/3d/framework/mesh-renderer.ts'),
                    'interface': str(ENGINE/'cocos/3d/assets/morph.ts'),
                    'method': 'setWeight(weight: number, subMeshIndex: number, shapeIndex: number): void',
                    'methodLines': [716,730], 'defaultEnableMorph': True,
                    'note': 'Setting renderer.mesh resets weights. Enable morph then setWeight after assignment. Works on native MeshRenderer; SkinnedMeshRenderer inherits it.'},
                'props': records}
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('[NATIVE_PROPS_MANIFEST]', relative(OUT/'manifest.json'), flush=True)
    if '--preview' in sys.argv:
        render_preview(objects)


def render_preview(objects):
    """Render the real exported objects and the author's Draw endpoint for QA."""
    by_name = {o.name.removeprefix('KayKit_'): o for o in objects}
    order = ['sword', 'greatsword', 'staff', 'wand', 'bow', 'bow', 'arrow']
    x_positions = [0, .62, 1.32, 1.95, 2.55, 3.40, 4.20]
    for obj in objects:
        obj.hide_render = True
    for index, (name, x) in enumerate(zip(order, x_positions)):
        obj = by_name[name].copy()
        obj.data = by_name[name].data.copy()
        bpy.context.collection.objects.link(obj)
        obj.hide_render = False
        obj.location = (x, 0, -min(v.co.z for v in obj.data.vertices))
        if name == 'bow' and index == 5:
            obj.data.shape_keys.key_blocks['Draw'].value = 1
        # Labels are preview-only; FBXs contain exactly the official prop mesh.
        text = bpy.data.curves.new('Preview label', type='FONT')
        text.body = name + (' Draw=1' if index == 5 else ' Draw=0' if name == 'bow' else '')
        text.align_x = 'CENTER'
        text.size = .075
        label = bpy.data.objects.new('Preview label', text)
        bpy.context.collection.objects.link(label)
        label.location = (x, -.10, -.13)
        label.rotation_euler = (math.pi/2, 0, 0)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 820
    scene.render.resolution_percentage = 100
    if scene.world is None:
        scene.world = bpy.data.worlds.new('Preview world')
    scene.world.color = (.11, .12, .14)
    scene.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add(location=(2.15, -8, 2.0))
    camera = bpy.context.object
    camera.rotation_euler = (Vector((2.15, 0, .80)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 4.85
    scene.camera = camera
    for location, energy, size in [((0, -3, 5), 650, 4), ((4, 1, 3), 420, 3)]:
        bpy.ops.object.light_add(type='AREA', location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = 'DISK'
        light.data.size = size
        light.rotation_euler = (Vector((2, 0, .8)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(SOURCE/'native-props-preview.png')
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    if '--preview-only' in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'native-props.blend'))
        render_preview([o for o in bpy.data.objects if o.type == 'MESH'])
    else:
        build()
