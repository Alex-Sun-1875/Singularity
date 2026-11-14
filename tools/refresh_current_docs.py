"""Refresh active entry points and remove references to explicitly retired versions.

This script edits text only. Physical deletion is a separate, reviewed PowerShell plan.
"""
from pathlib import Path
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tools/latest-version-cleanup.json").read_text(encoding="utf-8"))


def retired(path):
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        return False
    return relative in MANIFEST["files"] or any(relative == p or relative.startswith(p + "/") for p in MANIFEST["directories"])


def write(relative, text):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


PAGES = {
"README.md": """
# 剑与火 · 白枝第七远征

当前路线为 **TapTap Maker／UrhoX／Lua，本地单机开发，完成后再绑定云端项目**。工程根在 `src/`，规则与入口放在 `src/scripts/`，素材放在 `src/assets/`。

## 当前内容

- [人物与剧情](docs/story/revision-v5/README.md)：拉斐尔、弥菈、洛恩、夜祈、瑟维恩与其余四位关键人物；四幕主线、六条支线和选择回响。
- [当前地图](docs/maps/world-atlas-v3.md)：四地表、两地下，七张地理美术图与七张SVG关系图。
- [装备与合成](docs/interactions/equipment-and-crafting.md)：基础48种物品；[随机传奇候选](docs/interactions/random-legendaries.md)另列。
- [本地小章节规格](docs/superpowers/specs/2026-11-03-maker-local-chapter-design.md)与[实施进度](docs/PROGRESS.md)。

## 本地开发状态

官方开发套件和独立 Runtime 已安装到 `src/` 的本地辅助目录。当前 Lua 规则实现已通过9个真实Runtime用例，场景绘制、界面、素材接入和完整游玩验收仍在进行。

首个片段为“旅店接约 → 隘口夺匣 → 发现求援信”。使用当前v5造型和v3地图方向；不使用早期低模角色。当前人物PNG是概念与立绘资料，尚无通过验收的完整战斗动作。

## 只保留最新版

已按用户明确选择准备全面清理：旧素材、旧剧情文档、旧JSON和JS原型一并移除。**实际删除尚未执行：自动审批拒绝了删除命令，返回 `blocked by policy`。**

已核对的清单为[清理清单](tools/latest-version-cleanup.json)，约282个旧文件、266MiB；[清理脚本](tools/Remove-OldVersions.ps1)默认只预览，验证保留素材的哈希和每个绝对目标路径。需要在本机执行时：

```powershell
pwsh -NoProfile -File .\tools\Remove-OldVersions.ps1 -Apply
```

最新角色为 `hero-v5-balanced.png`、`explorers-v5-recast.png`、`rivals-v5-balanced.png`。游戏入口只使用当前清单；旧文件即使尚在磁盘，也不作为回退素材。

本地调试不创建项目身份、不登录、不上传、不远端构建。绑定与发布留到本地版本完成后。
""",
"docs/README.md": """
# 当前设计与开发资料

只维护当前版本。剧情采用v5，地理采用当前v3，游戏采用Maker本地Lua工程。

1. [最新决定](decision-log.md)与[实际进度](PROGRESS.md)。
2. [人物、剧情与外观](story/revision-v5/README.md)。
3. [地理图册](maps/world-atlas-v3.md)与[节点合同](maps/world-geography-v3.md)。
4. [装备、交易与交互](interactions/README.md)，[随机传奇候选](interactions/random-legendaries.md)。
5. [美术与资源](assets/README.md)，[当前资源登记](assets/resource-register.md)。
6. [本地小章节规格](superpowers/specs/2026-11-03-maker-local-chapter-design.md)与[实施计划](superpowers/plans/2026-11-03-maker-local-chapter.md)。
7. [验证结果](REVIEW_REPORT.md)与[设计验收清单](REVIEW_CHECKLIST.md)。

当前最新稿、概念图、已实现规则和已跑通场景分别登记。文稿完整不代表游戏全部实现，概念板不代表正式角色与动画。
""",
"docs/PROGRESS.md": """
# 剑与火当前进度

更新：2026-11-03。

## 已明确

- 使用TapTap Maker／UrhoX／Lua；在当前仓库 `src/` 开发，先完成本地版本再绑定云端。
- 采用v5人物与剧情、当前恢复后的v3地理方向；早期低模和失败研究不得再作为角色回退素材。
- 全面清理旧素材、旧剧情、旧设计JSON和JS原型，只保留当前版本。

## 已实际完成

- 官方开发套件已安装；独立Runtime版本为 `20261030-1103-fefb855`。
- 本地运行不使用项目身份或登录授权，未绑定云端。
- Lua规则模块已实现接约与知情状态、场景流转、三种基础武器、两件随机传奇、敌人、碰撞、油桶连爆、奖励去重、快照恢复和死亡重试。
- 已在真实Runtime观察到缺失规则的失败，再实现后通过9项规则用例；最终报告为PASS、Lua/资源/引擎错误均为0。
- 最新素材保留清单已核对22份图像/矢量资产的SHA-256，清理脚本的只读预览通过。

## 正在进行

本地场景绘制、v5素材接入、HUD/对白、持久化文件保存、键鼠与触屏、实际游玩与截图验收。新图仍需转为适配战斗的角色精灵与动作，不能拿旧低模顶替。

## 清理状态

清单涉及282个旧文件，约266MiB。批量删除和单个旧目录删除均被自动审批拦截，理由为 `blocked by policy`，因此**旧文件尚未物理删除**。[清理脚本](../tools/Remove-OldVersions.ps1)和[精确清单](../tools/latest-version-cleanup.json)已准备；默认只读预览，传 `-Apply` 才执行已校验的计划。

已清除当前入口对旧版本的依赖；保留的源图、开发套件与游戏规则没有冒称为已完成的可玩美术成品。
""",
"docs/decision-log.md": """
# 剑与火当前决定

更新：2026-11-03。这里只记录当前方向。

| 主题 | 当前决定 |
| --- | --- |
| 技术路线 | 用户选择TapTap Maker／UrhoX／Lua |
| 工作位置 | 当前仓库src/，Lua入口遵循src/scripts/main.lua |
| 开发顺序 | 先使用本地资源完成单机版，再绑定云端项目 |
| 首个片段 | v5 M1：旅店接约、隘口夺匣、发现近期求援信 |
| 完整世界 | v3四个地表地区、两个地下网络；小章节只限制生产批次 |
| 人物与剧情 | v5拉斐尔和八位关键人物，人物目标、隐瞒与选择回响交织 |
| 视觉 | 细腻写实手绘2.5D，使用最新v5造型；早期低模与失败研究不得接入或回退 |
| 装备 | 基础40永久装备＋8消耗符；另增机制不同的随机传奇候选 |
| 名称 | 使用本轮更新的武器、防具、首饰和符咒名称，稳定目录ID保持 |
| 清理 | 用户明确选择全面移除旧素材、旧剧情文档、旧JSON和JS原型 |
| 云端 | 当前不登录、不绑定、不上传、不远端构建、不发布 |

本机Maker0.0.39的preview包装命令要求绑定，独立官方Runtime可本地运行；当前采用开发套件提供的独立运行方式，不伪造绑定配置。工具提示0.0.40可更新，尚未升级。

全面清理的删除命令被自动审批拦截，当前仅完成清单、保护校验与脚本准备；磁盘清理仍待实际执行。
""",
"assets/concepts/README.md": """
# 当前角色与场景参考

| 用途 | 当前文件 |
| --- | --- |
| 主角拉斐尔 | [hero-v5-balanced.png](revision-v5/hero-v5-balanced.png) |
| 弥菈、洛恩、夜祈、瑟维恩 | [explorers-v5-recast.png](revision-v5/explorers-v5-recast.png) |
| 凯尔、伊芙琳、艾莉丝、阿德里安 | [rivals-v5-balanced.png](revision-v5/rivals-v5-balanced.png) |
| 普通敌人最新专项参考 | [raider-detail-reference-v2.png](raider-detail-reference-v2.png) |
| 头目最新专项参考 | [captain-detail-reference-v2.png](captain-detail-reference-v2.png) |
| 场景材质参考 | [chapter01-environment-v1.png](chapter01-environment-v1.png) |

专项敌人/场景参考是各类别目前保留的最新文件，不等于主角v5的早期版本。地理采用[当前v3图册](../../docs/maps/world-atlas-v3.md)。

三张角色板均为1536×1024 PNG。它们是造型和立绘依据，尚非配准动画图集或正式模型。群像图内英文标签与当前人物对应见[人物表](../../docs/story/revision-v5/characters.md)。

当前源记录只保留三个最终输出对应的提示词。旧过程稿和旧模型已从当前选用范围排除，实际物理删除状态见[进度](../../docs/PROGRESS.md)。
""",
"source-art/README.md": """
# 当前美术源资料

- `maps/world-atlas-v3/`：当前地图的源PNG、可编辑SVG和生成提示词。
- `references/`：当前核心人物重塑使用的盖尔、阿斯戴伦官方外观参考，仅用于设计研究，不作为游戏素材分发。
- 角色当前输出与对应提示词在[概念目录](../assets/concepts/README.md)。

当前没有通过验收的角色模型、绑定或完整动作。早期低模及失败研究已停用，列入全面清理计划；不再提供旧版本重建命令。
""",
"source-art/maps/world-atlas-v3/STATUS.md": """
# 当前地图源资料

当前保留世界、石桥边地、沉桥高地、沉钟河湾、灰石城域、旧誓下城、沉钟地宫共七幅美术图及七幅地理SVG。采用当前恢复后的v3色彩与地理方向。

剧情权威为v5文稿。对应的旧剧情覆盖图已停用并列入清理；当前没有宣称已交付新的v5覆盖图。地图仍为静态设计，未完成导航、碰撞或游戏装配验收。
""",
"docs/assets/README.md": """
# 当前美术与资源

采用[最新v5人物外观](../story/revision-v5/art-direction.md)和[当前v3地图](../maps/world-atlas-v3.md)。角色、环境、装备、特效与声音按[制作路线](production-roadmap.md)分批实现。

- [方向与质量要求](art-direction.md)
- [当前文件登记](resource-register.md)
- [角色与动画规格](characters-and-animation.md)
- [环境与道具规格](environment-and-props.md)
- [UI、特效与声音规格](ui-icons-vfx-audio.md)

三张角色概念板不等于模型或动作。不得使用已停用的低模、失败模型或不匹配的旧人物作为回退。物品设计数量、图片张数、模型数量和运行验收分别统计。
""",
"docs/assets/resource-register.md": """
# 当前资源登记

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
""",
"docs/assets/art-direction.md": """
# 当前美术方向

采用细腻、材质可信的写实手绘2.5D。人物以[当前v5外观](../story/revision-v5/art-direction.md)为准，地理以[当前v3图册](../maps/world-atlas-v3.md)为准。

## 人物

自然成年人体比例；保留面部辨识度、功能性服装、皮革厚度、布料受力和金属层次。女性金色波浪发，男性不同深发；具体人物差异按v5人物稿。早期棱角低模、拼接圆柱人体和失败研究不得作为可用成品或回退素材。

## 角色生产

当前三张概念板用于立绘与造型。可采用符合方向的高质量源模型预渲染精灵，或依据统一结构稿制作2D动作；输出必须通过朝向一致性、脚底锚点、动作时序与实际屏幕可读性检查。逐帧独立生成而未校准的图片不算完成动画。

## 场景与镜头

固定正交镜头方向保持；逻辑构图1280×720横屏，常规人物在视口目标高100—132px。主光来自屏幕左上，脚底接触影单独处理。前景遮挡应允许看清脚底与交互符号。

地理延续当前v3的自然层次、青蓝水体、深绿与冷影；U1异常炉核为冷白。聚落内部有街巷和功能空间，不用悬浮沙盘代表大地区。

## 输出与预算

PNG动作图集按实际裁边、图集页与解压纹理计算内存，不能用PNG压缩字节代替显存；按场景卸载不用的NPC与敌人资源。角色近景细节、场上动作、武器家族轮廓分别验收。

## 质量状态

当前尚无通过验收的正式角色模型或完整动作。概念图、资源接入、功能样板和最终美术各自登记；本地版不得使用已明确停用的角色占位。
""",
"docs/assets/production-roadmap.md": """
# 当前资源制作顺序

1. 锁定[当前角色概念](../story/revision-v5/art-direction.md)与[当前地理](../maps/world-atlas-v3.md)，只从当前资源清单选取。
2. 从拉斐尔开始制作实际游戏视角的角色资源，验证待机、移动、攻击与受击；不批量扩大未通过的质量。
3. 将首个小章节的旅店、野路、隘口做成可走的场景，分别检查地形、碰撞、遮挡和交互。
4. 将基础剑、弓、杖与两件首批随机传奇接入，验证武器轮廓、出手时点、弹道与回响。
5. 加入对白、背包、提示、音效和保存反馈，检查键鼠与触屏。
6. 用真实Runtime、受控多帧截图和完整流程验收；美术与功能分别报告。

先完成本地版本，再绑定云端项目。当前正式角色动画仍未交付；早期低模、失败研究和过程稿不属于此路线。
""",
"docs/maps/world-atlas-v3.md": """
# 当前世界地理图册

当前采用v3地理方向：四个地表大地区、两个独立地下网络。人物与故事以[v5主线](../story/revision-v5/story-bible.md)为准，节点与入口以[地理合同](world-geography-v3.md)为准。

| 地理层 | 美术图 | 地理关系图 |
| --- | --- | --- |
| 世界 | [世界地貌](../../source-art/maps/world-atlas-v3/00-world-geography-draft.png) | [世界关系](../../source-art/maps/world-atlas-v3/00-world-relations.svg) |
| R1石桥边地 | [地貌](../../source-art/maps/world-atlas-v3/01-stonebridge-region-draft.png) | [地点与入口](../../source-art/maps/world-atlas-v3/01-r1-geographic-plan.svg) |
| U1旧誓下城 | [地下美术](../../source-art/maps/world-atlas-v3/03-old-oath-undercity-draft.png) | [内部关系](../../source-art/maps/world-atlas-v3/03-u1-geographic-plan.svg) |
| U2沉钟地宫与旧水道 | [地下美术](../../source-art/maps/world-atlas-v3/04-drowned-necropolis-draft.png) | [深闸与回环](../../source-art/maps/world-atlas-v3/04-u2-geographic-plan.svg) |
| R2沉桥高地 | [高地美术](../../source-art/maps/world-atlas-v3/05-sunken-bridge-highlands-draft.png) | [矿镇与条件桥](../../source-art/maps/world-atlas-v3/05-r2-geographic-plan.svg) |
| R3沉钟河湾 | [河湾美术](../../source-art/maps/world-atlas-v3/06-drowned-bell-riverbend-draft.png) | [聚落与转运岸](../../source-art/maps/world-atlas-v3/06-r3-geographic-plan.svg) |
| R4灰石城域 | [城域美术](../../source-art/maps/world-atlas-v3/07-greystone-city-domain-draft.png) | [外城与内堡](../../source-art/maps/world-atlas-v3/07-r4-geographic-plan.svg) |

保留七张PNG与七张SVG。PNG为1536×1024，SVG为2400×1600。美术表达地貌与气氛，SVG表达地理节点和条件连接；两者未逐像素配准，尚未完成游戏导航与碰撞验收。

当前使用恢复后的自然色彩版本。地区规模不受首个小章节限制；石桥镇有内部功能空间，地下单独成网。剧情覆盖以v5文稿标注为准，当前未声称已完成新的剧情覆盖图。

[检查与未验证项](world-atlas-v3-validation.md)
""",
"docs/maps/world-atlas-v3-validation.md": """
# 当前图册检查与限制

当前保留世界、四地表与两地下的七张美术PNG和七张地理SVG。清理清单保护这些文件的SHA-256，预览已验证文件存在且哈希一致。

地理关系仍依[节点合同](world-geography-v3.md)。U1与U2须经地表连接；地下端口方向、矿桥条件、河湾吊臂条件、灰石堡两外台与内堡门槛分别保持。

当前未执行导航网格、实际碰撞、高差、战斗视线、实机耗时或完整场景装配验收。美术图中的房间、道路与建筑不能自动当成已开放内容。剧情按v5文稿，旧覆盖图已停用。
""",
"docs/REVIEW_REPORT.md": """
# 当前验证记录

更新：2026-11-03。

| 对象 | 已观察证据 | 结论范围 |
| --- | --- | --- |
| 本地Runtime | 官方独立Windows运行时启动，单机工具模式，无项目绑定 | 本地引擎能执行Lua |
| Lua规则RED | 实际报告捕获Game.Chapter缺失 | 已观察功能缺失失败 |
| Lua规则GREEN | 9项用例完成；报告PASS，Lua/资源/引擎错误均0 | 规则模块通过首批检查 |
| 当前素材保护 | 22份PNG/SVG的路径与SHA-256一致 | 清理保留清单通过只读检查 |
| 全面删除 | 批量与单目录删除均被自动审批拒绝 | 旧版本尚未物理移除 |

9项规则覆盖初始武器、斜向/帧间隔、接约前置与金币去重、装备拥有权、连爆和击败收据、折返箭分程命中、快照中的随机/选择/奖励、非法快照拒绝、死亡保留已败敌。

场景绘制、UI、文件保存、资源接入、触屏、完整游玩、实际图像与运动检查仍待完成。基础装备和全世界设计用例不因9项规则通过而视为已实现。旧JS原型的测试不再作为当前Lua版验收依据。
""",
"docs/story/narrative-rules.md": """
# 当前叙事与状态规则

剧情唯一阅读入口为[v5](revision-v5/README.md)，地理为[当前图册](../maps/world-atlas-v3.md)。主角拉斐尔与八位关键人物使用当前姓名和关系。

- 接约前查看求援抄件，后续只揭开被隐去的姓名与关系，不能重复指控玩家已知的信息。
- 样片、抄件、完整星片与签名原信各有明确持有和转运顺序。
- 选择后果依据实际行为记录，不从已到地区或装备拥有权推断立场。
- 主线最低安全条件有无同伴均可完成，支线提供关系、证据与局部接近方式。
- 显影只能重放已留下的记录，模仿声音不等于理解、同意或原谅。
- 任务、已败敌、机关与奖励独立持久化。死亡、休整、回访和重复提交不复制奖励。
- 固定装备仍按[获取规则](../interactions/equipment-and-crafting.md)提交，随机传奇另按自己的掉落收据，不吞主线保底。

首个本地片段覆盖M1，完成取匣与求援信发现后收尾，不提前执行S10阶段战、地下重逢或后续结局。
""",
"docs/story/exploration-map-logic.md": """
# 当前探索与地图规则

采用[当前v3地理图册](../maps/world-atlas-v3.md)和[节点合同](../maps/world-geography-v3.md)，剧情以[v5主线](revision-v5/story-bible.md)为准。

四地表、两地下互连；聚落有内部街巷，地下有自己的回路。地表路径与地下端口需实际走到后发现，投影相邻不表示可以穿墙或跨楼层互动。

- 地标、人物、记录和可见风险引导探索；普通支路允许先发现再接任务。
- 多条接近方式可以交叉使用，支路能回接；不开互斥走廊选择菜单。
- 同一地点能承载不同人物任务，回访根据已保存行为变化，已败敌和已取宝物不自动刷新。
- 地图只显示已知地点和入口，不自动揭出全图、隐匣或未发现商人。
- 快速旅行只列已制作、亲抵并解锁的安全点；附近战斗、弹体或交易/领奖提交时不能传送。
- 机关有不消耗稀有装备的解法，主线不要求特定随机传奇或全清支线。
- 大地区愿景与小章节制作批次分开；本地功能场地不等于完整世界已实现。

首个本地片段采用旅店、野路和隘口三处制作场地，验证主路、绕行、交互与战斗。最终空间装配仍需与地理合同逐项对应。
""",
}

