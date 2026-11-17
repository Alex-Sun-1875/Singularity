# 剑与火 · 四职业技能动效对照

本版范围圈造型已被用户否定。当前设计审稿使用 [原稿法阵动画](../reference-seals-v3/README.md)。

这组审稿录像取自当前 Cocos 工程的 S04 全 3D 战斗场景。主角、敌人、武器、动作、材质、弹道和命中反馈均由游戏渲染。录制使用横屏近景和固定训练靶，隐藏 HUD。所有技能为一级。调整参数和特效模块只加载到录制会话，接入主工程前仍需确认美术方向与战斗手感。

[战士三连 GIF](media/warrior-combo.gif) · [四职业同场对照](media/four-classes-comparison.mp4) · [调整稿单画面](media/four-classes-full-size.mp4) · [四职业范围圈设计稿](media/range-rings.jpg)

## 在画面里看什么

| 职业 | 本轮镜头 | 观察点 |
| --- | --- | --- |
| 战士 | 普攻三连、断空斩、破军突袭、裂地审判、破晓裁决 | 手部带出向前的钢刃，顺斩、反斩、重斩有独立高低点。突袭到位后先挑再压。裂地审判保留圆形落点。 |
| 弓系 | 穿云箭、万箭齐发、缚足陷阱 | 箭头先行，渐尖的浅青绿尾迹只画已飞过的路径。齐发保留分波和独立箭体。陷阱的双环间做倒钩纹。 |
| 火系 | 赤焰枪、焚星坠落 | 火枪向前送出。陨石放在终极位，先落地预警，再从左上斜入，命中后火浪向外扩。 |
| 雷系 | 连锁雷弧、万钧雷潮 | 手部接入第一条蓝紫主弧，后续沿实际命中目标跳转。较粗的导电主线贯穿一拍，细分叉只作接触点附近的辅光。 |

战士普攻从 **1.85 米、110°** 调至 **2.65 米、48°**。两名靶子的距离和朝向在两次录制中相同。现版三刀都打中 1.63 米、偏轴 44° 的近靶，调整稿三刀都打中 2.53 米的正面靶。一级断空斩从 3 米、110° 调至 3.75 米、40°。一级破晓裁决从 4.375 米、120° 调至 5.03 米、62°。

现版的扇形判定和刀光绘法可从以下入口核对。[普攻判定](../../../src/cocos/assets/scripts/core/GameSession.ts) · [各等级技能范围](../../../src/cocos/assets/scripts/features/combat/data/PureSkills.ts) · [战士挥砍](../../../src/cocos/assets/scripts/features/combat/runtime/MeleeSkillEffects.ts) · [刀光网格](../../../src/cocos/assets/scripts/features/actors/runtime/MeleeBladeSurfaces.ts)

焚星坠落接替焚天火海的终极位，焚天火海进入空出的常规主动位。这一版把陨石前摇设为 0.78 秒，让外缘、内纹和下落方向各有可见时间。范围圈正视图直接使用录制模块同一组线条坐标，实战列截自技能生效前。

火浪沿用当前火系图集。预览逐帧柔化火焰贴片底缘，让前后两层火焰在砂地上有渐隐的接触面。原图与审稿用的派生图分别读取。

## 动作参考

战士参考橘右京「居合」的前方路径与刀尖重点，以及韩信「国士无双」的连续发力和末段收束。弓系参考虞姬「楚歌起」的蓄力后单发，火系参考沈梦溪「综合爆款」的定点投落，雷系参考司空震在「雷霆万钧」变身期间用远程普攻打出的连锁闪电。参考依据为官方技能介绍，录像里的模型、贴图和动作来自剑与火工程。[橘右京](https://pvp.qq.com/web201605/herodetail/163.shtml) · [韩信](https://pvp.qq.com/web201605/herodetail/150.shtml) · [虞姬](https://pvp.qq.com/web201605/herodetail/174.shtml) · [沈梦溪](https://pvp.qq.com/web201605/herodetail/312.shtml) · [司空震](https://pvp.qq.com/web201605/herodetail/537.shtml)

## 复核与复现

两段 MP4 均为 30 帧/秒，每个章节对应一次完整施放。录制按 60 Hz 推进 Cocos 逻辑和骨骼，输出相邻的每两个引擎帧中的后一帧。当前版和调整稿使用同一 Cocos 主包、场景、世界坐标和相机参数。录制器校验配对镜头，记录实际受击者和播放的骨骼动作，以及陨石焰尾和飞行方向的屏幕投影。逐招结果与文件指纹见 [provenance.json](provenance.json)。

在本目录执行以下 PowerShell 命令可复现录制。基础素材为本机已有的 `src/cocos/build/concept-2d` Web 导出，启动时显式选择 `view=3d`。媒体合成使用 Pillow 和带 H.264 编码器的 PyAV。下方变量指向本机已有这两个库的 Python。

```powershell
foreach ($motionStudyVariant in 'current','design') {
    node capture.cjs --world native --variant $motionStudyVariant --shots BASIC_WAR,WAR_01,WAR_02,WAR_04,WAR_05 --skip-write WAR_04
    node capture.cjs --world native --variant $motionStudyVariant --shots FIR_02,FIR_01,THU_02,THU_05,BOW_01,BOW_05
    node capture.cjs --world native --variant $motionStudyVariant --shots WAR_04,BOW_06
}
$motionStudyPython = 'F:/Models/ComfyUI_windows_portable/python_embeded/python.exe'
& $motionStudyPython -X utf8 review-media.py warrior
& $motionStudyPython -X utf8 review-media.py compare
& $motionStudyPython -X utf8 review-media.py full
& $motionStudyPython -X utf8 review-media.py rings
& $motionStudyPython -X utf8 review-media.py provenance
```
