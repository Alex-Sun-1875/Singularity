# 万箭齐发与持续战斗优化（V35，2026-11-13）
> **2026-11-13 清理并暂停**：用户要求保留有效改动、去掉过度依赖引擎内部实现的方案并暂停优化。现已撤回浏览器帧时钟桥接、Line 上传回调替换、Graphics 私有路径池替换、未公开粒子 `emit` 接口的合批；保留原生实例化、公开接口的对象池与预热、字形缓存、HUD 去重、迷雾计算缓存及无损索引重排，严格使用 WebGL 2。下文 V35 与低于 50% 试验数字为历史记录，**不能视为清理后版本的实测收益**。清理版仅做功能／构建验证，不再追加性能试验；CPU 低于 50% 尚未达到／验收。详情见末尾清理记录。

用户确认卡顿发生在手机 TapTap 小游戏。此次保持原有 60 FPS 设置、分辨率、箭矢与粒子数量、技能伤害和命中规则。Android 模拟器 Web 构建用于定位及回归；手机 TapTap 容器中的温度、GPU 时间和体验另行验收。

[昨天的设备记录](iphone14-moving-combat-2026-11-12.md)确认用户使用 iPhone 14。此次先按该设备作为真机重点；Android 的 Line 上传降幅不能套到 iOS。iOS 分支保留引擎原有完整缓冲／orphan 策略；箭体 Instancing、加法命中特效合批、预热、字形缓存与索引复用不依赖这一上传适配，均会在 iOS 执行，但未完成 iPhone 实机验证。

## 实现

- 箭杆、箭头和箭羽复用 Cocos 原生 GPU Instancing；保持原网格、材质参数及非均匀缩放。以安装的 Creator 3.8.8 `world-transform` 着色器为准核对法线变换。
- 把箭矢／拖尾组件池、常见伤害字形和命中粒子存储的首次创建移到加载或换装界面，分帧准备，不制造战斗事件。既有池上限和借用逻辑保留。
- 预热入口在对象已销毁时立即返回，防止切场／退出与异步加载交错后重新创建节点。这两处销毁守卫在计时采样后补入，未改动计时窗口中的更新、绘制或玩法路径；通过最终类型检查和小游戏编译。
- 同阶箭矢的加法混合火花／闪光共用原生粒子系统，在原生 Burst 阶段按原位置、颜色、角度和数量排队发射。尘土仍独立绘制；不支持的布局与原生平台回退旧路径。
- `ManagedLine` 保留原生几何，只向 GPU 上传实际占用的连续前缀。复用有界的 Uint8Array 视图，避开 Cocos WebGL(2) 在“整块 ArrayBuffer＋较小长度”路径中的 slice 复制。安装前检查 3.8.8 布局，销毁前还原回调，防止引擎模型池保留实例闭包。iOS 保留引擎原有缓冲上传策略。粒子完全使用原生 ParticleSystem 的模拟、模型与上传。
- 浮动伤害数字使用原生 CHAR 字形缓存，长数字／长字幕保留原有 SHRINK。血条与浮字在一次反馈更新内复用相同的头／脚投影，跳过不变变换。取消训练 HUD 每帧先隐藏再显示的中间状态。
- 翻译适配器仍以 i18next 为准；每个已注册词条只缓存最后一组参数，语言和词库修订变化时失效，未知动态键不留存。
- 角色 GLB 仅重排三角形索引，提高顶点缓存复用；不减面、不改顶点顺序／精度、骨骼、UV、贴图或动画，也不把 uint16 索引提升为 uint32。源发型标注 BLEND，但当前 NativeActorMaterials 实际使用不透明 alpha-test；仅在这一已核实的运行配置下重排。离线复现：`node src/cocos/tools/performance/reorder-actor-indices.cjs` 检查结果，追加 `--write` 才写入。使用现有 meshoptimizer 1.1.1（MIT），无新增依赖或下载；未知输入版本拒绝处理。

## 正确性证据

数据保存在 `src/cocos/test-results/performance/`，新诊断脚本仅置于忽略的 `temp/`，没有增加常驻测试框架。

| 检查 | 结果与边界 |
| --- | --- |
| 投影 | `volley-v27-projection-equivalence`：78,429 次结果与原算法相同，包括事件阶段和同帧缓存路径 |
| 翻译 | `v27-localization-equivalence.json`：300,000 次输出对照，含可变参数、显式／默认语言、语言切换和词库覆盖 |
| 箭矢／拖尾 | `volley-v26-visual`：文字区域外无像素差异；CHAR 数字字距略有变化，已检查字体、字号、颜色、描边和裁切 |
| 命中发射 | `volley-v30-emission-equivalence`：284 次请求对应 284 次原生发射，852 个粒子，位置／规模／角度／颜色／dt=0 一致；未准备阶级另经 V31 检查 |
| 粒子合批画面 | `volley-v30-particle-visual`：同一批 62 个粒子，19 个系统变为 2 个；约 278 万像素中 196 个差异超过 3 色阶，来自微小的混合重叠顺序变化，非逐像素等同 |
| 实际上传 | `v35-live-upload-qa`：68 次真实 WebGL 上传，569,696 → 82,880 字节（少 85.45%）；其中只有 60 个 Line 模型使用适配，8 个粒子模型完全原生。253 次绘制／187,546 三角形相同，原始缓冲 slice 复制 0；清零 VBO 后比较最大差异 1 色阶 |
| 回收与拖尾 | `v33-pool-and-lines-qa`：20 次创建销毁、40 个回调正确还原；120 种拖尾参数共 61,248 字节活跃顶点逐字节一致 |
| 网格 | `v32-mesh-lossless.json`：16 个导入网格的三角形／绕序、顶点属性、关节映射、形变与边界通过；原始 GLB 除索引区段外每个字节相同 |
| 蒙皮画面 | `v32-mesh-visual`：4 发型 × 8 姿态，原版／优化／重复共 96 张截图；32 个姿态合计 8 个像素差异超过 3 色阶，原版重复差异为 0 |

