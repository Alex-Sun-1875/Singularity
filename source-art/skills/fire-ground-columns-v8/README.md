# 地面火柱修订 v8

按用户纠正：“应该是地上喷火，排成一列”。新技能改为沿施法方向的一列地面喷火柱；弃用 v7 从手掌向前喷射长火流的表现。陨石扩围与火墙/火海合并设计继续保留。

本轮动态稿使用当前 Cocos 3D 角色、场景与原有施法、收回动作。施法后五个地面喷口由近到远快速点燃，形成一列：约每隔 1.25 米一个喷口，整列约 7 米长；单柱约 2.45 米高，约 0.08 秒的启动间隔使它们迅速同时成列。火柱持续喷发一小段时间后降低，留下地面余焰，再逐渐消散。各根火柱底部逐点读取地形高度。

这些是候选动画尺寸和节奏，不是已确认的正式数值。整列应共享一次施放的伤害预算，不能简单叠加成五份完整伤害；伤害判定、打断和地形遮挡仍待设计确认后接入。本轮沿用零伤害动画载体，不将原火墙的命中冒充新技能已实现。

素材复用 [v7 云端生成的火焰图集](../fire-kit-revision-v7/provenance.json)，确定性裁切去掉尖细喷嘴，保留厚实的主体，通过当前引擎的三维排布朝上喷发；本轮没有重新生图，没有改动生产源码或贴图。每个喷口的原生火柱、火焰根部和低位余焰单独更新，没有从手掌发出的攻击火流。施法动作正常回收，不再保持 v7 的手持喷射姿势。摄像机略微拉远，完整容纳整列喷火柱。

完整组合动画中的陨石、合并火域镜头复用 v7 的已录制版本，新技能镜头重新录制。法阵仍是确认原稿的透视合成层，只有陨石使用。其余火焰均来自原生预览。

- [地面火柱动画](media/flame-jet.mp4) / [GIF](media/flame-jet.gif)
- [更新后的完整火系组合](media/fire-kit-revision-motion.mp4)
- [设计总览](media/fire-kit-design-board.jpg)
- [原生预览检查](verification.json) / [媒体检查](media-validation.json)

```powershell
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-ground-columns-v8/prepare.py
node source-art/skills/fire-ground-columns-v8/capture.cjs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-ground-columns-v8/media.py
```

状态：设计候选，待用户评审；尚未接入正式技能，尚未进行 TapTap 真机验收。
