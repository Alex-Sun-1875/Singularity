# 原设计稿脸型与短卷发对齐

最终68张原生动作图位于 `assets/`，已统一安装到实际游戏资源，覆盖88个动作记录。26张复用项目内匹配的原素材，42张使用内置ImageGen编辑头脸。HUD直接使用原设计稿PNG，由Cocos SpriteFrame裁切特写。

- 原稿：`references/original-design.png`
- 固定四方向头部参考：`head-identity-master.png`
- 通用提示词：`head-edit.prompt-template.txt`；每张最终PNG旁保存其实际 `.prompt.txt`、`.provenance.json`（包含raw、SHA及必要的packing/重试链）。
- 完整安装：`full-install-report.json`；原文件备份目录见其 `backupDirectory`。
- 验证与局限：`verification-summary.json`、`served-build-audit.json`。
- 实机截图/录像：`actual-game-run.png`、`actual-game-motion.webm`。
- 外部库的官方来源、授权及复用结论：`library-reuse-review.md`。未导入外部库的人物像素、代码或新运行依赖。

修改栅格图仅使用内置ImageGen。最终源图与其原生raw字节相同；Python/Pillow/SciPy只测量透明度、裁切和身体注册，不绘制、抠图或重采样交付PNG。三个需要重新留白排版的图有明确packing例外记录，未声称其身体像素和精确像素尺度不变；四张W01新版跑步图没有采用该例外。

W07步行最终恢复首轮头脸编辑图，使用已复核的语义裁切分开低透明度桥，保留原身体大小；明显缩小的中间packing稿已排除。Cocos帧时序、世界缩放参数及方向映射保持冻结基线不变。

本次最终manifest SHA256：`e1e1d5bdde78dff15892acecbd1c460551855a776cc60f7441a125eb1e772541`。

原子安装脚本只接受冻结的5f基线，完成后不能直接重复运行覆盖新状态。后续修改请使用当前已安装资源作为新基线，避免旧脸型或旧跑步图被重新带回。

预览：<http://127.0.0.1:7469/?view=2d&identity=reference-v1>
