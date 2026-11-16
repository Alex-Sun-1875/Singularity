# 现行 UI 视觉风格

本文件维护剑与火当前 UI 的视觉来源与复用入口。尺寸适配、触控和生命周期见[布局规范](ui-layout-guidelines.md)，不在这里另存一套规则。表中组件数值与资源版本以链接到的源码为准。

## 来源优先级

1. 用户本轮明确要求和已确认修改，优先于旧稿及旧记录。
2. 当前已确认的游戏外观、原稿提取皮肤和对应逐项对照；核对被修改的具体部位，不能仅凭文件夹版本号判断。
3. 实现该外观的共享组件、skin 与语义 token。运行画面若与确认稿有差异，应记录偏差，不能直接把偏差提升为风格规范。
4. 外部游戏参考只用于任务层级、地图组织、阅读与选择方式，不接管本项目的页头、字体、材质、装饰或关闭样式。
5. 未确认稿标为候选；用户已否定的稿只留历史。生成完成、类型检查和浏览器验收分别记载，不等同于美术或用户确认。

本轮`source-art/ui/adventure-journal-v2/`的顶部和整体风格已被用户否定，不能作为新页面的视觉基线；后续稿仍须对齐下列现行来源，未确认方向不能先写成新的审美规则。

## 可核查的现行来源

| 来源 | 用于核对什么 | 状态边界 |
| --- | --- | --- |
| [管理页原稿](../../../../source-art/ui/equipment-profession-points-v1/03-profession-preview.png)、[rpg-alignment-v5/README](../../../../source-art/ui/rpg-alignment-v5/README.md)、[局部对照](../../../../source-art/ui/rpg-alignment-v5/marked-regions-comparison.jpg)、[取样记录](../../../../source-art/ui/rpg-alignment-v5/reference-parts.json) | 原稿提取的姓名牌、侧栏、装备框、选中边框、属性／技能条和暖色材质 | 使用其已确认外观与提取依据；个别新绘图标的待确认状态不能被略去。 |
| [rpg-shared-v6/README](../../../../source-art/ui/rpg-shared-v6/README.md)、[运行总览](../../../../source-art/ui/rpg-shared-v6/runtime-overview.jpg)、[实现记录](../../../../source-art/ui/rpg-shared-v6/implementation-result.json) | 将上一版外观归入公共配置和组合组件，保持原有配色与布局 | 这是复用入口，不是另一套新美术。 |
| [header-navigation-v1/design](../../../../source-art/ui/header-navigation-v1/design.json)、[确认记录](../../../../source-art/ui/header-navigation-v1/review.json) | 同一 Header 的细线直向左箭头／细线关闭、标题、分隔线与状态反馈 | 已有用户确认；平台胶囊与真机安全区验收仍单独登记。 |
| [设置原图](../../../../source-art/ui/double-gold-frame-v6/reference-design.png)、[settings-alignment-v11/provenance](../../../../source-art/ui/settings-alignment-v11/provenance.json)、[分隔线来源](../../../../source-art/ui/settings-alignment-v11/rules-provenance.json) | 设置页原稿比例、淡出金线、鹿首透明轮廓及贴形暗衬 | v11保存提取件与溯源，不是另一张新增确认的整页稿；不将鹿首、比例或全部装饰套到其他页面，保留来源文件中的待验收状态。 |

## 应保留的视觉语言

- **材质与边框**：暖深棕、近黑内衬及克制的金属高光。管理页沿用原稿空白纹理，普通菜单沿用现有深色实底；圆角双细暗金边保持角与直边色泽连续，不另加厚黑框。已有雕纹按原皮肤与适用部位保留，不从外部参考新加大卷草、花冠或满屏装饰。
- **文字与层级**：沿用`RpgFont.applyRpgFont`的公共衬线字库、暖白正文和暖金强调。标题、导航、列表标题、正文、辅助文字从相应组件的字级字段读取，不临时套一组网页字体或把整页文字缩小来补布局。
- **页头与页签**：页名、标签文字和细分隔线优先复用现有 Header／管理页导航。选中态使用原有细金线、暖金或组件指定的语义强调；不将普通页签改成蓝绿大牌匾、厚金属招牌或带大块发光底色的主视觉。
- **颜色与状态**：状态读取`FeedbackPalette`／`FeedbackView`。现有浅青选中文字、数值与局部徽记可以继续按语义使用，不能把这个 token 扩成整条蓝绿页头或新的主色体系。选中、悬停、按下、禁用不能只靠装饰表达或挪动布局。
- **按钮与图标**：普通明确动作复用既有暗金菜单按钮；管理页使用对应原稿按钮与行卡。可见按钮和触控范围分别计算，不为填满热区放大整张按钮贴图。返回与关闭只使用公共细线图标，不另画弯曲回转箭头、圆形关闭徽章或第二套常驻底板。

## 组件、skin 与 token 映射

以下路径均位于`src/cocos/assets/scripts/shared/ui/`；设计稿先核对这些入口，运行实现也从同一入口取值。

