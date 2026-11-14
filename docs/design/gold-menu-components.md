# 暗金菜单公共组件

按钮皮肤取自已确认的[居中菜单稿](../../source-art/ui/start-menu-v8/centered-menu-proposal-v8.png)，继续复用现有 Cocos Sprite、Button 与衬线字体，不新增依赖或图片。

| 组件 | 职责 | 接入位置 |
| --- | --- | --- |
| `GoldMenuButton` | 切角皮肤、居中文字、主次样式、按下与禁用状态、点击回调 | 纵向操作组、普通列表底部按钮 |
| `GoldMenuActions` | 按数据排列等宽按钮，支持不同行高、间距和异步就绪状态 | 主菜单、新建确认、帮助与各类提示／恢复弹窗 |
| `DoubleGoldFrame` | 双层面板边框、内衬、阴影与可选鹿首 | 普通菜单和设置面板 |
| `GoldPanelShell` | 公共标题栏、关闭、页签、淡出分割线、简短底部动作 | 设置与 `MenuPanel` 各类内容面板 |
| `GoldPanelToggle` | 金属开关与实时状态文字，不重复注册点击区 | 设置及后续需要同类开关的面板 |

组件只管理显示和输入。游戏操作、返回目标、存档、登录和前后台恢复仍由页面负责。设置标签、关闭符号、开关行继续用对应的控件语义，不能注册成重复的操作按钮。

完整外壳与局部复用范围、预设选择及接入示例见[暗金面板公共组件](gold-panel-components.md)。

## 使用操作组

在已有 UI 节点上添加组件，传入文案和动作标识；节点坐标代表整组中心。`height` 是单项触控高度，`unit` 是每个逻辑屏幕像素对应的 Cocos 设计单位。手机传入至少 `48 * unit` 的触控高度、`8 * unit` 的间距和足够的按钮宽度。

```ts
const unit = sys.isMobile ? hud.touchTargetSize / 48 : 1;
const node = hud.node('MenuActions', parent, x, y, 220 * unit, 0);
node.addComponent(GoldMenuActions).configure([
  { label: '继续旅途', action: 'begin', primary: true },
  { label: '设置', action: 'settings' },
], {
  width: 220 * unit,
  height: 48 * unit,
  gap: 8 * unit,
  unit,
}, action => hud.actions.click(action));
```

`primary` 选择深青色，普通项使用深棕色；`disabled` 同时禁用点击并改变文字和皮肤状态。长文案可传 `wrap: true` 和实际测量的单项 `height`，由页面保留足够高度。短按钮的可见条带与触控区分开，不为压缩外观而缩小触控区。

单独使用按钮时调用 `GoldMenuButton.configure(options, callback)`；可用 `setLabel` 和 `setInteractable` 更新内容或状态。重复配置会更新原控件，不叠加点击监听。操作组重复配置只重建自己创建的按钮，不删除调用方添加的装饰或页面节点。

`GoldMenuActionsLayout.visualGap` 可单独收紧可见条带间距；组件会限制皮肤和文字在原触控区内移动，不改变按钮中心、触控高度或触控区间距。不传该参数时保留原布局；主菜单继续使用原稿的节奏。

`loaded` / `ready` 表示皮肤加载状态，可用于截图验收。页面清理继续通过 `Hud.clearModal()` 销毁节点，不保留隐藏触控区。

## 样式维护

`UI_MENU_BUTTON` 集中维护公共皮肤、源图尺寸和可见高度，`UI_START_MENU` 维护主菜单的位置比例。颜色与文本反馈复用 `UiTheme`、`FeedbackView`，页面不复制按钮绘制代码，也不重新生成近似皮肤。
