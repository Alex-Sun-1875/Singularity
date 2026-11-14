# 六流派技能五级效果图

**旧v1五级材质基础。** 当前六系的远距攻击形状与目标组织见[新方向图集](../pure-skills-v2/README.md)、[技能v2](../../../docs/design/combat-skills-v2.md)和[空间规则v2](../../../docs/design/skill-spatial-v2.md)。本目录原图与审阅记录保留，不再代表当前BOW_02单箭连穿/THU_02固定首击中心形态，也不计作运行实现或动画。

2026-11-08。六张原生OpenAI image_gen云端概念板，每板从左到右展示同一代表技能的1—5级形态。角色只作稳定比例的灰衣示意，不替换当前已验收主角身份。没有启动本地模型。

**已完成生成和概念方向审阅。** 五级形态差异清楚；高阶部分构型接近画布边缘，正式独立技能纹理、透明通道、序列帧、命中时序、镜头内遮挡与手机性能尚未验收。不能把这些静态板切成五帧当动画。

![六流派五级效果总览](evolution-overview.jpg)

## 当前设计

- [44技能、220级记录](../../../docs/design/combat-skills-v1.md)
- [人物升级、四维属性与等级解锁](../../../docs/design/character-progression-v1.md)
- [每个技能的五级特效与命中规则](../../../docs/design/skill-vfx-v1.md)
- [97地点纯技能反制](../../../docs/design/world-combat-v3.md)
- [74件装备技能联动](../../../docs/design/equipment-skills-v3.md)
- [技能JSON](skill-catalog.json)、[当前世界战斗JSON](campaign-v7.json)、[静态核对](design-validation.json)
- [逐图来源、提示词、SHA256与独立审图](provenance.json)

## 代表技能

| 图 | 技能 | 1—5级的角色门槛 | 视觉审阅 |
|---|---|---|---|
| [evolution-war.png](evolution-war.png) | 断空斩 | Lv1/Lv8/Lv16/Lv24/Lv32 | 五列双弧→交叉→三斩→半环→完整剑阵变化明确；第五级高光需实机降透明度，不是正式剑帧或碰撞。 |
| [evolution-bow.png](evolution-bow.png) | 天穹贯星箭 | Lv16/Lv20/Lv26/Lv32/Lv38 | 星矢羽翼、三环、天弓结构逐级明确；高阶边缘偏紧，正式特效需独立画布，不能直接按等宽切片。 |
| [evolution-fir.png](evolution-fir.png) | 焚星坠落 | Lv4/Lv8/Lv16/Lv24/Lv32 | 小陨星→火环→次爆→晶冠→凤凰爆核逐级明确；巅峰光翼有边缘裁切和跨列视觉，仅作整体方向。 |
| [evolution-fro.png](evolution-fro.png) | 永冬降临 | Lv16/Lv20/Lv26/Lv32/Lv38 | 冰环、六角阵、中央冰冠、浮空冰花、完整冰冠/冰轮层次明确；冰晶不代表物理障碍。 |
| [evolution-thu.png](evolution-thu.png) | 九霄雷狱 | Lv16/Lv20/Lv26/Lv32/Lv38 | 三束落雷到多层雷冠/雷网的形态差别明确；装饰电弧不代表新增伤害次数或控制。 |
| [evolution-arc.png](evolution-arc.png) | 星界崩解 | Lv16/Lv20/Lv26/Lv32/Lv38 | 细束、螺旋、三环门、银轨、巨大星核门逐级明确；第五级边缘偏紧，尚非可直接使用的光束纹理。 |

图中粒子、光刃、电弧和晶体数量是表现，不等于伤害段数；命中段数/范围/复制上限由技能目录决定。六张是每流派一个代表技的方向板，不声称已逐个生成44技能×5级的生产资产。其他技能的逐级形态、音效和判定均已写入设计稿。

## 可复核的保存记录

每张原图与工具输出逐字节SHA256一致，真实尺寸见provenance.json；不把提示词的期望尺寸冒充实际尺寸。六张均为全新文生图，无参考图输入，底层模型版本未由工具返回。没有关于上传缓存次数的假设。

实际完整提示词在[prompts](prompts/)。本地Pillow仅生成总览缩略排版，不修改六张原图。原输出继续保留在Codex生成目录，项目使用副本已全部保存到本目录。

运行 `python tools/design/build-skills-v1.py` 重建技能/人物/装备/世界设计JSON与五份文档；运行 `python tools/design/catalog-skill-art.py` 核对原图/提示词哈希并重建本索引与总览。两脚本不下载文件、不调用本地模型、不改运行数据或存档。
