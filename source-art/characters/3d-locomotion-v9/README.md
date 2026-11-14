# 走跑骨盆与躯干协调 v9

2026-11-10。针对用户指出的“走路上半身固定、跑步一直撅臀”，同时修改实际 3D 的 walk / walk_staff / run / run_staff。2D 图集没有修改。

v8 步行的骨盆偏航仅约 0.5°、胸部约 1.8°；跑步骨盆相对待机一直前压约 28°，下腰向后补偿约 23°。本版将骨盆恢复至中性步行参考，分散调整腰、胸的前倾，恢复随脚步交替的骨盆与胸肩活动。步行骨盆活动约 6.3°、胸部约 16°；跑步骨盆前倾约 6–11°，躯干保持约 14–17°前倾，并随支撑转换自然变化。头部保留轻微跟随和视线稳定；不把全套上半身锁在世界朝向。

步行复用缓存的 CC0 Quaternius UAL1 Walk_Loop。跑步骨盆、脊柱、头部的活动复用已缓存并已转至 Native65 的 CMU 16_36（2–26 帧），均值回正后以左腿摆动匹配周期，相关系数约 0.948；保留 v8 已整理的完整 UAL 摆臂、抬腿、后蹬与脚掌轨迹。使用现有 Blender FK / 原生无拉伸双骨 IK，在转髋后保持脚掌落点；最大必要根节点高度调整约 2.6mm。游戏仍只播放烘焙骨骼动画，没有新增运行时 IK、平台 API、依赖或下载。

来源、许可与取舍见 `motion-sources.json`。UAL 为 CC0：[官方动画库](https://quaternius.com/packs/universalanimationlibrary.html)。CMU 数据允许用于商业产品，不能单独转售数据；现有转换版本使用说明位于 `source-art/characters/mocap/cmu/READMEFIRST.txt` 的 Usage Rights，官方来源为 [CMU Graphics Lab Motion Capture Database](https://mocap.cs.cmu.edu/)。离线重定向沿用已部署的 BVH Retargeter 4.4.0，没有将其加入游戏运行依赖。来源与致谢同步至运行清单及第三方声明。

制作：`responsive-body.py`；编辑源：`raphael.blend`；运行文件：`raphael-polish.glb`。`inspect-posture.py` / `posture-before.json` 是问题诊断，`source-verification.json` 与保存后重新读取的 `saved-source-review.json` 是工程证据。四条走跑动作外的十条动作、16 个网格、绑定、UV、权重、材质及四款发型均保护。重新导出外形继续通过现有 `locomotion_refinement.py` 保留本版动作。

预览使用真实 Cocos Creator 3.8.8 角色、材质、武器挂点和骨骼动画。`runtime/body-side-comparison.gif` 与 `runtime/body-back-comparison.gif` 是正常速度前后对比；`runtime/responsive-walk-run.gif` 展示新版侧面、背面的步行与跑步，固定地面格线每格 0.5m，角色和跟随相机按实际步行 1.6m/s、跑步 5.2m/s 移动。

复用现有检查覆盖四向弓/杖 96 个静态采样、240 个连续动作采样、240 个带地面参照的移动采样，以及正常 ChapterGame 的步频、移动、暂停恢复、攻击和外形重导出。工程检查、代理画面审阅与用户美术认可分别记录。`art-review.json` 不代替用户认可或 TapTap 真机验收。

本地试玩：[v9 3D 主角](http://127.0.0.1:7469/?view=2d&player=3d&revision=locomotion-v9)。页面版本以实际加载的 actor-raphael 配置哈希核对。