32 项模拟顶点 LRU 缓存的缺失总数 170,001 → 101,540，约少 40.3%；包含四套替换发型，不能当作同时可见模型的实测 GPU 时间。当前模拟器不提供硬件 GPU timer，提交数、上传字节和缓存模型只是工作量证据，不能换算成手机降温或功耗百分比。

## 性能对照与交付

普通走打使用既有 `farm.cjs` 的 H12／Lv17／BOW、300 秒日常协议。技能窗口使用游戏已有训练场的 20 怪配置、BOW_05 五阶和真实技能输入；内置无限资源只用于这个训练夹具，不能充当自然狩猎或持续发热验收。

最终采用重启后同一环境中的 `volley-v35-reboot-control` → `volley-v35-reboot-final`，均完成 6 次实际施放；汇总 `volley-v35-comparison.json`。首次四秒窗口主线程 5.60 → 4.84 ms／绘制帧（少 13.6%），进程 CPU 105.88% → 96.14% 单核（少 9.2%）；峰值绘制提交 357 → 274（少 23.2%）。后五次主线程均值约少 10.2%，进程 CPU 约少 9.8%。两边命中数会随真实帧时序变化，六次施放与伤害均正常，未减少弹道或伤害来压低工作量。

最终首次最长帧 79.9 → 35.4 ms（少 55.7%）；后五次最长帧分别为原版 46.7／31.7／34.9／40.3／37.0 ms、V35 24.9／24.2／28.6／31.6／24.9 ms。后五次超过 33.33 ms 的帧数由 7 变为 0，首次仍有一次长帧，不能宣称卡顿完全消除。重启前一组曾测到 113.2 → 103.5 ms、持续 CPU 基本持平；V33／V34 重复还出现过 45–103.7 ms，所有原始数据和 `volley-v35-pre-reset-comparison.json` 均保留，不混进本组收益。

最终日常回归 `android-v35-reboot-control` → `android-v35-reboot-final`，各连续 300 秒移动、普攻与技能，原预算全部通过；仅覆盖 H12／Lv17／BOW，不扩大为四职业或完整多场景基线。

| 指标 | 原版 | V35 |
| --- | ---: | ---: |
| 平均 FPS | 59.9975 | 59.9982 |
| 最低完整滑动 1 秒 FPS | 58 | 58 |
| 主线程 ms／帧 | 3.4499 | 3.4525 |
| 进程 CPU，100%=1 核 | 66.71% | 65.32% |
| 进程族 PSS 峰值 | 509.45 MB | 512.83 MB |
| 绘制调用中位数／P95 | 167／181 | 166／181 |

普通走打主线程基本持平，整进程 CPU 约少 2.1%，主要收益集中在群攻峰值。以上均为模拟器观察，没有取得 A15 硬件 GPU 时间、物理功耗或温度，不能承诺 iPhone 14 降温幅度。

早先旧版普通走打约 65% 单核 CPU，后续相同旧版已约 84%；保留原始报告，并重新连续采集相同长度的旧版与候选版。不能把不同环境时段或 60 秒与 300 秒窗口混作优化比例。

长时间诊断后，`android-v35-final` 五分钟回归失败（平均 34.79 FPS、最低一秒 25），未批准。随后同一原始构建在 `android-v35-late-control-smoke` 也失败（35.78 FPS、最低 31），而其此前五分钟为 59.84 FPS；分辨率、Chrome、帧率设置、亲和性和计时策略记录一致。恢复旧模拟器的原始亲和性后，仅关闭并冷启动本任务专用 AVD，再以相同 4 核／物理核亲和性／Vulkan 禁用配置重跑两边。重启是环境处理，不计为代码收益；旧失败报告保留。重启后完整对照另记，不能用后一次通过覆盖先前失败。

未采用：V21 的角色方向／经验计算实验、Cocos 内置 meshOptimize（索引被提升到 32 位）、V22 Graphics 合批着色器。V29 的粒子预热曾残留用于预热的粒子，修复为先 play 再 emit 再 stop 后重新检查；V29 性能数据全部排除，不以它作为收益证据。

V33／V34 自定义粒子上传虽然减少了传输字节，没取得可重复的 CPU 收益，最终已移除其组件和元数据。原生粒子上传对照的五次热施放主线程平均 4.34 ms／帧、整进程约 100.85% 单核；V34 为 4.60 ms／帧和 110.98%。这些短窗口有明显噪声，无法归因全部差异，但足以拒绝将“字节更少”当作采用理由。V34 的不完整日常回归明确登记为 cancelled-unselected，因方案被撤回而停止，不作为验收。

## 2026-11-13 后续：以模拟器进程合计 CPU 低于 50% 为目标

用户再次确认以 Android 模拟器的 Chrome 进程族合计衡量，包含浏览器 GPU／合成线程的 CPU；100% 表示一个核心。用户暂缓 FPS 验证，并要求继续优化代码与画面，后台视频保持运行。现有 60 FPS 设置保留，目标尚未达到。

