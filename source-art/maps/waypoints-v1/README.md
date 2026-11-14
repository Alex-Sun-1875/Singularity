# 传送入口符文与定位

当前运行采用[古代符文传送阵版](../waypoints-runes-v8/README.md)，下面保留第一版制作与交互验收记录。

2026-11-08。依据用户要求，参考《博德之门3》古代符文环的地标识别方式，把当前换图出口改为青紫色符文阵，并同步改善目的地与地图定位。

当前97区有320个定向ExitDef（160条双向区域连接）。本轮呈现跟随真实出口坐标、开启条件与1.35m交互半径；实际执行继续使用既有F/触屏交互。24个安全休整区保持篝火语义，区别于换图入口。

## 画面与操作

每个出口有2.6m直立符文环和3.2m贴地阵纹。贴地网格直接复用实际Ground三角，透明边缘配合Clamp采样；旅店整图模式同样叠加。符文缓慢呼吸，已开放入口青紫发光，受剧情门闩约束的入口变暗。

场景标牌常驻显示目的地；近距提示F或触屏点击，锁定入口明确显示未开启。已发现的屏外入口提供方向和距离。小地图及本地图采用统一双环符文与高对比描边；休整点保留独立的金色标识。

世界地图补齐高地、河湾、城域选择，并按CAMPAIGN_ATLAS画面坐标修正地下地点重叠。新增三张地区图复用本项目原有世界atlas，保留来源记录，不引入BG3运行素材。

## 素材与实现

- [云端生成及来源](generation.json)、[完整提示词](prompt.txt)
- [原始RGBA](raw/ancient-sigil.png)、[处理记录](processing.json)
- [灰底透明小样](sigil-gray-preview.jpg)
- [第一版纹理（保留）](../../../src/cocos/assets/resources/flat2d/waypoints-v1/ancient-sigil.png)
- [历史简化加粗纹理](../../../src/cocos/assets/resources/flat2d/waypoints-v1/ancient-sigil-balanced-v3.png)
- [准备脚本](../../../tools/model-pipeline/prepare_waypoint_sigil.py)

仅一次云端OpenAI image_gen生成，用户石厅图用作必要风格参考。原图1254×1254，按实际输出保存。模型输出的宽紫色雾幕由Pillow/NumPy确定性alpha提取去除，并以细笔画生成克制的局部光晕，运行纹理1024×1024 RGBA。没有调用本地模型或下载依赖。生成结果、像素处理和运行验收分别记录。

实现复用Cocos原生Mesh、Material、Graphics与项目已有FairyGUI地图控件；没有新增UI框架。World里的符文可穿过，碰撞、导航、出口条件和到达坐标仍由原数据负责。

## 验收

最终portal-sigil-v3已通过97区/320个实际出口的正常生产渲染；桌面与手机DPR2完成8次新旅程真实换图、E03原有解锁与回程、锁定拒绝、六地区地图、场景与RT资源释放检查，错误和失败请求均为0。手机近距标牌46 CSS像素高，点击不同时触发攻击。

原E03近入口镜头已复核：安静安全靠近时人物和阵法完整入镜；真实攻击时镜头扩大，松开恢复。构建中发现的Set展开兼容问题也已修复，保留现有真实敌人素材与身份映射。

- [最终运行与美术验收](runtime-review.json)
- [游戏内画面对照](runtime-portal-review.jpg)与[原截图索引](runtime-portal-review.sources.json)
- [最终构建和一致性校验](portal-sigil-v3-build.json)
- [地图标记与原图来源](map-marker-review.json)

全区域轮巡用于生产渲染覆盖；实际交互另有独立流程，手机检查为浏览器触屏模拟。

参考页面：[Ancient Sigil Circle](https://bg3.wiki/wiki/Ancient_Sigil_Circle)。参考其识别语言，符文图形为本轮独立生成的分枝纹样。
