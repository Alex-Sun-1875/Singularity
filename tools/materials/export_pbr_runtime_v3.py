"""Export selected, matched PBR sources through Blender's native compositor.

Run the existing Blender 4.5 LTS executable with --background --factory-startup
--python tools/materials/export_pbr_runtime_v3.py. No downloads or dependencies.
The compositor performs color-managed resampling and native channel packing;
this adapter only selects source files, configures nodes and writes provenance.
"""
from pathlib import Path
import hashlib
import json
import struct
import uuid
import bpy

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'assets/materials/chapter-one-v3'
OUTPUT = ROOT / 'src/cocos/assets/resources/surfaces/pbr-v3'
SIZE = 512
SELECTED = {
    'wood': ('pbr-library', 'grey-planks'),
    'cobble': ('pbr-library', 'grey-paving'),
    'rock': ('pbr-library', 'natural-rock'),
    'fabric': ('pbr-library', 'neutral-woven'),
    'earth': ('terrain-library', 'forest-earth'),
    'grass': ('terrain-library', 'green-grass'),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def texture_meta(path):
    """Use the project's existing Cocos 3.8 image/texture importer contract."""
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity:' + relative(path)))
    sub = uid + '@6c48a'
    data = {
        'ver': '1.0.27', 'importer': 'image', 'imported': True,
        'uuid': uid, 'files': ['.png', '.json'],
        'subMetas': {'6c48a': {
            'importer': 'texture', 'uuid': sub, 'displayName': path.stem,
            'id': '6c48a', 'name': 'texture', 'ver': '1.0.22',
            'imported': True, 'files': ['.json'], 'subMetas': {},
            'userData': {
                'wrapModeS': 'repeat', 'wrapModeT': 'repeat',
                'minfilter': 'linear', 'magfilter': 'linear',
                'mipfilter': 'linear', 'anisotropy': 4, 'isUuid': True,
                'imageUuidOrDatabaseUri': uid, 'visible': False,
            },
        }},
        'userData': {'type': 'texture', 'fixAlphaTransparencyArtifacts': False,
                     'hasAlpha': False, 'redirect': sub},
    }
    path.with_suffix(path.suffix + '.meta').write_text(
        json.dumps(data, indent=2) + '\n', encoding='utf8')


def input_image(tree, path, role):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = 'sRGB' if role == 'albedo' else 'Non-Color'
    image.alpha_mode = 'CHANNEL_PACKED'
    node = tree.nodes.new('CompositorNodeImage')
    node.image = image
    scale = tree.nodes.new('CompositorNodeScale')
    scale.space = 'ABSOLUTE'
    scale.inputs['X'].default_value = SIZE
    scale.inputs['Y'].default_value = SIZE
    tree.links.new(node.outputs['Image'], scale.inputs['Image'])
    return scale.outputs['Image']


def output_image(tree, socket, name, color=False):
    node = tree.nodes.new('CompositorNodeOutputFile')
    node.base_path = str(OUTPUT)
    node.file_slots[0].path = name
    fmt = node.format
    fmt.file_format = 'PNG'
    fmt.color_mode = 'RGB'
    fmt.color_depth = '8'
    fmt.compression = 80
    fmt.color_management = 'OVERRIDE'
    fmt.display_settings.display_device = 'sRGB'
    fmt.view_settings.view_transform = 'Standard' if color else 'Raw'
    fmt.view_settings.look = 'None'
    fmt.view_settings.exposure = 0
    fmt.view_settings.gamma = 1
    tree.links.new(socket, node.inputs[0])


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    # Data channels must preserve exact 0/1 endpoints, especially metallic=0.
    scene.render.dither_intensity = 0
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    camera = bpy.data.objects.new('ExportCamera', bpy.data.cameras.new('ExportCamera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    records = []
    for surface, (group, source_id) in SELECTED.items():
        manifest_path = BASE / group / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf8'))
        definition = next(d for d in manifest['materials'] if d['id'] == source_id)
        sockets, sources = {}, []
        for item in definition['maps']:
            source = manifest_path.parent / item['file']
            actual = sha256(source)
            if actual != item['sha256']:
                raise ValueError('Source checksum mismatch: ' + str(source))
            sockets[item['role']] = input_image(tree, source, item['role'])
            sources.append({**item, 'verifiedFile': relative(source), 'verifiedSha256': actual})
        output_image(tree, sockets['albedo'], surface + '-color', color=True)
        output_image(tree, sockets['normal'], surface + '-normal')
        # Cocos 3.8.8 builtin-standard: AO.r, roughness.g, metallic.b, specular.a.
        # RGB PNG samples an implicit alpha of 1, preserving specularIntensity.
        combine = tree.nodes.new('CompositorNodeCombRGBA')
        for role, channel in [('ao', 'R'), ('roughness', 'G')]:
            separate = tree.nodes.new('CompositorNodeSepRGBA')
            tree.links.new(sockets[role], separate.inputs[0])
            tree.links.new(separate.outputs['R'], combine.inputs[channel])
        combine.inputs['B'].default_value = 0
        combine.inputs['A'].default_value = 1
        output_image(tree, combine.outputs['Image'], surface + '-pbr')
        records.append({
            'surface': surface, 'id': source_id, 'sourceAsset': definition['sourceAsset'],
            'sourcePage': definition['sourcePage'], 'license': definition['license'],
            'sourceManifest': relative(manifest_path), 'sources': sources,
            'tileMetres': definition.get('tileMetres'),
            'designTileMetres': definition.get('previewTileMetres'),
            'physicalScaleStatus': definition.get('physicalScaleStatus', 'see source manifest'),
            'creationMethod': definition.get('creationMethod', 'see source metadata'),
            'normalConvention': definition['normalConvention'], 'exports': [],
        })
    bpy.ops.render.render()
    for record in records:
        for role in ['color', 'normal', 'pbr']:
            stem = record['surface'] + '-' + role
            path = OUTPUT / (stem + '.png')
            (OUTPUT / (stem + '0001.png')).replace(path)
            texture_meta(path)
            header = path.read_bytes()[:26]
            width, height = struct.unpack('>II', header[16:24])
            record['exports'].append({
                'role': role, 'file': relative(path), 'sha256': sha256(path),
                'size': [width, height], 'pngBitDepth': header[24],
                'bytes': path.stat().st_size,
                'colorSpace': 'sRGB' if role == 'color' else 'linear data',
            })
    record = {
        'date': '2026-11-04', 'tool': 'Blender ' + bpy.app.version_string,
        'script': relative(Path(__file__).resolve()),
        'credit': 'Powered by Poly Haven; Fabric082A and Grass007 from ambientCG',
        'licenseSources': ['https://polyhaven.com/license', 'https://docs.ambientcg.com/license/'],
        'processing': {
            'sourcePolicy': 'Read-only official source files verified against source manifest SHA256.',
            'resize': 'Blender native compositor Scale ABSOLUTE 512x512; float compositing.',
            'albedo': 'sRGB input -> scene-linear scale -> Standard sRGB PNG output, no look/exposure/dye.',
            'data': 'Non-Color input (including original PNG16) -> float scale -> Raw PNG8 output.',
            'normal': 'Matched OpenGL +Y data; no green flip, generated normals or cross-asset mixing.',
            'pbr': 'Blender native Separate/Combine RGBA: R=AO, G=roughness, B=0, implicit A=1.',
            'quantization': 'Explicit PNG8 runtime export after float resampling; originals retain original bit depth.',
            'cocos': 'builtin-standard USE_PBR_MAP; roughness=1, occlusion=1, metallic=0; mipfilter linear.',
        },
        'materials': records,
    }
    (OUTPUT / 'provenance.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('PBR_RUNTIME_EXPORT ' + json.dumps({
        'materials': len(records), 'textures': len(records) * 3,
        'bytes': sum(e['bytes'] for r in records for e in r['exports']),
        'output': relative(OUTPUT),
    }), flush=True)


if __name__ == '__main__':
    main()
