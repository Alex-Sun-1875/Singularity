# 四款发型细修 v3

> 当前背弓与箭筒的校准另见 [贴背修正](../../weapons/3d-bow-carry-v2/README.md)。发型与武器导出均复用该校准；安装外观包前需用当前运行时代码重新构建。

本轮承接 [v2](../3d-hairstyles-v2/README.md)，范围经用户确认是当前银白卷发、但丁、尼禄、维吉尔四款。重点修正“但丁鬓角太厚重”，同时整理另外三款的发际线、额角、鬓角与后颈收尾。

- **但丁：** 耳前发片按原生头部曲面减薄，下缘收轻；鬓角细束缩短并减窄，额前与耳前补束改为更薄的截面。中长分帘和后颈覆盖继续保留。
- **银白卷发：** 保留 2D 稿的大 S 卷走向；耳前细束缩短、减细，减少低处多余尖尾，保留后颈长度。
- **尼禄：** 继续使用已下移的发际线；减少前缘过大的齿状起伏，耳前、发梢细束改为短而轻的收尾。
- **维吉尔：** 保留后梳方向与已补齐的额角；鬓角贴合头型并向耳后收束，减轻后颈零散尖条。

取根改用现有 Blender BVH 的外侧射线，剔除内表面、皮肤内或颈前低处的不合适根部；发束路径保持皮肤间隙。沿用项目现有 Blender、Pillow、SciPy、Cocos 管线，无新依赖或下载。颜色与原有发流参考继续复用既有素材，本轮没有新生图，也没有使用被否决的发型库模型。

可编辑文件：[raphael.blend](raphael.blend)、[构建入口](reproject-rebuild.py)；游戏导出：[raphael-polish.glb](raphael-polish.glb)、[manifest.json](manifest.json)。脸、衣服、武器、骨骼和原有 14 组动作继续共用。

实际效果：[四款前/侧/后](runtime/hairstyles-all-views.jpg)、[相同镜头前后对比](runtime/hairstyles-before-after.jpg)、[但丁耳前近景](runtime/dante-temple-comparison.jpg)、[八方向旋转](runtime/hairstyles-turntable.gif)。[本地游戏](http://127.0.0.1:7469/?view=2d&player=3d&hair=dante&revision=hairstyles-v3-refined) 中按 **B → 发型** 切换。

检查记录：[保存后源文件](source-verification.json)、[选择与头罩](runtime/selection/report.json)、[美术观察](art-review.json)、[接入](install-record.json)、[本地入口](runtime/canonical-smoke.json)。工程通过、实际渲染检查和用户美术认可分开记录，不标记为用户已经验收。

2D 权威与既有云端四视图的完整来源沿用 [v2 来源记录](../3d-hairstyles-v2/README.md)。未采用的条带、体积发束与发型库试验仍保留在原目录，不打入本轮资源。

当前走跑姿势已参照 2D 继续调整，跑步保留抬腿并增加上身整体前倾，最新可编辑动作来源与正常速度演示见 [locomotion-v7](../3d-locomotion-v7/README.md)。本目录保留外观来源；重导出会通过适配器复用 walk / walk_staff / run / run_staff。
