# 石场快速跑动的 CPU / GPU 对照

后续[安卓模拟器实测](android-quarry-cpu-gpu-2026-11-12.md)复现了移动初期的寻路CPU尖峰，并已优化；本文保留此前桌面硬件对照的原始结论。

2026-11-12，0.3.21 本地构建，S13「断镐石场」。本轮只采样，没有修改游戏运行代码或帧率。

**本地样本没有显示 CPU / GPU 随跑速持续大幅上升。** 4.0 提到 5.2 米/秒后，CPU 主线程平均耗时增加约 8.5%，两组范围重叠；GPU 3D 引擎占用没有向上增长的规律。这个结果不等同于手机结论。

## 预热后的结果

环境是 i9-12900KF / RTX 3080，Chrome 硬件 D3D11 / WebGL2；未使用软件 GPU。逻辑视口 844×390，请求 DPR3，Cocos 实际画布 1688×780，原 60 帧设置保持不变。

48 秒交替预热所有模式后，按正反顺序各测一轮；每种模式有两段 8 秒样本。表中均值和范围来自这两段，不是手机占用率。

| 模式 | CPU 主线程，毫秒/帧 | 本机游戏 GPU 进程的 3D 引擎占用 | 绘制调用/帧 |
| --- | ---: | ---: | ---: |
| 静止 | 2.49（2.29–2.69） | 6.2%（5.9–6.5%） | 176.0 |
| 慢走 1.6 米/秒 | 2.85（2.75–2.95） | 6.3%（6.3–6.4%） | 173.0 |
| 当前跑速 4.0 米/秒 | 2.77（2.46–3.09） | 6.3%（6.1–6.6%） | 174.1 |
| 原快跑 5.2 米/秒 | 3.01（2.62–3.40） | 5.2%（4.4–6.1%） | 174.4 |

快跑相对静止的 CPU 均值约增加 21%，相对当前跑速约增加 8.5%。慢走与普通跑动也存在样本波动，不能把每个小差额都解释成速度的因果影响。GPU 会受到动态频率与系统调度影响，快跑样本中的较低百分比不代表跑得更快就更省电。

## 尖峰与首次探索

先前的探索性三轮采样中，最初静止约 2.13 毫秒/帧，首次慢走约 4.62 毫秒/帧，之后多种移动模式均逐渐回落。这个初始开销真实保留在原始记录中；缓存、JIT 和其他暂态因素没有逐项隔离，不能直接归因于跑速。

另行清空探索记录、保留完整场景和导航缓存的两段 10 秒检查中，4.0 / 5.2 米/秒分别触发约 30 / 40 次探索扫描，CPU 主线程约 2.38 / 2.37 毫秒/帧。这说明速度确实增加按距离触发的工作次数，但本次没有观测到相应的 CPU 大幅上升。这两段没有独立的 WDDM 占用计数，不将其 GPU 查询耗时冒充占用率。

## 测量方法与边界

- CPU 使用 Chrome DevTools `Performance` 的 `threadTicks`，计算主线程 CPU 时间增量 / 实际绘制帧数；不是 24 线程整机 CPU 百分比。
- GPU 同时使用 `EXT_disjoint_timer_query_webgl2` 异步计时和独立的 Windows GPU 引擎计数。即使静止，查询耗时也有明显长尾，因此判断是否持续增加负载时，以显卡进程的 3D 引擎忙碌时间为主要旁证，不把查询耗时直接换成占用率。
- Windows 原始计数类型为 `PERF_100NSEC_TIMER`（542180608），采用 `100 × Δ原始占用计数 / ΔTimestamp_Sys100NS`。显卡计数窗口包含 WMI 取数时间，期间同一移动模式继续运行。
- 同一 Seed19、Lv40 会话，保留既有敌人，选择距敌人至少约 74 米的畅通往返路线，按正常输入、物理与渲染循环运行；没有测近距离怪群和战斗叠加的最坏情况。
- 计时包装和 GPU 查询只存在于隔离的诊断页面，会有测量开销；没有将它们打入游戏包。初始探索性检查与最终确认检查的全部数据均保留，不删除高值。
- 当前 `adb devices` 没有连接的手机。尚未测得荣耀 X60i / iPhone 的 CPU、GPU、功耗、温度或降频。

因此，降速可以缓和探索节奏，但不能据此认定石场发热已解决。下一步真机采样应分别覆盖静止、持续跑动、首次进入未探索地段和接近怪群，并保持亮度、充电状态和帧率一致。

证据：[结构化结论](../../src/cocos/release/taptap-quarry-cpu-gpu-validation.json)、[原始探索性采样](../../src/cocos/test-results/quarry-cpu-gpu-v1/discovery.json)、[显卡计数复核](../../src/cocos/test-results/quarry-cpu-gpu-v1/confirmation.json)。

测量依据：[Chrome Performance 协议](https://chromedevtools.github.io/devtools-protocol/tot/Performance/)、[Khronos GPU 计时扩展](https://registry.khronos.org/webgl/extensions/EXT_disjoint_timer_query_webgl2/)、[Microsoft 计时计数器](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types)、[Windows GPU 占用统计](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/)。
