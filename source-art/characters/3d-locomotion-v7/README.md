# 参考 2D 的 3D 跑步前倾 v7

2026-11-10。用户指出 v6 上身过于竖直，应按 2D 跑步设计向前倾。本版保留 v6 的抬腿和安静的骨盆，调整胸肩、头部位置的整体前倾。

参考 [现有 2D 四向跑步](../2d-concepts/locomotion-repair-v3/shared-body-run.jpg)，经过实际侧面同屏比较，3D 的髋部至颈部方向从约 9° 调为约 22° 前倾；整个上身从下脊柱一起带动。胸、肩、手臂和背负装备随躯干前移，颈部补偿前倾，头部在原朝向上抬起 8°，避免仍显得低头看地。

只替换 run / run_staff 中 `spine_01`、`neck_01`、`Head` 的四元数旋转曲线。骨盆、两侧腿与脚的位置、抬膝时序、手臂自身摆动、身体起伏、接地、步频和速度保持。大腿最大前摆仍约 88°，每条腿超过 70° 的时段仍约 27.5%。其余十二个动作、16 个网格、UV、权重、材质、骨架绑定和四款发型保持。

复用现有 Blender 原生 FK / 四元数插值与 Cocos SkeletalAnimation，没有新依赖、下载、生图或运行时 IK。来源与许可沿用 [v5 的 Quaternius CC0 记录](../3d-locomotion-v5/README.md)。

[适配源](lean-run.py)、[可编辑文件](raphael.blend)、[曲线与腿部保护](source-verification.json)、[保存后真实前倾与抬腿检查](saved-source-review.json)。只有保存后回读及实际引擎画面均核对后才接入；工程检查、代理画面检查与用户美术认可分别记录。

实际 Cocos 预览：[半速前后对照](runtime/lean-run-comparison-slow.gif)、[关键帧](runtime/lean-run-keyframes.jpg)、[正常速度背面](runtime/back-walk-run.gif)、[正常速度侧面](runtime/side-walk-run.gif)。半速仅用于看清动作，游戏速度保持原样。

[本地 3D 游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v7)。
