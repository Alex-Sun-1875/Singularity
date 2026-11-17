# 陨石体积与爆燃 v31 实景检查

更新：用户再次提供v29原稿并否定陨石对齐，after7与delivery现已标为 `user-rejected-v29-reference-mismatch`。v31完整保留为历史失败候选，后续工作位于 `fire-reference-alignment-v32`；下文的本地候选复核仅为历史记录。

v30陨石的爆燃密度、体积翻卷和亮度已被用户否定。before只保存该被否定的实际版本作对照，技术检查成功不构成美术通过。

录制复用v30正常训练场：只通过正式固定火系技能栏的ultimate输入施放FIR02。normal与empty均为独立新训练会话中的第一次陨石，固定rank1、9秒270帧，模拟步长1/60、导出30fps；不改seed、时间、人物可见性、镜头或正式玩法。normal保留cluster/4米，empty使用正式单靶12米并瞄准-30°/4米空地，远靶不在技能范围内。完整原生MP4保持2560×1272实际画布及HUD。

开始录制前拒绝已有构建锁。只由主代理统一构建，before录完关浏览器通知主代理，after仅在build-ready后开始。

```powershell
node source-art/skills/meteor-volume-v31/capture.cjs --stage before --rank 1
node source-art/skills/meteor-volume-v31/capture.cjs --stage before --rank 1 --empty
node source-art/skills/meteor-volume-v31/capture.cjs --stage after --rank 1
node source-art/skills/meteor-volume-v31/capture.cjs --stage after --rank 1 --empty
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/meteor-volume-v31/media.py --stage after --rank 1
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/meteor-volume-v31/media.py --stage after --rank 1 --empty
```

每帧保存完整fire/impact inspect（含根代理添加的age/progress/height/density/front等字段），另记录真实blast cue age；命中、hpLost、冷却、释放和清理由实际战斗事件与池状态验证。相同单技能序列的before/after直接比较实际伤害、命中、暴击、miss与冷却，不把进度参数当成时间。

阶段图按真实impact事件取约0.05/0.25/0.65/1.25/1.65/4.60秒，查看冲击开始、前锋外扩、翻卷、1.2秒后收势、向余火过渡、4.55秒后退尽。v29仅提供必要的陨石局部静态风格参考，比较图保留各自透视；实际图只裁切、缩放与排版，不后期添加火焰。指标数量不替代对真正native画面的体积、方向、密度和亮度审看；实装美术用户反馈与TapTap/真机验收分别记录。

首次 after-r1 虽然技术检查和数值对照通过，但native形成套层圆柱/碗壁、中心空洞，本地形状审看明确失败。相关记录单独保留，不作为最终美术通过依据。

after2-r1 同样保留完整9秒记录，本地形状审看失败：横向弧帽呈伞花/硬花瓣。该轮实际4hit、740伤害、0暴击，before/after1为4hit、1556伤害、4暴击；单次hpLost分别185与389。两轮cast:1、rank1、W11、释放时刻、目标、4hit/1miss、范围和冷却一致，期间存在其他聊天的core平衡修改，旧记录未保存seed，因此不声称精确数值回归通过，不改玩法或seed补齐结果。

后续recordRevision3增加只读seed/sequence/玩家装备与进度快照，以及GameSession/PureSkills/BuildProfile等core哈希。紧邻VFX修改可用 `--baseline-stage after2` 与after2直接对照，同时保留原before历史差异。此参数只选择验证文件，不改变游戏运行。

after3-r1 与after2紧邻基线的实际伤害、暴击、命中、miss和CD精确对照通过，暂停/切职业/末帧清理通过；本地美术审看仍失败：高扇片形成长帘、中心暗穴。该轮不编码最终媒体，保留原帧及失败审看记录。

after4-r1 的中心、密度和亮度明显改善，技术检查与after2紧邻基线精确对照通过；本地边缘审看仍失败：火焰片底部及侧边的直切边与平台阶可见。不编码最终媒体；两目录的shader-asset-evidence.json记录生产effect、实际导出shader及源/导出同SHA的PNG，排除旧缓存误判。

after5-r1 技术及紧邻数值对照通过，导出shader/PNG整个录制期间SHA稳定；本地边缘审看仍失败：下沿变为曲线但亮齐边、侧截断及分层火板仍可见。保留原帧及失败记录，不编码最终媒体。

after6-r1 技术及紧邻数值对照通过；本地边缘审看仍失败。收身后不规则轮廓有所改善，但实际front夹取仍露出内部不透明UV的侧截面与弧形亮承载边。保留完整原帧，不编码最终媒体。

after7-r1 与after7-empty-r1已完成完整原生MP4、仅裁切局部MP4与六阶段图，root/audit实际看图确认旧竖直截面与矩形底线不再构成同等级阻断。状态为 `local-native-candidate-user-review-pending`，前部仍可辨宽瓣叠层，不声称完全对齐v29或用户已验收。最终路径、逐片哈希、原始v30与紧邻数字基线的区别见 [delivery/README.md](delivery/README.md) 与 [manifest.json](delivery/manifest.json)。不再构建或扩录场景。
