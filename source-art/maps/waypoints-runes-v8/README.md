# 古代符文传送阵 v8

按用户最新要求从空间裂隙重新设计为符文传送阵，参考《博德之门3》Ancient Sigil Circle 的发光刻线、断开的圆环和几何符号语言，保持左右对称与游戏视角下的可读性。

研究来源为 [Larian 游戏画面 / PC Gamer](https://www.pcgamer.com/baldurs-gate-3-waypoints-fast-travel/)及 [Ancient Sigil Circle 条目](https://bg3.wiki/wiki/Ancient_Sigil_Circle)。参考截图只用于查看和必要局部的云端参考输入，不作为运行素材发布；新符文为原创生成图。

## 素材

- [原始生成图](rune-initial-generated.png)、[初始提示词](prompt.txt)：Codex 认为浮雕徽章感过重，未接入运行。
- [修订生成图](rune-revised-generated.png)、[修订提示词](revision-prompt.txt)：改成平面魔法刻线，缩小中央符号，保留大面积透明负空间。
- [生成、处理与校验记录](generation.json)、[不同背景及140px小样](rune-art-review.jpg)。

使用内置 OpenAI image_gen 云端生成两次（一次初稿、一次针对性编辑），未启动本地生成模型。Pillow 复用生成图的真实透明通道，作512px缩放、轻微颜色调整、一个像素的笔画透明度扩张和精确左右镜像，另从符文遮罩生成窄柔光。两张运行贴图逐通道水平镜像误差均为0。处理脚本：`tools/model-pipeline/prepare_waypoint_runes.py`。

## 接入与验收

复用项目已有 Cocos Creator 3.8.8 的 quad、builtin-unlit 和透明混合；无需新增库、shader或美术模型下载。[官方渲染状态文档](https://docs.cocos.com/creator/3.8/manual/en/shader/surface-shader/builtin-surface-shader.html)支持深度测试、关闭深度写入及加色混合。主符文保持静止，独立柔光按实际游戏时间轻微呼吸，运动由运行代码实现，不把单帧贴图称为生成动画。

符文放在原出口的准确坐标，仍使用原 F/触屏操作、1.35m距离和解锁规则，视觉不添加碰撞或障碍。实际画框为2.5m正方形、中心离地1.3m，朝向固定在世界中；两层分别是稳定主纹和8秒轻微呼吸的窄柔光。锁定入口减弱亮度并停止呼吸。

最终运行为 `portal-runes-v2`：[构建与运行素材校验](portal-runes-v2-build.json)。第一轮实景发现标签遮住上环，v2 改用 Cocos Quat/Vec3 投影符文四角，按屏幕最高角加半个标签高度和12个UI像素定位；不随缩放使用固定的世界高度猜测位置。

Codex 已实际查看桌面四类场景、触屏模拟四类场景及H07坡地，[运行美术记录](art-review.json)为通过。代表场景中标签与有效符文边界间距：桌面24–26像素，触屏模拟14–15 CSS像素，交叠面积均为0。此记录不代表用户已经认可风格。

- [实际游戏裁切图](runtime-rune-preview.png)、[截图来源与处理记录](runtime-rune-preview.sources.json)：原像素裁切，没有放大或生成式修改。
- 原始v1与v2构建记录和被弃用的第一张徽章感小样均保留，便于核对过程。

本包使用隔离冻结源码构建。同一时间其他chat随后修改了 `PureCombat.ts`；该战斗改动没有覆盖，也没有纳入本轮视觉预览，差异SHA记录在v2构建证明中。

## 最终验证与预览

- [运行总记录](runtime-review.json)、[主预览独立核验](live-preview-review.json)：实际HTTP与浏览器载入的主包SHA一致，初始场景载入正常。
- [桌面、触屏及原生3D记录](runtime-input-review.json)：两种输入各4次真实换图，锁定拒绝、原规则真实解锁、1.55m范围拒绝与快速重复输入检查通过；符文世界朝向固定、主纹静止，真实游戏时间驱动柔光变化。
- [97区与640路径记录](navigation-review.json)：320个符文位于原出口，零新增碰撞或实体；1842个原导航障碍footprint不变，640条实际及基线路径通过，228个原角色正常。两张纹理引用稳定，旧节点、四份材质和共享网格释放正常。

触屏检查采用Chrome触摸与DPR模拟，不代替手机真机性能测试；区域重建和代表输入不冒充完整战役通关。全部检查保留原角色、地形和规则，未发布或上传游戏。

本地预览：[刷新游戏](http://127.0.0.1:7470/?view=2d&v=runes8)。
