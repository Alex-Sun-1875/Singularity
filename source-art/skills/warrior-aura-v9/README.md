# 战士剑气 · 半透明冲击波版

**用户本轮重新选用本稿造型。主体改实、交叉钝角 120° 的当前修订见 [warrior-reference120-v14](../warrior-reference120-v14/README.md)。本目录保留原银白透明稿；中间银青修订保存在 [v10](../warrior-silvercyan-v10/README.md)。**

按用户最新要求，剑气保留透明状态。每道波前的峰值不透明度约为 55%，波身和尾流进一步递减；交汇处自然叠亮。护身气幕也降低了密度，能透过气流看到人物、目标和地面。沿用上一版的冲击波推进、横纵交错、形状、淡色与动作节奏。

[整套原速动画](media/warrior-all-skills.mp4) · [半速细节](media/shockwave-detail.gif) · [透明度同帧对照](media/transparency-comparison.gif) · [对照静态图](media/transparency-comparison.jpg) · [整套总览](media/all-skills-overview.jpg)

| 动作或技能 | 动图 |
| --- | --- |
| 普攻三连 | [普攻](media/basic_war.gif) |
| 断空斩 | [断空斩](media/war_01.gif) |
| 破军突袭 | [破军突袭](media/war_02.gif) |
| 铁誓壁垒 | [铁誓壁垒](media/war_03.gif) |
| 裂地审判 | [裂地审判](media/war_04.gif) |
| 破晓裁决 | [破晓裁决](media/war_05.gif) |
| 战艺精通 | [战艺精通](media/war_p1.gif) |
| 铁誓不屈 | [铁誓不屈](media/war_p2.gif) |

原速合集为 30 fps，半速细节和透明度对照标注 0.5×。透明度对照在同一场景、同一骨骼姿态和同一模拟帧上改变波面材质透明度后以零时间步重绘，便于直接观察目标与地面的透出程度。

本轮复用 v8 的画稿和四种淡色参数，通过独立预览材质调整透明度，没有新增生成图像。历史素材来自云端 OpenAI image_gen，原始提示词保留在 `generation-prompt.txt`；其中旧的不透明要求是历史生成记录，当前显示以本轮半透明材质为准。素材处理与配色参数见 `processing.json`、`palette-candidates.json`。

这是独立 Cocos 3D 设计预览，未接入正式游戏。角色动作、技能命中、护盾受击和被动触发来自真实游戏会话。媒体与输入记录见 `provenance.json` 和 `opacity-verification.json`。用户尚未验收本轮效果，TapTap 真机性能未验证。