for path, text in PAGES.items():
    write(path, text)

# Current names selected during this conversation. IDs, source events and costs stay stable.
NAMES = {
"旅人铁剑":"佣兵长剑","余烬钢剑":"未熄之誓","守桥钉锤":"桥上的最后一人","矿道裂岩斧":"铁山之牙","星炉重剑":"陨星","守门者誓剑":"无冕者的誓言","旅人短弓":"白蜡木短弓","逐风枝弓":"银鹿的足迹","霜棱长弓":"冬猎","雷枝猎弓":"暴雨将至","学徒灰枝杖":"灰木短杖","烬灯长杖":"灰烬祷文","沉钟霜杖":"沉钟挽歌","断穹引雷杖":"天穹的裂隙","石誓圆盾":"洛恩的旧盾","铜星法器":"黄铜星环",
"誓钉护额":"白枝护额","鹰眼兜帽":"游隼兜帽","灯灰头冠":"烛灰冠冕","冷钟面罩":"冬祷面具","旧誓锁甲":"幸存者的锁甲","风径皮衣":"游猎者皮甲","烬灯法袍":"灰烬司祭的礼袍","寂钟长衣":"沉钟祭衣","承击护手":"老兵的回敬","扣弦手套":"银弦手套","缄印手套":"秘仪手套","拾秘护腕":"远征护腕","誓石战靴":"阵线之锚","逐风短靴":"林海行者短靴","静墨行靴":"无声仪式","越隙皮靴":"远征者之履",
"灰心戒":"余烬之心","涟冰戒":"冬湖之眼","寻纹铜戒":"探险家的印戒","归息银戒":"静思银环","余灯坠":"落日余辉","静水钟坠":"沉钟之泪","双印绳结":"双生契约","归路坠牌":"归乡信物",
"刻痕符页":"奥术札记","蚀墨诅印":"黑契封印","回声封札":"回响祷文","壁垒符石":"守护圣印","霜缚蜡印":"寒冬敕令","响雷骨签":"风暴判词","归火誓札":"焚夜祷书","葬誓长卷":"终誓遗卷",
}
ACTORS={"艾妲":"弥菈","布兰":"洛恩","蕾萨":"夜祈","墨伦":"瑟维恩","娜薇":"艾莉丝","洛德里克":"阿德里安","伊洛":"凯尔","埃林":"伊芙琳"}

