# 剑与火 · 3D 技能动态设计稿

2026-11-16。独立 Three.js 设计预览，使用当前真实 3D 角色、骨骼动作和武器。**用户美术审阅待确认，尚未接入 Cocos；未打包、未升版，未进行 TapTap／真机验收。** 旧的 `dynamic-redesign-v1` 预览已弃用，仅保留历史文件。

## 查看动态稿

- [四职业动态总览 GIF](media/00-four-class-overview.gif)／[WebP](media/00-four-class-overview.webp)
- 完整技能：[战士](media/war-all-skills.webp)、[弓系](media/bow-all-skills.webp)、[火系](media/fir-all-skills.webp)、[雷系](media/thu-all-skills.webp)、[通用闪避与治疗](media/com-all-skills.webp)
- [逐项技能清单](skill-inventory.json)、[动作分段设计](motion-direction.txt)、[美术审阅与验证边界](art-review.json)
- 当前[交互预览](http://127.0.0.1:58265/source-art/skills/dynamic-redesign-3d-v1/preview.html)可切换职业与技能、慢放、拖动时间轴或查看四职业总览。该地址依赖本机服务运行。

在仓库根目录恢复本地预览：

```powershell
node source-art/skills/dynamic-redesign-3d-v1/capture-preview.cjs --serve --port 58265
```

仅在设计源码更新后重新生成独立预览 bundle：

```powershell
node source-art/skills/dynamic-redesign-3d-v1/bundle-node.cjs
```

## 本轮范围与素材

覆盖 **37 项：33 项现有技能与被动反馈＋4 职业普攻**，其中包含通用疾影步和灵泉复苏。预览时长用于展示施放节奏，不是技能冷却。战士近身挥斩约扩大 **25%**，属于视觉覆盖提案，未改变游戏命中判定、目标数或数值；焚星坠落按火系终极设计，槽位调整尚未写入游戏。

法阵依据用户选定的首版透地线纹：双层圆环、圈间职业刻纹与连贯内部纹样；战士银金、弓系青绿、火系橙红、雷系蓝紫。四系效果分别突出金属刃面、实体箭路、连续陨火与粗主干电场。

主角读取当前 [raphael-polish.glb](../../../src/cocos/assets/resources/actors/raphael/raphael-polish.glb)、[材质与动作 manifest](../../../src/cocos/assets/resources/actors/raphael/manifest.json)、[卷发模型](../../../src/cocos/assets/resources/actors/raphael/hair-curly.glb)。基础 14 个 clip 与 [combos-native.glb](../../../src/cocos/assets/resources/actors/player-melee-combo/combos-native.glb) 中两段追加挥剑，共加载 **16 个原生骨骼动作**；敌人来自 [raider.fbx](../../../src/cocos/assets/resources/actors/raider/raider.fbx)。武器复用当前设计模型：[W01 剑](../../weapons/3d-design-v1/glb/W01.glb)、[W07 弓](../../weapons/3d-design-v1/glb/W07.glb)、[W11 杖](../../weapons/3d-design-v1/glb/W11.glb)。模型／材质读取与手部挂点适配只发生在此独立设计目录。

两份新材质由云端 OpenAI `image_gen` 生成，生成成功与美术确认分别记录：

- 火焰：[完整提示词](references/new-fire/prompt.txt)、[来源／图集／RGBA 检查记录](references/new-fire/atlas.json)。
- 金属刀光：[完整提示词](references/new-steel/prompt.txt)、[来源／确定性裁切／RGBA 检查记录](references/new-steel/provenance.json)。

材质已完成内部静态透明度检查；3D 捕获记录确认为 `native3D=true`、模型加载警告为空。当前离屏导出采用 Chromium WebGL2／SwiftShader，只证明设计画面可渲染，不能作为设备帧率或游戏运行验收。角色、武器与特效的整体美术效果仍待用户审阅；生产代码、正式资源、存档及伤害规则均未修改。

[最终内部检查](qa-final.json)已复核 37 项捕获完整性、代表效果帧及战士／陨石两段动作衔接，修正了刃光上飘、陨体裁切和主爆偏小。动图均已验证循环与完整播放时长；WebP 会合并相同的停留帧。内部抽查不等于全部动画逐帧美术验收，整体节奏、密度与陨石峰值的短暂遮挡仍留待用户观看。

本轮最终重捕获前，已修正战士刀光上飘与剑路连接、火系陨体构图及主爆体量，并将敌人受击动作对齐各技能的实际命中时机；自保、闪避与治疗不触发敌人假受击。37 项已按冻结后的 3D 预览重新捕获，最终整体美术复核与用户确认仍待完成，详见 `art-review.json`。
