# 移动攻击与施法脚步 v1

战士及近战武器的动作已按用户反馈恢复为原有全身动作，不再单独替换腿部；见[战士动作恢复 v4](warrior-motion-v4.md)。

原地施法的短踏步、回步和重心变化已在 [v2](stationary-footwork-v2.md) 补充；下文保留本轮移动脚步的历史记录。

2026-11-12。修复主角移动攻击时整套骨骼只播放攻击／施法动作、双腿无法跟随位移的问题。适用当前 TapTap 小游戏的原生 3D 主角与绘制场景。

`PlayerCombatLocomotion` 复用已安装的 walk／run 动作、标定步速与 Cocos `AnimationState` 采样。采样骨架只有节点，没有网格、材质或第二个可见角色；在 Cocos 完成动作求值后，仅向髋部和腿部混入步态，并恢复上半身的原始世界位置与旋转，保留攻击姿势、手部和武器挂点。没有新增依赖、动作资源或生成素材。依据为 [Cocos 3.8 骨骼动画说明](https://docs.cocos.com/creator/3.8/manual/en/animation/skeletal-animation.html)。

脚步相位由实际位移和既有标定速度推进，连续普攻、切换攻击拍点不会重置。髋部跟随移动方向平滑转向，后退反向采样，侧移与后退切换带方向滞后。停止移动后冻结步态相位并用 0.10 秒退出混合；退出期间保留原有走／跑种类，避免瞬间换步。暂停保持腿部姿势；闪避、受击与死亡直接交还完整动作。原地施法使用原有动作。

近战沿用实时骨骼；弓和法杖只在移动攻击及短暂退出期间使用实时骨骼，退出后恢复原有烘焙路径。其他角色、技能规则、命中拍点、移动速度、资源加载与帧率设置沿用现有实现。

验证：类型检查通过，现有 116 项测试通过，Cocos 3.8.8 Web mobile 隔离构建完成。手机 844×390、DPR3 实际场景覆盖剑／弓／法杖普攻、火系／雷系／近战技能、后退、停止、暂停和闪避。记录中连续三个剑普攻动作仍保持步态相位连续；混合后上半身位置与旋转误差均低于 0.0001。浏览器没有脚本或控制台错误。代表帧内部审阅可见迈步变化，用户美术确认另计。

同时复用了现有移动瞄准浏览器检查，手机真实双指移动＋攻击、移动拉弓与松手射击、取消和桌面移动攻击均通过，详见 [input-review.json](../../test-results/combat-locomotion-v1/input-review.json)。

运行记录位于 [review.json](../../test-results/combat-locomotion-v1/review.json)，代表帧位于 [contact-sheet.jpg](../../test-results/combat-locomotion-v1/contact-sheet.jpg)。独立本地预览为 `http://127.0.0.1:18755/?view=2d&player=3d`，构建名 `concept-2d-combat-locomotion-v1`。Web 预览与这些检查不替代真实 TapTap AppID 下的平台和 Android 目标设备验收；真机效果、持续负载与耗电待验证。
