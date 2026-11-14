# 雷电照片参考与运行实现

用户于2026-11-08提供照片，并明确要求“散成片状，不仅仅是连接几个怪物”。本目录保留[user-reference.jpg](user-reference.jpg)及修改前的代码快照，供色相、白亮核心、分叉、区域覆盖和光团对照。

本轮使用实时原生几何与现有光斑遮罩，没有调用图像生成，也没有把参考图裁成静态特效贴片：

- [SkillEnergyStrokes.ts](../../../../src/cocos/assets/scripts/features/combat/runtime/SkillEnergyStrokes.ts)：蓝白主干、并行电丝、短支叉和受击碎电。
- [ThunderArcField.ts](../../../../src/cocos/assets/scripts/features/combat/runtime/ThunderArcField.ts)：覆盖真实命中区域的批量游离电弧网格，三高度、多分叉和每拍不同形态。
- [ThunderContactLights.ts](../../../../src/cocos/assets/scripts/features/combat/runtime/ThunderContactLights.ts)：白亮光核与蓝色柔光，复用现有light_01/star_01及[Kenney CC0许可](../../../../src/cocos/assets/resources/vfx/kenney/LICENSE.txt)。

色相方向为电蓝主体、蓝白亮芯和蓝色外围光。颜色经过现有材质、透明叠加和场景共同输出；原始参考与实机没有合成互换。生成/实现成功与用户美术验收分开，当前已完成实际运行复核，详见[运行记录](../../../../docs/assets/thunder-reference-v6.md)。
