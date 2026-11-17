# 管理界面公共设计与组件

人物、装备、职业、属性／技能加点、技能配置和锻造共同使用本套设计。当前外观以[已校正运行稿](../../source-art/ui/rpg-alignment-v5/README.md)为基准；这次整理提取公共配置和组合组件。

## 修改入口

| 内容 | 公共入口 | 页面职责 |
| --- | --- | --- |
| 画布、安全区留白、浮层大小、页头、底栏、字号、间距、控件尺寸和主要分栏 | `shared/ui/PreparationTheme.ts` 的 `PREPARATION_DESIGN` | 提供真实内容，计算滚动范围及页面特有位置 |
| 皮肤名称、素材版本、九宫格切片 | 同文件的 `PREPARATION_SKINS`、`PREPARATION_SKIN_INSETS` | 按语义名称引用，不再拼接素材版本 |
| 暖白正文、金色强调、选中和禁用颜色 | `PREPARATION_DESIGN.colorRoles` 绑定 `FeedbackPalette.ts`；通用底色继续由 `UiTheme.ts` 管理 | 只选择状态，不在页面复制 RGB |
| 圆角浮层、遮罩、导航、底部动作、滚动区及文字基线 | `RpgPanel`；金属外框复用 `DoubleGoldFrame` | 选择当前标签，提供正文与动作 |
| 姓名牌、页签、职业卡片、属性行、技能行、点数盒、列表底板 | `PreparationControls` | 提供文字、数值、可用状态、回调 |
| 材质、分隔线、徽记、金色标签、加减控件、双色职业标注 | `PreparationSkin` | 使用语义皮肤，不另做近似图形 |
| 装备槽位边框与裁切 | `equipmentIconFrame(..., {appearance:'preparation'})` | 提供装备图像和选中状态；`quality` 外观继续服务已有品质展示 |

`UiTheme.ts` 也导出 `PREPARATION_DESIGN` 与 `PREPARATION_SKINS`，便于从通用主题入口访问。沿用现有公共颜色定义，不在页面新建一套色值；材质亮度由公共素材目录引用已校正纹理。

## 组件接入

```ts
import {PreparationControls as Controls} from '../../../shared/ui/PreparationControls';
import {PREPARATION_DESIGN as Design} from '../../../shared/ui/PreparationTheme';

Controls.identity(ui, {
  value: heroName,
  x: 102, y: ui.contentBottom - 32,
  width: 174,
});

Controls.tab(ui, {
  x: 93, y: 67, width: 160,
  label: title,
  action: 'example:attributes',
  selected: true,
  run: openAttributes,
});

// 技能配置、加点、锻造和服务列表共用同一组选中底板。
Controls.rowBackground(ui, rowNode, rowWidth, rowHeight, selected);

// 属性行不读取或修改 GameSession，业务层决定是否允许加减。
Controls.attributeRow(ui, {
  y: rowY, height: rowHeight,
  label: attributeName, icon: 'attribute-strength',
  before, after,
  decrease: {action: 'example:decrease', enabled: canDecrease, run: decrease},
  increase: {action: 'example:increase', enabled: canIncrease, run: increase},
});
```

`professionCard`、`skillRow` 和 `pointCounter` 同样只接受展示数据与 `PreparationAction`。新页面复用组件，不复制对应的底板、文字与按钮组合；场景、成长规则、装备适配、存档和确认流程仍由功能模块负责。

## 单位与状态

- `PREPARATION_DESIGN.canvas` 使用844×390原稿坐标；九宫格切片是1844像素源图中的尺寸。公共组件在渲染时换算到 Cocos 坐标。
- `Logical` 后缀表示实际屏幕逻辑像素。手机热区48、间隔8；不能为了缩小可见皮肤一起缩小热区。
- `identity`、`tab`、`professionCard`、`attributeRow`、`pointCounter` 的位置是面板原稿坐标。`skillRow` 的位置是列表父容器内的原稿单位，y沿用Cocos局部坐标方向。
- 低层 `PreparationSkin.art`、`caption`、`badge` 以及 `Controls.icon` 保留已有Cocos位置参数，宽、高和字号按原稿单位传入；新页面优先使用高层组合组件。
- 当前值、草稿值、是否可用与动作均来自页面。公共组件不推断职业、不修改点数，也不写入存档。
- 组合组件继续创建原生Node、Button、Label、Sprite与既有裁切节点，随所属`RpgPanel`统一销毁；没有新增运行依赖。
- 公共Header下的正文边界统一读取`RpgPanel.contentTop/contentBottom`；`column`背景不向上补到旧原稿顶线。宽桌面保留原稿字级与控件尺寸，原稿正文坐标通过`referenceY`映射到当前正文范围，避免64逻辑像素Header被分栏、人物图或首排内容覆盖。底部动作继续由`RpgPanel.footer`固定布局。

2026-11-17正文边界修复通过类型检查与正常test的`concept-2d`构建；1920×1080桌面连续切换六个管理页签，844×390与932×430／3倍密度检查加点、技能和培养，均未发现正文覆盖Header。实际触摸滚动后Header保持固定，关闭后无残留模态节点；截图与测量见`test-results/rpg-header-content-boundary-v1/review.json`。使用隔离浏览器会话并禁用保存回调，TapTap真机与真实安全区仍待单独验收。

## 后续调整

1. 改颜色：修改公共颜色表对应语义；改适用范围则改`colorRoles`。
2. 改控件尺寸／间距：修改`PREPARATION_DESIGN`中对应组件或布局配置。
3. 换材质：在`PREPARATION_SKINS`登记版本与切片，通过`PreparationSkin`引用。
4. 增加组合控件：放在`PreparationControls`，参数提供数据和回调，避免引入功能模块规则。
5. 复用现有手机、桌面与安全区检查；整理公共代码时，对比已有运行截图，确认外观没有意外变化。

本轮构建和运行结果记录在`source-art/ui/rpg-shared-v6/`。Web预览不代替TapTap平台与真机验收。
