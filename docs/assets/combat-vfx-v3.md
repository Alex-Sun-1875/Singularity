# 第一章战斗特效 v3

2026-11-11 火系普攻与五个技能的最新重做见 [火系表现 v7](fire-vfx-v7.md)，方向为用户确认的亮火核、翻卷爆燃与暗红外焰。v4 观感已被用户否定；下方火系素材及截图保留为历史。

2026-11-10 后续已实现[按技能实际范围绘制的连击与火系优化](../design/skill-vfx-range-integration-v1.md)：共享近战刃面、三段原生骨骼动作、透明火舌，以及圆盘／矩形／走廊边界约束。下文保留2026-11-08材质迭代的阶段数据。

最新交互修订见 [蓝色近邻雷网与同箭连穿](combat-connections-v4.md)：雷电已改蓝色互连闭网，BOW02 已按用户明确选择改为同一支箭转向连穿。下文的分裂箭描述和 b5871 截图为历史迭代，不能作为当前默认包的行为。

2026-11-08。本轮针对“效果没有贴近设计稿、近战像远程、抬手与释放衔接不足”的反馈，重新核对正常战斗镜头中的材质、轮廓、空间层次与动作时刻。当前记录覆盖代表技能和连续运行样例；生成成功、运行检查和美术验收分别记录。

## 对稿依据与实际调整

| 系别 | 本轮依据 | 调整 |
| --- | --- | --- |
| WAR | [v1 近身刃弧](../../source-art/skills/pure-skills-v1/evolution-war.png) | 银白锋、透明银金细纹与窄亮刃分层，曲面跟随近身挥砍。破军战技继续使用近战扇形、真实突进停止点与落刃范围。 |
| BOW | [combat-bow](../../source-art/skills/pure-skills-v2/combat-bow.png) | 保留实际箭体、首击后子箭和已飞过的弯曲路径；路径延续到实际接触后 0.24 秒，未来路径不参与显示。 |
| FIR | [火焰 redesign-v4](../../source-art/skills/pure-skills-v2/combat-fir-redesign-v4.png) | 爆燃由一张横向拉扁的整云改为真实 XZ 错深的五层卷焰，保持各裁片比例、地形脚锚与角色穿插。 |
| THU | [combat-thu](../../source-art/skills/pure-skills-v2/combat-thu.png) | 冷白细裂主干、电蓝柔边、有限细枝与真实命中接点分开组织，替换稀疏大折线和硬边宽色带。 |

人物继续使用已有[准备、抬手、释放、连段回势与收势](action-sequence-v1.md)。特效发射端保留手部锚点与短暂衔接，释放和实际有效段仍服从同一动作时钟。表现只读取权威事件、弹体和已解析几何。

## 素材来源与原生接入

近战 `steel-ribbon` 由云端 OpenAI image_gen 生成透明原图，保留[完整提示词](../../source-art/skills/pure-skills-v2/melee-material-v3/prompt.txt)、[原始输出](../../source-art/skills/pure-skills-v2/melee-material-v3/generated-strip.png)及[来源与 SHA256](../../source-art/skills/pure-skills-v2/melee-material-v3/provenance.json)。[Pillow 派生脚本](../../tools/make-melee-material-v3.py)完成裁切、灰雾透明抑制、曝光和缩放，接入已有透明曲面与独立加法亮刃；生成结果不直接作为美术通过凭证。

火焰复用已保存的云端四相原图与[提示词](../../source-art/skills/pure-skills-v2/fire-volume-v2/prompt.txt)，由 [derive-lobes.py](../../source-art/skills/pure-skills-v2/fire-volume-v2/derive-lobes.py)确定性裁成后左高卷、后右卷冠、中心压力层、前左低卷和前右低卷。各层采用真实 XZ 脚锚和相位错开，四相交叉淡化约 43 毫秒；单次体积火最多七张卡片，共享 quad，池上限 64。[派生来源](../../source-art/skills/pure-skills-v2/fire-volume-v2/lobe-provenance.json)与[空间、时间迭代审阅](../../source-art/skills/pure-skills-v2/fire-volume-v2/LAYERED-RUNTIME.md)独立保留。

雷电继续复用 Cocos 3.8.8 原生 Line、CurveRange 和内置粒子材质。显式白纹理消除默认 `119/255` 灰纹理的亮度损耗；[确定性 Gaussian 软边纹理](../../src/cocos/assets/resources/vfx/production/ribbon-masks-v1.source.json)提供柔晕。蓝干、白芯、软晕采用不同材质与排序，池复用时恢复纹理和 priority，敌方预警优先。当前接入沿用项目现有依赖和引擎组件。

两项原生 Line 约束已修正：

