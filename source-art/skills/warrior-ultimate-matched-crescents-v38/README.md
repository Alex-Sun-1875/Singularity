# 战士最终技：红线月牙 v38

沿用户最新红线重画：前尖更高、更竖，前部刀腹加宽，外下弧回弯更深。忽略红线的重描和孤立点，只取两条边构成完整月牙；参考图保存在 `reference-red-outline.png`，采样轮廓由 `trace-profile.py` 与 `swoosh-profile.json` 追溯。

**三道共用同一固定刀气网格与高度**，全部 scale=1、formation=1，取消末道放大与按波龄缩高。仅位置、释放时间和消散状态不同；尾部从人物脚边低起，主体离体前进，不随途经地形挤形或抬落。保留 0.22 秒接出、原生连贯动作、前进节奏与流动纹理。

## 展示

- [红线与拟合轮廓叠对](reference-trace-overlay.png) / [统一模板示意](shape-direction.png)
- **[三道同形同高慢放](media/three-wave-detail-slow.gif)**：三道共用轮廓与高度，观察分别接出、推进与消散。
- [单道近景慢放](media/single-wave-crescent.gif)：1 道实录第 35–77 帧，固定裁切，0.5×，观察红线月牙轮廓。
- [1／2／3 道三列动态](media/wave-count-comparison.mp4) / [三列原速 GIF](media/wave-count-comparison.gif)
- [1 道原速](media/wave-count-1.mp4) / [2 道原速](media/wave-count-2.mp4) / [3 道原速](media/wave-count-3.mp4)
- [普通地面 3 道](media/three-waves-field.mp4)
- [3 道近景慢放](media/three-wave-detail-slow.gif) / [慢放视频](media/three-waves-slow.mp4)
- [三列概览](media/wave-count-overview.jpg) / [三道阶段](media/three-wave-stages.jpg)

等级映射保持：1 级 1 道，2–3 级 2 道，4–5 级 3 道。代表录制等级为 1、3、5，各原速片段 3.6 秒、30 fps。三列为独立原生实录排版，没有复制单道图片叠加。本轮采用新机位 centre=3.6、height=5.9，四组 current／proposal 共八段全部重新实录，不复用旧基线；逐组核对编译产物哈希及同等级命中事件。

## 验证

逐帧确认三道真实共用同一网格，严格比较每道 18 个局部轮廓采样点及局部高度范围，确认所有波、所有波龄同形同高；实际世界缩放、formation 均为 1。每个场景内尖端与尾端世界高度误差小于 0.000001 米，整体高度固定在施法原点，避免用不同位置相对地面的高度误判。端点收尖、波面竖立、尖端向上继续检查；局部最低点不少于 0.04 米，尖端超过 3.5 米。不再强制飞行中的尾部、刀腹或主体随地形贴合，也不沿用 v37 的单调外边曲率约束。

保留 1／2／3 道数量、0.22±0.04 秒间隔、逐波单调前进、收招后继续推进、渲染与原生动作连贯检查。同一真实技能等级的命中逐项匹配，视觉多波不新增伤害。视频和 GIF 完整解码核对帧数、速度、时长，结果写入 `provenance.json`。

这是独立原生渲染小样，未接入正式代码或资源引用，未制作新包；用户美术验收、TapTap 真机及性能待确认。护盾等其他技能保持。原始记录位于 `src/.tmp/warrior-ultimate-matched-crescents-v38/`。
