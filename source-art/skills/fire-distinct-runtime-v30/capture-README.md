# v30 正常训练场实录

本工具复用 v28 已验证录制流程。按已确认 v29 的三个不同造型验收：集中穿刺火矛、连续低矮火面、单中心爆燃与连片余火。喷流和统一护盾只做回归。录制完成与美术验收分别记录，不把概念图或编码成功当作实际效果通过。

只由主代理统一构建，收到 build-ready 后执行：

```powershell
node source-art/skills/fire-distinct-runtime-v30/capture.cjs --stage after --rank 1
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-distinct-runtime-v30/media.py --stage after --rank 1 --verify-only
node source-art/skills/fire-distinct-runtime-v30/capture.cjs --stage after --rank 1 --empty
node source-art/skills/fire-distinct-runtime-v30/capture.cjs --stage after --rank 1 --single
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-distinct-runtime-v30/media.py --stage after --rank 1
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-distinct-runtime-v30/media.py --stage after --rank 1 --empty
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-distinct-runtime-v30/media.py --stage after --rank 1 --single
```

正常五技能顺序固定为 FIR01、FIR05、FIR02、FIR04、FIR03，前四段与 v28 before-r1 的真实伤害、命中、暴击、冷却对照。使用现有训练场独立会话、正式调试菜单的等级和固定职业装配流程，等待资源准备，再通过真实 combatSlot/ultimate 输入施法。保持默认4.3镜头和完整HUD，30fps导出实际2560×1272画布，模拟步长1/60秒。不会构建、改生产源码、追加伤害或替换渲染效果。

额外空地展示使用正式单靶和12米距离，明确瞄准左前方-30°、距离4米空地。原来的同方向远靶方案会被12米火矛打中，本版射线距该远靶至少6米；技能范围/射线与远靶分离，不隐藏演员、不改敌人生命。选择左前方使大范围更完整留在原默认画面内，避开下方操作提示。空地默认只录本轮三种新造型，保存到 after-empty-r1；它只证明真实施法轮廓与退火，不替代正常命中证据。首次shape-probe使用+30°，仅作中间材质检查。

额外 `--single` 通过正式单靶、4米距离单录FIR01，避免cluster其他靶遮住胸口真实接触，保存到 after-single-r1。单靶与空地都不会代替正常五段的玩法和生命周期证据。

每帧记录 fire/ground/meteor/shield inspect、真实 hit.hpLost、命中/伤害/冷却、投射物与原生池。正常录制之后检查五技能暂停恢复、低动态换帧、训练场重置和 THU→WAR→FIR 正式职业按钮切换清理。每段JSON和生命周期增量文件先保存，媒体只在实景审看后导出。

Recorder revision 2 将FIR01暂停点提前到23 tick、低动态间隔4 tick，覆盖它的新短接触期；其他技能沿用65/12。首次 after-r1 在旧65 tick时接触已经自然结束，因此它只能证明FIR01暂停期间核心状态稳定，不能证明短接触特效恢复，最终版本重新录制该项。

完整技能MP4只编码原生画布。合集加标题、局部WebP和阶段图只做确定性裁切/缩放/排版，不后期叠加特效。全程记录编译bundle SHA256，核对录制期间未被其他构建改写；源码哈希仅是当时工作区快照。浏览器实景与TapTap平台/真机验收分开，后者不由此录制宣称完成。

最终主要预览只展示三种本轮重做的技能：`fire-three-skills-native.mp4` 保留完整命中画布/HUD；`fire-three-skills-empty.mp4` 是明确标注的实际空地画布局部，保持原镜头透视，仅裁切缩放增强聊天中的可读性。每技能完整原生MP4继续保留，喷流与盾不抢主要预览。WebP局部仅在显式 `--details` 时导出。

最终交付位于 `delivery/`：`fire-three-skills-native.mp4` 和 `fire-three-skills-empty.mp4`。使用已通过本地审看的final4 FIR01/FIR05，与final5仅补录的FIR02组合；合集并非来自同一个build。逐段编译SHA、原生MP4 SHA、事件/帧来源和当前PNG源SHA均在 `delivery/manifest.json`。新FIR02是独立真实施放，随机序列位置与完整五段的第三招不同，正常段4次命中/1556伤害与1次miss按实际记录，未改变seed；完整final4五段仍保留原玩法数值回归证据。

重建交付仅需现有素材与帧缓存：

```powershell
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-distinct-runtime-v30/assemble.py
```

录制 `--only FIR_02` 支持单技能补录，也支持逗号列表；媒体 `--only` 只编码选中的原生单片，避免重复编码已否定的旧陨石。组装不添加特效、不改变任何片段的时序。最终每个合集690帧、23秒，解码帧数已核对；实装美术的用户反馈和TapTap/真机验收仍待完成。
