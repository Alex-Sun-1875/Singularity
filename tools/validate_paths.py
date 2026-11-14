"""Validate every local path in data and art JSON manifests (relative to each JSON)."""
from pathlib import Path
import json, re
ROOT = Path(__file__).resolve().parents[1]
checked = set()

def walk(value, base, key=''):
    if isinstance(value, dict):
        for k, v in value.items(): walk(v, base, k)
    elif isinstance(value, list):
        for v in value: walk(v, base, key)
    elif isinstance(value, str):
        # Path fields contain filenames rather than narrative text or status values.
        if re.fullmatch(r'(?:\.\./|[\w-]+/)+[\w.-]+\.(?:json|png|glb|blend|py|docx)', value):
            p = (base / value).resolve()
            assert p.is_relative_to(ROOT), f'Path escapes repository: {value}'
            assert p.is_file(), f'Missing path in {base.relative_to(ROOT)}: {value}'
            checked.add(str(p.relative_to(ROOT)))
for folder in ['data', 'assets']:
    for p in (ROOT / folder).rglob('*.json'):
        walk(json.loads(p.read_text(encoding='utf-8')), p.parent)
print(f'All {len(checked)} unique referenced files exist within the repository.')
