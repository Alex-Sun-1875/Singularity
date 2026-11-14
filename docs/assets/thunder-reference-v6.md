# 按用户照片对齐的片状雷电场

2026-11-08。用户指定[照片1](../../source-art/skills/pure-skills-v2/thunder-reference-v6/user-reference.jpg)，并明确要求向四周散成片状的雷电，而不只连接人物。本轮已接入默认本地包 `http://127.0.0.1:7469/?view=2d`，实际加载 `index.a3e4d.js`。

雷电现在由四层共同组成：从施法手部发出的蓝白主干、最近可见敌人组成的连接骨架、覆盖命中区域的游离电弧场，以及受击点的白亮核心和蓝色柔光。区域电弧有低处、中间与胸口附近三个高度，向空处展开并交错分叉，每次放电更换裂变形态；光丝会汇合、散开，形成整片电光。雷击时的短受击闪身也改为冷蓝色。

片状层使用现有Cocos原生MeshRenderer、builtin-unlit和顶点颜色，一张批量网格承载数十道独立放电，不挤占160条Line的公共池。受击光团复用已有Kenney CC0的light_01/star_01透明遮罩与原生quad。字段池上限8，光团池24；新拍替换网格，间隙、暂停、到期及换区都有隐藏或释放路径。没有新增依赖、下载、生成图片或全场景后处理。

连接骨架继续由既有最近边森林负责真实命中，额外近邻闭环由最近三个邻居补成网，敌人间边数上限仍为2N−1。闭环、游离片状场、支叉和光团都只负责表现。原目标预算、射程、伤害、冷却、三次放电、首击雷晕及最后约1.5秒余晕保持。

| 实际验证 | 结果 |
| --- | --- |
| [同场景前后及参考对照](../../src/cocos/test-results/thunder-reference-v6/reference-comparison.jpg) | 原始用户照片、旧版、完整原生效果及单独游离电弧层。后两张为同一原生取样隐藏HUD，单独层另隐藏Line作诊断；未将照片中的电弧贴入游戏。 |
| [8目标实际技能与原速记录](../../src/cocos/test-results/thunder-reference-v6/current/actual-resonance.json) | 五阶代表场景有64道游离电弧，覆盖约11.95×10.55米、12267顶点的单张网格。三拍129/116/116条Line，单条最多64点；光团9/8/8个，两间隙均清空片状层与光团。 |
| 真实伤害对照 | 与[修改前](../../src/cocos/test-results/thunder-reference-v6/baseline/actual-resonance.json)一样，只结算8次命中：264、185×7；两次余电与片状电场不追加HP扣除。 |
| [低阶与手机尺寸](../../src/cocos/test-results/thunder-reference-v6/extra/extra-review.json) | S08真实两只猎兽、角色5级：仍有34道游离电弧，而非一根人物连线。844×390下实际ChapterGame更新完成命中、地晕、血条和区域放电。暂停清空、原时刻恢复不补伤害。 |
| 清理与稳定性 | 最后一拍之后只留地晕，最终Line/片状场/光团/地晕全清；226个连续原生CDP帧，无浏览器异常、无失败请求。类型检查、现有95项检查及Cocos本地构建通过。 |

[2.62秒原速动图](../../src/cocos/test-results/thunder-reference-v6/thunder-area-native.gif)从原生实录按时间戳取帧，640×360、约854KB；没有插帧或变速。[保留帧与时长](../../src/cocos/test-results/thunder-reference-v6/animation-artifacts.json)、[最终汇总](../../src/cocos/test-results/thunder-reference-v6/summary.json)。这是实际实现与代表画面复核，用户美术验收另计；区域场使用当前游戏的地表与角色。
