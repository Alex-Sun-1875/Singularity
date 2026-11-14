# 原地施法踏步与重心 v2

用户随后要求恢复战士原有全身动作：近战武器与 WAR 技能不再叠加本文的独立脚步和重心修正，当前适用范围见[战士动作恢复 v4](warrior-motion-v4.md)。

2026-11-12。按用户补充要求，为原地技能和普攻加入短踏步、落脚承力与收势回步。接入当前原生 3D 主角的 `PlayerCombatLocomotion`，起手约向前迈 0.15 米、抬脚最高约 0.055 米；连续动作交替领步脚，另一只脚保持支撑。身体同时侧向换重心、略微下沉并前移约 0.045 米。拉弓在踏稳后保持站姿，持续蓄力时有轻微重心起伏。

踏步、落脚和回步读取当前动作的 `elapsed`、`releaseAt` 与 `duration`。从移动施法停下时按剩余动作时间接入，移动后淡出原地踏步并接回已有走跑层；暂停冻结脚步，闪避、受击和死亡使用完整动作。脚下的视觉位移不写入玩家坐标。

两条腿通过解析两段 IK 保持骨段长度、支撑脚锚点与脚掌方向；按待机姿势的脚踝高度标定接地位置，髋部和上半身一起转移重心。连段抬高髋部时自动屈膝下沉，使双脚仍能抵达目标。武器挂点从修正后的真实骨骼重新绑定；每帧先还原上次的局部骨骼修正，再采样新动作，防止常量通道或播放模式切换造成姿势残留和挂点偏移。

`TwoBoneLegIK.ts` 的位置求解适配自本机已安装的 Cocos Creator 3.8.8 源码，移除调试器并接入 Cocos Node 的世界旋转。项目当前使用 `SkeletalAnimation`，因此采用节点适配，避免为此迁移到实验性姿势图；没有新增运行依赖、动作包或贴图。

官方参考：[两段 IK](https://docs.cocos.com/creator/3.8/manual/en/animation/marionette/procedural-animation/pose-graph/pose-nodes/modify-pose.html)、[程序式动画](https://docs.cocos.com/creator/3.8/manual/en/animation/marionette/procedural-animation/)。源文件为 `cocos/animation/marionette/pose-graph/pose-nodes/ik/solve-two-bone-ik.ts`，MIT 许可与署名保留于适配文件及两个 Web 模板的 `THIRD_PARTY_NOTICES.txt`。

当前源码及构建快照的类型检查通过，现有 120 项测试通过，Cocos 3.8.8 Web mobile 隔离构建完成。844×390、DPR3 的浏览器实际场景覆盖火系、长雷系终极、近战连段、弓术、连续法杖普攻及持续拉弓，含原地与移动互切、暂停恢复及闪避优先。迈步达到 0.15 米，抬脚约 0.055 米；连续法杖普攻记录到左右脚交替领步。完全接入后最大脚部目标误差低于 0.00026 米，骨段长度误差低于 0.000001 米，挂点与真实骨骼位置一致；实际玩家坐标保持原位。六组移动攻击回归及既有真实双指／键盘输入检查通过，浏览器无脚本或控制台错误。

[运行记录](../../test-results/stationary-footwork-v2/review.json)、[移动回归](../../test-results/stationary-footwork-v2/moving-review.json)、[触控检查](../../test-results/stationary-footwork-v2/input-review.json)与[代表帧](../../test-results/stationary-footwork-v2/contact-sheet.jpg)分别保存。代表帧经过内部审阅，用户美术确认另计。新版仍使用本地预览 `http://127.0.0.1:18755/?view=2d&player=3d`；真实 TapTap AppID 下的平台、Android 目标设备与持续负载验收待验证。
