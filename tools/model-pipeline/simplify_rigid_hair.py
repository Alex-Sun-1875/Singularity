"""Blender export LoD for a single, rigidly Head-weighted glTF hair mesh.

Run with Blender --background --factory-startup --python this.py --
  --source original.glb --output game.glb --triangles 4500 --report report.json
Only geometry changes: retain the original glTF hierarchy, skin, material and
joint numbering so the game's shared hero skeleton remains compatible.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile

import bpy


def read_glb(path):
    data = Path(path).read_bytes()
    assert data[:4] == b'glTF' and struct.unpack_from('<I', data, 4)[0] == 2
    length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + length])
    offset = 20 + length
    size, kind = struct.unpack_from('<II', data, offset)
    assert kind == 0x004E4942 and offset + 8 + size == len(data)
    return document, data[offset + 8:]


def accessor_bytes(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    assert 'sparse' not in accessor and 'byteStride' not in view
    width = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[accessor['componentType']]
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return binary[start:start + width * count * accessor['count']]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--triangles', type=int, default=4500)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert args.source.resolve() != args.output.resolve(), 'Keep the full-detail source'
    original, original_bin = read_glb(args.source)
    assert len(original['meshes']) == len(original['skins']) == 1
    assert not any(original.get(k) for k in ['animations', 'images', 'extensionsUsed'])
    primitive = original['meshes'][0]['primitives'][0]
    assert len(original['meshes'][0]['primitives']) == 1
    assert set(primitive['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'}
    joints = accessor_bytes(original, original_bin, primitive['attributes']['JOINTS_0'])
    weights = accessor_bytes(original, original_bin, primitive['attributes']['WEIGHTS_0'])
    assert set(struct.iter_unpack('<4B', joints)) == {(6, 0, 0, 0)}
    assert set(struct.iter_unpack('<4f', weights)) == {(1., 0., 0., 0.)}
    head = original['skins'][0]['joints'][6]
    assert original['nodes'][head]['name'].split(':')[-1] == 'Head'
    before = original['accessors'][primitive['indices']]['count'] // 3
    assert 200 <= args.triangles < before

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source.resolve()), merge_vertices=True)
    obj, = [o for o in bpy.context.scene.objects if o.type == 'MESH'
            and o.data.name == original['meshes'][0]['name']]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    # Same mature Blender Collapse/Triangulate operation as cocos_optimize_exports.
    modifier = obj.modifiers.new('GameLOD', 'DECIMATE')
    modifier.ratio = args.triangles / before
    modifier.use_collapse_triangulate = True
    while obj.modifiers.find(modifier.name) > 0:
        bpy.ops.object.modifier_move_up(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for rig in bpy.context.scene.objects:
        if rig.type == 'ARMATURE':
            rig.select_set(True)
    with tempfile.TemporaryDirectory(prefix='singularity-hair-lod-') as temp:
        exported = Path(temp) / 'geometry.glb'
        bpy.ops.export_scene.gltf(filepath=str(exported), export_format='GLB',
                                  export_animations=False, export_yup=True, use_selection=True,
                                  export_all_influences=False)
        candidate, candidate_bin = read_glb(exported)

    candidate_mesh, = candidate['meshes']
    reduced, = candidate_mesh['primitives']
    positions = candidate['accessors'][reduced['attributes']['POSITION']]
    old_positions = original['accessors'][primitive['attributes']['POSITION']]
    bounds_delta = max(abs(positions[k][i] - old_positions[k][i])
                       for k in ['min', 'max'] for i in range(3))
    assert bounds_delta < .003, ('Unexpected coordinate transform/bounds', bounds_delta)
    after = candidate['accessors'][reduced['indices']]['count'] // 3
    assert abs(after - args.triangles) < 20

    # Repack only used data; never retain the unused high-detail vertex payload.
    result = copy.deepcopy(original)
    result['accessors'] = []
    result['bufferViews'] = []
    binary = bytearray()

    def add(document, payload, index, replacement=None):
        accessor = copy.deepcopy(document['accessors'][index])
        data = accessor_bytes(document, payload, index) if replacement is None else replacement
        binary.extend(b'\0' * (-len(binary) % 4))
        accessor['bufferView'] = len(result['bufferViews'])
        accessor.pop('byteOffset', None)
        result['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        result['accessors'].append(accessor)
        binary.extend(data)
        return len(result['accessors']) - 1

    result['skins'][0]['inverseBindMatrices'] = add(original, original_bin, original['skins'][0]['inverseBindMatrices'])
    count = positions['count']
    attributes = {}
    for semantic in primitive['attributes']:
        index = reduced['attributes'][semantic]
        if semantic == 'JOINTS_0':
            # Export may reorder the armature. Keep the source hero's Head slot.
            candidate['accessors'][index]['componentType'] = 5121
            replacement = bytes([6, 0, 0, 0]) * count
        elif semantic == 'WEIGHTS_0':
            replacement = struct.pack('<4f', 1, 0, 0, 0) * count
        else:
            replacement = None
        attributes[semantic] = add(candidate, candidate_bin, index, replacement)
    output_primitive = result['meshes'][0]['primitives'][0]
    output_primitive['attributes'] = attributes
    output_primitive['indices'] = add(candidate, candidate_bin, reduced['indices'])
    result['buffers'] = [{'byteLength': len(binary)}]
    binary.extend(b'\0' * (-len(binary) % 4))
    encoded = json.dumps(result, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    data = (struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary))
            + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
            + struct.pack('<II', len(binary), 0x004E4942) + binary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    report = {'tool': 'Blender ' + bpy.app.version_string + ' Decimate COLLAPSE',
              'sourceSHA256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'outputSHA256': hashlib.sha256(data).hexdigest(),
              'triangles': {'before': before, 'after': after},
              'vertices': {'before': old_positions['count'], 'after': count},
              'bytes': {'before': args.source.stat().st_size, 'after': len(data)},
              'boundsMaxChangeMetres': bounds_delta,
              'preserved': ['node hierarchy', 'skin/joint order', 'inverse bind matrices',
                            'materials', 'mesh name', 'Head weights'],
              'validationScope': 'Geometry invariants only; visual review recorded separately'}
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
