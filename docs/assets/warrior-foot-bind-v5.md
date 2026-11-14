# 战士连斩脚部绑定修复 v5

2026-11-12。用户反馈 v4 后脚部仍歪。v4 仅关闭额外走跑／原地踏步层，没有修复连斩载体与主角色的骨架差异。

当前主角色实际加载 `raphael-polish.glb`。旧第二、三刀由 UAL 素材人形的 FBX 直接导出：腿长、脚部绑定轴、模型缩放与当前角色不同，运行时腿部局部平移相对角色基线最多偏离约 0.0458 米。此外 FBX 把 Y-up 转换分配到父节点与根骨骼，和主角色 GLB 的转换层级不同；跨片段混合会同时插值两套表示。

`build-player-melee-combo.py` 继续采样已有 CC0 UAL2 B/C 动作，改用当前角色 manifest 指定的完整源骨架烘焙，并沿用主角色 GLB 的导出参数。新载体为 `combos-native.glb`，原运行 FBX 已移除；`Actors` 加载新载体。用角色实际靴子几何校准竖直根位移，使支撑脚接地；保留原有髋、膝、踝、脚趾动作和战斗时序。战士仍不叠加独立踏步层。

类型检查及 Cocos Web mobile 构建通过。复用现有运行检查，覆盖静止／移动普攻、WAR_01/02/03/05 共十组，确认三段动作均运行，额外脚步层为零，挂点和实际绘制关节一致。另逐帧抽查三段原动作：腿部局部平移与角色基线差异小于 0.000001 米，根骨骼朝向统一；法师切入战士无叠加残留，法师、弓的踏步继续生效。此次未新增正式测试或依赖。

[导出来源](../../source-art/characters/player-melee-combo-v1/provenance.json)、[运行记录](../../test-results/warrior-foot-bind-v5/review.json)、[绑定比对](../../test-results/warrior-foot-bind-v5/binding-review.json)、[动作抽帧](../../test-results/warrior-foot-bind-v5/source-poses.jpg)分别登记。画面已内部复查，用户美术确认另计。默认 `7469` 与检查版 `18755` 同步使用本次构建；已打开的页面需重新加载。浏览器检查不代替 TapTap AppID 及 Android 真机验收。

默认 `7469` 入口重新加载后，已实际运行第一、二、三刀及回到待机，未出现页面错误；[原速连斩预览](../../test-results/warrior-foot-bind-v5/warrior-combo.gif)取自该入口的真实画面，40 帧约 1.33 秒。
