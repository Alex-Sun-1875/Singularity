# 背剑贴合与斜背方向修正

2026-11-10。用户指出侧面背剑与身体分离，背面斜向也不自然。本轮修正当前 3D 主角的九把剑，已接入[默认本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&revision=sword-back-contact-v2)。

复用当前人物、武器、剑鞘和 Cocos 原生骨骼挂点。握柄中心从 `[-.145,1.63,-.29]` 收到 `[-.14,1.60,-.222]`，模型空间斜角约 28.8°，剑柄在右肩上方，剑鞘横过背部至左胯；增加约 4° 的前倾，使剑鞘沿衣服背面靠近腰部。原先 W02 使用另一斜角，本轮九把剑统一为同一挂载方向，仍保留各自模型尺寸。配置见 [calibration.json](calibration.json)。

挂点仍为 `spine_03`：当前 `locomotion-v9` 的站、走、跑和闪避均进行比较后保留此挂点。基于当前源文件的 Blender 求值蒙皮与 BVH，剑鞘中心线上背至腰部的五个采样点，在站立／走跑代表帧里与衣服表面的距离由约 8.7～11.7 厘米缩至约 1.2～4.1 厘米；这是中心线距离，包含剑鞘自身厚度，不是整把剑每个表面的间隙。测量方法复用此前背弓工作，装饰面法线方向不一致时以动画背部坐标系判断内外侧。见 [measure.py](measure.py)、[测量摘要](measurement-summary.json)。

实际画面与校验分别记录：

- [侧背前后对照](runtime/sword-before-after.jpg)：真实 Cocos RenderTexture 裁切排版。
- [场景背面](runtime/scene-back.png)、[场景侧面](runtime/scene-side.png)、[外观面板](runtime/appearance-back.png)。
- [153 个视图记录](runtime/after/report.json)：九把剑八向背负、三把代表剑走跑／闪避、九把剑持握与返回。校验正确父挂点、位置／旋转、单组可见武器和身体蒙皮部件；页面异常为零。由原背弓采集脚本适配，不新增测试依赖。
- [真实攻击后收剑](runtime/natural-transitions.json)：九把剑均由 GameSession 实际攻击、原脱战计时返回背部。
- [外观预览与其他装备](runtime/current-preview-review.json)、[2D 入口](runtime/flat-entry.json)。当前行囊为装备面板，3D 人物预览位于“外观”面板。
- `npm run check` 与完整 `web-mobile` 构建通过，3195 个新构建文件校验后复制到原 7469 试玩目录；旧试玩备份于 `src/cocos/temp/concept-2d-before-sword-carry-v2/`。

只调整九把剑的背负数据；身体 GLB／FBX、导入元数据、动作、手掌参数、背弓、箭筒、锤和杖由结构对照及哈希核实保留。现有导出流程通过 [weapon_carry_calibration.py](../../../tools/model-pipeline/weapon_carry_calibration.py) 重用校准，重复应用结果一致。背部跟随继续使用 [Cocos 3.8 官方骨骼 Socket](https://docs.cocos.com/creator/3.8/manual/en/animation/skeletal-animation.html)，没有新建 IK、物理模拟或逐帧位置补偿。

没有生成式图像、模型下载或身体重导出。[接入记录](install-record.json)与[画面观察](art-review.json)分开保存，用户美术验收仍待确认。以上为本地浏览器验证，TapTap 平台真机表现尚未在本轮验证。
