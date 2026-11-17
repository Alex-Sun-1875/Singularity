# TapTap 店铺素材 · v1

- `icon-512.png`：建议上传的512×512图标；`icon-1024.png` 是大尺寸备选，均为直角、不透明完整方图。
- `cover-landscape-1920x1080.jpg`：横版宣传图，约0.92MB。
- `cover-square-1440x1440.jpg`：方形宣传图，约0.94MB。
- 两张宣传图只包含游戏名称“剑与火 / 破晓之战”，均小于2MB。
- `icon-192.png`、`icon-32.png`、`favicon.ico` 供网页图标和桌面快捷方式复用。

采用云端 OpenAI image_gen 生成图画、本地 Pillow 精确排字和导出。原图、提示词、字体与验收记录在仓库 `source-art/branding/taptap-v1/`。这些是宣传插画，不是游戏实机截图。素材已完成助手视觉检查，尚未上传或通过平台审核。

官方规格：[小游戏宣传物料](https://developer.taptap.cn/minigameapidoc/quick-start/guide/game-publish/material/)、[图标规范](https://developer.taptap.cn/docs/store/release/publish/material/)。

2026-11-17：`icon-512.png` 已上传至当前游戏素材库（image-926830），选入 V-20261110 待提审草稿并观察到自动保存；后台页眉图标已同步。未提交审核或发布，手机启动页同步尚待重新进入验证；封面与其他宣传材料仍未上传。此次未修改代码或重打包。

2026-11-18后续状态：横版宣传图 image-926958、方形宣传图 image-926957 与正式图标均已选入 V-20261110 草稿，随0.3.60 release包体、九张截图和四职业视频一起保存；游戏版本未提审或发布。详见仓库 `promotion/records/taptap-upload-progress.json`。
