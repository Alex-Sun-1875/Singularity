# 环境纹理压缩审查 v3

2026-11-05，Cocos Creator 3.8.8，横屏 `web-mobile`。**本轮未交付纹理缩容，交付元数据已回退全部 48 张环境 PNG。** 官方压缩预设与 `genMipmaps=true` 保留，48 张图的 `useCompressTexture=false`；生成入口 `src/cocos/asset-pipeline/environment/metadata.py` 同样持久化禁用，避免重新导出时误启用。软件渲染器的全 PNG 控制仍复现树枝亮色异常，根因未确认，不能把该现象直接归因于 ASTC，也不能记为已完成手机压缩验收。

## 实测预算与兼容路径

环境库仍首次加载 31 个共享模型、24 套材质及 48 张图，没有实施分区延迟加载。20 张颜色图为 512²、4 张为 1024²，24 张法线图为 512²。下表来自运行中 `Texture2D.getGFXTexture()` 的格式、`levelCount` 与 `size`，是引擎报告的纹理有效载荷，不包含驱动额外开销，也不是下载包体或 TapTap 首包。

| 实际运行分支 | 环境格式 | 完整 mip 有效载荷 | 画面结论 |
| --- | --- | ---: | --- |
| NVIDIA RTX 3080 / ANGLE D3D11，自然 PNG 回退 | 48 × RGBA8 | 83,886,016 B，约 80 MiB | 森林截图正常，0 页面错误、0 失败请求 |
| SwiftShader / ANGLE Vulkan，首次全压缩审查 | 48 × ASTC 4×4 / 6×6 | 15,217,120 B，约 14.51 MiB | 树枝出现亮洋红，未通过 |
| SwiftShader / ANGLE Vulkan，树木 6 图 PNG 回退审查 | 42 × ASTC，6 × RGBA8 | 32,489,272 B，约 30.98 MiB | 树枝仍出现青绿异常，未通过 |
| SwiftShader / ANGLE Vulkan，最终全 PNG 控制 | 48 × RGBA8 | 83,886,016 B，约 80 MiB | 同样青绿树枝，0 页面错误、0 失败请求；异常并非只发生于 ASTC 路径 |

512² 图实测 10 级 mip，1024² 图 11 级；RGBA8 基层共 60 MiB，完整 mip 共约 80 MiB。另有六套地表 PBR 的 18 张 512² 图，共 25,165,800 B、约 24 MiB；因此全 PNG 路径两组图合计约 104 MiB，尚未包含人物、UI、阴影、深度和其他渲染目标。首次加载/常驻预算仍需后续缩容。最终构建的 48 张环境 PNG 共 21,439,454 B、约 20.45 MiB，运行请求全部成功；这只统计这组纹理的文件量。48 张源图 SHA-256 均与原环境 manifest 一致。

RTX 上实际只宣告 S3TC 扩展，没有 ASTC；引擎选择 PNG 后全部 48 张为 RGBA8。SwiftShader 使用 Chrome 官方 `--use-angle=swiftshader --enable-unsafe-swiftshader` 开关，实际宣告 `WEBGL_compressed_texture_astc`；压缩分支 GFX 格式确为 `ASTC_RGBA_4X4` / `ASTC_RGBA_6X6`。没有改写扩展、格式或运行中替换材质来伪造通过。Android UA、915×412 CSS 视口和 DPR 2 只是手机布局模拟；SwiftShader 是软件渲染器，RTX 是桌面 GPU，两者均不能证明手机硬件帧率、耗电或驱动兼容性。

## 官方流程与画质边界

采用 [Cocos 官方纹理压缩预设与兼容回退](https://docs.cocos.com/creator/3.8/manual/en/asset/compress-texture.html)，通过本机 `Editor.Profile` 保存真实项目字段。预设为不透明颜色 ASTC 6×6、透明颜色及法线 ASTC 4×4，均 `thorough`，并保留 PNG 兼容图；未新增库或引擎模块开关。

本机 Creator 随附的 [Arm ASTC Encoder](https://github.com/ARM-software/astc-encoder)（Apache-2.0）`5.2.0` 完成编码和官方 `-dl` 解码。检查实际构建的 Cocos CMIP 容器、逐级 ASTC 头、尺寸和有效载荷；42 图混合方案的压缩有效载荷为 11,517,760 B。树枝/树干颜色与法线的官方逐级解码未发现截图中的亮色，树枝颜色基层逐 RGB 平均绝对误差约 0.77/0.71/0.75（0–255）。这些结果只证明离线解码与结构检查，不能取代实际渲染；异常根因仍未证实，不能归咎某一驱动或宣称压缩成功。树木六图在启动时已是 PNG，仍出现异常，因此局部回退不足以隔离问题。

透明测试阈值保持 0.38、双面开启；PNG 兼容图的 alpha 与源图逐像素相同。官方 ASTC 4×4 单图往返的覆盖率变化较小：树叶 54.6464%→54.6401%，草 19.0044%→18.9957%，蕨类 16.0564%→16.0408%。普通 mip 在远处仍会让细草变薄；没有实现或宣称覆盖率保持 mip，也没有通过改色、降低阈值或手写压缩算法掩盖问题。

环境资源仍为 [Poly Haven CC0 原作者素材及派生网格](environment-fidelity-v2.md)，逐文件来源、官方 MD5、SHA-256 见 [来源清单](environment-fidelity-v2-sources.json)。本轮只改变导入元数据和官方预设，原 PNG 未改绘、未染色。

## 留存证据

- [最终 RTX PNG 运行记录](../../src/cocos/test-results/environment-compression-png-delivery-final.json)及[正常森林帧](../../src/cocos/test-results/environment-compression-png-delivery-final-forest-mobile.png)，0 页面错误、0 失败请求。
- [最终 SwiftShader 全 PNG 控制](../../src/cocos/test-results/environment-compression-swiftshader-png-control.json)及[仍有青绿树枝的森林帧](../../src/cocos/test-results/environment-compression-swiftshader-png-control-forest-mobile.png)，0 页面错误、0 失败请求。
- [最终 PNG 产物与源哈希检查](../../src/cocos/test-results/environment-png-delivery-build.json)：48 PNG、0 ASTC、48 个源 SHA-256 一致。
- [42 ASTC + 6 PNG 运行记录](../../src/cocos/test-results/environment-compression-astc-tree-png.json)及[未通过的森林帧](../../src/cocos/test-results/environment-compression-astc-tree-png-forest-mobile.png)。此轮旧预览服务器有 21 次连接拒绝，资源重试后 48 图齐全；不能写成零错误。
- [实际构建容器检查](../../src/cocos/test-results/environment-compressed-build-final.json)、[树木逐 mip 官方解码](../../src/cocos/test-results/environment-tree-astc-diagnosis.json)、[alpha 往返与 mip 诊断](../../src/cocos/test-results/environment-alpha-compression.json)。这些是历史压缩审查产物，当前交付元数据全部禁用压缩。

最终两轮已串行完成并关闭浏览器。全 PNG 控制排除了“仅在 ASTC 图采样时才出现”的解释，但尚未定位软件渲染器、着色器或场景数据中的具体原因；没有继续修改运行材质来制造正常帧。RTX PNG 画面通过此次桌面检查，真实手机 GPU 仍未验证。森林画面采用独立视觉区域切换，明确属于视觉 fixture，不是无授予主线通关证明。
