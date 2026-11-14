"""Fit Quaternius' free Hair_Long to the current actor; retain face/rig/actions."""
from pathlib import Path
import bpy, sys, json, hashlib, copy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
sys.path.insert(0, str(ROOT / 'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import cocos_native_characters as native

SOURCE = ROOT / 'source-art/characters/3d-appearance-v3'
KIT = ROOT / 'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]'
HAIR = KIT / 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Long.gltf'

def mesh_digest(o):
    return hashlib.sha256(repr((
        [tuple(v.co) for v in o.data.vertices],
        [tuple(p.vertices) for p in o.data.polygons],
        [[tuple(v.uv) for v in layer.data] for layer in o.data.uv_layers],
        [(g.name, g.index) for g in o.vertex_groups],
        [[tuple((g.group, g.weight)) for g in v.groups] for v in o.data.vertices],
    )).encode()).hexdigest()

def visible_bounds(objects):
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for o in objects:
        ev = o.evaluated_get(deps)
        mesh = ev.to_mesh()
        points.extend(ev.matrix_world @ v.co for v in mesh.vertices)
        ev.to_mesh_clear()
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]

BASE.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / 'raphael.blend'))
rig = bpy.data.objects['raphael_Native65']
manifest = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
original = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('nativePart')]
body_hash = {o.name: mesh_digest(o) for o in original if o.get('nativePart') != 'hair'}
action_hash, bind_hash = pipeline.curves(), pipeline.skeleton(rig)
rig_transform = [list(r) for r in rig.matrix_world]
rig.data.pose_position = 'REST'
bpy.context.scene.frame_set(0)

hair_rig, hairs = native.imported(HAIR)
assert len(hairs) == 1
correction = rig.data.bones['Head'].matrix_local @ hair_rig.data.bones['Head'].matrix_local.inverted()
head = next(o for o in original if o.get('nativePart') == 'head')
head_surface = BVHTree.FromObject(head, bpy.context.evaluated_depsgraph_get())
crown_height = max(v.co.z for v in head.data.vertices) - .055
crown_fit = {'adjustedVertices': 0, 'maximumDisplacementMetres': 0, 'minimumClearanceMetres': .0035}
for hair in hairs:
    for vertex in hair.data.vertices:
        vertex.co = correction @ vertex.co
        if vertex.co.z > crown_height:
            near, normal, index, distance = head_surface.find_nearest(vertex.co)
            if near is not None and distance < .03:
                gap = (vertex.co - near).dot(normal)
                if gap < .0035:
                    move = .0035 - gap
                    vertex.co += normal * move
                    crown_fit['adjustedVertices'] += 1
                    crown_fit['maximumDisplacementMetres'] = max(crown_fit['maximumDisplacementMetres'], move)
    native.transfer(hair, rig)
    hair.name = 'raphael_native_hair_Hair_Long'
    hair['nativePart'] = 'hair'
    hair['defaultVisible'] = True
    hair['sourceAsset'] = HAIR.relative_to(ROOT).as_posix()
    hair['sourceLicense'] = 'CC0-1.0'
    for polygon in hair.data.polygons:
        polygon.use_smooth = True
    mat = hair.data.materials[0]
    mat.name = 'Quaternius_Hair_Long_Silver'
    tree = mat.node_tree
    bsdf = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for node in tree.nodes:
        if node.type != 'TEX_IMAGE' or not node.image:
            continue
        is_normal = 'normal' in (node.image.name + node.image.filepath).lower()
        node.image = bpy.data.images.load(str(BASE / 'textures' / ('long-normal.png' if is_normal else 'long-silver.png')), check_existing=True)
        node.image.colorspace_settings.name = 'Non-Color' if is_normal else 'sRGB'
    bsdf.inputs['Roughness'].default_value = .72
    bsdf.inputs['Metallic'].default_value = 0

bpy.data.objects.remove(hair_rig, do_unlink=True)
for old in original:
    if old.get('nativePart') == 'hair':
        bpy.data.objects.remove(old, do_unlink=True)

