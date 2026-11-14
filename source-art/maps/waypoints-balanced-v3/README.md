# 符文简化加粗版

本版作为历史留存，当前运行采用[古代符文传送阵版](../waypoints-runes-v8/README.md)。

2026-11-08。采用原双环、中心分枝和八组疏朗大符文，通过加粗笔画、紫色描边和紧凑光晕提高识别度。高密多层候选被用户反馈过于复杂，保存为[过程稿](../waypoints-bold-v2/generation.json)，本版回到原有结构。

## 素材处理

本版直接复用[第一版云端素材](../waypoints-v1/generation.json)，用项目现有Pillow/NumPy做确定性alpha笔画扩张和描边合成，没有调用本地生成模型，也没有再次生图。双环和符文数量保持，主笔画覆盖更饱满，镂空处仍透明。

- [原版与加粗版灰底对照](comparison-gray.jpg)
- [暗底对照](comparison-dark.jpg)
- [处理记录和SHA](processing.json)
- [确定性准备脚本](../../../tools/model-pipeline/prepare_waypoint_sigil_balanced.py)
- [当前运行纹理](../../../src/cocos/assets/resources/flat2d/waypoints-v1/ancient-sigil-balanced-v3.png)

开放入口的直立层透明度改为220±12，贴地层164±12，仍以5.2秒缓慢呼吸；未开启入口保持原来的灰紫弱光。尺寸、出口坐标、提示、镜头与交互使用现有实现。

像素处理后的alpha>128覆盖从4.68%升至13.22%，用于比较视觉分量，并非独立的笔画宽度测量。灰底和8组桌面/手机DPR2同机位画面已目视检查，实际新纹理GPU加载与97区320入口生产渲染均通过，0错误/0失败请求；快速双F和双点击仅换图一次且不出剑。

- [游戏内新旧对照](runtime-before-after.jpg)与[截图来源](runtime-before-after.sources.json)
- [最终运行验收](runtime-review.json)
- [构建校验](portal-sigil-balanced-v1-build.json)
