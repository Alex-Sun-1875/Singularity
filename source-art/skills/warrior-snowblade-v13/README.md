# 战士银白刀气 · 电视剧雪饮狂刀参考稿

**用户随后重新选用此前银白波前稿，并要求取消半透明、交叉钝角改为 120°。当前修订见 [warrior-reference120-v14](../warrior-reference120-v14/README.md)。本目录保留电视剧参考方向的历史稿。**

用户明确参考的是电视剧。本轮按《风云》中聂风雪饮狂刀的刀气，观察亮刃前伸、沿攻击方向拉长的气流与快速掠过的光痕。[参考片段约 3:14–3:16](https://www.bilibili.com/video/BV1dU4y1w7Cz/?p=16&t=194)，来源是含电视剧画面的解说剪辑，并非游戏录像或官方技法说明。观察时间、缩略图和借鉴范围见 [参考记录](references/sources.json)。

[整套原速动画](media/warrior-all-skills.mp4) · [断空斩半速细节](media/shockwave-detail.gif) · [突袭三段细节](media/triple-cross-detail.gif) · [上一版与本轮对照](media/design-comparison.gif) · [三段截帧](media/three-wave-stages.jpg) · [整套总览](media/all-skills-overview.jpg)

保持银色和较实的透明感，单层主体峰值不透明度约 78%，边缘和尾流继续柔化。刀气的亮刃先行，后面的气流从当前角色持剑手向移动波前拉长，以表现纵深；亮刃有局部柔光，内部有几条宽缓的流动纹理。能量仍有弧形、尖端和内凹轮廓。

三段分别突出横向刀气、纵向劈波、最终十字冲击，并沿用现有挥刀时序衔接：普攻三连逐次对应横、纵、十字；断空斩的首刀发出横向刀气，第二次出手接纵劈与十字；破晓裁决每个原生出手段各对应一道波前。单次释放内部的接续约 0.10 秒，三道波前有不同的位置。十字与三段是本项目沿用的用户要求，没有声称原剧采用相同的招式组合。护身、被动与贴地冲击保持各自用途，战士没有装饰法阵。

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

新增的[银白气流原图](texture-original.png)由内置云端 OpenAI image_gen 生成，[完整提示词](texture-prompt.txt)保存于本目录；没有把电视剧画面提供给生成模型或用作游戏纹理。保留原始透明 PNG，以 Pillow / NumPy 对流纹做连续 UV 整理、银色归一和透明边缘处理，输出 [blade.png](blade.png)；过程和哈希见 [texture-processing.json](texture-processing.json)。原图生成成功与美术验收分开记录，当前效果待用户审阅。

独立预览复用冻结的 Cocos 3D 场景、真实角色骨骼、实际技能事件、目标和镜头，逻辑与动作按 60 Hz 推进，原速媒体以 30 fps 输出，细节与对照标注 0.5×。仅替换审稿服务响应中的表现模块，没有改动正式游戏代码或增加伤害段数。媒体、事件、投影夹角、波前间距与输入指纹记录见 `provenance.json`、`comparison-verification.json`；TapTap 真机性能未验证。
