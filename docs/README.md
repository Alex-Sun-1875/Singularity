# 当前设计与开发资料

长期规范入口：[开发 skill](../.agents/skills/singularity-development/SKILL.md)、[UI 设计 skill](../.agents/skills/singularity-ui-design/SKILL.md)、[dev / test / release 打包与 release 日志](development/build-profiles.md)。未指定打包类型时默认 test；UI 布局规范已迁入 UI 设计 skill，原文档保留跳转。

2026-11-11 [装备与经验生命周期v3已接入](design/equipment-lifecycle-v3-integration.md)：前两章十天成长预算、按等级共享战斗经验日限额、四份任务装备与四类战斗随机目标、所有Boss共享神器1%／传奇3.6%及10分钟复战。八章目录已配表，后六章保持关闭；旧档保留，TapTap真机待验。

2026-11-10 [金币锻造与装备强化第一版已接入](design/equipment-forging-integration-v1.md)：装备分别配置强化上限，品质默认＋3／5／8／10／12／15，前两章阶段＋3／6；金币用于锻造、强化与传承，支持洛恩与行囊入口及旧档迁移。精炼、宝石和后续章节继续按[完整方案](design/equipment-forging-and-gold-v1.md)扩展。

2026-11-10 当前采用[八章剧情与双路线设计v8](design/campaign-v8.md)，先确定完整故事与伏笔，本轮仅制作第一、第二章。后六章保留剧情规划和未开放状态；刷怪与任务均能成长并挑战共同关底。下方v7四章方案为历史过程。

2026-11-10 [剧情重构提案v7](design/campaign-v7.md)：兽潮之夜、群山战火、沉没王座、破晓之战。刷怪与任务并重，都能独立成长并击败共同的章节Boss和最终Boss通关，允许混合游玩；地区按等级开放，关底首胜决定通关。当前运行剧情仍以v6及既有任务数据为准，新主线与双路线配平尚未接入。

2026-11-08 当前为**四系WAR/BOW/FIR/THU＋通用，共30技能、150阶**。奥术秘法暂撤、冰系职业移除，ARC/FRO各7技仅作历史保留；奥术不是当前待必须补完的项目。飞刃走廊与BOW_02分裂箭沿用最初原图结构，本轮另存四系强化候选；BOW_01/03/05仍走直线，雷电保留用户认可的既有`combat-thu.png`方向。四系加强材质层次、真实接触、短尾迹和逐级轻重节奏，不暗增伤害、段数或目标。

当前入口：[技能v2](design/combat-skills-v2.md)、[空间规则v2](design/skill-spatial-v2.md)、[特效v2](design/skill-vfx-v2.md)、[97地点战斗v4](design/world-combat-v4.md)、[74装备联动v4](design/equipment-skills-v4.md)。人物1—40级、属性成长及保留技能的等级门槛沿用[成长基础](design/character-progression-v1.md)，原97节点、12首领和74装备保留。

BOW_02“分裂箭”主箭有效命中后，从首击点分出1/2/3/4/5支子箭，总共最多命中2/3/4/5/6个不同目标；首目标射程12/13.5/15/16.5/18m，固定首击包络半径3/4/5/6/7m。子箭在首击时冻结各自平滑弹道弧线（fixedBallisticPath/noMidflightRetarget），不在飞行中追踪、不补位、不递归分裂、不穿墙，细淡青箭路清楚区分主箭与子箭。THU_02固定原首击中心，五级连接半径3/4/5/6.5/8m、总目标2/3/4/6/8（含首目标），不从接点向圈外递推。

[当前图集与审阅](../source-art/skills/pure-skills-v2/README.md)只登记静态概念及其选用状态，不代表运行实现或动画。飞刃走廊以[WAR最初原图](../source-art/skills/pure-skills-v2/combat-war.png)、弓术以[首版分裂箭](../source-art/skills/pure-skills-v2/combat-bow.png)为基础，当前四系强化候选与审阅以图集为准；曲线单箭和后续直线版退为过程对照。奥术历史方案保留过程记录，已撤出当前交付与待补完列表，v1图保留可复用材质基础。当前运行预览仍夹在1.2—4.5m、手机镜头正交半高3m，后续须按[远距接入门槛](design/ranged-combat-integration-v2.md)同步实现瞄准、镜头、判定与敌方反应。

当前完整设计采用[破晓之战v6](design/campaign-v6.md)，人物身份沿用v5，地理采用v3；游戏运行工程为Cocos Creator 3.8.8 / TypeScript，旧Maker/Lua资料保留为历史。完整设计与首章实际实现分列。

最新交付：[六区首领与怪物](design/encounters-and-loot-v2.md)、[97处逐关设计](design/world-levels-v2.md)、[装备和掉落](design/loot-catalog-v2.md)、[13张云端概念板及来源](../source-art/encounters/cloud-world-v2/README.md)。

1. [最新决定](decision-log.md)与[实际进度](PROGRESS.md)。
2. [人物、剧情与外观](story/revision-v5/README.md)。
3. [地理图册](maps/world-atlas-v3.md)与[节点合同](maps/world-geography-v3.md)。
4. [装备、交易与交互](interactions/README.md)，[随机传奇候选](interactions/random-legendaries.md)。
5. [美术与资源](assets/README.md)，[当前资源登记](assets/resource-register.md)。
6. [本地小章节规格](superpowers/specs/2026-11-03-maker-local-chapter-design.md)与[实施计划](superpowers/plans/2026-11-03-maker-local-chapter.md)。
7. [验证结果](REVIEW_REPORT.md)与[设计验收清单](REVIEW_CHECKLIST.md)。

当前最新稿、概念图、已实现规则和已跑通场景分别登记。文稿完整不代表游戏全部实现，概念板不代表正式角色与动画。
