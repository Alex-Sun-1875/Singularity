# 侧面跑步腿线与夹角 v10

**已撤回。** 用户反馈不如调整前，当前恢复为 [v9 跑姿](../3d-locomotion-v9/README.md)。本目录保留试调记录，不能作为当前接入版本。

2026-11-15 资源清理：已将本版 `raphael.blend`、`raphael-polish.glb`、`preview/side-leg-angle.gif` 和两张试调预览移至仓库外可恢复归档。当前 v9 资源及其制作依赖保留；本目录的脚本、来源、撤回记录、验收报告和代表静态画面继续保留。下文描述历史制作过程，重新运行本版安装或检查脚本前需先按[清理清单](../../../tools/resource-cleanup-2026-11-15.json)恢复对应文件。

2026-11-10。用户明确要求调整**侧面**的支撑腿与抬起腿的斜向关系。本版只修改 3D run / run_staff；以当前 2D 跑步的侧面姿态为参考。

前腿的大腿保持约 66–67° 前抬，小腿向膝下、身体方向收回，改变原来抬腿时小腿近乎竖直下垂的轮廓。后侧腿在对侧抬膝时形成更清楚的斜向伸展，支撑中段落点向后微调，腾空后保留向下、向后的脚尖方向。脚踝曲线经过连续平滑，随后用原生无拉伸双骨 IK 求解并烘焙；不把关键帧的脚踝姿势突然切换。

复用现有 Native65 动作、Blender 4.5.15 的 FK / 原生 IK / 四元数曲线及现有脚底采样方法，没有新增动画引擎、运行时 IK、依赖、模型或下载。现成组件依据：[Blender 4.5 IK Constraint](https://docs.blender.org/manual/id/4.5/animation/constraints/tracking/ik_solver.html)。本轮代码是按 2D 姿态布置目标和烘焙的离线适配，腿长与关节求解由 Blender 原生约束完成。

v9 的上半身、骨盆、摆臂、头部、根节点、时序与步频曲线均以排除六根腿骨后的曲线 SHA 核实保持；脚踝左右轨迹保留。步行、持杖步行及其他十条动作完全保持，16 个网格、绑定、UV、权重、材质和四款发型保护检查通过。后续外形重导出仍装入四条完整的已整理走跑动作。

制作入口：`side-legs.py`；编辑源：`raphael.blend`；运行模型：`raphael-polish.glb`；工程保护：`source-verification.json`、`saved-source-review.json`。`back-view-study.py` 和 `diagonal-legs.py` 为用户澄清前的背面试调记录，已停用，未接入；正式源从 v9 重新读取，仅做本版侧面调整。

`preview/side-leg-angle.gif` 是实际 3D 源动作的离线 Blender 腿部预览，按游戏跑步节奏播放，并与当前 2D 侧面参考、v9 源动作对照。画面裁切到腿部并转为灰度，核对姿态、夹角、回收和接地。它不是 Cocos 游戏截图，整角色仍使用现有 Cocos 材质和武器挂点。

当前 Work 设置禁用了本地浏览器访问。本轮未绕过设置控制浏览器，验证使用保存后源动作回读、离线连续渲染与 Cocos 3.8.8 构建/导入检查；游戏页面与 TapTap 真机的本轮画面尚待人工复核。`art-review.json` 区分代理源动作审阅、引擎实机审阅与用户认可。

[本地 v10 试玩](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v10)。来源与许可沿用 v9：Quaternius UAL 为 CC0，v9 身体活动使用的 CMU 数据及致谢保持。