- 每条主干最多 99 段、含端点 100 点，符合引擎固定容量，最大索引数 594。
- 两点路径使用 taper 时补为九个采样点。原生 Line 只在路径顶点读取宽度曲线，原先两端都取到 `.001`，会使交叉斩、竖刃等有效刀光消失。

## 当前运行证据

当前默认包已重建为 `http://127.0.0.1:7469/?view=2d`，实际加载 `index.b5871.js`。最终包的[四系代表帧](../../src/cocos/test-results/vfx-art-redesign-v3/current-four-families.jpg)、[同镜头前后对比](../../src/cocos/test-results/vfx-art-redesign-v3/before-after.jpg)和[原速近战连段](../../src/cocos/test-results/vfx-art-redesign-v3/live/war-combo-live.gif)均来自真实 Cocos 渲染；拼版只裁切和缩放，未修改角色、地面或效果像素。

| 证据 | 已确认内容 |
| --- | --- |
| [同镜头实际施放报告](../../src/cocos/test-results/vfx-art-redesign-v3/after/actual-render-report.json) | 真实 GameSession 技能、释放边界、代表接触与池复用；运行异常 0。每个受控步让出真实渲染帧，原生粒子正常推进。 |
| [12 场连续实机序列](../../src/cocos/test-results/vfx-art-redesign-v3/live/actual-sequences.json) | 最终 b5871，480 个状态采样、378 个实际录屏帧；抬手、释放、连段、收势与效果连续观察，异常及失败请求均 0。[12 个 GIF](../../src/cocos/test-results/vfx-art-redesign-v3/live/animation-artifacts.json)按原始 CDP 时间戳播放，没有新增中间帧或慢放。 |
| [连续火带及八方位](../../src/cocos/test-results/fire-ribbon-angle-review/ribbon-review.json) | 最终 b5871 的真实火墙/波前与同 renderer 八方位方向审计；无串团、侧向消失或浏览器异常。方向审计不冒充额外实际伤害。 |
| [THU02 材质与雷网报告](../../src/cocos/test-results/ribbon-material-v2-graph/actual-renderer-review.json) | 88 条 Line，最多 88 点、522 个索引；软晕、蓝干、白芯排序及重新激活复用正常。 |
| [THU01 最长真实长线报告](../../src/cocos/test-results/ribbon-material-v2-long/actual-renderer-review.json) | 12、13、14、16、18、20m 的六个真实目标均受伤；66 条 Line，最多 100 点、594 个索引，无 WebGL、console 或页面异常，复用失配 0。 |

[本轮截图与原速序列目录](../../src/cocos/test-results/vfx-art-redesign-v3/)保留改前、迭代和当前画面；[雷网代表帧](../../src/cocos/test-results/ribbon-material-v2-graph/new-native-material.png)与[20m 长线代表帧](../../src/cocos/test-results/ribbon-material-v2-long/new-native-material.png)来自真实渲染。同一几何和时刻的材质 A/B 仅用于判断材质改善，不能冒充完整旧版本对比。

## 最终代表审阅

最终 `b5871` 中，[突进交叉斩](../../src/cocos/test-results/vfx-art-redesign-v3/after/phone-war-rush-cross-late.png)和[落刀](../../src/cocos/test-results/vfx-art-redesign-v3/after/phone-war-ground-impact.png)已经接入同源纹理斜刃与稳定的窄白热芯；[原速突进](../../src/cocos/test-results/vfx-art-redesign-v3/live/rush-strike-live.gif)可见两拍刃光及退去。普通挥斩、终结连斩保留透明残锋，消除灰色硬片，未出现不透明白大片。火墙和推进火浪使用专门的连续低卷焰带，双排错缝并在真实 depth 内处理侧向观看，完全不再为每段重复整团爆炸；[八方位实图](../../src/cocos/test-results/fire-ribbon-angle-review/eight-angle-contact.jpg)可复核。

类型检查、本地 Cocos 构建及现有 95 项检查通过，没有新增测试依赖或正式测试用例。最终包同镜头施放保留七项释放边界、WAR 近身实际命中、敌预警优先和清池验证；近战没有飞刃弹体。此前 `6e061` 的淡刀/高塔火、`a39fc` 的弱交叉/竖刃与 `90a41` 的旧火墙均保留为迭代证据，不能冒充最终画面。雷电 20m 独立检验来自 `90a41`，相关雷电代码与最终包相同。

当前代表画面仍可能有细金丝密度、局部残留与设计稿存在差异。以上是代理对代表样例的实现与美术审阅，尚未覆盖全部 150 阶逐项外观，也未宣称用户验收通过；实体手机的帧率与持续负载仍待测量。
