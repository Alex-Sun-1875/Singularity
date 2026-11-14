"""Deterministic silver tint and resize of Quaternius' own supplied hair maps."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
SOURCE = ROOT / 'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)'
OUT = BASE / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
rgb = np.asarray(Image.open(SOURCE / 'T_Hair_2_BaseColor.png').convert('RGB'), dtype=float)
gray = rgb @ np.array([.2126, .7152, .0722])
silver = (gray[:, :, None] - np.median(gray) + np.array([180, 186, 190])).clip(0, 255).astype('uint8')
Image.fromarray(silver).resize((1024, 1024), Image.Resampling.LANCZOS).save(OUT / 'long-silver.png')
normal = Image.open(SOURCE / 'T_Hair_2_Normal.png').convert('RGB').resize((1024, 1024), Image.Resampling.LANCZOS)
vec = np.asarray(normal, dtype=float) / 127.5 - 1
vec /= np.linalg.norm(vec, axis=2, keepdims=True).clip(.00001)
Image.fromarray(((vec * .5 + .5) * 255).clip(0, 255).astype('uint8')).save(OUT / 'long-normal.png')
records = [{'path': str((SOURCE / name).relative_to(ROOT)), 'sha256': hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()} for name in ['Hair_Long.gltf', 'Hair_Long.bin', 'T_Hair_2_BaseColor.png', 'T_Hair_2_Normal.png']]
report = {'publisher': 'Quaternius', 'source': 'https://quaternius.itch.io/universal-base-characters',
          'license': 'CC0-1.0', 'download': 'Reused installed official Standard archive; no new asset download',
          'processing': 'Pillow resize + luminance-preserving silver recolor; normal vector renormalization',
          'generativeEditing': False, 'sourceFiles': records,
          'runtimeMaps': [{'name': p.name, 'size': Image.open(p).size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.glob('*.png'))]}
(BASE / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('Prepared original hair PBR maps')
