# 火系 v28 实景录制

2026-11-17 最新指示已改为先出设计稿，当前已停止实现后的构建与录制；没有 final 产物。after-r1 的多簇火苗外观被否定，仅保留玩法与生命周期检查证据，不作为最终效果展示。下方 final 命令仅供设计获确认后的后续工作使用。

录制复用 v27 的浏览器训练场工具，仅导出实际 Cocos 画布。游戏生产源码、技能碰撞、伤害、冷却、镜头和 HUD 均由当前编译游戏控制。

```powershell
node source-art/skills/fire-family-wisps-v28/capture.cjs --stage before --rank 1
node source-art/skills/fire-family-wisps-v28/capture.cjs --stage final --rank 1
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-family-wisps-v28/media.py --stage final --rank 1
node source-art/skills/fire-family-wisps-v28/capture.cjs --stage final --rank 1 --empty
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-family-wisps-v28/media.py --stage final --rank 1 --empty
```

录制器不执行构建。必须先由主代理协调构建锁；修改后录制仅在 build-ready 后执行。`--only FIR_01` 等参数用于单技能检查，`--rank 1..5` 使用正式调试菜单设置本系等级。`media.py --verify-only` 只运行既有实录检查并导出指标，不编码媒体。2026-11-17 的 after-r1 是根部切口/排列问题修正前的中间检查，最终展示使用 final-r1；中止的 lifecycle-probe 不构成证据。

进入 `ChapterGame.enterTrainingRange()` 后，通过 `debug:rank`、`debug:family-rank`、`debug:loadout` 与现有资源预加载流程准备火系固定技能栏。保持训练场默认 4.3 镜头高度、正常 HUD、cluster 阵型、4 米距离与训练场原有无限职业资源设置；不关闭冷却。施法使用真实 `pulse.combatSlot` / `pulse.ultimate`，随后正常执行 `ChapterGame.update` 和 Cocos tick。30fps 导出画面，模拟步长为 1/60 秒。

`--empty` 是暂停扩展时保留的未验原型，尚不可作为有效无靶录制使用。它会通过正式菜单切换单靶和12米距离，保留默认镜头与完整HUD，瞄准前方4米；但后续只读检查发现 FIR01 的弹体射程为12米，仍会打到同方向远靶，需要先偏转空地瞄准方向，再验证远靶不在射线和范围内。原型不会隐藏演员、删除敌人或改写命中。默认选火矛、火域和陨石，预留输出 `final-empty-r1`，目前没有该目录的有效证据。正常命中仍应由 `final-r1` 片段单独证明。

每个技能录制一次完整起手、释放、命中、持续/退火：赤焰枪 6 秒，焚焰火域 8 秒，陨星天坠 9 秒，已确认烈焰喷流 8 秒，统一焰心护盾回归 7 秒。帧缓存位于 `src/.tmp/fire-family-wisps-v28/<stage>-r<rank>/<skill>/`，每段 JSON 保存实际 skill 事件、generic hit 的 hpLost/critical、命中数、伤害、冷却、投射物、火焰/地面/陨石原生池指标。记录实际游戏 bundle SHA256，并核对录制期间未被其他构建改写；源码哈希只是当时工作区快照，不作为编译内容证明。

完整录制后另行走正式靶场设置页的暂停/恢复，比较暂停期间核心施法状态不推进、恢复后特效还原，记录 reduced motion 两个时刻的原生图集状态并检查重置清理。再点击真实技能调试页的雷系、战士、火系按钮，等待现有异步资源准备完成，检查切职业后旧火焰/法阵/陨石/护盾池清空。before 最初四技能基线不含这些后追加的回归步骤；after 报告逐项记录。

媒体输出保存到 `<stage>-r<rank>/media/`。四段 MP4 保留完整 2560×1272 原始画布，不添加或替换特效。合集只在画布上方加标题；局部 WebP 与分阶段图只作裁切、缩放、排版，并保留真实透视。浏览器实录与美术验收、TapTap/真机验收分别记录。编码只复用现有 Python/PyAV/Pillow，不启动本地生成模型。
