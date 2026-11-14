# 地面补给瓶 v1

后续状态：用户指出本版瓶子仍显漂浮，并要求不透光瓶身。此版本作为历史原画保留；当前替代方案见[贴地补给瓶v2](../supply-bottles-v2/README.md)。v2同时修正竖直朝向镜头的网格与阴影方向。

2026-11-12按用户要求制作并接入三种实体瓶子外观：圆腹红色生命药瓶、棱面蓝色专注药瓶、带皮革束带与未点燃布塞的棕色火油瓶。

原画由云端 OpenAI `image_gen` 分别生成，均为1254×1254透明PNG；完整提示词在[对应记录](prompts.json)，原始生成图在`raw/`。生成成功与美术验收状态分别记录于[来源与校验](provenance.json)。本批没有使用本地生成模型。

通过仓库已有Pillow进行透明区域裁切、Lanczos缩小和轻微接触阴影合成，输出三张256×256透明PNG。处理脚本为`tools/design/prepare-supply-bottles.py`，游戏素材位于`src/cocos/assets/resources/equipment/supplies-v1/`，合计211739字节，复用已有装备资源加载与分包路径。

地面呈现使用原画颜色、低贴地锚点和每瓶一张网格，不再加载药剂／火油UI符号，不再显示补给光晕。HUD仍按其既有设计显示快捷操作图标。瓶子是适配当前绘制场景的透明道具精灵，并非新建的三维模型。

使用既有规则驱动复核满库存保留、消耗后补入、部分拾取、隔墙禁止、过期清理及重载，结果见`test-results/supply-bottles-v1/rules-review.json`。实际Web场景结果、844×390／DPR3及932×430画面记录在同目录的`browser-review.json`和PNG。TapTap包和真机表现仍需后续验证。
