# 战士技能动态稿与四套配色候选

**此稿已按用户最新要求迭代为淡色、亮芯不透明的冲击波剑气。实体材质版本仅作历史存档，后续以 [warrior-aura-v8](../warrior-aura-v8/README.md) 为准。**

按用户指定的 warrior-impact-v6 刀锋造型展开。用户先要求青蓝钢刃，查看后要求重新给出几个配色候选，当前配色尚未选定。

[四配色同步动图](media/palette-comparison.gif) · [完整配色对照视频](media/palette-comparison.mp4) · [攻击静态对照](media/palette-attack.jpg) · [护盾静态对照](media/palette-guard.jpg)

| 候选 | 配色 | 动图 |
| --- | --- | --- |
| A | 银白钢刃，银灰刀面与深灰蓝暗边 | [单独预览](media/palette-A.gif) |
| B | 赤金钢刃，赤金主刃与暗红刀背 | [单独预览](media/palette-B.gif) |
| C | 暖金钢刃，金色刀面与深棕暗边 | [单独预览](media/palette-C.gif) |
| D | 银紫钢刃，银紫主刃与深紫暗边 | [单独预览](media/palette-D.gif) |

四个候选使用同一份原始美术做确定性颜色处理。每个动画帧只推进一次真实 Cocos 3D 动作，随后暂停时间，依次替换四套刀锋与屏障纹理渲染，保证人物、姿势、靶位和镜头一致。对照采用断空斩及铁誓壁垒，视频为 30 fps 原速，循环动图按 15 fps 保留原始播放时长。

四版的颜色数据见 [候选配色参数](palette-candidates.json)。新增护盾采用云端 OpenAI image_gen 内置工具生成，完整提示词见 [护盾素材提示词](guard-prompt.txt)；后续四套配色由本地确定性色彩处理得到。

进攻技能使用横斩、纵劈与短促交汇反馈。护盾采用新绘制的三片式屏障。原始刀锋沿用 v6 的云端 OpenAI image_gen 画稿；护盾同样通过云端 image_gen 生成，提示词保存在 `guard-prompt.txt`。用户选择青蓝后及本轮四种候选的颜色处理由 Pillow / NumPy 完成，记录在 `palette.json`、`palette-candidates.json` 和对应处理脚本中。

整套动作形态已经在独立审稿预览中录制，包括普攻三连、断空斩、破军突袭、铁誓壁垒、裂地审判、破晓裁决，以及战艺精通、铁誓不屈的真实触发演示。当前交付重点是用户最新要求的配色候选，整套动作仍在等待配色选择。

所有候选模块只由本机录制器在内存中替换，未写入正式游戏。动画与真实技能事件来自同一份冻结的当前 3D Cocos 导出。护盾受击来自训练敌人的实际攻击，被动通过实际技能条件触发。背景像素一致性、事件、输入与媒体指纹见 `palette-provenance.json`。这是设计审稿，尚未取得本轮美术确认，也未进行 TapTap 真机性能验收。
