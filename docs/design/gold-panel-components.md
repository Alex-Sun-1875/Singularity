# 暗金面板公共组件

以用户确认的[设置页实装对照](../../test-results/settings-alignment-v11/reference-vs-runtime.png)为视觉基准。继续使用 Cocos 原生 Node、Button、Label、Sprite、ScrollView 与既有图片，不增加运行依赖或生成新皮肤。

2026-11-15按用户反馈修正公共框直边与圆角的亮度差：保留原版四个48×48圆角和全图透明通道，直边RGB按相邻圆角的切线采样连续衔接。当前运行素材与静态图集由[确定性修正脚本](../../source-art/ui/frame-edge-match-v1/prepare.py)复现，来源及哈希见[处理记录](../../source-art/ui/frame-edge-match-v1/provenance.json)；原始提取图保留在`source-art/ui/double-gold-frame-v6/`。

## 组件边界

| 组件／配置 | 管理内容 | 页面管理内容 |
| --- | --- | --- |
| `GoldPanelShell` | 外框组合、标题、公共Header入口、页签、选中标记、淡出分割线、简短底部动作 | 安全区与面板位置、正文和列表、滚动区、业务动作、返回目标 |
| `GoldPanelHeader` | 20像素几何图标、48像素完整触区、胶囊避让、左返回／右关闭切换及交互状态 | Header的宽度与中线、视口、原有关闭／返回动作及禁用状态 |
| `GoldPanelToggle` | 开关轨道、金属旋钮、开／关文字、状态更新 | 整行触控区、点击回调、设置持久化 |
| `DoubleGoldFrame` | 双层暗金边、内衬、阴影、可选对称鹿首与贴形暗衬 | 内容节点 |
| `GoldMenuButton` / `GoldMenuActions` | 切角按钮、主次状态、纵向操作组 | 确认／取消、交易、登录等业务规则 |
| `UI_GOLD_PANEL_RULES` | 标题线、横向行线与底部竖线的公共皮肤及源尺寸 | 具体位置与可用宽度 |
| `UI_GOLD_PANEL_CONTENT` | 说明文字的左右内缩、顶部留白与正文底部留白，普通操作组的可见间距 | 正文与按钮数据 |
| `UI_SETTINGS_REFERENCE` | 已确认425×506设置页的参考坐标 | 真实开关值与三个标签页内容 |

`MenuPanel` 是已有菜单数据的接入层：`Hud.show`、`Hud.showList` 自动创建 `GoldPanelShell`，页面不再绘制另一套标题栏、页签或分割线。开关行自动创建 `GoldPanelToggle`，只有外层整行 Button 接收点击，避免旋钮和整行重复触发。

## 已接入与复用范围

| 页面 | 当前复用方式 |
| --- | --- |
| 设置三个标签页 | 完整外壳、页签、开关、分割线与底部动作；`settings` 预设，保持272×324逻辑尺寸及原稿位置 |
| 暂停、帮助、普通确认与系统提示 | 经 `MenuPanel` 自动使用外壳；保留原有按钮动作、关闭条件及内容滚动 |
| 旅程目录、章节列表、任务详情、章节奖励选择、狩猎列表 | 经 `Hud.show` / `showList` 共用外壳，内容决定高度，长内容在框内滚动 |
| 战役见闻、机遇记录及记录详情 | 同上；文案与返回目标仍由功能维护 |
| 商店交易列表 | 同上；购买、库存、禁用状态及锻造入口保持原有业务实现 |
| 人物、行囊、装备、技能、锻造工作台 | `RpgPanel` 已共用 `DoubleGoldFrame`；保留已确认的宽屏分栏、预览和专用操作，不套用设置页尺寸 |
| 旅途地图 | 专用地图、图例、选点和工具布局；适合后续逐项复用边框与线条，本次未迁入完整外壳 |
| 主菜单 | 继续复用 `GoldMenuButton` / `GoldMenuActions`，保持无大外框的居中窄幅布局 |
| 自动操作控件 | 继续使用紧凑胶囊与状态布局；不加入标题栏或大型面板 |
| 剧情字幕、掷骰舞台、加载主画面 | 保留各自已确认的专用呈现；普通错误或确认提示可走 `Hud.show` |

