# 战士剑气 · 银青半透明加厚版

**用户随后反馈交叉角度仍显得更大，且要求月牙轮廓与重新选色。当前修订见 [warrior-crescent-v11](../warrior-crescent-v11/README.md)。本目录仅保留此前波面稿。**

按本轮反馈，沿用最初冲击波的弧形波前、回卷波身和向前推进的尾流：配色改为浅银青，波前偏银白、波身偏青；保留透明混合与逐渐消散。波身法向厚度提高至上一版的 1.65 倍，前后深度提高至 1.22 倍。交叉斩两道波面绕前进轴分别倾斜 ±20°，交叉锐角由接近 90° 收至 40°。这是空间角度，画面角度随斜向镜头投影变化。

[整套原速动画](media/warrior-all-skills.mp4) · [半速交叉斩细节](media/shockwave-detail.gif) · [上一版与本轮对照](media/design-comparison.gif) · [整套总览](media/all-skills-overview.jpg)

| 动作或技能 | 单独动图 |
| --- | --- |
| 普攻三连 | [普攻](media/basic_war.gif) |
| 断空斩 | [断空斩](media/war_01.gif) |
| 破军突袭 | [破军突袭](media/war_02.gif) |
| 铁誓壁垒 | [铁誓壁垒](media/war_03.gif) |
| 裂地审判 | [裂地审判](media/war_04.gif) |
| 破晓裁决 | [破晓裁决](media/war_05.gif) |
| 战艺精通 | [战艺精通](media/war_p1.gif) |
| 铁誓不屈 | [铁誓不屈](media/war_p2.gif) |

单层波前材质峰值不透明度保持约 55%，波身和尾流继续减淡；交汇处自然叠亮。加厚通过卷曲波面的空间尺度调整。单独的落地重劈仍保留向下压落，40° 夹角用于交叉斩波面。战士没有装饰法阵。

复用上一版冻结 Cocos 3D 场景、原生角色骨骼、实际技能释放和命中事件。逻辑和骨骼按 60 Hz 推进，原速视频以 30 fps 输出；细节和对照为 0.5×。本轮仅对历史云端 image_gen 纹理作确定性银青映射，透明通道逐字节保留，没有新增生成式编辑；来源与处理参数见 [processing.json](processing.json)，原始图稿和历史提示词保留在 [v8](../warrior-aura-v8/README.md)。

这是独立设计预览，未接入正式游戏。录制与导出验证见 `provenance.json` 和 `comparison-verification.json`。生成完成与美术验收分开记录，本轮仍待用户审阅，TapTap 真机性能未验证。
