# 装备提示：图文间距与右侧属性

用户已确认本版布局；后续为传奇与神器补充四角花纹的最新效果见 [`../equipment-notice-ornaments/`](../equipment-notice-ornaments/README.md)。

2026-11-16。按用户反馈放开图文间距，并在两类被动装备提示右侧添加基础属性。沿用原 v2 切角暗金框、真实装备图、公共颜色与字体，没有生成新美术。

当前截图还包含后续名称微调：装备名称单独向左移动 4 逻辑像素，品质、状态与属性列保留原位。微调前局部保留为 `preview-stats-before-name-offset.png`；新位置记录在 `src/cocos/release/equipment-notice-name-offset-validation.json`，基础属性数值验证仍见下方记录。

日常 `concept-2d` test 游戏的实际 Cocos 渲染，使用独立浏览器上下文与隔离旅程夹具。满级夹具仅用于展示成长装备及满技能 HUD，不作为奖励来源或成长规则验收。Pillow 仅缩小完整截图，或裁切两条实际通知作局部对照。

- `preview-acquired.png`：获得冷焰短杖。此件目录没有基础数值加成，右侧显示单手杖及 Lv1 等级要求。
- `preview-dropped.png`：传奇最后一班岗。右侧显示按当前人物等级计算的威力与力量。
- `preview-stats.png`：上述两张游戏截图中的提示局部。

完整运行证据保存在 `test-results/equipment-notice-stats/`，当前验证记录为 `src/cocos/release/equipment-notice-stats-validation.json`。之前的居中、左对齐版本及其记录保留。用户最终美术确认、TapTap 真机、安全区与触控验收分开记录。
