# 完整跑姿协调 v8

2026-11-10。调整实际 3D 主角的 run / run_staff，以当前 2D 运行清单的完整八帧跑步为姿态参考。2D 身体图集未修改。

v7 将抬膝延长后，向后伸髋只剩约 3–5°，容易形成踏步感。本版复用已有 Quaternius UAL1 Sprint_Loop 的整套周期，保留完整前后步幅；同一条 Blender 时间曲线同时重采样所有关节，延长有效支撑和后蹬，缩短腾空回收中的停留。前倾约 18.4–20°，向后伸髋约 31–32°，向前抬腿峰值约 69–70°，身体起伏约 4.9cm。手臂保留原作对侧腿时序与约 80–96°屈肘，调整上臂平均方向和幅度，使双臂交替摆动。保留原脚掌滚动，平滑旋转；不在脚接近竖直时强行解算水平欧拉朝向。

工具复用 Blender 4.5.15 原生 FK、IK、Bezier 曲线与四元数，以及 Cocos Creator 3.8.8 SkeletalAnimation。没有运行时 IK、新依赖、下载或生图。仅修改两条跑步动作，另十二条动作、16 个网格、绑定、材质、UV、权重和四款发型保护检查通过。后续外形重导出通过现有 `locomotion_refinement.py` 保留本版四条已整理的走跑动作。

来源选择先比较已缓存 UAL Sprint/Jog、KayKit Running A/B 与 CMU 16_36 的完整周期（`inspect-candidates.py`、`candidates.json`）。采用与原骨架相同的 UAL Sprint，避免跨骨架比例转换影响原角色；适配代码仅负责节奏、姿态、窄腿道和脚底接触。UAL 官方来源与 CC0：[Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)。候选 KayKit 来源与许可：[KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations)。未安装或升级第三方软件。

制作入口：`coordinate-run.py`；可编辑源：`raphael.blend`；运行资源：`raphael-polish.glb`；源曲线与保护：`source-verification.json`、`saved-source-review.json`。工程检查、代理画面审阅与用户美术认可分别登记，`art-review.json` 的 `userApproved` 仍为 false。

实际 Cocos 检查覆盖四向及弓/杖的 96 个静态采样、240 个连续动作采样、120 个带固定地面参照的移动采样；所有静态图最小边距 20px，避免长步幅在审阅图中被裁断。移动采样按游戏 5.2m/s 平移角色与跟随相机；正常 ChapterGame 更新另行验证实际速度、自动步频、暂停恢复及攻击。预览使用工程真实网格、动画、材质和武器挂点。

正常速度预览：`runtime/coordinated-run.gif`，左为当前 2D 全周期，中为 3D 侧面，右为 3D 背面；地面格线每格 0.5m。`runtime/side-walk-run.gif` 与 `runtime/back-walk-run.gif` 为 2 秒走跑预览。美术审阅不是 TapTap 真机或用户认可结论。

默认试玩：[新版 3D 主角](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v8)。以实际 actor-raphael 资源配置哈希核实页面版本，不能只依据 URL 的 revision 字段。本轮发现原用户标签页实际仍加载 v5，另开新版供复核。
