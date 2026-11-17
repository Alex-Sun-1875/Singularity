# 战士最终技：刀气逐波真实命中 v40

使用最新正常 test 生产构建录制，无预览、碰撞替身或自制 effect 注入。五个实际技能等级分别验证 1／2／2／3／3 道刀气；每道亮芯前移时可独立命中同一敌人一次，命中去重按 cast／waveIndex／target 分开。

前两斩仍各占 20% 伤害，末段 60% 总预算按道数分摊，**没有把每道都变成额外一份 60% 伤害**。旧第三段瞬时扇面已经由移动刀气命中替换。真实碰撞与已批准月牙共用轮廓参数、出生时刻和推进曲线，仅有效亮芯造成伤害，尾流与末期散气不伤害。

## 实装展示

- **[三道逐波命中慢放](media/three-wave-detail-slow.gif)**
- [等级 1／3／5 原速对照](media/wave-count-comparison.gif) / [视频](media/wave-count-comparison.mp4)
- [1 道](media/wave-count-1.mp4) / [2 道](media/wave-count-2.mp4) / [3 道](media/wave-count-3.mp4) 原速
- [普通地面 3 道](media/three-waves-field.mp4)
- [单道到达时机](media/single-wave-crescent.gif) / [三道慢放视频](media/three-waves-slow.mp4)
- [命中阶段图](media/three-wave-stages.jpg) / [三档概览](media/wave-count-overview.jpg)
- 正常机位与 HUD：[靶场](media/normal-hud-training.jpg) / [普通地面](media/normal-hud-field.jpg)

沿路靶初始位于前方 7 米、9 米，避开前两斩原有近战范围，保留真实受击位移。侧方对照在前方 7 米、侧偏 1.6 米，身后对照在后方 3 米。排版数字直接读取真实目标 HP，不生成或预演扣血；原速 3.6 秒、30 fps，慢放 0.5×。

## 验证

所有实际等级逐一核对每波对两只路径靶分别命中一次，首波抵达前 HP 不变，7 米靶先于 9 米靶掉血，侧方／身后保持无伤。后续击退会自然延后接触时间；逐击使用 `skill_hit.to` 实际目标坐标及地表高差，调用生产 `warriorUltimateTouches` 核对该波上一逻辑步至当前 `waveAge` 的扫掠，不强求后波在初始靶位命中。HP 损失另与真实 `hit.hpLost` 事件逐项相符。

保留原形状、共享网格、scale=1、同形同高、0.22 秒间隔、收招后前进与渲染检查。1/60 秒和 0.2 秒渲染推进所得命中集合及伤害值一致；生产 GameSession 会进一步拆成不超过 0.02 秒逻辑子步，该录制不冒充未细分大逻辑步的扫掠测试。

暂停验证时钟与刀气位置冻结，暂停期间不扣血，恢复后继续前行命中。普通地面 HP 严格冻结；靶场真实 `prepareFrame` 会回满登记靶 HP，正常 HUD 或恢复菜单触发的回满如实记录，不作为伤害或冻结失败。clear 后再推进 0.4 秒不补伤。另通过实际离开训练场转场，验证原场景视觉与伤害状态不在新场景继续。结果及完整媒体解码记录在 `provenance.json`。

录制使用一次性浏览器上下文，仅在内存设置训练角色。没有修改正式档位门控或用户存档，没有制作 TapTap 包；浏览器实装验收不替代 TapTap 真机与性能验收。
