# v32 陨石原稿对齐录制工具

本轮使用 `assets/approved-reference.png` 的下方两格，对照法阵、陨石下落、真实着陆与爆燃余火。v31已被用户再次否定，保留为历史失败候选；不把技术通过或旧局部审查看作美术验收。

脚本只在根代理明确build-ready后运行，不构建，不改生产、玩法、seed或存档。使用全新非持久浏览器上下文；URL不含 `test=max`，先断言并记录正常test新旅程为1级，再通过正式 `training:enter` 动作进入既有独立训练会话。该训练场自身提供临时合法满级角色（当前独立训练上限80级）；结束通过正式 `training:exit` 验证同一原旅程会话、等级、进度与装备恢复不变。

固定FIR02终极实际输入、技能rank1，每段9秒270帧。normal为正式cluster/4米，empty为正式single/12米并瞄准-30°/4米空地。镜头保持默认4.3、人物和HUD保留，不伪造命中或叠技能。逐帧保存真实drop/blast事件落点、age/duration和完整meteor/fire/ground inspect；比较实际命中、伤害、暴击、miss、冷却及生命周期清理。生产effect/PNG及对应导出资产哈希在开始与结束核对。

当前旧实现下落仅约0.55秒，因此“施法0.2/0.6秒”与“可见下落20%/60%”分开记录，前者绝不伪称都有陨石。若runtime提供meteor.progress则直接据此取20%/60%；否则按真实可见下落区间选帧并标清选择依据。另保存着陆前最后实际可见帧，以及真实冲击后0.05/0.25/0.65/1.25/1.65/4.60秒。

```powershell
node source-art/skills/fire-reference-alignment-v32/capture.cjs --stage after --rank 1
node source-art/skills/fire-reference-alignment-v32/capture.cjs --stage after --rank 1 --empty
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/fire-reference-alignment-v32/media.py --stage after --verify-only
```

只有实际native形态通过本地候选复核后才编码；`--local-candidate`仅记录已发生的本地复核，不代表用户验收。native MP4为完整2560×1272原画布；closeup仅裁切 `(0,0,1550,1272)`，保持原速、原镜头和帧序。对照图保留原稿下两格；独立阶段JPG直接复制实际帧。TapTap与真机验收另记。

首轮after-r1/after-empty-r1完整采集与技术检查通过，正常旅程1级进出独立训练场未改变进度/装备，落点链及实际数值与历史紧邻记录一致。落地完整原稿轮廓为正确方向；飞行阶段岩核前端裸露、火焰包裹位置及法阵线纹仍待修正，状态记为 `intermediate-body-shell-alignment-review`，不编码作最终美术交付。

第二轮after2完整媒体保留为飞行角度待修中间证据。此轮其他聊天将CampaignProgression/TrainingRange合法临时满级从40调整到80，实际伤害812，不宣称与旧740跨级相等；正常test旅程进出仍为1级且进度/装备未改。regression两招录于后续真实315c...编译（主两段为ddcc...），各段稳定哈希独立记录，不能声称同一build。
