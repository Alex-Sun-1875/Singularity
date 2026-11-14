# 3D 抬头挺胸跑姿 v5

用户反馈本版抬腿仍不明显。当前 [v6](../3d-locomotion-v6/README.md) 保留本版上身姿势，直接加大并延长大腿前摆抬膝阶段。

2026-11-10。用户指出 v4 跑步仍缩成一团、低头、抬腿不明显。本版替换 3D 主角的 run / run_staff，2D 仅作为动作设计参考，2D 贴图没有修改。

复用项目已安装的 Quaternius CC0 `UAL1__Sprint_Loop`，使用同一 Native65 骨架。胸肩以当前站姿为基础，沿用 Sprint 的肩肘摆动、屈膝与后蹬时序；原生 Blender FK 将躯干调整为约 9° 的轻微前倾，颈部与头部使用站姿的世界朝向保持视线向前。抬高骨盆平均位置约 8 cm，前摆腿在对侧支撑阶段增加抬膝，双腿保持窄轨道。上身上下起伏维持约 3.5 cm。

足部沿用 Blender 原生两骨 IK、无伸长，CopyRotation 保留原生脚踝俯仰，以世界侧轴投影校正脚尖朝向，避免欧拉角翻转。按左右鞋底分别校正接地，双脚腾空的共同间隙最高约 5 cm。支撑脚名义速度约 5.24 米/秒，角色移动仍为 5.2 米/秒，由原有运行时按位移匹配播放速度；循环约 0.67 秒。

当前求值记录：骨盆平均高度约 0.95 m（v4 约 0.87 m），头部高度约 1.58—1.61 m（v4 约 1.45—1.49 m），最高膝关节约 0.85 m（v4 约 0.75 m）。这些数值仅描述姿势变化，是否美观仍需实际画面判断。[姿势与保护记录](source-verification.json)、[逐相位骨骼与鞋底](run-samples.json)。

动作源：[rebuild-run.py](rebuild-run.py)、[可编辑文件](raphael.blend)、[保存后回读](saved-source-review.json)。仅本轮两个跑步动作改变，步行、其他十个动作、16 个网格、UV、权重、材质、绑定和四款发型保持。用于外观重导出的权威动作集仍包括四个走跑动作，以免后续导出回退 v4 的步行。

`stage.py` 将现有 Cocos GLB metadata 中两个跑步剪辑的范围从 28 帧同步为 20 帧，保留原资源与子资源 UUID；这一步与实际动画数据同时更新，避免旧剪辑末尾补入停顿。

来源与许可：[项目原包校验](../library-kits/sources.json)、[Quaternius 官方 CC0 动作库](https://quaternius.com/packs/universalanimationlibrary.html)。沿用现有 Blender 4.5.15 / Cocos 3.8.8 管线，没有新下载、依赖或生成式图片。

实际游戏预览：[侧面新旧跑姿](runtime/upright-run-before-after.gif)、[背面走跑](runtime/back-walk-run.gif)、[侧面走跑](runtime/side-walk-run.gif)。工程与画面检查分别记录于 [art-review.json](art-review.json)，用户美术验收不预先声称通过。

[本地 3D 游戏](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v5)。