record = {
    'runtimeName': 'Quaternius_Hair_Long_Silver',
    'parts': ['hair'],
    'maps': {'albedo': '../hair-long-v1/textures/long-silver.png',
             'normal': '../hair-long-v1/textures/long-normal.png'},
    'sourcePBR': {'effectiveFactors': {'roughness': .72, 'metallic': 0},
                  'authorMaterial': 'MI_Hair_2', 'authorGLTF': HAIR.relative_to(ROOT).as_posix()},
    'doubleSided': True,
}
manifest['materials'] = [r for r in manifest['materials'] if 'hair' not in r.get('parts', [])] + [record]
objects = [o for o in bpy.data.objects if o.type == 'MESH' and o.get('nativePart')]
assert len(objects) == 13
assert {o.name: mesh_digest(o) for o in objects if o.get('nativePart') != 'hair'} == body_hash
assert pipeline.curves() == action_hash and pipeline.skeleton(rig) == bind_hash
assert [list(r) for r in rig.matrix_world] == rig_transform

rig.data.pose_position = 'POSE'
idle = bpy.data.actions['idle']
rig.animation_data.action = idle
if idle.slots:
    rig.animation_data.action_slot = idle.slots[0]
scene = bpy.context.scene
scene.frame_set(0)
scene.name = 'raphael-polish'
pipeline.select([rig] + objects)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(BASE / 'raphael-polish.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
    export_force_sampling=True, export_frame_step=1, export_def_bones=False,
    export_skins=True, export_all_influences=False, export_vertex_color='NONE',
    export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(BASE / 'raphael.blend'), relative_remap=False)

manifest.update(appearanceRevision='quaternius-long-v1', prefabRoot='raphael-polish',
                appearanceReview='source-art/characters/3d-hair-long-v1/README.md',
                triangles=sum(pipeline.triangles(o) for o in objects))
manifest['parts']['hair']['nodes'] = [o.name for o in hairs]
manifest['source'] = (BASE / 'raphael.blend').relative_to(ROOT).as_posix()
manifest['hairstyle'] = {'asset': 'Hair_Long', 'publisher': 'Quaternius', 'license': 'CC0-1.0',
                         'edition': 'Official free Standard; already installed',
                         'color': 'Silver, preserving original painted strand shading',
                         'attachment': 'Original head-bone bind matrix; same skeleton and animations',
                         'crownFit': crown_fit,
                         'physics': 'Head-bound original mesh; no simulated hair physics'}
(BASE / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
proof = {'faceBodyGeometryUVWeightsUnchanged': True, 'all14ActionsUnchanged': True,
         'bindPoseUnchanged': True, 'rigTransformUnchanged': True,
         'nonHairMeshHashes': body_hash, 'actionHash': action_hash, 'bindHash': bind_hash,
         'hairSource': HAIR.relative_to(ROOT).as_posix(), 'sourceSHA256': pipeline.sha(HAIR),
         'crownFit': crown_fit,
         'hairBoundsIdle': visible_bounds(hairs), 'meshes': len(objects),
         'triangles': manifest['triangles'], 'hairTriangles': sum(pipeline.triangles(o) for o in hairs)}
(BASE / 'preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print('LONG_HAIR_EXPORTED', json.dumps(proof), flush=True)

# Native Blender preview before installing: same face, body, materials and actual mesh.
if '--render' in sys.argv:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 12
    scene.render.resolution_x = 512
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    if scene.world is None:
        scene.world = bpy.data.worlds.new('HairReviewWorld')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs[0].default_value = (.055, .065, .075, 1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value = .65
    for obj in objects:
        obj.hide_render = not obj.get('defaultVisible', True)
    target = Vector((0, 0, 1.65))
    camera = bpy.data.objects.new('HairReviewCamera', bpy.data.cameras.new('HairReviewCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = .78
    for name, loc, energy, size in [('Key', (2, -3, 4), 370, 3), ('Fill', (-3, -2, 2), 230, 3), ('Rim', (1, 3, 3), 300, 2)]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.shape, light.size = energy, 'DISK', size
        node = bpy.data.objects.new(name, light)
        scene.collection.objects.link(node)
        node.location = loc
        node.rotation_euler = (target - node.location).to_track_quat('-Z', 'Y').to_euler()
    folder = BASE / 'blender-preview'
    folder.mkdir(exist_ok=True)
    for angle in [0, 90, 180]:
        rad = math.radians(angle)
        camera.location = (math.sin(rad) * 4, -math.cos(rad) * 4, 1.68)
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(folder / ('head-' + str(angle) + '.png'))
        bpy.ops.render.render(write_still=True)
