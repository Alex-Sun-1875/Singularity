# 随机强化界面设计稿 v2

后续用户要求进一步对齐原稿，当前运行界面与逐屏对照见[视觉对齐v3](../character-panels-bg3-v3/README.md)。本页运行截图保留上一轮记录。

2026-11-10。用户已确认按装备品质确定随机强化属性容量，最多三条。本版延续暖金、深棕皮革与旧铜细框，更新同一次强化的预览和完成两个状态。用户已确认按此方向实施。现已接入人物、装备、技能及强化四类Cocos原生面板；最终运行画面仍待用户美术验收。

![强化前后总览](review/overview.jpg)

## 两个状态

| 设计稿 | 关键表达 |
| --- | --- |
| [强化前](screens/01-preview.png) | 传奇单手剑“最后一班岗”＋5，已有伤害＋3.8%、暴击率＋1.4%，第三条标明＋6解锁；右侧展示候选、概率与费用。 |
| [强化后](screens/02-result.png) | 到达＋6，高亮新增“力量＋2”，原两条保留；显示消耗、剩余资源和已达阶段上限。 |

品质规则：普通／精良最多一条，稀有／史诗最多两条，传奇／神器最多三条。＋1／＋3／＋6按容量依次开槽，其余阶数随机增强已有属性。完整规则见[装备随机强化方案](../../../docs/design/equipment-random-enhancement-v2.md)。

示例消耗130金币、3废铁，持有868金币、96废铁，完成后738金币、93废铁。阶段上限＋6，装备自身极限＋12。设计稿词条数值属于说明样例；运行版按真实存档随机生成，范围与概率直接取规则层，因此不强制与稿中结果相同。

## 生成与验收

- 云端 OpenAI 内置 `image_gen` 分别生成两张，原图完整保存在 screens，不修改生成像素。完整提示词见 [prompts](prompts/)，来源与SHA256见 [provenance.json](provenance.json)。
- 两张原始强化稿的图像输入为[第一版工坊稿](../character-panels-bg3-v1/screens/04-forging.png)。后续运行资源使用项目自己的角色、图标及局部工坊参考；具体输入分别记录在各来源清单中，没有上传官方游戏截图。
- 原生尺寸每张1844×853，按844×390手机横屏比例构思。总览仅用Pillow缩放、排版和添加审阅标题。
- 生成状态：完成。设计检查：已核对三条属性位、传奇品质、前后强化等级、候选与实际结果的区别、费用和阶段限制。
- 用户确认了方向并授权实施。生成完成、助手视觉检查、用户最终美术验收分别记录；最终运行画面待用户审阅。Web触控与布局结果见下方，TapTap平台及真机表现待验证。

总览和归档可通过 [prepare-review.py](prepare-review.py) 重现；脚本仅做确定性的本地图像处理，不运行生成模型。

## 运行资源与实际界面

- [空工坊来源](room-background-provenance.json)：从局部工坊参考生成空房间，移除武器和文字，作为可独立叠放的展示背景。
- [立绘与技能来源](painted-assets-provenance.json)：全身拉斐尔透明立绘，以及逐风、烈焰、雷霆技能图谱；[破军图标提取](approved-icon-extraction.json)直接使用已确认稿中的七个插画。共30个独立技能图供技能页与HUD共用。
- [大剑来源](sword-provenance.json)：独立透明剑插画，供“最后一班岗”的强化大图展示，其他装备仍按实际物品使用自身资源。
- [界面提取清单](runtime-chrome.json)：皮革纹理、细铜框、按钮、标志、属性图标及部位缺图时的同风格插画，以Pillow确定性提取；按钮去除原稿文字，所有运行数值和操作文字使用原生Label。
- [字体来源及许可](font-provenance.json)：复用已安装的Noto Serif SC，FontTools按项目字符集子集化、固定450字重并改名，完整OFL 1.1许可证随字体与资源保存。未下载字体或模型。

[源资源清单与SHA256](runtime-asset-manifest.json)记录59件运行文件共9,847,002字节（约9.39MiB，包含字体及许可，不含.meta）；不是平台上传包、首包或可玩前下载量。界面材质与技能插画已登记独立TapTap分包配置，平台构建与真机加载另验收。

运行代码为Cocos原生组件，资源位于 `src/cocos/assets/resources/ui/quiet-bronze/` 与 `ui/combat-relief/`。人物页采用完整立绘，九个装备槽、物品格、技能升级与装配、随机强化均读取实际存档。为了满足手机48逻辑像素触控区及8像素间距，紧凑视觉按钮与触控区分别布局，长详情可滚动；示例装备和数值不会硬编码为设计稿的演示状态。

[接入与验证记录](../../../docs/design/equipment-random-enhancement-integration-v2.md)说明规则、旧档迁移、已完成检查与平台待验收项。最新运行截图（不是新生成的设计稿）：

![四类面板的实际运行画面](review/runtime-panels-v2.jpg)

[强化稿与运行画面对照](review/forge-runtime-comparison-v2.jpg)；[截图来源与验收状态](runtime-review.json)。

| 面板 | 手机运行截图 |
| --- | --- |
| 人物 | [属性预览](../../../src/cocos/test-results/random-forging-v2/mobile-character-preview.png) |
| 装备 | [装备与行囊](../../../src/cocos/test-results/random-forging-v2/mobile-equipment.png) |
| 技能 | [目录与装配](../../../src/cocos/test-results/random-forging-v2/mobile-skills.png) |
| 强化 | [确认前](../../../src/cocos/test-results/random-forging-v2/mobile-forge-preview.png)、[揭晓后](../../../src/cocos/test-results/random-forging-v2/mobile-forge-result.png) |

生成资源、助手视觉复核及用户验收是三个独立状态。当前为资源生成完成、已接入并进行实际运行对照；用户对最终效果的确认和TapTap真机验收尚未完成。[默认本地试玩入口](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural)已同步，刷新后可打开人物、行囊、技能和工坊查看。
