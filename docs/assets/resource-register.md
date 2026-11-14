# 当前资源登记

2026-11-12 近战连斩载体替换为 135,728 字节的 `combos-native.glb`，绑定当前角色骨架，沿用主角色 GLB 导出参数；旧运行 FBX 已移除。使用已有 Quaternius UAL2 CC0 动作、本地 Blender 确定性适配；[导出来源与哈希](../../source-art/characters/player-melee-combo-v1/provenance.json)、[运行检查](warrior-foot-bind-v5.md)。

2026-11-11 发型运行贴图精简：四张2048×2048 RGBA图经Pillow确定性缩放为1024×1024，同步GLB内嵌图并继续校验纹理复用；2655个非图片二进制区段、模型、骨骼、UV和动作保留。高分原件、候选、哈希和独立美术验收见[运行贴图记录](../../source-art/performance/mobile-hair-textures-v1/README.md)。代表放大预览检查通过，TapTap真机清晰度待验收。

2026-11-10 运行素材新增：火焰4张512×512 RGBA火舌（PNG共509,392字节），云端内置OpenAI image_gen生成，Pillow执行裁切、透明衰减和脚锚对齐；[原图／提示词／哈希与审阅状态](../../source-art/skills/fire-runtime-v3/provenance.json)。近战新增936,588字节原生动作载体，使用已有Quaternius UAL2 CC0动作及本地Blender适配，[来源和导出哈希](../../source-art/characters/player-melee-combo-v1/provenance.json)。生成、美术检查、运行接入分别登记，[接入范围和验证](../design/skill-vfx-range-integration-v1.md)。

2026-11-10 近战连招强化v2：云端内置image_gen完成[三刀峰值图](../../source-art/skills/melee-combo-flair-v2/contact-peaks-v2.png)与[十二格分镜](../../source-art/skills/melee-combo-flair-v2/storyboard-v2.png)，另由Pillow制作[同尺寸前后对比](../../source-art/skills/melee-combo-flair-v2/before-after-v2.png)。三刀效果逐步强化银白主刃、交错残痕、金白爆点与低位尘环。静态概念和中文排版已检查，用户美术验收、真实动作帧与Cocos接入均未完成，未更新试玩构建。[提示词](../../source-art/skills/melee-combo-flair-v2/prompts/index.json) · [原图哈希与审阅](../../source-art/skills/melee-combo-flair-v2/provenance.json)。

2026-11-10 火系与近战连招方向：云端内置image_gen生成[火系1／3／5级对照](../../source-art/skills/fire-melee-direction-v1/fire-direction-v1.png)与[近战三刀分镜](../../source-art/skills/fire-melee-direction-v1/melee-combo-v1.png)各一张，原图不改像素，Pillow仅在外部增加中文说明带。均待用户审阅，不是动画序列帧、Cocos运行资源或真实判定图；未更新试玩构建。第三方游戏截图仅用于视觉研究，未交给生图、未接入项目资源。[来源与哈希](../../source-art/skills/fire-melee-direction-v1/provenance.json) · [研究资料](../../source-art/skills/fire-melee-direction-v1/research.json)。

2026-11-10 技能分级概念稿：云端内置 image_gen 完成10次生成／编辑，选出6张1—5级主板与1张火系过程板，中文说明由Pillow确定性排版。火系前版过淡与弓术目标数不符的过程稿保留为未选用；当前7张候选均待用户审阅，尚未接入Cocos、制作动画或作为发布素材。[图集](../../source-art/skills/rank-vfx-draft-v1/boards-overview.jpg) · [原图与提示词来源](../../source-art/skills/rank-vfx-draft-v1/provenance.json)。

2026-11-08 当前为**四系WAR/BOW/FIR/THU＋通用，共30技能、150阶**。奥术秘法暂撤、冰系职业移除，ARC/FRO各7技仅作历史保留；奥术不是当前待必须补完的项目。飞刃走廊与BOW_02分裂箭沿用最初原图结构，本轮另存四系强化候选；BOW_01/03/05仍走直线，雷电保留用户认可的既有`combat-thu.png`方向。四系加强材质层次、真实接触、短尾迹和逐级轻重节奏，不暗增伤害、段数或目标。

当前入口：[技能v2](../design/combat-skills-v2.md)、[空间规则v2](../design/skill-spatial-v2.md)、[特效v2](../design/skill-vfx-v2.md)、[97地点战斗v4](../design/world-combat-v4.md)、[74装备联动v4](../design/equipment-skills-v4.md)。人物1—40级、属性成长及保留技能的等级门槛沿用[成长基础](../design/character-progression-v1.md)，原97节点、12首领和74装备保留。