| 部位 | 共享入口 | 应读取的配置／皮肤 |
| --- | --- | --- |
| 管理页整体与分栏 | [RpgPanel](../../../../src/cocos/assets/scripts/shared/ui/RpgPanel.ts)、[PreparationTheme](../../../../src/cocos/assets/scripts/shared/ui/PreparationTheme.ts) | `PREPARATION_DESIGN.shell/header/layouts`；`PREPARATION_SKINS.header/surface/logo/rule/active`。当前 Header 高度取`UI_PANEL_HEADER.height`，旧`header.visibleHeightLogical`仅是原稿测量，不能当作当前 Header 高度。 |
| 管理页字级与行距 | [PreparationTheme](../../../../src/cocos/assets/scripts/shared/ui/PreparationTheme.ts)、[RpgFont](../../../../src/cocos/assets/scripts/shared/ui/RpgFont.ts) | `typography.navigation/body/rowTitle/small/lineHeight`等角色字段；`ui/quiet-bronze/rpg-serif-v2`公共字体。`minimumLogical`是下限，不是所有正文的目标字号。 |
| 姓名牌、侧栏、行卡和点数盒 | [PreparationControls](../../../../src/cocos/assets/scripts/shared/ui/PreparationControls.ts)、[PreparationSkin](../../../../src/cocos/assets/scripts/shared/ui/PreparationSkin.ts) | `identity`、`side-tab`、`side-tab-selected`、`attribute-row`、`skill-row`、`skill-selected`、`point-counter`等原稿皮肤；不重画近似版本。 |
| 共用金属框与内衬 | [DoubleGoldFrame](../../../../src/cocos/assets/scripts/shared/ui/DoubleGoldFrame.ts)、[UiSkin](../../../../src/cocos/assets/scripts/shared/ui/UiSkin.ts)、[UiChrome](../../../../src/cocos/assets/scripts/shared/ui/UiChrome.ts) | `UI_FRAME_LAYOUT`、`UI_FRAME_GOLD`；`double-gold-frame-v6`、管理页`double-gold-frame-rpg-v4`及对应内衬／切片。不能拉粗边框或把特定页面鹿首作为通用页头。 |
| 普通内容框、设置与开关 | [GoldPanelShell](../../../../src/cocos/assets/scripts/shared/ui/GoldPanelShell.ts)、[GoldPanelToggle](../../../../src/cocos/assets/scripts/shared/ui/GoldPanelToggle.ts) | `UI_GOLD_PANEL_RULES`、设置专属`UI_SETTINGS_REFERENCE`；`settings-title-rule-v11`、`settings-row-rule-v11`、`settings-footer-rule-v11`。 |
| 返回／关闭 | [GoldPanelHeader](../../../../src/cocos/assets/scripts/shared/ui/GoldPanelHeader.ts)、[UiChrome](../../../../src/cocos/assets/scripts/shared/ui/UiChrome.ts) | `UI_PANEL_HEADER`的高度、图标、线宽与反馈面。根据完整触区与真实安全区／胶囊关系选择左返回或右关闭，只留一个入口；切换样式不改变原路由。 |
| 菜单动作 | [GoldMenuButton](../../../../src/cocos/assets/scripts/shared/ui/GoldMenuButton.ts)、[GoldMenuActions](../../../../src/cocos/assets/scripts/shared/ui/GoldMenuActions.ts) | `UI_MENU_BUTTON`；`start-menu-primary-v8`／`start-menu-secondary-v8`。管理页则从`PREPARATION_SKINS.button-dark/button-gold`等对应原稿部位取材，不混成另一套按钮。 |
| 文字、强调与业务状态色 | [UiTheme](../../../../src/cocos/assets/scripts/shared/ui/UiTheme.ts)、[FeedbackPalette](../../../../src/cocos/assets/scripts/shared/ui/FeedbackPalette.ts)、[FeedbackView](../../../../src/cocos/assets/scripts/shared/ui/FeedbackView.ts) | `UI_COLORS`、`PREPARATION_DESIGN.colorRoles`与`text.*`／`state.*`等语义角色；不在页面另存RGB。 |

## 本轮地图／任务设计稿补充

用户已批准[冒险日志v6](../../../../source-art/ui/adventure-journal-v6/design-spec.json)开始运行接入；设计文件原有`pending`记录是批准前的静态阶段状态，不等于运行或手机触控验收已通过。

- 整体紧凑通过减少可见皮肤、重复边框、说明与空白实现，沿用既有字级且任何文字不低于11逻辑像素；除下一条明确的右栏例外，不能借此缩小其他控件触区。
- **28逻辑像素仅适用于地图右栏传送点列表行**，选中皮肤高22；列表独立滚动，传送动作固定右栏底部并保留48触区及列表间8像素净空。逐行命中不得叠加重合的隐形48触区，也不能宣称已满足48触控标准；接入后单独验证点选相邻行和滑动精度。任务树仍为连续48行，Header、页签、地图工具与主要动作仍保留48触区，独立按钮间距规则不变。
- 本次地图与任务接入明确使用左侧返回，覆盖这两个页面的Header自动选侧，不将全部页面一律左返写成全局规则；其他页面继续按原安全区／胶囊规则处理。
- 返回复用公共20逻辑像素细线直箭头与48逻辑像素触区，不新增常驻底板；设计批准、Cocos运行接入、浏览器触控和TapTap真机验收分别记录。

## 使用时的最小核对

先选一个最接近本次页面的已确认部位，对照其字体、标题／页签、材质、按钮和边框；从上表复用对应字段。新稿中仍需决定的布局或插画标候选，不把外部参考的整体装饰复制进来。接入后在实际游戏核对同一部位；来源、设计稿、生成结果、运行接入和用户确认分别记录。
