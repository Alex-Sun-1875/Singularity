# 第一章人物外观 v6

2026-11-06 后续方向已变更：用户要求直接使用前面设定图制作2D人物，保留原Cocos HUD，仅替换地图和人物画面。当前入口与实际验收见[设定图2D样片](concept-2d-preview.md)。本文以下保留未完成的3D适配记录，不作为当前人物交付方案。

本轮接续 2026-11-05 中断的人物重做。角色身份以 `docs/story/revision-v5/characters.md` 为准；暖金界面、地理、即时战斗、存档与现成11动作继续使用现有实现。

## 来源与适配

- 身体、衣装基础、原生65蒙皮骨骼和走跑/剑击/施法等动作：项目已保存的 Quaternius 原包；来源、许可、哈希见 `source-art/characters/library-kits/`。
- 自然头颈与皮肤：项目已有 MakeHuman/MPFB 可编辑资源；不引入旧53骨骼，仅追加网格，绑定现有头颈骨骼。保留原授权照片皮肤 UV，并通过 Blender 烘焙到运行图集。
- 发型：已有 MakeHuman 系统与社区资源；各作者、资产地址、具体许可和适配记录随角色清单及发行包 THIRD_PARTY_NOTICES 保存。社区资源并非全部 CC0。
- 武器：既有 KayKit 资源加概念所需的战锤、盾面、地图筒等适配；弓保留原 Draw 形变和动态握点。
- 自定义工作集中在脸发尺寸/轮廓、概念衣装、蒙皮转移、材质烘焙和引擎绑定。现成免费衣装没有完整覆盖青绿短披布、酒红长马甲和分层卫甲，因此保留必要的网格适配。

官方来源：[Quaternius 人物](https://quaternius.com/packs/universalbasecharacters.html)、[动作库](https://quaternius.com/packs/universalanimationlibrary.html)、[MakeHuman 许可](https://www.makehumancommunity.org/about/license.html)。实际分发许可以项目保存的原包及逐资产归属记录为依据。

## 导出与安装

`tools/model-pipeline/cocos_v5_character_redesign.py` 从已有 native 源文件读取动作与骨架，调用脸发和衣装适配器，用 Blender 原生 UV/Cycles/FBX 导出到 `src/.tmp/character-redesign-v6/actors/`。可编辑文件保存在 `source-art/characters/redesign-v6/`。

每次导出校验动作曲线、骨骼绑定与整体变换没有改变。眼睫与眉毛共享透明细节图集，身体保持独立材质；颜色为 sRGB，法线和 ORM 为数据。角色清单记录实际可见鞋底至发顶高度，避免沿用旧发型的几何测量。

使用已有 `cocos_verify_characters.py` 对真实 FBX 回读；使用 `src/cocos/tools/install-native-actors.ps1 -CandidateRoot <绝对候选目录> -BackupRoot <绝对备份目录>` 安装。安装保留根资源 UUID，并由 Cocos 导入器生成子资源与纹理元数据。

## 验收边界

头颈接缝、发片透明边缘、走跑与攻击时的衣装遮挡必须查看实际渲染。现有规则检查不替代外观验收，离线 Blender 图不替代引擎画面；手机浏览器尺寸/触控模拟不等于真机帧率、内存或发热结论。

本轮结果与交付路径在完成构建后写入本页和 `docs/PROGRESS.md`。
