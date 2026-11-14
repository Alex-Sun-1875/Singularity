# 公共设计配置与组合组件

本轮把上一版已校正的外观整理成公共配置与原生组合组件，继续复用原稿素材、公共金属外框和颜色表，没有新增运行依赖或生成图片。

- [接入说明与修改入口](../../../docs/design/preparation-components.md)
- [公共设计配置](../../../src/cocos/assets/scripts/shared/ui/PreparationTheme.ts)
- [公共组合组件](../../../src/cocos/assets/scripts/shared/ui/PreparationControls.ts)
- [构建与验证记录](implementation-result.json)
- [运行截图差异记录](../../../src/cocos/test-results/rpg-shared-v6/pixel-comparison.json)
- [上一版外观与素材来源](../rpg-alignment-v5/README.md)

公开配置覆盖浮层尺寸、手机触控、页头底栏、字号、间距、主要分栏、63项皮肤引用与九宫格切片。姓名牌、页签、职业卡片、属性行、技能行、点数盒和列表底板通过`PreparationControls`组合；徽记、加减按钮和双色职业标注继续由`PreparationSkin`提供，装备边框复用`equipmentIconFrame`的`preparation`外观。

页面只提供实际数据、状态和回调。类型检查、Cocos构建、手机／桌面运行及默认入口检查完成；相同数据下的画面布局和配色保持原样。人物速度与随机强化词条的展示数据差异单独记录，没有修改对应玩法文件。

默认预览为[7469](http://127.0.0.1:7469/?preview=rpg-shared-v6)。验证使用独立存档上下文；TapTap平台与真机仍需另行验收。
