# 拉斐尔：2D 银白卷发重建 v6

目标：按照已验收的 2D 设计，重做可随原生骨架连续转身的 3D 发型。保留现有脸型、身体、服装、武器和动作。

- 设计依据：[原始四视图](../2d-concepts/identity-reference-v1/head-identity-master.png)。
- [生成提示词](generation-prompt.txt)；[来源记录](texture-provenance.json)。仅用云端 OpenAI image_gen 提取原稿的头发，不生成替换脸型。
- 四视图遮罩恢复卷发外轮廓，并以圆润头型约束俯视截面，避免正交视图相交产生方形头顶。使用现有 Pillow、SciPy 适配，Blender 原生 OpenVDB 重网格、平滑和减面完成发型表面。
- 多视角投射保留原稿的卷发纹理；法线方向与有效遮罩控制衔接。原稿没有俯视图，头顶复用后视卷发纹理。
- 2048 像素独立纹理，细微卷发起伏，完整 UV 边缘扩色；Cocos 线性 mip 过滤与 4 倍各向异性过滤，避免缩小时出现黑缝、细节闪烁。
- 原 Head 骨骼绑定，不新增物理毛发系统。

模型：[raphael.blend](raphael.blend)、[游戏 GLB](raphael-polish.glb)。运行资源位置由 [manifest](manifest.json) 记录。

生成状态：透明发型四视图提取完成。美术检查：已查看实际 Cocos 近景、正常俯视和动作抽样；13 个视图、180 帧动作录制完成。早期 pilot 目录为未接入的试作。详细记录见 [art-review.json](art-review.json)。

已接入 [本地游戏预览](http://127.0.0.1:7469/?view=2d&player=3d&revision=reference-silver-curls-v6)。[实际四视图](runtime/silver-curls-views.jpg)、[跑步与射箭动画](runtime/silver-curls-actions.gif)、[八方向视图](runtime/silver-curls-turntable.gif)。本地入口复核：新发型、2048 纹理、12 级 mip、13 个有效蒙皮网格、14 个动作均加载，无页面错误；默认 2D 入口也通过检查。见 [canonical-smoke.json](runtime/canonical-smoke.json)。

验证：复用项目实际 Cocos RenderTexture 与动作录制入口；几何、UV、权重、非头发材质、14 组动作曲线及绑定矩阵的保存后校验见 source-verification.json。无新增测试框架或依赖。

复现：`python prepare.py` → Blender 后台执行 `build.py`（内部调用本地像素扩色）→ `stage.py` → 临时 Cocos 镜像 `Build-Local.ps1` → `capture-appearance.cjs` / `capture-actions.cjs`。只在观察实际效果后执行安装。
