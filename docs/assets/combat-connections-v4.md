# 蓝色近邻雷网与同箭连穿

最新雷电材质、三次放电、地面余晕及头顶血条/MISS 见 [雷电与受击反馈 v5](thunder-feedback-v5.md)。本页保留最近互连网与同箭转向的规则修订记录；当前包以 v5 为准。

2026-11-08。按用户本轮明确修订，雷电改为蓝色、邻近敌人互连成网；原分裂箭改为同一支箭命中后转向连穿。历史设计稿与先前截图保留，不再作为当前 BOW02 分散子箭行为的依据。

- THU02/04/05 保留原来的合法目标集合、连接半径、阶级上限及每拍伤害。先在可见邻接中选最短边形成连通骨架，再补每点两个最近可见邻边，形成局部闭环。独立可见分量各有合法入口，不跨墙强连；补环只发连接事件，不重复结算伤害或触发被动。THU01 的直线贯雷保留独立玩法，配色同步改蓝。
- 雷电主体 `#2679ff`、亮蓝芯 `#72afff`、柔晕 `#316dff`，不再用冷白主干。敌人间网边固定四条原生 Line、无额外装饰分叉，保留敌预警优先；节点接点也是蓝色。每条最多 100 点。
- BOW02 名称改为“连穿箭”。全程同一 projectile ID、一个物理箭体、零子箭；每次真实命中后，从当前箭位置选择首击固定半径内最近、存活、可见、未命中的敌人。只冻结下一段路线，实际飞到并命中才续接下一名；落空、碰墙、无后续合法目标或达到原总 2/3/4/5/6 敌上限时结束。首击与后续伤害系数、冷却、等级门槛沿用原值。

数据补丁在 [combat-connections-revision-v1.json](../../tools/design/combat-connections-revision-v1.json)，通过原导出入口生成，不重写历史技能目录。`HISTORICAL_SKILL_RANKS` 保存 BOW02 补丁前完整 rank，允许校验旧存档临时施放记录；恢复后按现有流程清理临时动作、弹体，保留学习、装备、冷却与持久进度。技能面板同步更新，另清理了近战技能遗留的远程文案。

当前默认本地包为 `http://127.0.0.1:7469/?view=2d`，实际加载 `index.561e9.js`。

| 证据 | 结果 |
| --- | --- |
| [规则验证](../../src/cocos/test-results/combat-graph-chain-v4/core-audit.json) | 9 个实际 GameSession 场景；近邻闭环、遮挡、独立分量、连接半径、每目标每拍一次伤害；同箭六敌、落空、移动目标、新墙、已发箭取消后继续均通过。 |
| [最终实际渲染](../../src/cocos/test-results/combat-graph-chain-v4/render/actual-render-report.json) | 22 个代表画面、七项动作释放边界、敌预警优先和清池检查通过，浏览器异常 0。 |
| [蓝色雷网视觉复核](../../src/cocos/test-results/combat-graph-chain-v4/render/blue-network-visual-review.json) | 桌面与手机视口均为蓝色近邻闭网，8 目标帧 72 条 Line、最多 88 点。 |
| [原速连续运行](../../src/cocos/test-results/combat-graph-chain-v4/live/actual-sequences.json) | 单箭与三种雷网四场原速实机，浏览器异常、失败请求及游戏内 failure 均 0；单箭始终同 ID、最多一个箭体，实际连续命中六敌。 |

类型检查、本地 Cocos 构建和现有 95 项检查通过；旧 BOW02 分裂断言按新玩法改写，没有增加测试依赖或额外正式测试用例。临时验证复用已有 GameSession 和浏览器入口。

首个打包样例暴露了 Creator loose spread 对 `Map` 的转换差异：原生 TS 中可用的 `[...map]` 被打包成单元素数组，闭合边读取失败。已改为显式 `Array.from(map.entries())`，再经最终正式包真实运行确认修复。不能用原生 TS 通过替代打包实机通过。

图示与动画只对真实截图裁切、缩放和 GIF 调色，播放间隔取实际 CDP 时间戳，没有合成中间帧：[前后对比](../../src/cocos/test-results/combat-graph-chain-v4/before-after.jpg)、[同箭原速连穿](../../src/cocos/test-results/combat-graph-chain-v4/live/bow-single-chain-live.gif)、[蓝色雷网原速](../../src/cocos/test-results/combat-graph-chain-v4/live/staff-thunder-net-live.gif)。
