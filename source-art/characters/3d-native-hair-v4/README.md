# 原生短发细化

2026-11-09。按用户最新要求撤下长发试验，在当前原生 `Hair_SimpleParted` 上继续优化；脸、身体、服装和动作保留。

本轮保留原生短发的分缝与发束走向，微调头顶、前额与鬓角的控制点，再用 Blender 原生一级细分柔化折面并处理头皮间隙。没有替换人物、重新捏脸或添加另一套骨架。纹理参考项目 2D 稿的银白发丝、灰银暗部和柔和高光；短发轮廓仍来自原生模型，并非完整复刻 2D 稿的中长卷发几何。

## 发丝与材质

- 将原作者使用的三个 UV 岛整理为专用 1024×1024 图集，保留原有纹理走向，并由 Blender 原生烘焙原作者底色与切线法线。
- 使用内置云端 `image_gen.imagegen` 一次编辑发纹，输入只有该 UV 图集与必要的 2D 头发参考。完整[提示词](generation-prompt.txt)、[实际编辑输入](cloud-input-uv.png)、[原始生成结果](hair-cloud.png)保留；生成尺寸 1254×1254，运行底色与法线为 1024×1024，ORM 为 512×512。
- 本地保留原有发束主要明暗，按[局部遮罩](fine-detail-mask.png)合成细发丝；原 UV 透明通道保持一致，并对透明区域填充邻近颜色以避免 mip 接缝。原切线法线增加轻微细纹起伏，粗糙度加入细微变化，金属度保持 0。
- 脸、衣料、皮革、身体等贴图与材质记录没有改动。新生成纹理只用于头发，未调用本地生成模型、安装依赖或下载新模型。

原模型、原发型与原 PBR 图来自已安装 Quaternius Universal Base Characters 免费 Standard 包，CC0 许可。来源与归档校验见[已有资源记录](../library-kits/sources.json)。云端生成与美术检查分别记录于[纹理来源](texture-provenance.json)。

## 原件保护与实机检查

`stage.py`、`export.py` 复用项目现有 Blender 导入、烘焙与 glTF 导出能力；`verify-source.py` 重新打开最终源文件核对脸、身体、UV、蒙皮、服装材质、67 节点绑定和 14 条原始动作曲线。证明见[preservation.json](preservation.json)与[source-verification.json](source-verification.json)。

以 `runtime/after/` 的实际 Cocos 渲染为最终预览，使用相同灯光与机位对照修改前后，检查正侧背面与动作。云端 UV 图片不代表人物实机效果或用户美术验收。

当前源文件：[raphael.blend](raphael.blend)。运行导出：[raphael-polish.glb](raphael-polish.glb)。本轮仍使用既有 glTF 接入方式，不修改旧有效 FBX、游戏规则、武器、镜头或动作节奏。
