# 运行发型贴图精简

2026-11-11。复用当前已验收的 Raphael 设计，使用 Pillow RGBA LANCZOS 将四张发型运行贴图从2048×2048缩放到1024×1024，并同步替换 GLB 内嵌的同像素图片。没有生成式编辑，也没有更换脸型、发型轮廓、UV、骨骼、权重或动作。

- 原始高分文件统一保留在 [v9 原 GLB](../../characters/3d-locomotion-v9/raphael-polish.glb) 与 [v3 四张发型 PNG](../../characters/3d-hairstyles-v3/textures/)。2026-11-15 已删除 `original/` 下五份字节完全相同的副本；制作脚本直接读取这些源文件，并核对既有 `review.json` 的原始 SHA-256。
- `candidate/`：确定性缩放候选；代表性运行验收后已接入 Cocos 运行资源。
- `review.json`：输入／输出SHA-256、修改的图片 bufferView、未改动的2655个二进制 bufferView及独立美术检查结论。
- [`prepare-mobile-hair-textures.py`](../../../src/cocos/tools/prepare-mobile-hair-textures.py)：复现候选。若美术在本次基线后另有修改，脚本会停止，避免旧候选覆盖新素材；脚本本身不自动安装候选。

四张RGBA8贴图按完整mipmap计算的理论GPU分配由约85.33降到21.33 MiB。GLB内嵌图和外部PNG继续通过现有像素／采样校验复用；没有靠关闭mipmap或修改材质采样参数换取这部分节省。

Curly、Nero的Cocos原生人物预览放大对照已检查：身份、轮廓与服装一致，细小纹理分辨率降低。证据为 `src/cocos/test-results/movement-hair-review.jpg`。这是本地运行美术检查；TapTap真机清晰度与发热仍需另行验收。
