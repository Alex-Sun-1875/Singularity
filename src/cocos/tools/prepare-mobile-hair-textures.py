"""Create a deterministic 1024px hair-texture candidate, preserving original art and GLB geometry."""
import hashlib
import io
import json
import struct
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
RESOURCES = PROJECT / 'assets/resources'
REVIEW = PROJECT.parents[1] / 'source-art/performance/mobile-hair-textures-v1'
SOURCE_ART = PROJECT.parents[1] / 'source-art/characters'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    names = ['actors/raphael/raphael-polish.glb'] + [
        f'actors/hairstyles-v3/textures/redesigned-{name}-color.png'
        for name in ('curly', 'dante', 'nero', 'vergil')]
    candidate = REVIEW / 'candidate'
    # The original review copies are byte-identical to these retained art sources.
    # Pin their hashes to the existing review before generating any candidates.
    sources = {names[0]: SOURCE_ART / '3d-locomotion-v9/raphael-polish.glb'}
    sources.update({name: SOURCE_ART / '3d-hairstyles-v3/textures' / Path(name).name
                    for name in names[1:]})
    baseline = json.loads((REVIEW / 'review.json').read_text(encoding='utf-8'))
    reviewed = {item['resource']: item['originalSha256'] for item in baseline['files']}
    for name in names:
        target = sources[name]
        old = target.read_bytes()
        if digest(old) != reviewed.get(name):
            raise ValueError('Original artwork no longer matches the review baseline: ' + name)
        # Refuse stale candidates after an artist has changed either source or runtime art.
        current = (RESOURCES / name).read_bytes()
        prior = candidate / name
        if current != old and (not prior.exists() or current != prior.read_bytes()):
            raise ValueError('Artwork changed since this review baseline: ' + name)
    raw = sources[names[0]].read_bytes()
    if raw[:4] != b'glTF' or struct.unpack_from('<I', raw, 4)[0] != 2:
        raise ValueError('Expected GLB 2.0')
    length = struct.unpack_from('<I', raw, 12)[0]
    data = json.loads(raw[20:20 + length])
    blob = raw[28 + length:]
    if len(data['buffers']) != 1:
        raise ValueError('Expected one embedded binary buffer')
    replacements, expected = {}, {}
    for name in names[1:]:
        image = Image.open(sources[name]).convert('RGBA')
        if image.size != (2048, 2048):
            raise ValueError('Unexpected hair atlas dimensions: ' + name)
        expected[digest(image.tobytes())] = name
        image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
        stream = io.BytesIO()
        image.save(stream, format='PNG', optimize=True)
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(stream.getvalue())
    for image in data['images']:
        if 'bufferView' not in image:
            continue
        index = image['bufferView']
        view = data['bufferViews'][index]
        start = view.get('byteOffset', 0)
        original = blob[start:start + view['byteLength']]
        decoded = Image.open(io.BytesIO(original)).convert('RGBA')
        name = expected.get(digest(decoded.tobytes()))
        if name:
            replacements[index] = (candidate / name).read_bytes()
    if len(replacements) != 4:
        raise ValueError('The four embedded hair atlases must exactly match their external runtime PNGs')
    rebuilt = bytearray()
    untouched = 0
    for index, view in enumerate(data['bufferViews']):
        if view.get('buffer', 0) != 0:
            raise ValueError('Unexpected external buffer')
        start = view.get('byteOffset', 0)
        original = blob[start:start + view['byteLength']]
        payload = replacements.get(index, original)
        rebuilt.extend(b'\0' * (-len(rebuilt) % 4))
        view['byteOffset'], view['byteLength'] = len(rebuilt), len(payload)
        rebuilt.extend(payload)
        if index not in replacements:
            assert rebuilt[view['byteOffset']:view['byteOffset'] + view['byteLength']] == original
            untouched += 1
    data['buffers'][0]['byteLength'] = len(rebuilt)
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    rebuilt.extend(b'\0' * (-len(rebuilt) % 4))
    output = (struct.pack('<III', 0x46546C67, 2, 28 + len(encoded) + len(rebuilt))
              + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
              + struct.pack('<II', len(rebuilt), 0x004E4942) + rebuilt)
    target = candidate / names[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(output)
    review = {'method': 'Pillow RGBA LANCZOS 2048 to 1024; embedded and external pixels match exactly.',
              'source': 'Current approved runtime art; no generative editing.',
              'unchangedGeometryBufferViews': untouched, 'modifiedImageBufferViews': sorted(replacements),
              'geometrySkeletonAnimationChanged': False, 'visualAcceptance': 'pending-runtime-review',
              'estimatedFourAtlasMipmappedGpuBytesBefore': 4 * 22369620,
              'estimatedFourAtlasMipmappedGpuBytesAfter': 4 * 5592404,
              'files': [{'resource': name, 'originalSha256': digest(sources[name].read_bytes()),
                         'candidateSha256': digest((candidate / name).read_bytes())} for name in names]}
    (REVIEW / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': str(candidate), 'preservedBufferViews': untouched, 'images': len(replacements)}))


if __name__ == '__main__':
    prepare()
