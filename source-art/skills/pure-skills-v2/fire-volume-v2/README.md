# 火爆体积素材 v2

本目录保留2026-11-08云端OpenAI image_gen原始输出、实际提示词和必要参考局部。原图为1254×1254 RGBA；四阶段尺寸并不严格遵守等分网格，因此按独立主体区域裁切，不截掉跨中线的第二帧。

运行图位于 `src/cocos/assets/resources/vfx/production/fire-volume-v2/phase0..3.png`，统一768×432画布、脚锚(384,400)。仅Pillow裁切、排版和清除alpha≤4的背景噪声，没有生成新像素。原始输出字节未改。

小样审阅确认了红橙翻卷、暗腔、横向爆开和无人物/地面。已在默认试玩包的FIR_02代表爆燃画面核对透明边缘、共同脚锚与红橙翻卷主形，证据见[实际运行记录](../../../../src/cocos/test-results/combat-design-alignment-final/actual-render-report.json)；其他阶级的逐项美术验收另记。生成成功不代表设计稿已经完全对齐。这些是OpenAI生成资产，不能标成Kenney CC0。

提示词见 `prompt.txt`，SHA256、源裁切框、透明清理及状态见 `provenance.json`。

2026-11-08 后续重构改用 [五个不同卷层的空间火体](LAYERED-RUNTIME.md)，不再把整张主火纹理横向压成椭圆。派生来源、等比处理和新的实际审阅状态独立记录；上面的旧单卡运行记录不代表本次五层火体已通过美术验收。
