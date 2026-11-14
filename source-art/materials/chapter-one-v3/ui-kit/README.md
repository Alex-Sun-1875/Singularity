# 白枝蜂蜜金与深棕黑 UI 源文件

最新暖金v4：蜂蜜金 `#DAAE65`、香槟高光 `#F7DA9D`、棕铜暗边 `#8D6030`，深棕黑底；主金属边3.4源像素，面板覆层为3.5%暖象牙。按用户最新参考执行，历史段落只说明既有内凹/角饰结构。

17 张 SVG 均为本作原创矢量几何，沿用原有资源名称、尺寸、切片和 Cocos UUID。2026-11-05 按用户要求对齐 BG3 的奇幻金属界面语言：烟黑渐变、微弧肩角、窄香槟金明暗包边、层叠内凹暗槽和克制的原创卷叶角饰。金色仅占细边与小刻线，没有大面积黄褐底。悬停提高中性亮度，按下保留黑底并以内陷阴影和细青蓝边反馈。生命填充为红莓，专注填充为蓝青。没有使用或打包参考图中的像素。

从仓库根目录重新导出并同步既有 Cocos PNG：

```powershell
node source-art/materials/chapter-one-v3/ui-kit/export.cjs --sync-cocos
```

省略 `--sync-cocos` 时只更新 `assets/materials/chapter-one-v3/ui-kit/`。同步只覆盖既有同名 PNG，拒绝缺少既有 PNG/meta 的资源，不创建或改写 meta。资源目录保留 `ui/quiet-bronze/` 以维持现有引用。

导出器复用项目已安装的 `@resvg/resvg-js@2.6.2`（MPL-2.0），无新增依赖。它校验目录中的源尺寸，记录 SVG/PNG SHA-256、完整 alpha 分布和代表点，生成 `skin.json`、`alpha-report.json` 与 SVG/PNG 静态样张。样张直接组合源矢量并保留半尺寸九宫格边，不启动浏览器或编辑器；它不代表实机验收。

`skin.source.json` 记录设计角色、尺寸、切片与组合规则。2 源像素 = 1 逻辑像素，框线 2 源像素约为显示 1px。Cocos 的切片子节点按目标尺寸两倍设置、局部缩放 0.5；文字与点击区域保持未缩放。所有原尺寸和 insets 均保留；四角刻线全部置于 24 源像素角区，横向拉伸不拉大装饰。

**面板底色由父节点绘制。** `panel-surface` 是冷白、仅 3.5% alpha 的中性抛光覆层，使用 `Color.WHITE`，避免覆盖危险/选中/内嵌等语义底色。它不是不透明背景或皮革材质。

原资源已检视 Kenney Fantasy UI Borders（CC0、1.0/2023）作为九宫格流程参考。细边、独立端帽和白枝角饰沿用项目自有 SVG；本轮重绘黑曜石面与金属层次；没有引入 Kenney 路径。运行时继续使用 Cocos 3.8.8 原生 Sprite/FILLED/SLICED，触区与交互逻辑未改。

- [Cocos 3.8 Sprite](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/editor/sprite.html)
- [resvg-js 与 MPL-2.0](https://github.com/thx/resvg-js)
- [Kenney 官方资源与许可](https://kenney.nl/assets/fantasy-ui-borders)

原创贡献属于本项目；该目录没有另外授予独立再分发许可。手机端画面、压缩、像素对齐和触控仍需由正式引擎运行复核。