CPU 采样发现靶场导航按钮同一帧先写“出发”，随后写“靶场设置”。最终画面虽不变，Label 仍每帧生成并上传纹理。`Hud.setAutomation` 现统一确定最终文案和可交互状态，移除 `Hud.update` 的二次覆盖。固定 120 帧原版重绘／上传均 120 次，修复版均为 0；普通导航、暂停、抵达、阻路、靶场进出及显隐共 10 项状态检查通过。

此项只改善靶场 HUD，不能推算普通走打 CPU。独立进程采样存在漂移：原版两组为 98.41%／113.92%，修复版为 88.26%／88.11%。另在同一进程中切换原版与修复版的实际编译方法，按 A-B-B-A 连续施放：6 次预热不计入，每组 6 次的第 1 次作为切换过渡不计入，其余全部保留。原版与修复版各 10 次热施放的 CPU 合计为 **112.94% → 95.46%**；CPU 毫秒／绘制帧为 **22.672 → 19.177**（约少 15.4%），共 20 次实际技能释放、命中 238／239 次。保留进程总量及每帧工作量，未因暂缓 FPS 验证而更改限帧设置。

展开任务栏的区域标题也有同类问题：先写普通区域名，再写靶场标题。现同样一次确定最终标题，并去除重复的空距离赋值。导航文字、区域标题在最终固定 120 帧检查中均无重复重绘／上传；对照中区域标题原为 120 次。`under50-captions-expanded-control-v1` 与 `under50-captions-expanded-candidate-v1` 的文案、显隐和 10 项导航状态一致。此项未单独量化整进程 CPU，不能叠加到上述降幅。

证据：`under50-caption-cpu-comparison-v1.json`、`under50-caption-cpu-same-process-v1/report.json`、`under50-caption-state-control-v2/report.json`、`under50-caption-state-candidate-v1/report.json`，均在 `src/cocos/test-results/performance/`。完整／核心 TypeScript、现有 140 项测试及隔离 Creator 构建通过；第二处标题修复后再次通过完整 TypeScript、Creator 构建和原生 HUD 状态／纹理上传检查。主工程已合入这两处 HUD 修复，其他 201 个脚本和引擎设置保持本轮基线。尚未制作包含修复的新 TapTap 包；上述模拟器观察不能替代手机功耗、温度或 GPU 时间验收。

另试验了在原生透明队列排序后，仅合并相邻且同材质的 Line 提交，保持原生顶点字节、三角顺序和着色器。混合实线／光晕／核心及优先级的画面对照为 251 → 203 次绘制，三角形数量相同，像素差异最大 1 色阶，恢复原版的重复截图也存在同等舍入差异。但同进程 CPU 对照仅为 98.25% → 95.69%；进一步合并上传后另一组为 96.66% → 95.68%，没有取得稳定的附加收益。该适配涉及引擎队列内部结构，**未合入主工程**，现有原生 Line 路径保留；不把绘制调用减少直接当作 CPU 目标完成。报告为 `under50-line-run-comparison-v1.json` 及 `under50-line-run-equivalence-v3/`。

### 原生采样与模拟器计时环境（同日后续）

使用设备已有的 Android simpleperf 对实际 H12 走打采样 30 秒，记录 2803 个样本且无丢失。原生样本中 `read_hpet` 约占 41.89%，`goldfish_pipe_read_write` 约占 27.75%；这是该次采样的函数占比，不能直接当作可消除的 CPU 降幅。FP 调用栈约 28.9% 无法完整展开，函数自身及库归类另存原始 CSV。GL 追踪未发现游戏侧每帧调用 `getError`、`getParameter`、`checkFramebufferStatus`、`readPixels` 或同步等待；不能以关闭这些不存在的调用来解释优化收益。

缓冲区归属采样另发现骨骼 UBO 占约 2.44 亿／3.61 亿上传字节。每个部件上传 12 KB 的 256 骨骼容量，实际使用 2～37 个矩阵。隔离实验保留原生蒙皮计算、网格和材质，只上传有效前缀并检查内容变化；GPU 全缓冲回读 159744 字节一致，画面对照最大差异 1 色阶，活动调试窗口的矩阵上传字节少约 95.6%。但普通走打同进程 CPU 为 102.90% → 105.51%，CPU 毫秒／帧为 19.008 → 19.434，**未采用**。报告：`under50-native-cpu-v1`、`under50-buffer-cpu-v1`、`under50-joint-upload-equivalence-v1`、`under50-joint-upload-decision-v1.json`。

计时优化仅用于本任务的 `SingularityPerf34` 专用 AVD。原配置已备份，在 AVD 配置增加 `kernel.parameters=clocksource=tsc` 后冷启动；未使用 `tsc=reliable`／`nowatchdog`，内核的稳定性检查保留。原 qemu PID 34292 已先恢复原始亲和性后关闭，新 PID 19144 保持 4 虚拟核、原分辨率、host GPU、Vulkan 禁用和相同物理核亲和性。内核实际提供 `tsc hpet` 并选择 TSC。15 秒独立主机／设备计时校准的比值为 0.999931；计时优化与手机代码收益分开记录。`android.cjs` 现把计时源写入环境指纹及 CPU 快照，防止混用不同计时环境的前后数据；现有 20 项性能检查通过。

