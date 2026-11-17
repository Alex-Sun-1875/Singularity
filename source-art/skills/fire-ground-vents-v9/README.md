# 低焰圆形地火造型 v9

用户指出前版火柱过高，并要求地面有圆圈。本轮把新技能重定为沿前方排列的五个圆形地火喷口：火焰约 0.4–0.6 米高，圆内铺少量粗而连续的热纹，喷发、回落、余烬渐退。陨石扩围与合并火域的提案保持原样。

## 最终评审素材

- [近景造型稿](media/ground-vent-lookdev-closeup.jpg)
- [当前场景中的整列效果概念稿](media/ground-vent-lookdev-scene.jpg)
- [近景动效示意 MP4](media/ground-vent-lookdev-motion.mp4) / [GIF](media/ground-vent-lookdev-motion.gif)

造型稿由云端 OpenAI image_gen 基于当前场景截图编辑，保留现有场景、摄像机和角色外观为参考，只修订火圈与低焰。橙红材质和内纹以用户先前选定的火系阵纹为参考，缩减成小喷发口，避免把小技能画成终极大法阵。完整提示词与来源见 [provenance.json](provenance.json)。

动效示意使用造型图里的圆形热纹，叠合当前引擎录制的低火焰帧，在清洁地面上展示聚热、翻卷、淡出。**这是美术与节奏的合成动画，并非这套造型已经在原生游戏中实现。** 原生预览脚本仅用于比例与地面锚点研究，其实体描边处理未被当作最终美术；最终外观以本目录的造型稿为准。

原生研究保存在 `capture.cjs` / `refine-modules.cjs`，素材沿用既有云端火焰图集；程序替换只发生在隔离 HTTP 预览中。正式源码、资源和发布配置均未改动。生成成功、原生研究运行无错误、合成动画可播放与用户美术确认分别记录；当前仍为待评审候选。

```powershell
node source-art/skills/fire-ground-vents-v9/capture.cjs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe -X utf8 source-art/skills/fire-ground-vents-v9/look-review.py
```
