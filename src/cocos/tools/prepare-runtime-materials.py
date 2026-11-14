"""Remove imported texture dependencies already restored by NativeActorMaterials.

Only material JSON links change. Embedded image, geometry, UV, skin and animation
bytes are retained exactly. The original approved model is archived once.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def prepare(write=False):
    folder = PROJECT / 'assets/resources/actors/raphael'
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    model = folder / (manifest['prefabRoot'] + '.glb')
    raw = model.read_bytes()
    size, kind = struct.unpack_from('<II', raw, 12)
    if raw[:4] != b'glTF' or kind != 0x4E4F534A:
        raise ValueError('Expected GLB 2.0 JSON chunk')
    data = json.loads(raw[20:20 + size])
    binary = raw[20 + size:]
    records = {r['runtimeName']: r for r in manifest['materials']}
    changed = []
    for material in data['materials']:
        record = records.get(material.get('name'))
        if not record:
            continue
        # A declared runtime record owns each map removed here. Never strip an
        # unrelated material, or a map without an actual replacement file.
        for value in record['maps'].values():
            if not (folder / value).resolve().is_file():
                raise ValueError('Missing runtime replacement: ' + value)
        removed = []
        for target, keys in [(material, ['normalTexture', 'occlusionTexture', 'emissiveTexture']),
                             (material.get('pbrMetallicRoughness', {}), ['baseColorTexture', 'metallicRoughnessTexture'])]:
            for key in keys:
                if key in target:
                    del target[key]
                    removed.append(key)
        if removed:
            changed.append({'material': material['name'], 'links': removed})
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    output = struct.pack('<III', 0x46546C67, 2, 20 + len(encoded) + len(binary))
    output += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + binary
    if output[20 + len(encoded):] != binary:
        raise ValueError('Binary data changed')
    result = {'changedMaterials': changed, 'binarySha256': hashlib.sha256(binary).hexdigest(),
              'geometryImagesSkeletonAnimationChanged': False, 'written': write and bool(changed)}
    if write and changed:
        archive = PROJECT.parents[1] / 'source-art/performance/runtime-material-dependencies-v1'
        archive.mkdir(parents=True, exist_ok=True)
        backup = archive / model.name
        if not backup.exists():
            backup.write_bytes(raw)
        result['beforeSha256'] = hashlib.sha256(raw).hexdigest()
        result['afterSha256'] = hashlib.sha256(output).hexdigest()
        model.write_bytes(output)
        (archive / 'conversion.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    prepare(parser.parse_args().write)
