# 剑与火：破晓之战 · 图标与封面 v1

2026-11-10，为 TapTap 小游戏制作。视觉主题是**燃焰长剑、青灰群山与破晓金光**：银蓝剑刃、黄铜护手与剑首、金红火焰，配合游戏现有的山谷、石桥、旧镇与暖金界面。采用器物与环境构图，不改动已确认的主角外貌。

## 交付文件

最终上传素材保存在 [`src/cocos/release/branding/taptap-v1`](../../../src/cocos/release/branding/taptap-v1)：

| 文件 | 用途 | 尺寸 | 体积 |
| --- | --- | --- | --- |
| `icon-512.png` | 建议上传的 TapTap 图标 | 512×512 | 478,917 字节 |
| `icon-1024.png` | 大尺寸图标备选 | 1024×1024 | 1,858,137 字节 |
| `cover-landscape-1920x1080.jpg` | 横版封面/宣传图 | 1920×1080 | 918,553 字节 |
| `cover-square-1440x1440.jpg` | 方形封面/宣传图 | 1440×1440 | 939,605 字节 |
| `icon-192.png` / `icon-32.png` | 网页构建图标 | 192 / 32 | 见 manifest |
| `favicon.ico` | 桌面快捷方式等备用 | 多尺寸 | 见 manifest |

图标为完整直角方图、实色绘画背景；未烘焙圆角或添加角标。封面仅排入“剑与火 / 破晓之战”，没有口号、平台标志、评分或其他宣传字样。封面是宣传插画，**不是实机截图**，不替代平台要求的实际截图和录屏。

项目的公开素材引用登记在 `src/cocos/release/taptap-project.json.branding`；Web 构建自动复制小尺寸图标并使用。店铺图标与封面仍需在开发者中心选择上传，本次没有上传或修改线上页面。

## 来源、处理与验收

- 生成方式：云端 OpenAI 内置 `image_gen`，两次生成。图标第一次无参考图；封面只使用本次图标作为剑型和绘画风格参考。未运行本地模型，没有额外下载模型或依赖。
- 原始输出：[`icon-generated.png`](icon-generated.png) 为 1254×1254，[`cover-generated.png`](cover-generated.png) 为 1672×941。保留原件，最终规格经本地 Lanczos 缩放/裁切；两个封面包含适量上采样，不能表述为模型原生 1920/1440 输出。
- 最终提示词原文与生成状态见 [`prompts.json`](prompts.json)。生成成功与美术检查分开记录，文件尺寸、SHA-256、字体来源及验收结论见 [`manifest.json`](manifest.json)。
- 本地处理：[`export.py`](export.py) 使用已有 Pillow 完成可重复的中文排版、金属字面、尺寸导出和压缩；未使用生成模型修字。标题使用系统已安装的 Noto Serif SC 可变字体，主标题900、次标题650字重；仅输出位图，没有分发字体文件。字体为 [SIL OFL 1.1](https://github.com/notofonts/noto-cjk/blob/main/Serif/LICENSE)。
- 无损排版母版保留为 `title-logo.png`、`cover-landscape-master.png`、`cover-square-master.png`；缩略检查见 [`preview.jpg`](preview.jpg)。
- 助手已视觉复核中文文字、构图、整剑边缘、图标48/64像素辨识度及两种封面；格式、尺寸、非透明图标及两张封面小于2MB通过文件检查。用户于2026-11-10明确选择沿用本第一版（燃焰长剑与破晓群山）；平台审核未进行。

在仓库根运行 `python source-art/branding/taptap-v1/export.py` 可重新排版导出，需本机已有 `C:/Windows/Fonts/NotoSerifSC-VF.ttf`；更换字体后应重新复核字形和版式。重新导出会将美术验收状态重置为待检查。

官方依据：[图标尺寸及直角要求](https://developer.taptap.cn/docs/store/release/publish/material/)、[小游戏宣传图尺寸/体积/文字要求](https://developer.taptap.cn/minigameapidoc/quick-start/guide/game-publish/material/)、[小游戏图标审核规范](https://developer.taptap.cn/minigameapidoc/tap-operation/operation-standards/review-standards/)。
