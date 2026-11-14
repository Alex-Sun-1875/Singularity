# FairyGUI 地图 UI 接入

运行工程：Cocos Creator 3.8.8。地图已实际使用官方 `fairygui-cc@1.2.2`，固定 npm 版本和 lockfile。官方仓库 `ccc3.0` 对应源码提交 `cd19b7049079550c3b184e94f0437dc9c11da623`（2024-05-21）；npm 发布于 2024-05。此适配版本并非持续高频维护，升级前应重新检查引擎兼容性。

## 直接复用

- `GRoot`、`InputProcessor`：输入坐标、命中测试、鼠标与触控事件分发。
- 官方示例 `MainMenu` 的序列化 `Button`：内建普通、悬停、按下与选中状态，标题、Radio 与 Controller 联动。只保留 3,684 字节包和 10,640 字节 atlas，没有引入整套大型示例。
- `GComponent`、`GGraph`、`GImage`、`GTextField`：布局、图像和文字。
- `Controller`：地图区域与可见地点筛选。
- `GObject.draggable/dragBounds`：拖动捕获、位移和边界；项目代码只同步缩放与平移状态，不实现拖动算法。
- `GComponent` 的 Hidden overflow：地图内容裁剪。

`AtlasUi.ts` 是项目皮肤与资源适配，`MapPanel.ts` 负责现有地点和道路数据的呈现；任务、装备、区域入口、存档规则保持现有实现。普通 HUD、行囊和骰子面板未迁移至 FairyGUI。

## 现成视觉素材

[Kenney Fantasy UI Borders 1.0](https://kenney.nl/assets/fantasy-ui-borders)，CC0。直接使用原图：

| 原素材 | 运行时文件 | 用途 |
| --- | --- | --- |
| `PNG/Default/Border/panel-border-009.png` | `ui/kenney/button-border.png` | 按钮边框 |
| `PNG/Default/Border/panel-border-014.png` | `ui/kenney/panel-border.png` | 地图与手记面板 |
| `PNG/Default/Divider Fade/divider-fade-003.png` | `ui/kenney/divider.png` | 标题和手记分隔 |

资源只做运行时着色和引擎九宫格拉伸，原 ZIP、许可及源文件保留在 `source-art/ui/kenney-fantasy-borders/`。运行时来源与 SHA-256 在 `assets/resources/ui/provenance.json`。地图插画仍为仓库自有 v3 atlas，未分发 BG3 素材。

## Cocos 兼容适配

`tools/patch-fairygui.cjs` 由 `npm ci` 的 postinstall 自动执行，仅接受 1.2.2，支持重复执行：

1. Cocos 3.8 裁剪构建的 `Mask` 别名不可用，使用同一引擎类的显式导出 `MaskComponent`。
2. 上游 `Math.max(scrollX, scrollY)` 会将向下滚动的负 Y 与零 X 比较而丢失符号；保留有符号 Y（无 Y 时使用 X），使地图滚轮向上放大、向下缩小。

Radio 的 Controller 回调在当前点击分发结束后再重建地图，避免销毁正在处理事件的 Button。关闭地图使用库的 `dispose()` 释放输入与控件；异步图像回调检查对象是否已经释放。纹理及小型 UI 包在本次运行中共享缓存。

Web Desktop 自定义全屏模板在设备旋转时可能已经更新 `screen.windowSize`，而渲染窗口与设计分辨率仍保留旧尺寸。HUD 的现有尺寸检查在物理尺寸变化时调用引擎 `Root.resize` 与固定高度适配，使裁剪、输入、相机和横竖屏提示保持同一尺寸。

## 设计状态

布局继续参考本地 BG3 地图侧栏、图例与层级；当前 UI 已复用 Kenney 素材。用户后来明确要求替换灰蓝背景，先提供[暖色方案清单](ui-color-direction-v2.md)，新配色尚未应用。配色决策与已完成的组件接入分别记录。

验证复用类型检查、本地 Web 构建及实际浏览器交互，不新增测试代码或测试依赖。固定来源资产的 MIT/CC0 许可随 `THIRD_PARTY_NOTICES.txt` 进入本地构建。
