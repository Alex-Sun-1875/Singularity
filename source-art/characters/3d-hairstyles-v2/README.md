# 发型重整 v2

> 后续四款细修、但丁鬓角减薄见 [v3](../3d-hairstyles-v3/README.md)。本目录保留上一轮模型和实际对照，作为细修前的参照。

针对用户指出的“与 2D 不一致、侧脑不好看”，以[已定稿的银白卷发四视图](../2d-concepts/identity-reference-v1/head-identity-master.png)为卷发权威，重新适配四款头发的表面、纹理分区与耳侧、后脑收尾。脸、身体、服装、武器、骨骼和原有 14 组动作共用；这是可切换的 3D 网格，不是替换人物的概念图。

本轮不再仅整体缩窄：去掉造成纹理重叠的细碎法线投射，改为连贯的头部四区投射；取消错误的后视图冠部叠印，重新压低卷发冠部、收薄但丁耳后和后颈、收紧两款短发的鬓角及后脑。在贴合底层上分别加入短的独立锥形发束，保留参考图的透明发丝边缘。四款仍分别绑定原 Head 骨骼，每次只显示一款。

按随后“鬓角、前额、脑后，并按发型遮住脖子”的反馈，分别整理额前分束和耳前过渡：卷发、但丁的后缘向下延至领口附近，后部曲面贴合颈后；尼禄保持渐短收尾，维吉尔把后梳层次延向后颈。长发的额外尖尾限制在耳后区域，避免落到颈前。另检查了卷发、但丁跑动及拉弓时的后颈覆盖；14 组动作仍逐曲线比对保留。

按“其他款也处理鬓角、前额，发际线太高”的补充，四款分别下移实际额前边界；尼禄、维吉尔幅度更大，并补齐额角、下接耳前，细束随新的发际线重新定位。冠部与脸部保持原有尺寸，纹理沿原有发流坐标重新烘焙。

可编辑源文件：[raphael.blend](raphael.blend)；游戏文件：[raphael-polish.glb](raphael-polish.glb)、[manifest.json](manifest.json)；重建入口：[reproject-rebuild.py](reproject-rebuild.py)。复用项目现有 Blender、Pillow、SciPy 与 Cocos 渲染流程，无新增依赖、测试框架或运行时发型库。

实际渲染：[额前/侧面/后颈](runtime/hairstyles-all-views.jpg)、[后颈四款](runtime/hairstyles-back.jpg)、[同镜头前后对比](runtime/hairstyles-before-after.jpg)、[八方向转动](runtime/hairstyles-turntable.gif)。游戏里按 **B → 发型** 切换，可拖动或用转向按钮查看头部。此前选择记忆、头罩遮挡恢复和移动端入口继续共用。

核验记录：[保存后源文件检查](source-verification.json)、[选择与头罩操作](runtime/selection/report.json)、[美术观察记录](art-review.json)、[接入记录](install-record.json)。工程检查与用户美术认可分开；当前呈现为本轮修改候选，不标记为用户已经验收。

## 素材来源与未采用的试验

最终头发继续使用项目原有银白卷发参考，以及 [v1](../3d-hairstyles-v1/README.md) 中已生成的但丁、尼禄、维吉尔四视图与提示词记录。新一轮网格编辑、投射、透明通道和排版为本地确定性处理；没有新下载、提取《鬼泣》模型。

- 本轮曾用云端 OpenAI image_gen 生成发束图集：[原始输出](hair-card-atlas-raw.png)、[提示词](generation-prompt.txt)、[必要参考局部](silver-hair-reference.png)。图像生成完成；实际条带/体积发束试装的走向与密度未达到 2D 稿要求，**未用于最终游戏模型**。构建入口 `build-groom.py` 与 `runtime/pilot*` 留作试验记录。
- 本地 MakeHuman 发型库试装由已有适配器完成，来源与许可证保存在 [library-sources.json](library-sources.json)，实际效果在 `runtime/authored`；因贴合缺口、侧面及轮廓不符，**未用于最终模型，也不把这些贴图打进最终发型资源目录**。`library-rebuild.py` 保留以便复现试验。

本地预览：[3D 人物](http://127.0.0.1:7469/?view=2d&player=3d&revision=hairstyles-v2-redesigned)。
