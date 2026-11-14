# 雷电三次放电、地面雷晕与怪物头顶反馈

后续片状区域电弧、蓝白亮芯与光团以[照片参考对齐v6](thunder-reference-v6.md)为准；当前默认包为`index.a3e4d.js`。

2026-11-08，按用户要求重新设计的v5基线；当时本地包实际加载`index.44f3a.js`。后续首击即铺雷晕、余电跟随移动敌人和有机怪兽/Boss以[最新运行记录](monster-ecology-v1.md)为准，当前默认包为`index.d210f.js`；下文保留v5原始验证状态。

雷电保留已确认的最近可见敌人互连网。重新参考 `combat-thu.png` 的电蓝与冰蓝高光，消除上一版偏青、等宽的线管；主体、细亮芯、柔晕和局部断闪分别组织。颜色取样与说明保存在 [palette-sampling.json](../../source-art/skills/pure-skills-v2/thunder-ground-v1/palette-sampling.json)。

每次实际雷击触发三次短促放电，释放后的窗口为 `0–0.105s`、`0.18–0.275s`、`0.40–0.54s`。每次脉冲用不同分形种子，端点仍来自同一批权威连接；后两次只在敌人之间重放余电，不重复从已经收势的施法者手部发射。原本有多拍真实伤害的雷法在新拍到达时替换当前连接图，避免叠加多套网挤满渲染池。表现重复不增加伤害、命中目标或被动触发。

最后放电后保留约 1.5 秒地面雷晕，由局部深蓝紫透明雾团和较低亮度的蓝色碎余电组成；同一受击点合并刷新，另有弱宽场雾。到最后实际拍之后 2 秒全部结束。地晕使用原生透明 quad、地形高度与有界复用池，没有描边圈、碰撞、额外伤害或全图光照修改。五张原始软雾/碎电遮罩由已有 Pillow 确定性生成，未使用生成模型、下载或新依赖；[来源与实现记录](../../source-art/skills/pure-skills-v2/thunder-ground-v1/README.md)保留首次白裂纹失败样例和最终实际审阅。

怪物反馈复用既有 HUD 与 Cocos Graphics、Label、UIOpacity：

- 真实受伤后显示约 3.2 秒红色生命条及短暂失血层，锚点读取该怪自有图集 idle 透明边界，避免透明画布或抬武器把血条顶高。普通怪被一击击杀时短暂显示归零条约 0.28 秒，再清理。
- 明确瞄准的活目标躲开实际攻击，或弹体当前飞行段失手，才由核心发出 `miss` 事件并在该目标头顶显示 `MISS`，上浮淡出约 0.72 秒。空挥、未发射就取消、已经命中、盾挡或死亡目标不会被随意标为 MISS。
- 普通攻击与弹体使用独立反馈意图元数据；这些字段不参与筛敌或碰撞过滤。单箭转向连穿的当前段落空可提示 MISS，仍保持同一个箭体及原来的总目标预算。
- 血条和文字各有 24 项复用上限；目标移动、暂停、换区、死亡、出屏、到期和窗口调整均有清理或重建路径。

| 最终证据 | 结果 |
| --- | --- |
| [雷电时序与实际 HP](../../src/cocos/test-results/thunder-resonance-v5/actual-resonance.json) | 按真实 `action.releaseAt` 采样，三次放电分别 70/64/64 条 Line，两段间隙均为 0；余晕时 9 个地面块、胸高连线为 0，最终全清。8 个目标只受最初 8 次真实命中，后续 HP 完全不变。 |
| [4 秒原速雷电](../../src/cocos/test-results/thunder-resonance-v5/three-pulse-ground-live-compact.gif) | 独立真实 ChapterGame 连续运行，227 个原始 CDP 帧、157 个状态采样；轻量动画只抽取原帧并依原时间戳播放，没有插帧或慢放。[保留帧与时长](../../src/cocos/test-results/thunder-resonance-v5/compact-animation-artifacts.json)。 |
| [真实头顶反馈](../../src/cocos/test-results/enemy-feedback-v5/actual-feedback-review.json) | HP700 实际受伤至 444 显示生命条；连穿箭冻结的下一段目标移开后收到真实 MISS。移动跟随、未知目标、暂停、到期、resize 均通过。HP72 怪真实一击死亡后短显归零条，0.333 秒后无残留。 |
| [MISS 规则](../../src/cocos/test-results/miss-feedback-v5/core-audit.json) | 9 个实际 GameSession 场景通过；无随机命中率规则，没有改伤害、筛敌、范围或弹道。 |

类型检查、Cocos 本地构建及现有 95 项检查通过；最终实机无浏览器异常或失败请求。检查复用了原有入口，没有新增正式测试脚手架或依赖。血条验证使用合法 40 级经验状态，并区分真实命中死亡与直接设置 HP 的 UI 清理合同。

[实机总览](../../src/cocos/test-results/thunder-resonance-v5/effect-feedback-overview.jpg)和[八个时序帧](../../src/cocos/test-results/thunder-resonance-v5/three-pulse-ground-contact.jpg)只裁切缩放原生画面。本记录是代表实现与画面复核，不声称用户验收或全部阶级逐项美术通过。
