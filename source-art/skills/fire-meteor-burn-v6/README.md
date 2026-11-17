# 陨石爆燃节奏修订 v6

用户要求延长陨石命中后的爆燃时间。本轮只调整动态设计预览，未写入正式实现。

- 保留快速命中的速度：约 0.18 秒展开主焰。
- 高火焰持续翻卷到命中后约 1.2 秒，再用约 0.45 秒回落。没有拉慢整段角色动作，也没有定格延长火焰。
- 低位残焰与余烬继续渐退，整个命中后火焰呈现约 4.55 秒。原版视觉段约 3.25 秒。
- 陨石仍为火系终极技能，蓄力、下落、范围和实际伤害时刻沿用 v5。法阵仍是已确认原稿的透视合成层。

新旧两版在同一浏览器里分别运行完整的 6.5 秒 Cocos 模拟，使用相同的目标、摄像机、随机种子、骨骼动作和战斗事件。通过评审开关切换纯视觉时序，两版均录制到火焰消散完成，不使用定格补足比较时长。结果见 `verification.json`。

素材复用 [v5 的云端生成图集及来源](../fire-spells-design-v5/provenance.json)，本轮没有重新生图。图集复制到本目录供独立预览；未覆盖 v5 或生产素材。额外注册当前渲染模块引用的雷系支持模块只是为了适配现有构建，录制只施放陨石。

```powershell
node source-art/skills/fire-meteor-burn-v6/capture.cjs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-meteor-burn-v6/media.py
```

[延长爆燃动画](media/meteor-long-burn-motion.mp4) · [GIF](media/meteor-long-burn-motion.gif) · [新旧对比](media/meteor-burn-before-after.mp4) · [阶段稿](media/meteor-long-burn-stages.jpg)

美术状态：候选，待用户评审。未进行正式游戏接入或 TapTap 真机性能验收。