def trim_retired_sections(text):
    lines=text.splitlines()
    result=[]
    skip_level=None
    for line in lines:
        heading=re.match(r'^(#{2,4})\s+(.+)',line)
        if heading:
            level=len(heading[1])
            if skip_level is not None and level<=skip_level:
                skip_level=None
            if re.search(r'历史迁移|旧.*追溯|区域.*v2|区域尺度第二版|被否决|永久符.*迁移|十二剑.*迁移|旧材料包迁移',heading[2],re.I):
                skip_level=level
        if skip_level is None:
            result.append(line)
    blocks=re.split(r'\n\s*\n','\n'.join(result))
    return '\n\n'.join(b for b in blocks if not re.search(r'区域v2|区域尺度v2|被否决.*v2|旧119|旧148|旧204|212候选|旧JSON',b,re.I))

EQUIVALENTS={
"docs/story/world-and-main-plot.md":"docs/story/revision-v5/story-bible.md",
"docs/story/characters.md":"docs/story/revision-v5/characters.md",
"docs/story/dialogue.md":"docs/story/revision-v5/scenes-dialogue.md",
"docs/story/revision-v4/README.md":"docs/story/revision-v5/README.md",
"docs/story/revision-v4/implementation-scope.md":"docs/superpowers/specs/2026-11-03-maker-local-chapter-design.md",
"docs/history/equipment-sword-only-v1.md":"docs/interactions/equipment-and-crafting.md",
"docs/maps/regional-scale-v2.md":"docs/maps/world-geography-v3.md",
"docs/maps/world-structure-v3-proposal.md":"docs/maps/world-geography-v3.md",
}

