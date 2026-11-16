# 装备获得页重设计

当前界面已更新为[紧凑的 v3](equipment-acquisition-v3.md)，本页保留 v2 运行记录。

2026-11-15。首次获得装备只展示装备图、说明和基础属性，不再提供免费掷骰、随机铸印或额外升格装备。随机属性仅在原有强化流程中产生。

![手机横屏运行效果](../../source-art/ui/equipment-acquisition-v2/preview-iphone14.png)

## 页面与接入

- `DicePanel` 的装备分支改为纯获得确认页，保留探索事件的 D20 页面。获得页显示真实装备名称、品质／部位、基础说明和基础属性，底部只有「收下装备」。按钮点击与 Enter／空格均直接确认。
- 复用 `DoubleGoldFrame`、`GoldMenuButton`、`equipmentIconFrame` 和 `EquipmentArt.rawIcon`，品质边线保持逻辑尺寸，不随大图加粗。按实际安全区居中，手机四周保留场景，横屏按钮触区高 48 逻辑像素；短横屏与竖屏分别排布。
- `equipmentBasePresentation` 从装备目录与等级成长计算基础展示，不混入强化、宝石或历史骰印。等级要求使用 `requiredLevel ?? 1`，武器威力沿用实际 `power / 3` 百分比，成长装备读取当前等级的基础数据。
- 示例佣兵护胸 DR1-02 的基础护甲为 +6%；说明中的物理伤害减免 4% 是独立固有效果，按真实数据分别显示。
- 首次装备队列复用已有 `gear:` 记录及回执，但不生成骰点、随机属性或额外装备；确认仅标记已看并关闭。背包的免费摇骰入口与相关帮助宣传已移除，强化继续使用 `EquipmentForging.enhance → syncRandomForging` 的材料消耗与持久词条。
- 已结算的历史记录和来源凭证保留，不清空已有装备或强化。旧未确认骰点在确认获得页时清空，避免激活新的免费属性或额外装备。

## 验证

使用日常 `concept-2d`、test 正常玩法档位进行浏览器验收。呈现夹具在独立浏览器上下文中显示，截图只证明布局与展示，不作为掉落来源或概率证据。

截图与按钮、属性、视口记录位于 `test-results/equipment-acquisition-v2/`。验收覆盖 844×390、932×430、915×412、568×320、1280×720、竖屏与受限安全区。TapTap 真机、安全区和触控仍需实机验收；本次未打包、上传或发布小游戏。

`npm run check`、Web 导出、现有骰子回归 20 项及获得／强化规则断言 15 项均通过。获得、重复确认、拒绝掷骰、强化词条持久化、旧未确认骰点清除及存档校验分别验证；汇总见 `src/cocos/release/equipment-acquisition-validation.json`。完整来源与持久留档见[运行截图说明](../../source-art/ui/equipment-acquisition-v2/README.md)。
