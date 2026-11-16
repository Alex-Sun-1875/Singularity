# 统一装备提示运行截图

后续按用户反馈放开图文间距并增加右侧基础属性，最新截图见 [`../equipment-notice-stats/`](../equipment-notice-stats/README.md)。本目录保留此前迭代。

2026-11-16。复用已确认的 `../loot-alert-v1/` v2 资源，没有重新生成装备或边框美术。

当前截图按用户复查修正为三行左对齐，正文靠近装备图，保持原字号与行距。此前误用居中的运行截图保留在 `before-left-alignment/`，仅作问题历史，不代表原稿。

日常 `concept-2d`、test 正常规则的实际 Cocos Web 游戏场景，使用独立浏览器上下文及临时旅程夹具。截图保存引擎真实渲染，Pillow 仅等比缩小留档，不替换或合成提示内容。

- `preview-acquired.png`：稀有冷焰短杖获得通知。
- `preview-dropped.png`：传奇最后一班岗地面掉落通知。
- `preview-alignment.png`：从上述两张游戏截图裁切的提示局部，便于检查共同左边界和图文间距。

当前左对齐的完整截图与测量在 `test-results/equipment-notice-left-alignment/`；验证记录在 `src/cocos/release/equipment-notice-left-alignment-validation.json`。此前生命周期检查继续保留在 `test-results/equipment-notice-unified-v2/` 及其对应验证记录。运行夹具不改用户原有存档，不作为合法掉落来源或概率证据；本轮美术复查与用户最终美术确认分开，TapTap 真机待验收。
