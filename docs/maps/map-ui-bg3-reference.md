# 旅途地图 UI：本地 BG3 参考与第一版

日期：2026-11-04。当前工程为 `src/cocos`，本次先交付地图 UI，不改写世界地理或实时战斗。

## 本地参考来源

已通过 Steam 库配置及 `appmanifest_1086940.acf` 确认安装目录：

`E:\SteamLibrary\steamapps\common\Baldurs Gate 3`

实际查看的资料：

- `DigitalDeluxe/BG3_Artbook_High_Res.pdf`：目录与世界地图跨页，PDF 第 2、20、21 页。
- `Data/Game.pak` 中的 `Mods/MainUI/GUI/Pages/JournalMap.xaml`：地图主体、区域名称、图例、侧栏、标记与拖动缩放的界面结构。
- 同包 `Public/Game/GUI/Assets/Map/` 下的 `BG3_Worldmap_A.DDS`、`map_banner.DDS`、`map_legend.DDS`、`map_sidePanel.DDS`、`waypointHeader.DDS` 和地点图标。
- 一并检查了 `JournalMap_c.xaml`、`Minimap.xaml`、`OverviewMap.xaml` 的资源位置；本次没有改写小地图。

使用 [Norbyte LSLib](https://github.com/Norbyte/lslib) 1.18.7 只读列出资源并定向解包地图界面。临时工具、参考图片和解包结果保存在 `src/cocos/temp/bg3-reference/`，没有修改游戏安装目录。

## 转化为本作 UI

- 地形为视觉主体，边框使用深色铁灰与克制的暗金线；中文标题使用宋体，操作文字使用雅黑。
- 地表、旧誓下城、沉钟地宫分层切换，避免上下层地点混在同一图面。
- 队伍、地点、未抵达地点、选中地点与自定义标记分别表示；地点状态同时以文字区分。
- 地点详情置于右侧，桌面显示相邻道路；手机横屏优先保留地点名称、状态、描述及标记按钮。
- 支持拖动、滚轮与按钮缩放、全览、定位队伍、地点筛选、标记与取消；桌面另支持方向键、Home、加减号，以及 M / Esc 关闭地图。

本作继续使用现有 v3 三张地形图及 `WorldData.ts` 的地点、道路、探索记录。Cocos 资源目录 `assets/resources/atlas/` 内的图片来自本仓库 `source-art/maps/world-atlas-v3/`，未把 BG3 原图、图标或界面文件加入运行时资源。

## 本次边界

- 这是可操作的地图 UI 第一版。地图标记保留在本次运行的界面状态中，没有新增存档字段。
- 道路高亮表示区域连接参考，未计算场景内的寻路或入口条件，不提供自动移动或传送。
- 地表继续采用已有 atlas 组合坐标；地下使用五区示意排布。美术底图与地点尚未逐像素配准，地图不作为碰撞或精确导航依据。
- U2 当前只有西北前厅可探索，其他部分只作为已有地形图展示。
- 375px 竖屏显示横屏提示，地图操作不会改变角色、装备、任务或存档。

## 实现与验证

`MapPanel.ts` 由 `Hud.atlas()` 调用，`ChapterGame.ts` 接入地图快捷键。后续已接入 FairyGUI 官方控件和 Kenney 边框，见[地图接入记录](../assets/fairygui-map-ui.md)；不新增测试代码、测试脚手架或测试依赖。用户要求替换灰蓝背景，已先列出[暖色方案](../assets/ui-color-direction-v2.md)，尚未应用到运行时。

使用现有 TypeScript 检查、本地 Cocos 构建及真实浏览器交互检查。截图位于 `src/cocos/test-results/map-ui-*.png`；手机横屏截图属于浏览器尺寸模拟，实机表现仍需在设备上查看。
