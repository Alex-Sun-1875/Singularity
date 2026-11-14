# 走跑身体晃动收敛 v4

用户随后指出跑步仍显得缩身、低头、抬腿不明显。当前 3D 跑步已由 [v5](../3d-locomotion-v5/README.md) 替换为更直立的抬膝循环；本版步行继续保留。

2026-11-10。用户反馈 v3 身体晃动过大。本版在 v3 的腿型与脚步轨迹上，只收敛身体的横摆、扭转和上下起伏。

使用项目已有 Blender 4.5.15 的四元数插值、两骨 IK 和 CopyRotation。身体绕原有平均姿态运动，骨盆世界位移幅度保留 20%（前后为 30%），躯干各段旋转幅度保留约 22%，头颈约 25%。原生 IK 将双脚保持在 v3 原有的世界位置和朝向，再烘焙成 Cocos 普通骨骼动画；游戏中没有追加 IK。没有下载、引入新依赖或生成图片。

| 实测峰峰幅度 | v3 | v4 |
| --- | --- | --- |
| 跑步髋部上下起伏 | 20.2 cm | 4.0 cm |
| 跑步头部左右摆幅 | 17.0 cm | 3.8 cm |
| 跑步头部上下起伏 | 18.7 cm | 3.6 cm |
| 步行髋部上下起伏 | 5.2 cm | 1.0 cm |
| 步行头部左右摆幅 | 3.9 cm | 0.8 cm |

这些数字来自保存前完整循环的实际求值骨骼矩阵，见 [source-verification.json](source-verification.json)。步行统一降低身体均值约 2.3 cm，使减小起伏后整条腿仍可触及原来的脚步轨迹，不伸长骨骼。跑步身体平均高度保持。双脚世界轨迹最大误差约 0.002 mm，实际鞋底接地和原有跑步腾空高度保持。

仅替换 walk、walk_staff、run、run_staff 四个动作。移动速度、步频、动作时长、16 个网格的几何 / UV / 权重 / 材质、绑定骨架、四款发型及其他十个动作保持。可编辑源 [raphael.blend](raphael.blend)，适配入口 [stabilize.py](stabilize.py)，回读检查 [saved-source-review.json](saved-source-review.json)。基础库许可与来源沿用 [v3](../3d-locomotion-v3/README.md) 的 Quaternius CC0 记录。

实际 Cocos 正常速度采集：[背面前后对比](runtime/body-sway-before-after.gif)、[背面走跑](runtime/back-walk-run.gif)、[侧面走跑](runtime/side-walk-run.gif)。两侧保持同一相机、相位、速度与 30 fps / 2 秒采样，不调整播放时长。

保存后动作哈希、循环闭合、骨长 / 尺度和旋转连续性，Cocos web-mobile 构建、96 个静态装备 / 方向 / 相位及 240 个连续帧、实际走跑 / 暂停恢复 / 挥剑、2D / 3D 与行囊入口分别检查。最终结论见 [art-review.json](art-review.json)，安装见 [install-record.json](install-record.json)。技术检查和代理画面检查不代表用户已经认可美术效果。

[本地游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v4)。
