# 第一章 PBR 来源档案

日期：2026-11-04。保存四套经实际 albedo 视觉检查后选择的官方 1K 原图、API 元数据和校验依据。候选副本及完整设计说明在 `assets/materials/chapter-one-v3/pbr-library/`。

- `wood_planks_grey/`：Poly Haven 灰褐旧木板，官方覆盖 1.5 × 1.5 m。
- `cobblestone_floor_08/`：Poly Haven 灰米铺石，官方覆盖 2 × 2 m。
- `rock_boulder_dry/`：Poly Haven 浅灰米自然岩面，官方覆盖约 1.8 × 1.8 m。
- `Fabric082A/`：ambientCG 中性浅灰细平织，程序材质；纤维身份及物理尺度 **unknown**。作为亚麻方向替代候选，不能称扫描亚麻。

Poly Haven 图像与 `files.json` 中的官方 MD5/文件大小校验一致；`info.json` 保存作者与毫米物理尺寸。Fabric082A 的 `api-v3.json` 明确 `surface-fully-procedural`，官方尺寸为 0；其原始 ZIP、官方 HTTP SHA1 及解包清单分别保存为 `.zip`、`download-record.json` 和 `archive-inventory.json`。API 不提供逐图 MD5，manifest 对应字段是 `null`，并记录官方 ZIP SHA1、条目 CRC32 和逐图本地 SHA-256。

`manifest.json` 的 `maps.file` 相对此 source-art 目录，`exportFile` 是候选副本的仓库路径。全部图像为官方原字节；没有缩图、调色、拼通道、AI 推导法线或运行时接入。官方 PNG 位深保留，部分为 16-bit。`selection-research.json` 记录实际看过的候选和排除理由；临时预览下载已清理，不作为生产资源。

复用项目已有 `tools/materials/fetch_surfaces.py` 的下载函数，未调用其运行时导出函数；解包采用 Python 标准库。现有 Pillow 仅用于只读解码/尺寸确认，未保存或改绘图像。

来源许可：[Poly Haven CC0](https://polyhaven.com/license)、[ambientCG CC0](https://docs.ambientcg.com/license/)。API 数据单位依据：[Poly Haven 官方 schema](https://github.com/Poly-Haven/Public-API/blob/master/swagger.yml)。Powered by Poly Haven；Fabric082A from ambientCG。
