# 自然绿地候选 Grass007

2026-11-04。来源：[ambientCG Grass007](https://ambientcg.com/a/Grass007)，[CC0 1.0](https://docs.ambientcg.com/license/)。四张 1024² PNG 均为同一官方 1K 包的未变色原字节，包含 Color、OpenGL Normal、Roughness 和 Ambient Occlusion；共 9,343,251 字节。没有染绿、缩图、预乘 AO、混搭材质或生成假法线。

仅比较了 Grass005 与 Grass007 的真实 1K Color：Grass005 是均匀亮黄绿的密短草，细线感和草坪感明显，未选；Grass007 的阔叶、苔草块面和零星枯枝更接近自然绿地，裸露褐土少，也减少满屏细线。实际原色是较鲜的橄榄黄绿，仍需在中性光和游戏正常视距检查；不能宣称已达到 BG3 的视觉表现。它是混合草叶/杂草地表，不能称纯草叶草坪。

官方 API v3 标记 `surface-procedural-bitmap-elements`，不是实地扫描；宽、高、深均为 0，物理尺度 **unknown**。`previewTileMetres: [2,2]` 仅作为地表比较的设计建议尺度，不能当成测量值。

Albedo 按 sRGB 解释，Normal/Roughness/AO 按线性数据解释，Normal 为原始 16-bit OpenGL +Y；非金属候选 `metallic: 0`。原始 ZIP、官方 SHA1、API 快照及 CRC32 清单在 `source-art/materials/chapter-one-v3/terrain-library/green-grass/`。官方 API 未提供逐图 MD5，故该字段为 `null`；各图另记本地 SHA-256。

`entry.json` 的 `maps.file` 相对上一级 `terrain-library/`，供主清单合并；此任务没有修改 terrain manifest、下载脚本或运行时。四通道原图已可解码，原 ZIP 官方 SHA1、ZIP CRC32 与副本一致性均已检查；平铺、缩小及引擎验收仍待完成。
