# 射箭箭矢不生成修复

复现当前 7469 的 locomotion-v2：弓上搭箭显示正常，但松弦进入发射时，GameSession.actionStep 报 `Cannot read properties of undefined (reading 'basicArrow')`。当前源码已引用 `COMBAT_RULES.playerProjectileSpeeds`，C 盘构建镜像却仍保留旧 PureSkills.ts，缺少该字段；PureCombat.ts 也还是旧版本。详见 [复现](reproduction.json)、[两个陈旧依赖](stale-dependencies.json)。

同步完整 assets/scripts，使规则、配置、运行时来自同一份当前源码，复用现有 Cocos 构建并重新接入。不改已完成的角色、发型、步行/跑步、武器模型或射线方向。无新依赖、资源下载或图片生成。[同步入口](stage-build.py)、[同步记录](stage-record.json)、[源码指纹](source-fingerprint.json)。构建包保存脚本指纹，安装前核对射箭相关源码及角色资源；旧 locomotion 安装器也增加完整指纹校验，避免再次接入部分同步的旧包。

验证：TypeScript 检查、web-mobile 构建通过。实际引擎中检查基础短拉与满弓、七把弓八向搭箭及飞行朝向、BOW_01/02/03 发射、FIR_01 和普通法杖发射，均未再出现运行时错误。单次 BOW_03 生成五支箭，普通箭速 24、技能箭速 32 米/秒，沿用当前数据。技能验证仅在隔离浏览器内存中更换槽位，未改用户存档。

[搭箭与飞行截图](runtime/after/arrow-visible.jpg)、[基础放箭](runtime/after/report.json)、[弓术与魔法](runtime/after/skills-report.json)、[七把弓及收持回归](runtime/all-bows-review.json)。画面使用正常游戏镜头，已目视检查弓上的箭和空中的实体箭矢。[接入记录](install-record.json)。

[修复后的本地入口](http://127.0.0.1:7469/?view=2d&player=3d&revision=arrow-visibility-v1)。

本次构建完成后，工程内 core/CampaignLoot.ts、core/Contracts.ts、core/Progression.ts、data/EnemyCombat.ts、data/MonsterEcology.ts 又有同期更新，见源码指纹中的 concurrentSourceUpdatesPreserved。这些工作文件原样保留，未包含在本次已验证的构建快照。
