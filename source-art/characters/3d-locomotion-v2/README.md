# 3D 走跑节奏与步行姿势调整

后续双腿外撇、摆臂和完整走跑姿势已参照 2D 调整，当前动作来源与实际游戏预览见 [locomotion-v3](../3d-locomotion-v3/README.md)。本目录保留上一轮节奏调整记录。

当前 3D 人物的常规跑速从 3.6 提到 5.2 米/秒（+44.4%）。保留已对齐接地的紧凑跑步动作，通过实际位移驱动播放速度：常规跑步从约 1.00× 提到 1.44×，循环约 0.93 → 0.65 秒，约 129 → 186 步/分。Shift 步行保持 1.6 米/秒。纯 2D 的原有速度维持 3.6 米/秒。

复用当前 Native65、四款 v3 发型、Blender 原生四元数插值/FK、Cocos SkeletalAnimation 与现有 UAL1 Walk_Loop。只细修 walk / walk_staff：减小骨盆横摆、肩颈和躯干反扭；收敛摆臂幅度，放松空手肘部、手腕和手指；用求值后的鞋底做 root 的垂直接地修正。持杖右侧完整局部握持链保留。没有独立挪动手掌、改变骨长或重绑蒙皮。

步行名义速度由实际支撑脚轨迹测得约 1.005 米/秒，用于匹配位移与步频。走跑切换按实际速度并带 2.0 / 2.3 米/秒滞回；玩家的动画测速上限调整为 8，覆盖加速装备。GameSession 的速度配置只在内存中存在，创建/读档/切区域后由当前 3D 展示入口配置，不增加存档字段。

[可编辑来源](raphael.blend)、[导出与校验](refine-walk.py)、[网格/权重/材质与动作保护记录](source-verification.json)。16 个网格、全部 UV/权重/材质、绑定骨架、四款发型保持；其余 12 组动作曲线保持，包括攻击、拉弓、奔跑、翻滚。背弓继续沿用 bow-back-contact-v2 中背挂点与校准。没有生成图片、新下载或新依赖。

[正常速度前后对比](runtime/locomotion-comparison.webm)（60 帧/2 秒，两侧均为 30 fps；不是慢放）。[GIF](runtime/locomotion-comparison.gif)、[编码与时长校验](runtime/preview-review.json)、[实际游戏帧循环检查](runtime/live-review.json)、[三类武器正侧面与握持](runtime/poses/contact.jpg)、[48 个武器姿势检查](runtime/poses/report.json)。

验证复用已有类型检查、Cocos web-mobile 构建及 Playwright 角色检查脚本；检查真实帧循环中的跑速/步频、Shift 步行、暂停恢复、挥剑，另检查三类武器挂载、四款发型、纯 2D 入口和行囊预览。[外观重导出适配器](../../../tools/model-pipeline/locomotion_refinement.py) 复用这两组已编辑动作，防止后续只更新发型时回退走路姿势；[适配器检查](check-reexport.py)。

[接入记录](install-record.json)、[实际画面观察](art-review.json)。工程校验与画面检查分别记录；用户美术验收仍等待反馈。

[本地 3D 入口](http://127.0.0.1:7469/?view=2d&player=3d&hair=dante&revision=locomotion-v2)。重新导出请以本目录为当前动作来源，构建及画面复核后运行 install.py。
