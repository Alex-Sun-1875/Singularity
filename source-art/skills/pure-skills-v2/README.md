# 四系技能强化概念稿

## 当前近战修订覆盖说明

2026-11-08，用户明确要求“破军战技也改回近战”。当前WAR近战名称、范围与角度已由[独立运行覆盖](../../../tools/design/melee-revision-v1.json)恢复，现行数值表和时序见[近战恢复记录](../../../docs/design/melee-restoration-v1.md)。下文原WAR飞刃图、交战距离和强化候选属于此前远程阶段来源，逐字保留供追溯；它们不再定义当前破军的空间身份，也不构成此次近战美术验收通过。冻结的技能JSON与图片未被改写，导出器在读取时显式叠加修订。

## 此前四系远距阶段图集记录

2026-11-08。奥术秘法暂时撤下，冰系继续退出；当前只保留战技、弓术、火焰、雷霆四系与通用技能，共30技/150阶。人物1—40级、属性成长与保留技能门槛沿用原表。

四张新强化候选沿用原版造型与交战距离，把提升放在材质深度、方向短尾、真实接触爆发及消散节奏。150阶表现方案同步加强，伤害、目标上限与几何不因装饰增加。新稿尚待用户审阅，没有接入游戏或完成动画/碰撞/手机性能验收。

![四系强化总览](current-overview.jpg)

| 强化候选 | 方向 | 基础参考 |
|---|---|---|
| [破军战技 · 首版飞刃强化](combat-war-impact-v1.png) | 沿首版单层细长月牙与狭长走廊，强化锋缘、定向金属斩裂和接触火星；没有改成多层巨刃。 | [combat-war.png](combat-war.png) |
| [逐风弓术 · 首击分裂强化](combat-bow-impact-v1.png) | 沿首版主箭首击后分出细淡子箭，强化首击与五处分支的物理穿刺；不加光羽绸带或递归分裂。 | [combat-bow.png](combat-bow.png) |
| [烈焰秘术 · 体积爆燃强化](combat-fir-impact-v1.png) | 强化红橙体积翻卷、紧凑白金火核和敌人接触处的短促爆燃；脚部与安全区仍需动态验收。 | [combat-fir-redesign-v4.png](combat-fir-redesign-v4.png) |
| [雷霆秘术 · 横向电弧强化](combat-thu-impact-v1.png) | 沿此前认可的横向分叉图，强化冷白电芯、细紫层次和接点雷裂；人数与半径不随光效暗增。 | [combat-thu.png](combat-thu.png) |

## 当前规则

- [30技能与150阶](../../../docs/design/combat-skills-v2.md)、[人物属性和等级门槛](../../../docs/design/character-progression-v1.md)
- [分裂箭与限额电弧](../../../docs/design/skill-spatial-v2.md)、[四系五级表现](../../../docs/design/skill-vfx-v2.md)
- [差异化简报](../../../docs/design/skill-differentiation-brief-v2.md)、[参考与原创转化](../../../docs/design/skill-reference-bg3-v2.md)
- [74装备适配](../../../docs/design/equipment-skills-v4.md)、[97地点与12首领](../../../docs/design/world-combat-v4.md)
- [远程接入要求](../../../docs/design/ranged-combat-integration-v2.md)
- [技能JSON](skill-catalog.json)、[世界JSON](campaign-v8.json)、[设计核对](design-validation.json)、[交付核对](delivery-validation.json)

## 来源与审阅

全部使用内置云端OpenAI image_gen，没有启动本地模型。完整提示词与逐图参考、真实尺寸、SHA256见[provenance.json](provenance.json)和[prompts](prompts/)。原生输出逐字节复制，Pillow仅排版缩略图与灰度对照；不假定上传缓存行为，底层模型版本未由工具返回。

[当前选图](current-selection.json)与[独立审阅](independent-art-review-current.json)分别记录。生成成功、方向审阅、用户接受与运行生产通过相互独立。图中人物只是尺度示意，概念图不能证明实际米制、动作先后、弹体数量或命中。

奥术与冰系旧稿、失败探索及原版基础素材全部保留；它们不属于当前可选职业，也不自动成为后续必须补完的工作。历史[五系审阅](independent-art-review-five-styles-v6.json)及[v1基础稿](../pure-skills-v1/README.md)保留原记录，不代表本轮强化验收。

复核命令：`python tools/design/build-skills-v2.py`、`python tools/design/catalog-skill-art-v2.py`。前者导出当前设计，后者核对来源与排版；不改运行代码、存档或下载依赖。
