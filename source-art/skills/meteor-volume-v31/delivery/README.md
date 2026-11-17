# 陨石爆燃 v31 历史失败候选

用户再次提供v29原稿并否定陨石对齐；当前状态为 `user-rejected-v29-reference-mismatch`，本目录仅作历史证据。后续工作位于 `fire-reference-alignment-v32`。此前本地候选审查不能替代用户美术验收。

历史局部审查：中心向外的火浪、密度、亮度及前锋软边已进行原生画面复核；前部仍能辨认宽瓣叠层，尚不声称完全对齐v29或用户美术验收通过。TapTap与真机待验。

- [正常训练场原速9秒完整HUD](../after7-r1/media/FIR_02-native.mp4)
- [正常训练场局部原速9秒](../after7-r1/media/FIR_02-closeup.mp4)
- [空地轮廓原速9秒完整HUD](../after7-empty-r1/media/FIR_02-native.mp4)
- [空地轮廓局部原速9秒](../after7-empty-r1/media/FIR_02-closeup.mp4)
- [v29参考与实际六阶段](../after7-empty-r1/media/reference-vs-native-stages.jpg)
- [实际完整画布六阶段](../after7-r1/media/native-full-canvas-stages.jpg)
- [原始v30与当前爆燃对照](../after7-empty-r1/media/before-vs-after-native-curl.jpg)
- [逐片哈希、实际命中与验证清单](manifest.json)

每段270帧、30fps，实际镜头保持4.3，未隐藏人物或叠加技能。局部视频仅裁切原画布 `(0,150,1500,1272)`，不改镜头、时间或帧序；完整HUD保留在native原片。阶段取实际冲击后0.05、0.25、0.65、1.25、1.65和4.62秒。

正常段4次真实命中、740实际伤害、1次miss、0暴击，empty段0命中；释放、冷却、暂停恢复、减动态、切职业清理及末帧全清通过。与紧邻after2的数值精确一致。原始v30 before为1556伤害、4暴击，其间存在其他聊天的core平衡修改，旧录制未存seed，因此不宣称原始before的数字完全相同。原始v30仍用于视觉前后对照，after2仅用于紧邻玩法检查。
