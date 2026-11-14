# 参考 2D 的 3D 走跑姿势调整 v3

用户随后反馈身体晃动过大，已在 [v4](../3d-locomotion-v4/README.md) 收敛骨盆、躯干与头肩摆幅，脚步和速度保持。当前导出与游戏入口以 v4 为准。

2026-11-10。针对背向跑步双腿外撇、步行显老的问题，参考当前 2D 的 [步行](../2d-concepts/locomotion-repair-v3/shared-body-walk.jpg)与[跑步](../2d-concepts/locomotion-repair-v3/shared-body-run.jpg)，调整整套四向可见的 3D 步态。

复用已安装的 Quaternius CC0 Native65 / UAL1 Walk_Loop、Jog_Fwd_Loop、Blender 4.5.15 LTS 原生双骨 IK / CopyRotation / 四元数 FK，以及 Cocos 3.8.8 SkeletalAnimation。未下载、安装依赖或生成图像。许可和原包校验沿用 [库来源](../library-kits/sources.json)；[原生 IK 文档](https://docs.blender.org/manual/en/3.0/animation/constraints/tracking/ik_solver.html)。定制工作是现有动作的局部适配，未另写 IK 求解器或替换骨架。

- 双脚收回髋部下方：步行踝部轨道间距约 14.6 cm，跑步约 13 cm；膝盖弯曲平面朝前，减少脚尖扭转和侧向甩腿。
- 保留作者的前后迈步与屈膝时序，收敛脚步横摆、步行抬脚与跑步腾空高度；整条肩肘腕 FK 收窄摆臂，持杖右臂继续沿用现有握持链。
- 从原生库恢复闭合的下身循环，消除旧适配文件的首尾漂移。按实际鞋底做 root 垂直接地修正，骨长不伸缩。
- 3D 移动速度保持步行 1.6、跑步 5.2 米/秒；根据支撑脚轨迹重算名义速度（约 0.899 / 3.651 米/秒），由现有运行时代码匹配位移与步频。没有用整体加速替代姿势修改。

仅替换 walk、walk_staff、run、run_staff 四个动作；16 个网格的顶点、拓扑、UV、权重、材质与骨架绑定哈希相同，四款发型及其余十个动作曲线保持。[可编辑源](raphael.blend)、[适配导出](refine.py)、[保护记录](source-verification.json)、[保存后回读](saved-source-review.json)。[外观重导出适配器](../../../tools/model-pipeline/locomotion_refinement.py)同步指向本版，避免后续改发型时回退步态。

实际 Cocos 画面：[背面正常速度](runtime/back-walk-run.gif)、[侧面正常速度](runtime/side-walk-run.gif)、[背向前后帧对照](runtime/back-before-after.jpg)。动图是实际引擎 RenderTexture、30 fps 的 60 帧 / 2 秒采样；Pillow 排版与既有 ffmpeg 编码，未改播放时长。不是新生成的 2D 动画。

验证复用类型检查、Cocos web-mobile 构建、原有 Playwright 角色采集与正常帧循环检查。96 个方向 / 相位 / 装备画面无脚本错误，另采集 240 个连续帧；正常运行检查步行 / 跑步、暂停恢复和挥剑；默认 2D、可选 3D、四款发型和行囊预览检查通过。详见 [静帧记录](runtime/after/report.json)、[连续采样](runtime/after-motion/report.json)、[实际游戏循环](runtime/live-review.json)、[入口与换装](runtime/canonical-smoke.json)。

工程验证和代理画面检查分别记录于 [art-review.json](art-review.json)。尚未声称用户已通过美术验收。正式接入记录见 [install-record.json](install-record.json)。

[本地游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v3)。
