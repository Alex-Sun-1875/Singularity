# 蓝紫空间裂隙 v7

本版作为历史样式留存。用户要求改回符文并重新参考《博德之门3》，当前运行采用[古代符文传送阵版](../waypoints-runes-v8/README.md)。

按用户明确选择“蓝紫色空间裂隙”替换石刻样式，保留左右对称。主视角呈现冷蓝外缘、紫色能量层与凹陷的内部星云，人物可穿过视觉裂口。

## 素材与运动

- [云端原图](spatial-rift-generated.png)、[完整提示词](prompt.txt)、[生成和处理记录](generation.json)、[源图小样](rift-review.jpg)
- 处理脚本：`tools/model-pipeline/prepare_waypoint_rift.py`

主图由 OpenAI image_gen 云端原创生成。Pillow 将外缘、柔光、无缝星云贴图与内部半宽曲线分离，三张新运行图水平镜像逐通道误差为0。原始云端图保存不变。

实际运动复用 Cocos 3.8.8 原生网格与内置 unlit 材质：凹面深度约0.28m，两层星云按真实游戏时间以相反方向滚动UV；四对亮点沿两侧移动，左侧纹理和姿态对应镜像，单次周期4.8秒。轮廓固定在世界中，不随相机旋转。锁定入口停止流光并减弱亮度。

柔光与亮点复用项目现有 [Kenney light_01](../../../src/cocos/assets/resources/vfx/kenney/light_01.png)，其[许可为CC0](../../../src/cocos/assets/resources/vfx/kenney/LICENSE.txt)。该素材原本是单帧mask，当前运动由运行代码实现，不声称存在现成裂隙动画或生图序列。未下载模型、依赖或外部素材。

## 接入

320个裂隙均放在原 ExitDef 的准确坐标，保持原1.35m范围、F/触屏交互、解锁规则和到达坐标。取消传送点石碑的316块碰撞；新裂隙不添加碰撞，导航保留原地形与场景障碍。地面只有柔和环境光，不复制整套裂隙图案。休整点的篝火语义保持独立。

最终运行包为 `portal-rift-v1`。Codex 已查看旅馆、城镇、洞窟、湿地、H07坡地、移动端四场景及原生3D实景；此记录不代替用户对美术风格的判断。

- [最终运行记录](runtime-review.json)、[构建证明](portal-rift-v1-build.json)、[在线预览核验](live-preview-review.json)
- [实际游戏动效 GIF](runtime-motion.gif)及[原帧、游戏时间和裁切来源](runtime-motion.sources.json)：约4.75秒真实游戏时间，无生成或插值动画帧。
- [桌面、触屏与动画检查](runtime-input-review.json)：各4段真实换图、原锁定与真实解锁、快速重复输入、固定朝向、双向UV流动和四对镜像亮点均通过，错误及失败请求为0。
- [97区与640点导航](navigation-review.json)：320个裂隙都在原出口、零新增碰撞，1842个原障碍footprint完全一致。四纹理引用稳定，旧网格与七类材质释放正常。
- [素材与像素来源核对](source-art-review.json)、[复用mask记录](reused-mask.json)。

检查为原角色区域重建、导航与代表键盘/Chrome触摸模拟，不冒充完整战役通关或手机真机性能测试。原石刻与此前候选保留为历史过程。

此历史包不再由主预览提供。当前运行及预览见[古代符文版](../waypoints-runes-v8/README.md)。
