# 3D 前摆抬腿 v6

用户随后要求身体按 2D 跑步设计整体前倾，当前 [v7](../3d-locomotion-v7/README.md) 保留本版抬腿、位移和步频，继续调整了胸肩与头部朝向。

2026-11-10。用户反馈 v5 的腿仍像平着迈步。本版在已直立的 v5 跑姿上，直接调整大腿前摆旋转，并延长抬膝阶段。

以原生 Blender FK 在 v5 的 run / run_staff 上增加前摆覆盖：大腿最大前摆约 88°，膝盖接近髋部高度；左腿在源帧 9.5—12.5 渐入，12.5—15 保持，15—19 渐出，右腿错开半个循环。保留原有小腿相对大腿的屈膝，足部保持原世界朝向，使小腿折回、鞋底明显离地。触地时按原鞋底间隙将覆盖权重降为零。

这次修改的是大腿本身的旋转及抬膝持续时间。超过 70° 前摆的时段由每条腿约 4% 的循环增至约 28%；最高膝关节由约 0.85 m 增至 0.96 m。原身体、骨盆、手臂、小腿、位移与其他曲线逐曲线哈希保持，仅替换两个跑步动作内两侧大腿和脚的旋转通道。移动速度、步频、步行与其他动作保持。

复用项目已有 Quaternius CC0 Sprint / Native65、Blender 四元数 rotation_difference / slerp、Cocos SkeletalAnimation。原生 FK 足以完成这次动作适配，不新增依赖、下载、生成图像或自写 IK 求解器。网格、UV、权重、材质、绑定与四款发型保持。

[源适配](raise-knees.py)、[可编辑文件](raphael.blend)、[完整曲线保护记录](source-verification.json)、[保存后真实抬腿角度检查](saved-source-review.json)、[逐帧位置](run-samples.json)。重新打开保存文件后，双侧抬腿均达到约 88°，超过 70° 的时段约 27.5%，不是仅依据导出前的参数判断。

实际 Cocos 画面：[半速前后对照](runtime/knee-lift-comparison-slow.gif)、[关键帧](runtime/knee-lift-keyframes.jpg)、[正常速度背面](runtime/back-walk-run.gif)、[正常速度侧面](runtime/side-walk-run.gif)。半速仅用于看清动作，游戏仍按原速度运行。工程与代理画面检查分开记录于 [art-review.json](art-review.json)，用户美术验收不提前声称通过。

[本地 3D 游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v6)。
