"""Make a lightweight loading-only preview; preserve the full source artwork."""
import hashlib
import io
import json
import uuid
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / 'assets/resources'


def prepare():
    source = ROOT / 'ui/loading/stonebridge-valley.png'
    target = ROOT / 'ui/loading/stonebridge-valley-preview.jpg'
    with Image.open(source) as image:
        image = image.convert('RGB')
        image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        size = image.size
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=90, optimize=True, progressive=False)
    content = output.getvalue()
    if not target.exists() or target.read_bytes() != content:
        target.write_bytes(content)
    meta_path = target.with_name(target.name + '.meta')
    if not meta_path.exists():
        meta = json.loads(source.with_name(source.name + '.meta').read_text(encoding='utf-8'))
        previous = meta['uuid']
        current = str(uuid.uuid5(uuid.NAMESPACE_URL, 'singularity/loading-preview-v1'))
        def convert(value):
            if isinstance(value, str):
                return value.replace(previous, current).replace('stonebridge-valley', 'stonebridge-valley-preview')
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {key: size[0] if key in ('width', 'rawWidth') else size[1] if key in ('height', 'rawHeight') else convert(item) for key, item in value.items()}
            return value
        meta = convert(meta)
        meta['files'] = ['.json', '.jpg']
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sourceBytes': source.stat().st_size, 'previewBytes': len(content),
                      'previewSize': size, 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'previewSha256': hashlib.sha256(content).hexdigest()}))


if __name__ == '__main__':
    prepare()
