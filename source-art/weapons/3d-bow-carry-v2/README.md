# 背弓与箭筒贴背修正

用户截图指出背弓离身体太远。检查确认有两处原因：七把弓沿用较大的后向、侧向偏移；弓与箭筒又共用了背剑的 `spine_03` 上胸挂点，跑动时会偏离对应的下背表面。

本轮复用现有 Cocos `SkeletalAnimation.createSocket`、Blender 求值蒙皮与 BVH 测量：弓、箭筒单独使用 `spine_02` 中背挂点，站立时按当前衣服背面重新定位。W07/W09/W10/DE02/L02 的弓握点由 `[.22,1.20,-.34]` 调至 `[.13,1.20,-.155]`；W08/DU2-04 保留相反一侧，按其衣服表面调至 `[-.13,1.20,-.165]`。箭筒对应收向背部。原有弓轴、模型尺寸、手持/搭箭参数继续使用。

主挂点继续用于剑、双手剑及法杖；各武器绑定保存自己的背部父节点。两个背部挂点的参考矩阵在同一待机姿态下固定，避免异步加载附件期间参考姿势漂移。动作结束仍走原有脱战计时并收回背部。

- 数据依据：[背部表面](back-surface.json)、[不同骨骼的步行/跑动贴合测量](anchor-measurements.json)、[最终校准](calibration.json)。
- 实际画面：[前后对比](runtime/bow-carry-before-after.jpg)、[七把弓背面与侧面](runtime/all-bows-back-carry.jpg)、[步行、跑动、拉弓、收回](runtime/carry-motion-check.jpg)。均为实际 Cocos 网格与材质，没有重绘角色或替换截图里的武器位置。
- 验证：[78 个挂载/姿势视图](runtime/after/report.json)、[七把弓八向搭箭及七次放箭](runtime/all-bows-review.json)、[剑/双手剑/法杖收持回归](runtime/carry-controls.json)、[本地入口与行囊](runtime/canonical-smoke.json)。类型检查和 web-mobile 构建通过。

模型/纹理没有重建；人物、四款发型和原 14 组动作由原 GLB 字节哈希核对保留，见 [保护记录](preservation.json)。本轮没有新增依赖、图片生成或资源下载。校准通过 [数据适配器](../../../tools/model-pipeline/weapon_carry_calibration.py) 接入当前发型和武器导出流程，后续重导出沿用相同位置。

[接入记录](install-record.json)、[美术观察](art-review.json)。本轮检查覆盖所列角度与代表动作，不把用户的美术验收标记为已完成。

[本地 3D 入口](http://127.0.0.1:7469/?view=2d&player=3d&hair=dante&revision=bow-carry-v2)。旧来源与 2D 依据见 [24 件武器模型](../3d-design-v1/README.md)。