新 TSC 环境下，当前生产代码的 60 秒普通走打 CPU 为 **81.53%**，主线程 4.314 ms／帧，CPU 合计 14.297 ms／帧；实际击杀 18、自然重生 10、移动约 201 米，场景／存活／输入覆盖／原生图形检查通过，CPU 目标仍失败。万箭齐发 9 次真实释放中，首次为 **88.74%**，其余 8 次热施放按时间合计 **75.81%**，CPU 合计 14.195 ms／帧，均保持 TSC，未出现原生图形错误。实际 FPS／长帧不作为此次验收门槛，60 FPS 设置保持。以上是新的环境测量值，不能与早先 HPET 数据相减宣称游戏代码降幅。

尝试同一进程内切换 HPET／TSC 未成功，实际计时源未匹配要求即停止，报告明确为 failed、没有有效采样窗口，最终仍为 TSC；不作为成功的时钟 A-B-B-A 对照。当前 TSC 环境相同画布的空场诊断为 rAF 约 6.74%、清屏约 38.13%、单三角形约 35.04%，只用于判断固定开销，不能作为游戏达标。早先 HPET 清屏约 54% 的数字不再描述当前环境。**完整游戏的低于 50% 目标尚未达到。** 后续需继续降低实际游戏工作量及提交次数。

当前环境证据：`under50-clocksource-experiment-v1.json`、`under50-clock-calibration-v1.json`、`under50-tsc-normal-smoke-v1`、`under50-tsc-volley-cpu-v1`、`under50-cpu-canvas-floor-tsc-v1`。AVD 原配置备份为 `src/cocos/temp/performance-avd/config-before-clocksource-tsc-20261113.ini`，恢复文件并重启该专用 AVD 可回到原配置；不调整宿主机全局电源或计时策略。

### 静态 HUD 缓存与迷雾刷新（同日后续）

静态 HUD 缓存先用原生 RenderTexture／Camera／Sprite 做隔离原型，保留源节点、输入、动态文字和原生绘制顺序。普通单采样 RenderTexture 改变圆角边缘覆盖，未通过画面对照；匹配画布 4 倍 MSAA 后，两个面板、8 个装饰组件的截图最大差异为 2 色阶，没有像素超过 3 色阶，恢复原版截图差异为 0。绘制 178 → 173 次，但真实走打 A-B-B-A 的进程 CPU 均值为 85.46% → 86.18%，没有证实收益。此原型需要引擎内部 MSAA 帧缓冲适配，**未合入主工程**。证据：`under50-hud-cache-equivalence-v4`、`under50-hud-cache-trial-v5`、`under50-hud-cache-decision-v1.json`。同时核对 Cocos 3.8 官方 UI 合批说明与 UIStaticBatch API；后者已弃用，不作为新增优化组件。

新一轮 TSC 环境的主线程采样指向 `LocalCartography.drawFog` 的重复工作。现先把原始 Set 的格子查询放入一张包含一格边界的 Uint8Array，仍使用原始坐标字符串精确匹配；再按 3×3 邻接位图复用羽化距离。中心格未揭示，缓存最多 255 个非空模式、约 32 KB 数值数据。只缓存未舍入的覆盖值，原有透明度取整、矩形顺序、边界和探索刷新条件均保留；没有延后刷新或减少迷雾层。

忽略目录中的差分检查覆盖全部 255 个模式、7 种透明度、随机／全空／全满网格、区域边界及旧存档非规范坐标，共 1,825 组，Graphics 的颜色／矩形／填充命令及顺序完全相同。实际 Cocos 画面对照最大差异 1 色阶，原版重复截图同样存在该级差异；三方均为 177 次绘制、199412 个三角形，迷雾顶点／索引均为 4728／7092。固定同一实际图层，各 32 次原生几何刷新，原版两组耗时 115.7／114.6 ms，候选为 57.2／20.0 ms；这是局部刷新工作量证据，不能换算成整个游戏的 CPU 降幅。完整／核心 TypeScript 与现有 140 项测试通过。证据：`under50-fog-command-qa-v1.json`、`under50-fog-native-qa-v1`。

同进程走打四个 30 秒窗口的 CPU 为原版 86.94%、候选 83.11%、候选 81.68%、原版 81.24%。探索逐渐完成，四窗实际迷雾刷新分别为 38／22／7／4 次，敌人与绘制工作量也变化，因此不能把前两窗相减宣称总 CPU 收益；仍未达到 50%。保留完整原始窗口：`under50-fog-live-v1/report.json`。迷雾算法的局部收益与全游戏 CPU 目标分开验收，Creator 构建及正常走打 CPU 复核另记。

实际 `perf-under50-fog` 构建已通过正常走打 60 秒复核：进程合计 CPU **85.56%**，主线程 **4.250 ms／帧**，击杀 18、自然重生 9、移动约 200.5 米；现有玩法、内存、图形和 60 FPS 配置检查通过，CPU 目标为 false，未启用 FPS／长帧通过门槛。报告：`under50-fog-build-smoke-v1`，根工程与隔离构建的 202 个脚本逐字节一致；本目标相对基线只改 Hud 与 LocalCartography 两个文件。该次环境负载与此前 81.53% 的窗口不同，不能相减报告代码收益。尚未重新打 TapTap 包。

