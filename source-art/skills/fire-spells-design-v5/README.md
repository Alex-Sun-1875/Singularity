# 火系法术动态设计 v5

本轮依据当前 Cocos 3D 实现制作评审动画。角色、骨骼动作、技能的落点与几何来自现有游戏；通过临时 HTTP 响应替换渲染模块和火焰图集，没有写入正式技能、资源目录或构建产物。

## 技能定位

- **焚星坠落 FIR_02 为火系终极技能。** 预览中交换它与 FIR_05 的技能槽、类型、终极消耗和冷却角色，火海按普通主动技能展示。每个技能保留自己的伤害事件和范围。这只是设计配置，正式数值未定。
- 陨石按 0.85 秒聚能设计；末段约 0.55 秒下落，随后一次主爆燃，再转入低位残焰与余烬。该时间为本轮候选节奏，等待美术确认。
- 只有陨石使用范围法阵。法阵直接复用用户确认的首版橙红陨星阵：双圈、圈间刻纹、内部连续纹样。动画中的法阵为按游戏摄像机投影的设计合成层，含近似人物遮挡，没有声称原生法阵已接入。

## 火焰变化

重新设计同一套图集中的点燃、卷曲主焰、回落、低火与余烬。陨石爆燃呈现保留约 3.25 秒，其中高火迅速回落，后段由多个低位火点逐渐淡出；赤焰枪命中呈现约 1.85 秒。火墙和火海保留原本的有效时间，结束后添加约 1.8 秒的视觉收尾。余焰不会提交额外命中或延长伤害。

火弹使用新画的尖锐火核与连续尾焰；保留原弹道。陨石沿用当前彗星主体与下落方向。地面呈现继续使用现有火焰池，保持当前落点与可见范围裁切。

## 交付

- [完整火系动画](media/fire-spells-motion.mp4)：赤焰枪 → 火墙 → 火海 → 陨石终极技能，30 fps 原速。
- [陨石单独动画](media/meteor-ultimate-motion.mp4) / [GIF](media/meteor-ultimate-motion.gif)
- [当前与设计对比](media/meteor-current-vs-design.mp4)：按真实命中时刻对齐；两侧均为完整模拟录制，没有用定格填充消散段。
- [陨石阶段稿](media/meteor-ultimate-stages.jpg) / [火系效果总览](media/fire-kit-effects.jpg)
- [图集来源与提示词摘要](provenance.json) / [运行检查记录](verification.json)

## 复现

现有 `build/concept-2d` 在本轮录制时为空，使用本机最近可用的 Web 预览 `build/concept-2d-audio`。基线与候选使用相同构建、摄像机、目标、场景和随机种子，构建 SHA256 与源文件 SHA256 记录在每个 `capture.json`。本轮未重新构建或发布游戏。

```powershell
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-spells-design-v5/prepare.py
node source-art/skills/fire-spells-design-v5/capture.cjs --variant current --shots FIR_02
node source-art/skills/fire-spells-design-v5/capture.cjs --variant design
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-spells-design-v5/media.py
```

云端 OpenAI image_gen 生成两张透明图集；本地 Pillow/NumPy 仅做确定性的透明边缘、裁切、缩放、排版和透视合成。保留原始生成图和新图集，不覆盖生产素材。生成成功、运行无报错与美术通过分别记录；本轮为待用户评审的候选稿，TapTap 真机画质及多技能叠加性能仍待实际接入后验证。