2026-11-16按用户确认的[组件稿](../../source-art/ui/header-navigation-v1/00-navigation-proposal.png)，所有窗口使用同一个`GoldPanelHeader`。右上关闭的完整触区在安全区内且距TapTap原生胶囊至少8逻辑像素时显示右上叉号，否则显示Header左侧直向左箭头。平台几何来自`ViewportMetrics`，不按页面名字或全屏标记写死；HTML没有原生胶囊时显示右上关闭。窗口、Canvas、横屏方向、胶囊与前后台变化后重新判定，旧宿主缺胶囊接口时保守预留右上区域。详见[布局规范](ui-layout-guidelines.md#二级页面与大弹窗的返回入口)。

`GoldPanelShell.dismissAction`和`RpgPanel.footer`保留既有动作；`MenuChoice.back: true`仍明确详情页的上一级，`MenuPanel`优先采用它并移除底部重复导航。`GoldPanelHeader.setAction`同步动作及禁用状态；禁用时背景点击也不能绕过。确认流程继续通过`dismissOnBackdrop: false`要求明确操作，退出靶场等业务动作保留。图标用Cocos原生`CompactGraphics`绘制，不再加载弯曲回转箭头，不增加依赖。

专用窗口直接调用`GoldPanelHeader.attach(panel, {width, unit, hit, centerY, viewport: hud, action}, run)`。`centerY`使用当前父节点坐标中的Header中线，普通居中面板可取`height / 2 - 32 * unit`；FairyGUI页面同时传入其原点下的`centerX`／`centerY`。组件统一负责完整触区的屏幕坐标转换、两侧选择和图标反馈，页面不得自行强制某种模式。仅调整原有返回目标或可用状态时调用`setAction(action, run, enabled)`。

## 接入已有菜单

常规列表继续调用 `hud.showList(...)`，正文加操作组继续调用 `hud.show(...)`。默认使用 `standard` 外壳，高度由实际内容与安全区约束决定。标题居中，两侧对称预留公共入口空间；普通列表自动使用同一组柔和行分隔线。

普通说明文字在面板12逻辑像素基础内距上再内缩8像素，形成20像素左右留白；说明顶部增加8像素，避免贴着标题分割线。正文采用同一文字内缩。普通纵向操作组的可见间距为16像素；实际触控区仍至少48像素高、间隔8像素，通过在各自点击范围内微调按钮皮肤和文字位置收紧视觉节奏。主菜单保持自己的既有节奏，设置页继续使用已确认坐标。

设置页通过 `MenuPresentation.variant: 'settings'` 选择固定参考布局。`referenceSettings` 仅作为旧接口兼容项保留。设置页坐标与触控区分别管理，不能通过增高面板或挪动可见标签容纳触控区；三个标签页等高，较长内容框内滚动。

## 自定义内容面板

`panelNode` 由调用方放置到安全区内。`unit` 表示每个逻辑屏幕像素对应的 Cocos 设计单位，`hit` 在手机上至少为 `48 * unit`。

```ts
const shell = panelNode.addComponent(GoldPanelShell);
shell.configure({
  title: '面板标题', width, height, hit, unit, mobile: sys.isMobile,
  variant: 'standard', centeredTitle: true,
  dismissAction: 'close', crest: false,
}, action => hud.actions.click(action));

const bodyTop = height / 2 - shell.metrics.bodyTop;
// 页面在 bodyTop 以下添加自己的正文、列表或 ScrollView。
shell.divider(panelNode, 'row', footerTop, width * 0.82);
shell.footer([
  { label: '操作帮助', action: 'help' },
  // dismissAction 交给公共 Header 自适应入口，底部只保留业务动作。
]);
```

`footer` 用于一至两个简短文字动作；更多动作或长按钮使用 `GoldMenuActions`，并由页面预留操作区高度。`crest` 默认关闭，普通小面板不强制加入鹿首；启用时通过 `GoldPanelShell.measure(...).crestReserve` 为完整轮廓预留安全区。

`settings` 预设的完整外框使用425∶506比例；直接使用组件时由调用方提供该比例及可用尺寸。通常优先使用已经处理安全区和滚动的 `MenuPanel` 接入层。

## 更新和清理

组件重复 `configure` 只清理自己创建的装饰和控件，不删除页面正文或自定义子节点。回调随最新配置更新，不叠加旧点击监听。开关组件不注册 Button，也不保存偏好；页面把真实值传入 `on`，通过既有操作层保存。

`loaded` / `ready` / `loadError` 可用于资源与截图验收。页面仍通过 `Hud.clearModal()` 销毁整个菜单；弹窗外点击、必须确认的步骤、登录及前后台恢复继续由原有接入层管理，不因复用外壳增加关闭入口。

管理界面的宽屏皮肤、字号、间距、姓名牌、页签、列表行和卡片进一步统一到[管理界面公共设计与组件](preparation-components.md)；`RpgPanel`继续拥有外壳，公共组合组件只负责视觉和原生控件，业务动作仍由页面提供。