另尝试将 `FeedbackView.bar` 的纯色矩形改用项目已有的原生白色 Sprite 填充。10 个原生图形状态中，9 个对照最大差异 1 色阶，但带 128/255 祖先透明度的状态出现最大 93 色阶差异，暴露 Sprite 与原 Graphics 的透明度继承差别。**未采用此通用替换，也未采集或宣称其 CPU 收益**。`FeedbackView.ts` 保持本轮原样，隔离原型与失败画面对照保留在 `under50-bar-sprite-native-qa-v1`，不能跳过透明度状态直接按正常画面通过。

随后选择了带守卫的 V3 矩形填充：复用项目 `EnemyCombatFeedback` 已使用的原生白色 Sprite／水平 FILLED 路径；任一祖先存在 UIOpacity 组件，或渲染组件颜色不完全不透明时，使用原 Graphics。玩家带纹理的血条仍走原路径，父 Sprite 的 fillRange 同步保留，供 `BossHealthStrip.inspect` 读取。懒加载的两种填充最多各一个，切换时维持原兄弟顺序，不新增触控区域、着色器或贴图文件。

V3 的 11 组原生画面对照（包含非整数尺寸、0／满值／越界比例、资源与敌人颜色、透明度回退及原玩家血条）最大差异均为 1 色阶；8 次状态切换的活动填充、双节点上限和比例元数据一致。固定同一完整静止场景、每次绘制更新矩形，4 个 30 秒窗口保持 178 次绘制、199502 个三角形，进程 CPU 按时间合计 **66.19% → 63.95%**，CPU 毫秒／绘制帧 **11.906 → 11.375**，该填充 Graphics 上传 **3337 → 0 次**；局部方法均值约 0.101 → 0.042 ms。固定场景只作归因，不能当作游戏达到 50%。

正常走打另用同进程 A-B-B-A：原版与 V3 观察到 **90.42% → 88.02%**，CPU 毫秒／绘制帧 **16.171 → 15.787**，填充的 Graphics 上传 1100 → 0 次。自然战斗量与绘制量不同，不能宣称所有差额均由此改动引起。结合固定场景及画面结果，已合入此守卫版本。证据：`under50-bar-sprite-native-qa-v3`、`under50-bar-sprite-frozen-comparison-v1.json`、`under50-bar-sprite-live-comparison-v3.json`；完整／核心 TypeScript、140 项现有测试和 Creator 构建通过。当前累计相对本目标基线只改 Hud、LocalCartography、FeedbackView 三个游戏脚本，202 个脚本与构建源一致，引擎设置保持；无新 TapTap 打包。最新实际构建的正常走打和群攻 CPU 复核另记，低于 50% 的目标仍未达成。

实际 `perf-under50-fog-bars` 构建的 60 秒走打复核为 **90.56%** 进程 CPU、**3.895 ms／帧**主线程，16 次击杀、9 次自然重生、约 195.7 米移动；玩法／内存／图形检查通过，CPU 目标为 false。万箭齐发另完成 6 次真实释放，首次 **106.73%**，后 5 次按时间合计 **84.87%**、CPU **16.306 ms／绘制帧**，无原生图形错误，计时源均为 TSC；实际 FPS 与长帧仍不作此次通过门槛。报告：`under50-fog-bars-build-smoke-v1`、`under50-fog-bars-volley-cpu-v1`。这些未成对的窗口不能与此前 85.56%／81.53% 或群攻 75.81% 相减，宣称代码变好或变坏；目前只证实局部开销下降，尚未证实整体 CPU 有足够、稳定的下降。目标保持未完成，后续继续查原生提交和变换数据的重复工作。

### WebGL 2 约束与未采用的原生提交试验（同日后续）

用户明确要求不使用 WebGL 1。主工程一直保留 WebGL 2；隔离工作区的后端试验设置已恢复为主工程原值，两份引擎配置 SHA-256 均为 `0db6423e92df3e0abe06e5c8217c1dae1d0d1c87ebcdd4b447dbacf4b87d8267`，活动配置为 `migrationsConfig`。当前正式对照预览 `fog-bars-final` 的实际 Cocos gfxAPI 为 7（WebGL 2），帧率设置仍为 60。WebGL 1 的试验构建未选用，后续不再继续该方向；不能把试验结果作为当前代码收益。

原生角色的 12 个蒙皮部件在同一帧反复上传完全相同的 224 字节模型变换 UBO。隔离试验复用原生缓冲与描述符绑定，逐字节读回 2688 字节并对照原生画面，最大差异 1 色阶，177 次绘制／199412 个三角形相同；30 秒实际战斗跳过 18238 次重复上传且无守卫回退。但完整进程 CPU 未取得可靠改善。固定场景、每帧改变角色根变换的多窗比较，原版按时间合计 65.56%，共享缓冲 65.41%、复用矩阵 67.70%、原生流式孤立缓冲 65.09%、组合 66.19%。这些方案均未合入，不能按减少上传次数宣称 CPU 优化成功。证据：`under50-local-ubo-equivalence-v2`、`under50-local-ubo-stream-equivalence-v1`、`under50-local-ubo-modes-v1`、`under50-local-ubo-decision-v1.json`。

另用原生全画布 MSAA RenderTexture 做一次性 HUD 截图，冻结输入、规则与动画后，仅用于估计界面提交的上限。画面对照最大差异 2 色阶，固定场景 A-B-B-A 的进程 CPU 为 65.25% → 59.42%。这不是可交付的动态 HUD 优化，也不是游戏达标；没有把冻结、隐藏原 HUD 或缓存旧画面写入主工程。证据：`under50-full-ui-cache-equivalence-v1`、`under50-full-ui-cache-trial-v2`、`under50-full-ui-cache-attribution-v1.json`。

