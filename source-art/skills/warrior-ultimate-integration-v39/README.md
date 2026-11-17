# 战士最终技 v38：生产接入验收 v39

直接从最新 `src/cocos/build/concept-2d` 正常 test 构建录制，使用生产 `NativeSkillVfx → WarriorSkillEffects.ultimate` 路径及资源。没有注入旧预览、轮廓 profile、自制 effect 或渲染替换。角色、三段动作与命中均来自真实游戏时钟；录制环境是一次性浏览器上下文，仅在内存设置 80 级训练角色，不修改正式档位门控或用户存档。

已接入的等级表现：1 级 1 道，2–3 级 2 道，4–5 级 3 道。五个实际等级全部分别录制，展示对照取 1、3、5 级。**增道属于表现层，未给每道刀气增加伤害**；真实命中仍由原有三段动作事件处理，未修改 PureCombat／PureSkills 的伤害规则。

## 实装展示

- **[三道同形同高慢放](media/three-wave-detail-slow.gif)**
- [等级 1／3／5 原速对照 GIF](media/wave-count-comparison.gif) / [视频](media/wave-count-comparison.mp4)
- [1 道原速](media/wave-count-1.mp4) / [2 道原速](media/wave-count-2.mp4) / [3 道原速](media/wave-count-3.mp4)
- [普通地面 3 道实装](media/three-waves-field.mp4)
- [单道近景](media/single-wave-crescent.gif) / [三道慢放视频](media/three-waves-slow.mp4)
- [阶段图](media/three-wave-stages.jpg) / [三档概览](media/wave-count-overview.jpg)

每段原速 3.6 秒、30 fps。画面使用固定裁切，不复制单波进行叠加。正常游戏机位并保留 HUD 的截图：[靶场](media/normal-hud-training.jpg) / [普通地面](media/normal-hud-field.jpg)。正常机位下后期远行波尖端可能移出画面，近景录制保留完整轮廓用于验收。

## 验证范围

逐一核对五等级 `[1,2,2,3,3]` 道数、同一生产共享网格、全部波龄的 18 点轮廓与高度严格一致、实际 scale=1、0.22 秒连发、固定世界高度、收招后继续前进、三段原生动作无中途 idle、渲染与池容量。真实 skill_hit 数量及三段事件据实登记，没有套用旧版平衡数值。

普通地面通过真实 pause／close 菜单检验暂停时钟与位置冻结、隐藏并保留余波、同位置恢复及继续推进。靶场通过真实 training-range 暂停分支验证效果；fixture 强行直接调用 `open('pause')` 未走训练场正常设置路由，返回 `Unknown or unbuilt area: TRAINING`，该调用不作为正常训练场界面验收，也不算本次 VFX 渲染失败。另验证引擎暂停、自然过期、正式 clear 后 cue／原点缓存／活跃层归零；网格与材质池保留为正常复用。

视频与 GIF 完整解码核对帧数、速度与时长，证据记录于 `provenance.json`。类型检查、171 项既有测试和正常 test 构建日志由主任务提供。本轮没有制作 TapTap 包，浏览器实装验收不替代 TapTap 平台或真机性能验收。
