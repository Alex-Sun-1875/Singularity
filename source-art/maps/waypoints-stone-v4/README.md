# 环境符印石 v4

本版保留为历史构建与检查过程，当前运行采用[古代符文传送阵版](../waypoints-runes-v8/README.md)。

本轮对应用户要求“再优化一下，看看博得之门的传送阵是怎么做的”，承接此前“更粗、更突出”及“太复杂”的反馈。此前 balanced-v3 保留作为历史对照。本轮为实际出口的环境呈现更新，不增加旅行目的地或改动解锁规则。

## 参考与取舍

- 实际普通传送点参考：[BG3 Wiki 幽暗地域实景](https://bg3.wiki/wiki/File:Underdark_Beach_Rune_Circle.png)、[PC Gamer 的游戏截图](https://www.pcgamer.com/baldurs-gate-3-waypoints-fast-travel/)。核对了固定石面、亮主印、较暗不对称辅助几何、局部紫色柔光的层级。
- 本机 BG3 安装只供结构研究：普通 waypoint helper 的 Glyph_GlowMesh_Waypoint_01 不随相机对齐；decal 与 glow mask 分离。没有将游戏原图、原符文、模型、shader 或代码加入游戏资源。EA 期幽暗地域截图仅作形态补充，不声称代表所有正式版场景。
- Gale 异常传送门的黑色洞口及厚能量边属于另一类效果，本轮未套用。静帧不能验证动画周期；当前 6.8 秒轻微柔光变化为本项目自己的选择。

## 实现

原创竖向魔印由云端 OpenAI image_gen 生成，提示词见 [prompt.txt](prompt.txt)，原件、尺寸、alpha 和 SHA 见 [generation.json](generation.json)。人工核对主印可读性后，以 Pillow 保留原透明通道缩放；另从 alpha 得到柔光纹理，从主印裁出门洞地嵌纹理。常规处理脚本为 `tools/model-pipeline/prepare_waypoint_stone.py`。生成成功与实际游戏美术验收分开登记。

立碑复用 Cocos 3.8.8 原生 box 网格拓扑和项目已有 bedrock 石材，向内削边、逐面明暗，无新增运行依赖或 shader。石碑固定世界朝向，符印贴在前表面；主印稳定，柔光单独绘制。撤掉旧的同纹横竖重复与出口双木牌。狭窄位置使用一块低矮嵌地石片和单个主印。

首个 `portal-stone-v1` 编译小样因竖向 UV 倒置、载体太平整而未通过美术验收。后续 `portal-stone-v2` 修正原生 quad 的 V 轴方向，将石身改为无方台座的断顶旧石、加宽削角和自然石脚，侧面加深、削角提亮；固定视觉 yaw 10°、scale(.85,1,1.58)，让石厚可见，实际全部顶点仍在原规划碰撞框内。复用原生 plane 和顶点 alpha 提供轻微脚下接触阴影。嵌地石片逐顶点通过 Cocos rayTriangle 贴合原 Ground，避免坡脚出现悬空平板；地嵌标签移到人物头部以上。纹理源没有重新生成。

`PortalPlacement` 在原有实际 dressing 后规划远离镜头的路边位置；原始出口、spawn、incoming entry、物件和敌人点保留净空。立碑脚印同时加入原生 BoxCollider 与 Navigation，无法保证原通路时退为无新增碰撞的 floor-inlay。`PortalHud` 保留原出口的距离、F/触摸、锁定和屏外方向提示，标签锚定当前载体。3D 模式也加载相同载体，防止出现不可见的新碰撞。

## 验收状态

- 生成：成功；透明图小样已人工查看。
- 源码：`npm run check` 通过；已有 navigation/terrain 检查由本轮放置审查复用。
- 放置规划：[placement-review.json](placement-review.json) 保留实际旧包 dressing 上的316立碑/4地嵌规划、全部640个出口与回程落点的前后导航状态、源码/采样SHA和代表点；早期源数据305/15不是最终计数，最终以新编译包实测为准。
- 实际构建、四处代表画面、全部区域与输入/销毁验收：进行中，以后续 build proof 和 runtime-review.json 为准。

BG3 参考文件及结构调查位于忽略的 `src/cocos/temp/bg3-reference/`。生产素材仅使用本项目原创生成符印与已有石材。
