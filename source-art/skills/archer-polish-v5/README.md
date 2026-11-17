# 弓箭手攻击微调动态审阅

首轮以当前 Cocos 3D 场景、骨骼角色、实体箭和实际战斗事件录制，通过临时 localhost 响应替换形成审阅版本。2026-11-16 用户确认后，已将同一组美术调整接入产品渲染模块 `Effects.ts`、`NativeSkillVfx.ts` 和 `SkillEnergyStrokes.ts`，复用现有箭体、粒子与线段池。

- 普攻略微提亮箭尾，缩小零散尾粒子。实体箭宽度约增加 6%。
- 连穿箭 BOW_02 的亮尾最多保留已飞过的 2.35 米，增加很淡的青绿外晕。
- 实际转向时保留前一段已飞过路径，约 0.40 秒内淡出。命中闪光稍微增大。极短飞行段在真实转向或命中发生后补齐。
- 保留一支实体箭。没有增加分裂箭、速度、目标数、伤害或提前显示未来路径。
- 对其他弓箭技能仅沿用同一箭尾的细微美化，没有扩展技能形态。

## 交付

- `media/current-vs-polished.mp4` 同机位、原速前后对比。
- `media/polished-full-size.mp4` 微调版本完整视口。
- `media/chain-comparison.gif` 多目标连穿箭循环对比。
- `verification.json` 逐事件、源文件、镜头与帧数验证。

接入后的实际构建以 `capture.cjs --integrated` 录制，不替换运行模块。`media.py --integrated` 将其与优化前录制逐事件比较，输出 `integration-verification.json`、`integration-captures.json`、`media/current-vs-integrated.mp4` 和 `media/integrated-full-size.mp4`。接入检查同时确认真实转向的残光数量，以及清理后的路径、残光均为空。此前审阅视频和原始验收记录保留。

接入验收已通过类型检查、64 项既有战斗／技能／输入检查、正常 test 档 Web 构建，以及上述三段实录的逐事件比较。两目标、四目标连穿箭最多分别保留 1、3 段已完成转向残光，场上始终只有一支实际连穿箭，瞬态清理均通过。

当前构建的完整 UI 预热在软件光栅录制中超时，因此实录复用项目既有的 D3D11 与启动逐帧预热方式，预热期间使用人工渲染时钟，进入样本后按原有 60 Hz 会话、30 fps 输出录制。原始审阅使用 SwiftShader；两者镜头、目标、命中时间、顺序和伤害逐项一致，不以此作 GPU 性能对比。

## 复现

录制缓存和冻结输入保存在 `src/.tmp/archer-polish-v5/`。`capture.cjs` 复用现有 `cocos-motion-study-v2/review-fixture.js`，以短按释放录制真实普通箭，以实际技能释放录制 1 级和 3 级连穿箭。

```powershell
node source-art/skills/archer-polish-v5/capture.cjs
node source-art/skills/archer-polish-v5/capture.cjs --refined
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/archer-polish-v5/media.py
node source-art/skills/archer-polish-v5/capture.cjs --integrated --hardware --pump
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/archer-polish-v5/media.py --integrated
```

图像处理仅用于原始帧的标签排版和视频编码，没有使用生成式图像、重绘角色或叠画特效。

生成结果与美术验收分开记录。美术方向已由用户确认接入，运行与数据一致性由验证文件记录；本地实录不代表 TapTap 真机性能验收。
