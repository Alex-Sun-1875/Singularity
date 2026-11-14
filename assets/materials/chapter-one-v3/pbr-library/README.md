# 第一章 PBR 来源候选

日期：2026-11-04。此目录提供四套 **官方 1K PNG 原图的逐字节副本**，用于资源设计审阅；尚未进入 Cocos resources、材质实例或运行时。每套均为同一官方材质的 Albedo、OpenGL Normal、Roughness、AO 四通道，没有混搭、修色、缩图或从 AI 色彩图生成法线。

| 目录 | 官方来源 | 官方物理覆盖范围 | 实际视觉与设计差异 |
| --- | --- | --- | --- |
| `grey-planks` | [Poly Haven · Wood Planks Grey](https://polyhaven.com/a/wood_planks_grey) | 1.5 × 1.5 m | 低饱和灰褐旧木；宽板、钉头和纵纹明确。比组合板 v2 更暗、更旧、略偏冷；树种未确认，不能命名为扫描橡木。 |
| `grey-paving` | [Poly Haven · Cobblestone Floor 08](https://polyhaven.com/a/cobblestone_floor_08) | 2 × 2 m | 灰米为主，包含青灰/粉灰单石和稀疏绿缝；比旧 `cobblestone_floor_04` 绿植少。圆角矩形铺石较组合板更规整；岩性未确认，不能直接称石灰岩。 |
| `natural-rock` | [Poly Haven · Rock Boulder Dry](https://polyhaven.com/a/rock_boulder_dry) | 约 1.8 × 1.8 m | 浅灰米自然裂隙与矿物斑，含少量黄褐地衣；与铺石的规则接缝区分。比组合板偏暖、斑驳更明显，不能称纯冷灰岩或指定地质类型。 |
| `neutral-woven` | [ambientCG · Fabric082A](https://ambientcg.com/a/Fabric082A) | **unknown** | 原色中性浅灰细平织，无蓝染、格纹或毛毡纤维。比组合板亚麻更细、更干净、更浅；官方标记为程序材质、未证实亚麻纤维，只作为**中性亚麻方向的替代候选**。 |

Poly Haven 的尺度来自 `info` API 的毫米尺寸，换算为米；单位定义见[官方 API schema](https://github.com/Poly-Haven/Public-API/blob/master/swagger.yml)。Fabric082A 的官方宽高均为 0，故 `tileMetres: null`；`previewTileMetres: [0.25, 0.25]` 仅是衣料细纹审阅时的设计建议尺度，不是扫描测量值。

每个材质目录中的 `albedo.png` 用 sRGB 解释，另外三张是线性数据。法线均为官方 OpenGL +Y 版本，未翻转绿色通道；四套均按非金属候选记录 `metallic: 0`。AO 独立保存，未预乘进 albedo。PNG 保留官方位深：部分木、岩和布法线为 16-bit；这是来源审阅包，不是最终移动端纹理压缩规格。

文件来源、官方校验信息、SHA-256、实际尺寸/位深、字节数及逐套视觉限制在 `manifest.json`。16 张图全部为 1024 × 1024，共 41,304,892 字节。源文件、API 快照和 Fabric082A 官方 ZIP 保留在 `source-art/materials/chapter-one-v3/pbr-library/`，此处仅复制四张必需通道。

Poly Haven 每张文件均对照官方 API 的 MD5 和字节数。ambientCG API 没有公布逐图 MD5，因此对应字段保留 `null`，不能把本机计算的 MD5 冒充官方值；原始 ZIP 对照下载服务器返回的 `x-bz-content-sha1`，解包另校验 ZIP CRC32，各图均计算本地 SHA-256。

本次复用了 `tools/materials/fetch_surfaces.py` 的下载函数，没有调用其运行时导出流程，也未新增依赖或测试。旧来源中琥珀橙木 `wood_floor_worn`、红褐岩 `rock_face`、蓝布 `rough_linen` 经实际查看后未沿用；没有以 RGB 乘色把它们伪装成新方向。选择过程及其他排除项记录在 source-art 中的 `selection-research.json`。

许可已核对：[Poly Haven CC0](https://polyhaven.com/license)、[ambientCG CC0 1.0](https://docs.ambientcg.com/license/)。下载脚本以唯一 User-Agent 访问官方 API；[Poly Haven API 条款](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md)与已下载的 CC0 素材许可分开。来源鸣谢：Powered by Poly Haven；Fabric082A from ambientCG。

已验证原图可解码、官方校验值及源/候选副本一致。平铺、正常游戏镜头、mip 缩小、法线强度、粗糙度表现和角色衣料摩尔纹仍需独立审阅；本目录不宣称已通过无缝或引擎验收。
