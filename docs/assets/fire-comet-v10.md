# 焚星坠落：彗星轮廓 v10

2026-11-11。按用户要求，落体改为连续的「炽亮圆头＋向后渐细长焰尾」，火焰包住核心，保持浓橙、深红和少量暖白芯，不出现裸露岩块或黑烟。触地仍接原有真实爆燃事件，施法准备时间、目标、伤害和段数不变；四系范围辅助显示保持移除。

专用透明火体使用内置云端 OpenAI image_gen 生成，没有上传参考图。原始图、[最终提示词](../../source-art/skills/fire-comet-v10/prompt.txt)、[来源与验收状态](../../source-art/skills/fire-comet-v10/provenance.json)保存于项目。它是透明贴图，不是 3D 流体模拟。Pillow 使用预乘透明缩放；NumPy 仅位移尾部像素得到四个相位，保留头部和锚点，原始图不改写。

`SkillFireSprites.drawComet` 使用现有透明卡片池，对齐相机平面内的下坠方向，以火头为旋转与位置锚点。`SkillMeteorBody` 只维护原有落体时钟与位置，不再创建、预加载或绘制石块网格和岩石材质。火头和长尾在同一张纹理内连续，不再是石头后挂一束火。四个尾部相位使用已有密度保持切相方式；沿用原有 64 张卡片上限与帧率设置。

## 普攻短尾与离手 v12

按用户反馈，保留普攻火头尺寸，仅将尾部最长压短到此前的一半。复用同一 atlas，通过五档共享原生网格只压缩尾部；不增加卡片、图片或自定义 shader。尾焰根据实际飞行距离和当前手部位置逐渐形成，出生阶段保留空隙。普攻从固定释放位置沿自由飞行直线推进，移除原来的 0.14 秒贴手过渡；实际射线端点、速度、伤害和命中规则沿用现有值。陨火保持完整长尾。

默认试玩现为 `concept-2d-fire-basic-release-v12a`，主包 `index.8cb39.js`。类型检查与本地构建通过；手机和桌面各八方向、每方向十二个实际渲染帧检查通过，尾端始终离开手部，投影轨迹保持直线，飞行和命中无运行报错。普通与测试入口均已验证加载新版，配置帧率仍为 60。

[出手／离手／飞行代表帧](../../src/cocos/test-results/fire-basic-release-v12/actual-contact.jpg)、[原速实际施放](../../src/cocos/test-results/fire-basic-release-v12/actual-play.webp)与[运行记录](../../src/cocos/test-results/fire-basic-release-v12/validation.json)分别保存。代表样例的内部审阅不代替用户美术确认；本轮为 Web 预览，TapTap 与目标 Android 设备尚待验收。

## 普攻缩小复用 v11（历史）

用户随后要求普攻使用类似效果、尺寸更小。火系法杖普攻现直接复用同一 `drawComet` 与 `fire-comet-v10` atlas，火头、长尾轮廓、浓橙深红与动画保持一致；尺寸为五级落体的 30%。火头沿用实际手部／弹体锚点，尾部随飞行方向展开，移除原来独立的线状拖尾，不再额外画分离圆芯。命中仍读取原有结果与小型接触爆燃，速度、范围、伤害及陨火尺寸不变。此项没有生成或预加载新图，也没有增加卡片上限或修改帧率。

`v11` 构建为 `concept-2d-fire-basic-comet-v11`，主包 `index.9fd6c.js`；当时普通与测试入口均验证加载该版。类型检查、本地构建、手机和桌面实际普攻／陨火施放通过，无运行报错。普攻实际卡片使用同一纹理，宽高为五级落体的 30%，命中与清场正常，没有新增图片、材质引擎或运行依赖。既有 60 帧设置和四系范围辅助显示移除继续保留。

[普攻与陨火同镜头代表帧](../../src/cocos/test-results/fire-basic-comet-v11/actual-contact.jpg)、[原速实际施放](../../src/cocos/test-results/fire-basic-comet-v11/actual-play.webp)与[运行记录](../../src/cocos/test-results/fire-basic-comet-v11/validation.json)独立保存。

## v10 落体接入记录

`concept-2d-fire-comet-v10` 的主包为 `index.373a0.js`。当时普通与 `test=max` 入口均确认加载连续彗星模型，场景裸露岩块节点数为零，帧率设置为 60。

类型检查、Cocos 3.8.8 本地构建、手机 844×390 DPR3 和桌面代表施放通过，1／3／5 级施放无运行报错。八个方向、16 张实际卡片的火头锚点与方向检查通过，清场后卡片和落体均为零；四系 60 个预览状态保持没有辅助范围线。

[实际下坠与触地帧](../../src/cocos/test-results/fire-comet-v10/actual-contact.jpg)、[原速实际施放](../../src/cocos/test-results/fire-comet-v10/actual-play.webp)及[完整运行记录](../../src/cocos/test-results/fire-comet-v10/validation.json)分别保存，生成结果与实际游戏外观审阅分开记录。录屏沿用真实 CDP 时间戳，隔帧取样，没有生成中间帧。用户美术确认及 TapTap 真实 AppID、Android 目标设备验收仍待进行；本轮为本地 Web 预览。