WebGL 2 原生角色材质普查已完成，无脚本或原生图形错误。12 个蒙皮部件共享骨架，但材质的金属度／遮蔽值、纹理 mip 层数／过滤器不同，眼睛 UV 还超出 0–1；直接套用普通图集会改变现有采样，尚未采用。原生阴影投射／接收保持。报告：`under50-native-skin-census-v1/report.json`。本轮没有新增游戏源码改动，当前选用的仍是前述 Hud、LocalCartography、FeedbackView 三文件修复，CPU 低于 50% 的目标继续保持未完成。

### 粒子材质参数与图形传输试验（同日 19:42 后续）

重新采集当前 WebGL 2 构建，30 秒实际走打的整进程 CPU 为 95.97%，主线程 4.121 ms／绘制帧。2498 个原生采样、0 丢失，其中约 45.28% 样本在 goldfish 图形管道读写中；这只是归因，不能换算为可消除的 CPU 百分比。按 Android 官方支持试验 `hw.gltransport=asg`，实际配置切换成功，但重启后内核判定 TSC 不可用，只剩 HPET；60 秒 CPU 133.9%，未达标，不能与旧 TSC 直接比较。已将专用 AVD 配置逐字节恢复为原来的 pipe，保留全部失败数据；当前专用 AVD 为 PID 45868、物理 P 核亲和性 21845、HPET。没有绕过内核时钟校验或调整用户桌面视频。证据：`under50-native-cpu-tsc-webgl2-v1`、`under50-asg-transport-experiment-v1/state.json`。测量工具现将实际图形传输方式／drawFlushInterval 记入环境指纹，20 项既有性能检查通过。

WebGL 2 帧末 depth／stencil 丢弃提示的原生画面对照最大差异 1 色阶、相同 179 次绘制，3 次实际提示、无 GL 错误。但正常走打 A-B-B-A 观察为原版约 89.35%、候选约 94.22%，未证实收益，因此未合入。V1 画面对照曾遗漏启用候选、实际提示为 0 次，明确标为 invalid-inactive-candidate；只引用重新执行的 V2。小地图箭头改为保留原生 Graphics 网格、旋转节点的单姿态画面也一致，但尚无多角度与 CPU 验收，未采用。

全缓冲只读普查中，112659 次上传全部保留，有 20825 次内容与上次相同，其中 272 字节粒子材质为 10881 次调用／10808 次相同。核对当前安装与官方 3.8.8 源码，粒子尺寸／朝向会重复调用 `Pass.setUniform`，该方法即使值相同也会将材质置脏。隔离候选仅比较项目自建粒子材质实例的 `scale`／`nodeRotation` 与 `Pass.getUniform` 读取的当前 Float32 数据。完全相同才跳过写入，保留有符号零、外部重置与其他材质脏状态；没有修改粒子模拟、数量、画面或引擎原型。

原型的 5 组动态参数及实际编译版本的相同 5 组，均通过每组 272 字节 CPU／GPU 逐字节对照；截图最大差异 1 色阶，绘制量相同，无 GL 错误。原型实际走打 A-B-B-A 为 90.85% → 89.82%，但击杀／施放分别为 16／16 和 19／17，不能全部归因于代码。原型万箭齐发在同一进程先预热 6 次，再 A-B-B-A 共 24 次真实施放，每组首发作为切换过渡排除，各保留 10 发后为 **86.61% → 84.86%**，命中 239／237；候选避免 19789 次相同参数写入、保留 123 次实际变化。这里是参数写入数量，不能当作同等次数的 GPU 上传。

候选一度合入并通过完整／核心 TypeScript、140 项既有测试及 Creator 构建。实际新构建 60 秒走打为 **96.46%**、主线程 **4.801 ms／绘制帧**，16 次击杀、10 次自然重生、约 200.6 米移动，玩法／内存／原生图形／60 设置检查通过，CPU 目标 false。随后直接切换编译后的应用方法与原生 Pass，再做同进程 6 次预热＋24 次 A-B-B-A：原版与候选各 10 次有效施放，CPU **85.79% → 85.74%**，CPU **16.605 → 16.549 ms／绘制帧**，主线程 **4.431 → 4.478 ms／绘制帧**，命中 239／241。原版前后两组为 88.29%／83.28%，存在明显漂移；编译版没有复现可靠 CPU 收益，不能继续引用原型约 2% 的差额宣称优化成功。

**已撤回粒子材质适配。** 根工程与隔离工作区的 202 个脚本逐字节恢复至 `under50-fog-bars-source-manifest-v1.json`，当前仍只选用 Hud、LocalCartography、FeedbackView 三文件修复，继续 WebGL 2。未采用源码保存在 `under50-unselected-source/particle-uniform-v1/`，编译候选仅作历史试验，正式对照预览仍是 `fog-bars-final`。没有制作新 TapTap 包，低于 50% 的目标保持未完成。证据：`under50-particle-uniform-compiled-comparison-v1.json`、`under50-particle-uniform-equivalence-v3`、`under50-particle-uniform-build-smoke-v1`；撤回后的当前构建 60 秒走打复核为 **93.72%**、主线程 **4.577 ms／绘制帧**，19 次击杀、8 次自然重生、约 196.8 米移动，玩法／内存／原生图形检查通过、CPU 目标 false；环境为 HPET／pipe。报告：`under50-particle-uniform-restored-smoke-v1`。这与试验版未成对，不相减报告降幅。

