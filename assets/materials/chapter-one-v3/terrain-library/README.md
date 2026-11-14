# 地表配套资源候选

默认审阅选择 `forest-earth` 和 `green-grass`，每套完整 Albedo / OpenGL Normal / Roughness / AO。官方原始图逐字节保留，没有把AI图与扫描/程序材质通道混搭。

| 目录 | 来源与处理 | 尺度与状态 |
| --- | --- | --- |
| `forest-earth` | [Poly Haven Forest Ground 06](https://polyhaven.com/a/forest_ground_06)，原色林土、少量碎石和落叶，1K JPG未转码 | 官方尺寸约2.11m；源完整、待正常镜头与mip审阅 |
| `green-grass` | [ambientCG Grass007](https://ambientcg.com/a/Grass007)，原色橄榄阔叶/苔草块面，1K PNG未转码 | 官方尺寸unknown；2m仅是比较用预览建议。程序/bitmap元素来源，不能称实地扫描 |
| `leafy-grass` | [Poly Haven Leafy Grass](https://polyhaven.com/a/leafy_grass)，完整1K JPG | **未选对照**：粉黄土与斑秃感过强，不进入默认材质预览 |

许可为各自官方CC0，记录见[完整清单](manifest.json)及[Grass007来源记录](green-grass/entry.json)。Poly Haven逐图MD5核对；ambientCG用官方原始ZIP服务器SHA1、ZIP CRC和解包图SHA-256核对，不编造逐图官方MD5。Albedo=sRGB，其余为线性数据；Normal均OpenGL +Y。

这些是离线来源素材，不是移动端压缩包。Grass007的枯枝重复、亮绿程度以及与泥土过渡仍须按场景检查。来源图和下载元数据保留在 `source-art/materials/chapter-one-v3/terrain-library/`；`tools/materials/fetch_terrain_kit.py`复用既有下载帮助函数，缓存校验后生成汇总。Grass007已下载的entry与原图必须存在才会被汇总，不会在脚本里猜测新的下载地址。
