# 六区怪物、首领与掉落概念图

当前战斗已更新为[四系纯技能与人物等级](../../../docs/design/combat-skills-v2.md)，效果参考转看[当前四系强化参考](../../skills/pure-skills-v2/README.md)。本目录保留上一批13板的原始来源和当时概念审阅；R3投掷者与头目的投掷动作不再用于当前技能设计，后续需重画施法姿态，未宣称这些静态板已是技能动画。

2026-11-08。选用13张概念板：恢复原聊天的7张，加本轮6张区域掉落板；本轮另有1次吊坠链条的云端定向编辑。生成全部使用OpenAI内置image_gen，本轮没有启动Qwen/ComfyUI。

**生成完成与美术审阅分开记录。** 本轮只通过概念方向审阅；正式动画、透明切图、碰撞、武器握点、脚部锚点及手机实机验收尚未完成，也未声称用户已验收。

![十三张选用概念板总览](concept-overview.jpg)

## 内容入口

- [完整设计](../../../docs/design/encounters-and-loot-v2.md)
- [主线与命名](../../../docs/design/campaign-v6.md)
- [97处逐关表](../../../docs/design/world-levels-v2.md)
- [奖励和装备属性](../../../docs/design/loot-catalog-v2.md)
- [结构化设计数据](campaign-design.json)、[静态覆盖核对](design-validation.json)
- [生成来源、SHA256与独立审图记录](provenance.json)

## 逐板检查

| 文件 | 画面内容 | 审阅记录 |
|---|---|---|
| [r1-stonebridge.png](r1-stonebridge.png) | R1 铁誓边境 | 两首领、四普通敌、四装备的布局与成年轮廓可读；盾兵具体副武器仍须动画母版确认。 |
| [r2-highlands.png](r2-highlands.png) | R2 断岳高地 | 桥卫/督猎与四足采掘机可区分，钢木链环各有材质；山路位移须玩法制作。 |
| [r3-bellriver.png](r3-bellriver.png) | R3 风暴河湾 | 油壶头目、打捞者、钟卫及钩手轮廓可区分；油区与可破坏索桩是后续行为。 |
| [r4-greyrock.png](r4-greyrock.png) | R4 黑冠城域 | 统帅/典狱长与盾、弩、镜、旗可区分；人物和武器未做正式碰撞/帧锚点验收。 |
| [u1-oathcity.png](u1-oathcity.png) | U1 誓火深城 | 冷白炉槽、三像同基座、六足虫、负重架可区分；不是灵魂/熔岩生物。 |
| [u2-catacombs.png](u2-catacombs.png) | U2 沉钟禁域 | 闸轮盾、三脚镜匣、实体镜眼和钟傀可区分；光路与闸门需要独立制作。 |
| [elite-loot.png](elite-loot.png) | 八件精英固定奖 | 4×2八件奖，长剑/锤/轮盾/镜匣轮廓不同；边缘与透明切片未验。 |
| [drops-r1.png](drops-r1.png) | R1 区域掉落四件 | 护盔、护胸、双护手、绿晶指环四件完整，材料可区分。 |
| [drops-r2.png](drops-r2.png) | R2 区域掉落四件 | 双护胫、羊毛兜帽、短杖、风翼吊坠完整；护胫上边留白偏紧，正式图标需补安全边。 |
| [drops-r3.png](drops-r3.png) | R3 区域掉落四件 | 皮靴、双护腕、完整长弯刀、双色宝石戒四件完整；并非同图换色。 |
| [drops-r4.png](drops-r4.png) | R4 区域掉落四件 | 盔、胸甲、长窄直剑、双环蓝晶戒完整；剑尖靠近图角，正式切片需独立排版。 |
| [drops-u1.png](drops-u1.png) | U1 区域掉落四件 | 护额、围甲工装、带手指护手、封闭铜笼短杖完整，白光不吞材质。 |
| [drops-u2-v2.png](drops-u2-v2.png) | U2 区域掉落四件 | 布靴、分片护腕、三镜扣短弓及完整闭合链吊坠可读；吊坠已定向修正，矩形外像素保持原图。 |

区域板固定位置：上方左右是两首领，中排从左到右是该区四种普通敌，下排是四个既有装备/符的造型参考。精英奖板4×2，DE01—04在上排、DE05—08在下排。新增掉落板2×2，区域四件依次为左上、右上、左下、右下；具体键在JSON的art字段。

原六区板下排映射：R1=W02/W08/A09/T03；R2=W03/A05/W09/J02；R3=W10/W12/J05/A03；R4=W06/J07/W14/T08；U1=W16/A12/W13/A16；U2=J04/A15/J06/T06。位置是概念定位，不能直接作为SpriteFrame精确切片。

## 生成与处理记录

完整实际提示词分别保存在[prompts](prompts/)；每板的提示词路径和哈希均在provenance.json。原图只复制原始字节，未调色或缩放。总览由本地Pillow确定性缩略排版。生成服务未返回可核验的底层模型版本，不猜测型号，也不声称引用只上传一次。

沉钟区原drops-u2.png的吊坠链未闭合，未选作最终板。内置image_gen根据原板定向编辑，保存drops-u2-edit-raw.png；本地仅合成左下[0,450,750,1024]区域，其他三件保留原像素。最终为drops-u2-v2.png，遮罩与[矩形外像素核对](necklace-composite-verification.json)保留。修正后已检查闭合链与完整吊坠。

旧提示词中的历史地区名与主线新名不同，不修改历史生成证据；图注与内容数据使用新名。当地装备可能是在另一地区制造/取得，概念板位置不自动改唯一来源。

## 复现文档与清单

运行 `python tools/design/build-encounters-v2.py` 重新导出内容JSON与三份设计表；运行 `python tools/design/catalog-encounter-art.py` 检查图像、原始来源与哈希并重建本清单/总览。两脚本不调用模型、不下载依赖、不改游戏运行数据。主线叙事campaign-v6.md为独立人工稿。

runtime-content.json是中断前导出的首章32区/19项运行目录快照，只用于区分现状；campaign-design.json是未接入完整设计。历史本地模型试验位于相邻qwen-world-v1目录，按用户要求保留。

## 已有源图的图标接入

2026-11-08：从本目录已有云端板按明确物品编号处理49个RGBA行囊图标（24地区掉落、8精英奖、17旧永久装备），保留原板不变，没有新生图。确定性处理使用已安装Pillow/numpy/scipy；生成证据、像素处理和输出审阅分别记录于[equipment-runtime-v1](equipment-runtime-v1/manifest.json)、[review.json](equipment-runtime-v1/review.json)与[runtime-install.json](equipment-runtime-v1/runtime-install.json)。DU2吊坠沿已修正的完整闭合链源图；J06原板链条不完整，未接入新图标。加既有v3明确16件，运行图标覆盖65/74，剩余保留类别回退。

六区怪物/首领板仍是RGB纸底单视角概念，没有方向、动作或地脚锚点；不能把此次图标接入当作36敌/首领动画完成。当前完整97地点运行导出另见[最新运行内容](../../skills/pure-skills-v2/runtime/runtime-content.json)，本目录runtime-content.json保留历史首章快照。