### 图形传输批量与异步合成（同日 20:15 后续）

依据 Android 共享环形缓冲实现及当前模拟器硬件参数说明，专用 AVD 隔离试验 ASG 64 KB 事务块、4 MB 写缓冲、256 KB 数据环；有效启动参数与来宾 `asg` 配置均读回核对。完整 60 秒实际走打，HPET 下 **142.48%**、主线程 4.875 ms／绘制帧；同一配置在内核仍认可的 TSC 下为 **89.71%**、主线程 3.992 ms／绘制帧，均未达到 50%。TSC 来宾／主机时间比 1.000706，未绕过时钟校验。这些是环境测量，不计为游戏代码收益。原生固定场景的两边均为 WebGL 2、4 倍 MSAA、1608×768、127 次绘制及 198998 个三角形；截图差异集中于弓／箭袋，冻结夹具在采样骨架后遗漏附件同步，因此跨次画面不能据此批准。已改为用原生角色呈现同步附件，新的默认配置参考保存在 `under50-transport-restored-visual-v2`，跨进程重放仍待核实。ASG 配置未采用，已逐字节恢复原始管道配置。

另试验官方 `AsyncComposeSupport`，保留原 pipe、host GPU、Vulkan 禁用、60 设置与游戏源码，启动日志确认功能启用。60 秒实际走打为 **85.19%**、主线程 4.151 ms／绘制帧，18 次击杀、10 次自然重生、约 201.7 米移动，无原生图形错误，但没有成对证据确定收益来源。该选项未采用，已恢复默认功能开关。报告：`under50-asg-large-experiment-v1`、`under50-asg-large-normal-smoke-v1`、`under50-asg-large-tsc-smoke-v1`、`under50-async-compose-experiment-v1`、`under50-async-compose-normal-smoke-v1`。

当前专用 AVD 为 PID 37112（20:05:11 启动），恢复至原 pipe、仅 `-Vulkan`、亲和性 21845，游戏引擎仍为 WebGL 2；本次内核保留 TSC，复核时间比 1.000589。同画布／抗锯齿设置的短时归因为 rAF 6.41%、清屏 30.71%、单三角形 29.31%，只是容器成本分析，不能作为游戏达标。恢复后的完整 60 秒走打为 **76.31%**、主线程 **4.155 ms／绘制帧**，17 次击杀、9 次自然重生、约 197.4 米移动；玩法／内存／原生图形／60 设置检查通过，CPU 目标 false。不能与上一轮 HPET 的 93.72% 相减报告代码降幅。证据：`under50-cpu-canvas-floor-restored-v1`、`under50-restored-tsc-calibration-v2.json`、`under50-transport-restored-normal-smoke-v1`。

本轮未修改游戏源码，202 个脚本仍与 `under50-fog-bars-source-manifest-v1.json` 一致。测量工具新增有效启动传输尺寸／功能覆盖列表，兼容逗号分隔的官方功能参数，20 项既有性能检查通过；启动脚本的异步合成选项默认关闭。没有制作 TapTap 包、调整用户桌面视频或降低帧率设置，目标保持未完成。

## 官方与成熟方案依据

