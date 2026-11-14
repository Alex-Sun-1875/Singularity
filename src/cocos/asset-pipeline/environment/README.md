# CC0 environment adapter

Run from the repository root in PowerShell. Downloads are official Poly Haven
files with checked MD5 and recorded SHA-256. Runtime output contains only
derived compact geometry, texture maps, Cocos metadata and manifests.

```powershell
python src/cocos/asset-pipeline/environment/download.py
& src/.tools/blender-4.5.15-windows-x64/blender.exe -b --python src/cocos/asset-pipeline/environment/convert.py
python src/cocos/asset-pipeline/environment/pack.py
python src/cocos/asset-pipeline/environment/textures.py
python src/cocos/asset-pipeline/environment/metadata.py
```

The tree uses the source author's `tree_small_02_LOD1` object from the published
Blender file. Materials are separated before decimation so numerous disconnected
leaves cannot force the trunk to collapse into a few bad triangles. Authored
GeometryNodes leaf-cluster placements become standard two-triangle cards; the
whole runtime tree is 8,052 triangles with the source trunk and branches. Cutout alpha
comes from the official separate alpha map, not from the lossy GLTF JPG albedo.

`convert.py -- <key>` after Blender's `--` accepts selected keys and preserves
other converted models. The entire unpacked intermediate is temp-only.
`pack.py` converts it to a native Cocos BufferAsset and a small index JSON.

An optional offline review:

```powershell
& src/.tools/blender-4.5.15-windows-x64/blender.exe -b --python src/cocos/asset-pipeline/environment/render-review.py
```

No runtime dependency or test dependency is introduced. Python requests and
Pillow are authoring tools; Blender 4.5 LTS performs model conversion.