BOW_02“分裂箭”主箭有效命中后，从首击点分出1/2/3/4/5支子箭，总共最多命中2/3/4/5/6个不同目标；首目标射程12/13.5/15/16.5/18m，固定首击包络半径3/4/5/6/7m。子箭在首击时冻结各自平滑弹道弧线（fixedBallisticPath/noMidflightRetarget），不在飞行中追踪、不补位、不递归分裂、不穿墙，细淡青箭路清楚区分主箭与子箭。THU_02固定原首击中心，五级连接半径3/4/5/6.5/8m、总目标2/3/4/6/8（含首目标），不从接点向圈外递推。

[当前图集与审阅](../../source-art/skills/pure-skills-v2/README.md)只登记静态概念及其选用状态，不代表运行实现或动画。飞刃走廊以[WAR最初原图](../../source-art/skills/pure-skills-v2/combat-war.png)、弓术以[首版分裂箭](../../source-art/skills/pure-skills-v2/combat-bow.png)为基础，当前四系强化候选与审阅以图集为准；曲线单箭和后续直线版退为过程对照。奥术历史方案保留过程记录，已撤出当前交付与待补完列表，v1图保留可复用材质基础。当前运行预览仍夹在1.2—4.5m、手机镜头正交半高3m，后续须按[远距接入门槛](../design/ranged-combat-integration-v2.md)同步实现瞄准、镜头、判定与敌方反应。

2026-11-08 补充：[六区13张云端概念板](../../source-art/encounters/cloud-world-v2/README.md)与[逐图来源/哈希/审阅](../../source-art/encounters/cloud-world-v2/provenance.json)已登记，覆盖12首领、24普通敌和32新增掉落装备的概念造型。概念方向审阅通过，正式动画、透明切片、碰撞与手机实机尚未验收；未注册为可玩角色。下表2026-11-03的模型生产数量是历史阶段记录，当前2D运行证据见[实际进度](../PROGRESS.md)。

2026-11-08 装备复用接入：从已有云端六区/掉落板按明确ID裁切并处理49个RGBA图标（含全部32新增装备）；加既有v3明确16件，当前65/74永久装备有专属行囊图标，其余9件保留类别回退。未启动生图或本地推理，生成证据、像素处理与图标审阅分别记录；图标不代表持武器/穿戴动画完成。见[图标来源](../../source-art/encounters/cloud-world-v2/equipment-runtime-v1/manifest.json)、[输出审阅](../../source-art/encounters/cloud-world-v2/equipment-runtime-v1/review.json)和[运行接入](../../source-art/encounters/cloud-world-v2/equipment-runtime-v1/runtime-install.json)。

更新：2026-11-03。只登记当前选用资源，文件存在与游戏生产通过分别标记。

| 资源 | 当前文件 | 状态 |
| --- | --- | --- |
| 拉斐尔造型与肖像 | [主角板](../../assets/concepts/revision-v5/hero-v5-balanced.png) | 当前概念，未转完整动作 |
| 四核心探险者 | [核心人物板](../../assets/concepts/revision-v5/explorers-v5-recast.png) | 当前概念，未转完整动作 |
| 其余四位关键人物 | [关键人物板](../../assets/concepts/revision-v5/rivals-v5-balanced.png) | 当前概念，未转完整动作 |
| 普通敌人 | [细节参考](../../assets/concepts/raider-detail-reference-v2.png) | 当前专项参考 |
| 头目 | [细节参考](../../assets/concepts/captain-detail-reference-v2.png) | 当前专项参考 |
| 场景材质 | [环境参考](../../assets/concepts/chapter01-environment-v1.png) | 当前专项参考 |
| 地理 | [七地理PNG与七SVG](../maps/world-atlas-v3.md) | 静态设计，未装配成关卡 |
| 装备 | [基础目录](../interactions/equipment-and-crafting.md)、[随机传奇](../interactions/random-legendaries.md) | 设计与本地功能实现分列 |

正式角色模型、绑定和完整动画通过数仍为0。首批需依据当前主角制作可在实际视口下检查的待机、移动、剑击、弓、杖、受击和死亡资源；不能以概念板、图标或静态位移计为动画完成。

所有当前素材的路径与SHA-256由全面清理清单保护。早期低模和失败研究不再登记为可用资源。