- [TapTap 运行性能指南](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/runtime/runtime-guide/)、[平台性能检测](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/performance-test/)
- [Cocos 3.8 网格优化](https://docs.cocos.com/creator/3.8/manual/en/asset/model/mesh.html)、[骨骼动画](https://docs.cocos.com/creator/3.8/manual/en/animation/skeletal-animation.html)、[UI 合批限制](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-batch.html)
- [meshoptimizer JavaScript 官方说明](https://github.com/zeux/meshoptimizer/blob/master/js/README.md)
- [Cocos 3.8 Label API](https://docs.cocos.com/creator/3.8/api/en/class/Label)、[缓存模式](https://docs.cocos.com/creator/3.8/api/en/enumeration/CacheMode)；此次优先移除无意义的文案来回切换，未以更换字体或降低字形质量代替修复。
- [Cocos 3.8 RenderTexture](https://docs.cocos.com/creator/3.8/manual/en/asset/render-texture.html)、[UIStaticBatch 弃用说明](https://docs.cocos.com/creator/3.8/api/en/class/UIStaticBatch)
- [Cocos 3.8.8 Pass 源码](https://raw.githubusercontent.com/cocos/cocos-engine/v3.8.8/cocos/render-scene/core/pass.ts)、[原生粒子参数更新](https://raw.githubusercontent.com/cocos/cocos-engine/v3.8.8/cocos/particle/renderer/particle-system-renderer-cpu.ts)
- [Cocos 3.8 Sprite 填充模式](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/editor/sprite.html)、[UIOpacity API](https://docs.cocos.com/creator/3.8/api/en/class/UIOpacity)；透明度路径仍以当前安装的 3.8.8 原生画面对照为准。
- [Android ASG 共享环形缓冲](https://android.googlesource.com/platform/hardware/google/aemu/+/refs/tags/aml_mpr_341111020/host-common/include/host-common/address_space_graphics_types.h)、[官方异步合成调用](https://android.googlesource.com/device/generic/goldfish-opengl/+/60abeab4f846f93fd3f84b3078282ab69b539737/system/hwc2/HostComposer.cpp)
- [Android simpleperf 官方命令说明](https://android.googlesource.com/platform/system/extras/+/android16-release/simpleperf/doc/executable_commands_reference.md)、[Linux 时钟源参数](https://docs.kernel.org/admin-guide/kernel-parameters.html)、[Android Emulator 内核参数构造源码](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-32-release/android/android-emu/android/main-kernel-parameters.cpp)

Line 公开组件未提供“只上传活跃前缀”的应用层选项，故使用有布局守卫与还原机制的窄适配；没有另写粒子模拟器、替换渲染引擎或新增平台专用 API。


### 硬件 Guest ANGLE／Vulkan（同日 20:24 后续）

按 Android Emulator 官方实现核实并试验了 `-gpu host -feature Vulkan,GuestAngle`，只作用于独立性能模拟器。与早期 SwiftShader 软件路径不同，本次日志确认为 RTX 3080 硬件 Vulkan，Android 使用 `angle` EGL 和 `skiavk` HWUI；未覆盖引擎自动启用的 NVIDIA 兼容性修正。依据：[Android Emulator 官方启动属性实现](https://android.googlesource.com/platform/external/qemu/+/emu-master-dev/android/android-emu/android/userspace-boot-properties.cpp)。

- 实际游戏仍为 **WebGL 2**，1608×768、4 倍 MSAA、60 FPS 设置、127 次绘制和 198998 三角形的冻结渲染诊断均确认；没有启用 WebGL 1，也没有关闭抗锯齿。冻结画面只用于检查渲染，不用于 CPU 达标。
- TSC 可用且受内核支持，10 秒校验客体／主机时间比为 **0.999542**，未绕过时钟 watchdog。
- 完整 60 秒 H12／Lv17／BOW 移动狩猎进程合计 CPU 为 **102.925%**，主线程约 **4.108ms/绘制帧**，16 次击杀、9 次自然重生、约 196.67m 移动，内存峰值约 564.77MB；玩法、原生界面与图形检查通过，CPU 目标未达到。FPS 门禁仍按用户要求暂缓。相较近期原路径 76.311% 的结果，本方案没有采用价值，**已拒绝并恢复原 `-Vulkan`／pipe 配置**；不同启动环境不作为游戏代码收益。
- 原路径跨进程冻结截图仍有 1594 个差值超过 3 的像素，集中在弓／箭袋；候选与原路径有 2056 个，亦集中于此。该夹具的挂点姿势尚不能复现到像素级，因此没有宣称跨路径画面等价通过。
- 202 个主工程游戏 TS 文件与 `under50-fog-bars-source-manifest-v1.json` 全部一致，本轮未增加游戏源码改动；既有性能检查 20/20 通过。工具增加可选、默认关闭的 GuestAngle 启动项，并记录实际 EGL／HWUI 后端，以便识别硬件与软件路径。

记录：`under50-guest-angle-experiment-v1/state.json`、`under50-guest-angle-normal-smoke-v1/report.json`、`under50-guest-angle-visual-v1/report.json`。目标继续有效，尚未达到 CPU 低于 50%。


### 用户要求清理并暂停（2026-11-13）

按用户“保留有效的改动，去掉太 hack 的方式，然后暂停优化”收尾。移除 `BrowserPreviewFrameClock` 及其生命周期接入；`ManagedLine` 不再替换模型 `updateIA` 或读取私有顶点数组上传，仅保留模型／网格销毁；`CompactGraphics` 删除对私有 `paths/_points` 数组的替换，仅保留通过 protected 上传扩展点限制缓冲容量；删除使用未公开 `ParticleSystem.emit` 的 `ContactParticleBursts`，命中特效恢复标准 `Burst` 和有界组件池，spark／flash／dust 均在加载期间准备。迷雾几何／读数验证保留，删除仅检验已撤回私有路径池的断言。

保留原生箭体 GPU 实例化、对象池与公开接口预热、字形缓存、反馈投影复用、HUD 最终文案去重、翻译参数缓存、迷雾占用／羽化缓存、透明度守卫的原生 Sprite 血条，以及不改顶点／骨骼／贴图的索引重排。两套引擎配置均只包含 WebGL 2，构建前检查拒绝重新启用 WebGL 1；项目初始化模板同步此要求。

失败的 GuestAngle／AsyncCompose 试验启动选项已从维护入口撤下。专用模拟器恢复原进程亲和性 16777215 后关闭，计时策略保持系统管理 0/0，移除强制 TSC 启动参数。7554 性能预览服务已按进程身份核对后停止；历史构建／原始数据保留。删除历史目录链接的操作被自动审查拦截且未提供具体原因，因此不删除这些链接，改为停止专用预览服务。用户桌面浏览器与视频未操作。

验证：完整／核心 TypeScript、既有 140 项测试通过；隔离 Creator 构建 `perf-optimization-clean` 完成。20 怪训练场连续三次五阶 BOW_05 均观察到箭矢、粒子与真实伤害，模型上传回调替换次数为 0，无页面／原生图形错误；实际 WebGL 2，WebGL 1 构造器不存在，1608×768、4 倍 MSAA、60 FPS 设置保留。此为功能收尾，不采样 CPU、不执行 FPS 门禁、不新增性能试验。尚无清理后 CPU 或 TapTap 真机温度／功耗结论，先前版本的降幅不套用于清理版。

当前源码清单与决定见 `optimization-pause-cleanup-v1/source-manifest.json`、`optimization-pause-cleanup-v1/decision.json`，共 200 个 TS 文件；清理前源码归档仅作历史证据。未重新打 TapTap 包、未上传、未提交版本。**用户已要求暂停优化，低于 50% 目标尚未验收；后续须等待用户明确恢复。**
