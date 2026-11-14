# 第一章配套 PBR 运行接入 v3

2026-11-04。将已审阅的六套来源材质接入 Cocos Creator 3.8.8；本轮不增加玩法。

| 运行表面 | 完整来源 | 一次平铺宽度 | 运行贴图 |
| --- | --- | --- | --- |
| wood | [Poly Haven wood_planks_grey](https://polyhaven.com/a/wood_planks_grey) | 1.5 m，官方尺寸 | 512² Color / Normal / PBR |
| cobble | [Poly Haven cobblestone_floor_08](https://polyhaven.com/a/cobblestone_floor_08) | 2 m，官方尺寸 | 同上 |
| rock | [Poly Haven rock_boulder_dry](https://polyhaven.com/a/rock_boulder_dry) | 1.8 m，官方尺寸 | 同上 |
| fabric | [ambientCG Fabric082A](https://ambientcg.com/a/Fabric082A) | 0.25 m，本作建议，官方未知 | 同上 |
| earth | [Poly Haven forest_ground_06](https://polyhaven.com/a/forest_ground_06) | 2.11 m，官方尺寸 | 同上 |
| grass | [ambientCG Grass007](https://ambientcg.com/a/Grass007) | 2 m，本作建议，官方未知 | 同上 |

来源均为 CC0-1.0：[Poly Haven 许可](https://polyhaven.com/license)、[ambientCG 许可](https://docs.ambientcg.com/license/)。Fabric082A 为程序生成的细平织布，纤维种类未知；不能称为已确认亚麻或扫描亚麻。Grass007 为程序加位图元素地表，不能称为实地扫描。岩石未确认岩性，木板未确认树种。

原始 1K 文件保留在 `source-art/materials/chapter-one-v3/` 与 `assets/materials/chapter-one-v3/{pbr-library,terrain-library}/`，没有染色或覆盖。导出器逐图检查来源 manifest 的 SHA-256，再让本机已有的 Blender 4.5.15 LTS 完成图像解码、缩放、通道合并与 PNG 导出。不新增图像依赖，不手写重建材质算法。

运行文件在 `src/cocos/assets/resources/surfaces/pbr-v3/`。完整来源 URL、原图位深、原图 SHA-256、可用官方 MD5、每张运行图的尺寸/字节数/SHA-256，以及每套物理尺寸边界，记录在该目录的 `provenance.json`。18 张 PNG 共 **7,760,584 字节**。这份新清单只描述六套新表面，上一版 `surfaces/provenance.json` 继续描述保留的其他旧表面。

## 导出与色彩契约

复现命令（仓库根目录 PowerShell）：

```powershell
& src/.tools/blender-4.5.15-windows-x64/blender.exe --background --factory-startup --python tools/materials/export_pbr_runtime_v3.py
```

- 底色：Blender `sRGB` 输入，经原生 compositor Scale 在场景线性空间缩为 512²，再以 `Standard` / sRGB 输出；曝光 0、gamma 1、look None。没有烘焙 AO、染色或通道倍率。
- 法线、AO、粗糙度：`Non-Color` 输入，在 Blender 浮点 compositor 中缩放，以 `Raw` 输出。原 PNG16 由 Blender 原生解码，不经 Pillow RGB8 隐式截断；最后明确量化为运行用 RGB PNG8。所有源 PNG16 保留原字节。数据图没有 gamma 转换。
- 法线维持配套的 OpenGL +Y 约定，不翻转绿通道、不从底色推断法线、不混用 AI 色卡。
- 原生 Separate/Combine RGBA 节点打包 **R=AO、G=roughness、B=0**。RGB PNG 在 GPU 采样时隐含 A=1，维持材质的 specularIntensity。关闭输出 dithering，保证 metallic 通道精确为 0。
- Cocos 贴图使用 repeat、linear min/mag、linear mipfilter、anisotropy 4。纹理由材质库共享。7456 预览实际读取 18 张 GFX texture，均为 **RGBA8 / 10 级 mip**，每张 **1,398,100 字节**，总计 **25,165,800 字节（约 24 MiB）**。这是解压加完整 mip 的显存数，不是 PNG 下载尺寸；还不包含人物、环境物件、旧表面、阴影和帧缓冲。

适配使用 Blender 原生功能和 Cocos 官方标准材质，工具仅负责源文件选择、节点接线、Cocos metadata 与来源记录。Blender 为独立创作工具，不打入游戏；没有新增第三方运行库。

## Cocos 材质接入

已核对本机 3.8.8 的 `engine/editor/assets/effects/builtin-standard.effect`，并参考[官方 PBR 文档](https://docs.cocos.com/creator/3.8/manual/en/shader/effect-builtin-pbr.html)。该版本使用 `USE_PBR_MAP` 和 `pbrMap`，默认通道 R/G/B/A 分别为 AO/roughness/metallic/specularIntensity。

标准 shader 对 AlbedoMap 显式调用 `SRGBToLinear`，对 Normal/PBR 直接取样。因此数据 PNG 保持线性数值，不能预先做 sRGB 转换，也不能让底色被双重解码。PBR 粗糙度通道会乘 uniform，本轮设置 `roughness=1` 保留整套来源响应；`occlusion=1` 启用配套 AO（引擎默认值为 0）；六套均设置 `metallic=0`。

`SurfaceMaterials.load()` 在创建材质前载入六套的三张贴图，其他 plaster/leather/roof/metal 继续兼容原调用。`create()` / `actor()` 接口保留；移除旧岩石及旧蓝布的强 RGB 补偿。人物 fabric 将原模型的身份染色传入中性底布，织物 UV 重复 4 次；未将白布强行调回旧蓝布。透明眉毛、睫毛和发片在 Material.initialize 的 states 内配置双面，避免对共享 Material 直接 overridePipelineStates。

`SurfaceMaterials.tileMetres(surface)` 提供世界尺寸的平铺接口。场景地面与道路应使用世界米制 UV 除以该值，避免将 1.5 m 木板拉成数米宽。布与草的值是设计建议，不能把它们写成已测量的真实尺寸。

## 验证记录

Blender 导出成功，18 张 PNG 均为 512×512 RGB8，源图 SHA-256 与清单一致。独立重读全部导出图，核实 18 个输出 SHA-256 和六张 PBR 的 B 通道严格为 0。已运行现有 `npm run check`（`src/cocos`），TypeScript 通过。

通过项目现成 `cocos-mcp.py` 刷新源脚本和资源后，以现有 Playwright/Chrome 打开真实 7456 预览：游戏 ready、页面错误 0；地板、铺石、地毯及人物衣物的实际 `USE_PBR_MAP` / `USE_NORMAL_MAP` 均为 true，新贴图 UUID 与运行 metadata 对应，occlusion=1，衣物 roughness=1、normalStrength=.45，人物原身份染色保留。读取 18 张贴图确认 10 级真实 GPU mip；地面和人物衣物网格存在 `a_tangent`，满足标准切线空间法线前提。证据保存在项目既有输出目录 `src/cocos/test-results/pbr-runtime-v3*.json`。

2026-11-05 正式 `web-mobile` 构建已再次实际读取：18 张512² RGBA8/10级mip，合计25,165,800字节；Ground/Road 的 mainColor 为白、roughness=1、occlusion=1，实际 Pass UBO 的 albedoScale=(1,1,1)。正式包三种植被材质均启用 USE_TWOSIDE、cull NONE；直接读取已载入颜色图的 alpha，草与树的假黑不透明比例均为0。证据为 `src/cocos/test-results/final-release-material-audit.json`；较早 `pbr-runtime-v3.json` 含已被移除的调用端染色，应按历史记录理解。

手机镜头已缩近至正交半高3米，并用半球环境填光提高暗部可读性；路边草簇以共享模型补一株较低邻草，各自保留通行清理。实际触控旅店至林地的连续路线与最后正常镜头见 `final-release-visual-review.json`。以上证明接入与当前浏览器表现，不代表全章最终美术或真机性能验收。