for path in (ROOT/'docs').rglob('*.md'):
    if retired(path) or path.relative_to(ROOT).as_posix() in PAGES:
        continue
    text=path.read_text(encoding='utf-8')
    if '/revision-v5/' not in path.as_posix():
        text=trim_retired_sections(text)
        for old,new in ACTORS.items(): text=text.replace(old,new)
    for old,new in NAMES.items(): text=text.replace(old,new)
    def fix_link(match):
        label,url=match.group(1),match.group(2)
        target=url.split('#')[0].strip('<>')
        if not target or '://' in target or target.startswith('#'): return match.group(0)
        resolved=(path.parent/target).resolve()
        if not retired(resolved): return match.group(0)
        old=resolved.relative_to(ROOT).as_posix()
        if old.startswith('docs/story/chapters/'):
            new='docs/story/revision-v5/story-bible.md'
        else: new=EQUIVALENTS.get(old)
        if new:
            relative=Path(os.path.relpath(ROOT/new,path.parent)).as_posix()
            return f'[{label}]({relative})'
        # No replacement resource exists. Remove the link rather than mislabel a
        # concept image as a model or claim an obsolete file is current.
        return label+'（已停用）'
    text=re.sub(r'\[([^\]]*)\]\(([^)]+)\)',fix_link,text)
    if path.name=='equipment-and-crafting.md':
        text=text.replace('## 4 四十八种物品完整目录','## 4 基础物品目录（48种）')
        text=text.replace('完整目录为 **48种物品','基础目录为 **48种物品')
        text=text.replace('## 9 传承训练与历史迁移','## 9 传承训练')
        begin=text.find('### 十二剑设计到当前目录的可追溯')
        if begin>=0:
            end=text.find('\n## ',begin)
            text=text[:begin]+(text[end:] if end>=0 else '')
        text+='\n\n随机传奇使用[当前新增候选池](random-legendaries.md)，不替换基础目录的固定奖励。\n'
    path.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')

# Keep only the current reading instructions in the latest narrative entry.
p=ROOT/'docs/story/revision-v5/README.md'
text=p.read_text(encoding='utf-8')
if '## 版本与现有项目' in text:
    text=text.split('## 版本与现有项目')[0]+'''## 当前项目状态

本文是当前人物与剧情稿。地理采用[当前图册](../../maps/world-atlas-v3.md)，玩法采用Maker本地Lua工程，首个制作片段见[本地小章节](../../superpowers/specs/2026-11-03-maker-local-chapter-design.md)。

当前三张人物板为造型与立绘依据，未转为正式模型、绑定或完整动作。完整故事、装备与地图并未全部实现；旧版本已从当前阅读入口移除，物理清理状态见[进度](../../PROGRESS.md)。
'''
p.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')

print(json.dumps({'active_pages_refreshed':len(PAGES),'old_files_deleted':0},ensure_ascii=True))
