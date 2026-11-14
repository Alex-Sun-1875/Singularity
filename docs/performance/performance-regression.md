# 性能防劣化用例与执行协议

2026-11-13 万箭齐发专项的实现、逐帧／画面对照、撤回方案与模拟器状态退化记录见 [V35 群攻优化记录](volley-performance-v35.md)。最终交付状态单独记录，专项诊断不能替代真机持续发热验收。

## 2026-11-13 HUD渲染减负（V19最终选择）

依据[TapTap运行优化建议](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/runtime/runtime-suggestions/)与[Cocos 3.8合批规则](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-batch.html)，本轮减少常驻HUD的模板缓冲操作、透明叠层及渲染提交。保留原画、60 FPS配置、按钮布局、触控、技能规则与地图内容，未增加依赖。

- 37份HUD图标沿用原始RGB与分辨率，在原有小数裁切区域内预烘焙Cocos默认64边形圆形alpha；冷却图也预裁切。移除7个常驻技能图标Mask，保留头像、地图和禁用态所需的原有遮罩。
- 将既有阴影、光晕与金边按原尺寸比例预合成为一张1024px公共底图；按钮按压与输入节点不变。冻结同一实际场景对照，四职业及冷却、禁用、技能名、空槽状态均稳定减少28次绘制/帧。
- 复用已有Pillow与Cocos Sprite，无运行时canvas或新增平台接口。重建入口为 `python src/cocos/tools/build-hud-render-assets.py`；来源、输入/输出SHA-256、RGB保持校验及方法记录在 `assets/resources/ui/combat-relief/hud-circular/provenance.json`。新增PNG合计4,685,153字节，沿用 `skill-icons` / `panel-art` 分包；生成成功与画面验收分开记录。

同一4核Android14模拟器、原画质与60帧配置，分别连续5分钟H12/Lv17/BOW正常输入走打。原版先测一次、渲染候选测一次，另测V20试验，最后回测原版；这是三种版本的独立用例，**不是ABBA重复或真机功耗验收**。协议、采样器、玩法与环境指纹相同；四次均通过预算和逐分钟移动/命中/击杀检查，未发现Creator构建日志内容变化。

| 指标 | 原版V18第一次 | 最终V19 | 原版V18回测 |
| --- | ---: | ---: | ---: |
| 平均FPS | 59.99 | 59.99 | 59.98 |
| 最低滑动1秒FPS | 58 | 57 | 54 |
| 主线程CPU，ms/帧 | 4.101 | 3.847 | 3.969 |
| 进程族核心当量CPU，100%=1核 | 74.19% | 73.18% | 75.88% |
| 绘制次数中位数/帧 | 214 | 183 | 215 |
| 全程PSS观测峰值，MB | 535.60 | 538.02 | 529.55 |

最终版本相对两次原版的主线程CPU观测下降3.09%–6.20%，进程族CPU下降1.36%–3.57%，绘制次数中位数下降14.49%–14.88%。**整进程CPU改善仍较小，不能宣称大幅降耗。** 战斗时序、击杀与刷新次数有正常差异，冻结场景的28次绘制减少是更直接的渲染归因证据。内存没有下降；选中版本峰值增加约2.42–8.47MB，仍在800MB目标内。

V20另试了“只有fillRange变化才赋值”。在真实Cocos实例中，120次稳定HUD更新的重复赋值为0，生命降至25%和冷却开始各正常更新一次；但5分钟主线程3.964ms/帧、核心当量CPU76.66%，没有测得进一步收益。因此该试验**未进入最终源码或交付包**，保留源码快照、计数诊断及通过预算的报告，不能把逻辑层少调用次数当作降耗成功。

四职业和5种弓HUD状态的旧渲染/新渲染截图已人工检查；裁切区平均RGB通道差约0.67–1.37/255，来自alpha边缘与预合成采样，不能称为像素完全一致。没有发现矩形冷却溢出、缺失图标或按钮布局变化。当前模拟器没有 `EXT_disjoint_timer_query*`，**没有取得GPU硬件耗时/占用或电量、温度数据**；减少绘制和透明混合不等于同百分比GPU耗电下降。TapTap容器、ARM/iPhone及实际分包下载/画质仍须真机验证。

原始记录在 `src/cocos/test-results/performance/`：

- `hud-render-v19-comparison.json`：指纹、全部汇总及最终选择；`android-moving-v18-before-v19/`、`android-moving-v19-after-v18/`、`android-moving-v18-return-control/`：逐帧、每秒PSS、CPU计数、截图与原生图形日志。
- `hud-v19-visual/`：冻结场景旧/新截图、绘制计数、GPU扩展检查及像素差记录。
- `android-moving-v20-after-v18/`、`filled-sprites-v20-qa.json`、`v20-experiment-source.json`：未选择的试验及原因。

类型检查、140项现有检查、Cocos Web构建与Legacy管线检查通过。Creator普通CLI启动在本机反复出现已有的 `UNKNOWN open engine.json`；本轮通过带Node Inspector的编辑器进程及透明文件打开诊断完成编译，未改引擎安装，诊断未写入游戏源码/产物，也未挂在正式性能采样中。普通CLI启动问题原因尚未确认，不将诊断启动成功表述为已修复构建入口。

这次只验收上述H12/BOW/300秒范围与四职业HUD画面，不扩大为完整多场景或15–20分钟长测基线，既有失败记录继续保留。

交付为0.3.33游客测试包，完整ZIP 224,521,013字节（224.52MB），76个分包；本地主包离线审计ZIP 1,353,586字节（1.29MiB），主包未压缩文件5,579,206字节。**平台首包实际下载量与可玩前所需分包资源尚未测得**，1.29MiB不代表全部可玩资源。201份脚本在打包期间哈希一致，最终HUD/UiSkin与实测V19在统一换行后逐字节一致；游客入口、版本、优化资源标记、排除V20试验和编辑器诊断、ZIP CRC及交付SHA-256检查通过。官方转换和本地审计不代表平台/真机验收，未上传，正式登录服务仍待部署。详见 `src/cocos/release/taptap-hud-performance-v19-validation.json`。

## 日常验证：连续5分钟走动刷怪

按用户2026-11-13的最新要求，日常性能验证优先运行Android模拟器中的**连续5分钟边走边打怪**，自动挂机仅作补充。包含持续移动、普通攻击实际命中、合法技能释放、击杀与自然刷新；不以停在原地挂机代替移动战斗。保留60 FPS配置和原画质，继续检查最低滑动1秒FPS≥50、进程内存≤1000 MB（目标≤800 MB）及CPU。15–20分钟长测和完整多场景回归用于大改、发布前验收或进一步排查，不作为每次小改的默认流程。

```powershell
npm run test:perf:android:moving -- --url http://127.0.0.1:7514/ --family BOW --area H12 --out src/cocos/test-results/performance/android-moving-hunt-UNIQUE
```

针对截图中的Lv17弓角色及灰烬喷囊兽，补充夹具选择H12野外；截图本身不足以确认地图编号。测试通过正常输入入口移动与攻击，关闭游戏自动挂机；逐帧观测角色实际位置，每分钟记录移动距离、击杀、自然刷新、生命和CPU。每分钟实际移动帧须达到50%、移动至少30米且有击杀和实际命中，累计技能释放与自然刷新均须发生。有限库存、敌人伤害、掉落和刷新规则保持；角色死亡、离图或切回自动挂机均使测试失败。角色卡住或只在空地走动不能通过累计总量来掩盖。

`--control auto`用于补充自动挂机；`--profile smoke`为60秒夹具检查，`--profile soak`为显式20分钟长测，均不能冒充5分钟移动战斗。报告保存完整逐帧、渲染计数、截图、每秒进程族PSS及原生图形日志。优化前后比较须使用相同夹具、环境、玩法和采集脚本哈希；自动挂机的CPU变化不能当作移动战斗的CPU收益。

测试同时监听项目temp下的Creator构建日志。测量期间若其他任务正在构建，该轮保留数据并标为不可引用，不停止其他任务的进程。此前V16完整回归的5个低帧窗口中，4个与其他构建日志时间重叠；第二轮移动弓的47FPS尚无同类证据，仍保留失败结论。此监测只覆盖Creator构建日志，不代表排除了全部宿主干扰。

监测器对日志内容计算SHA-256，忽略Windows的只读访问／访问时间通知，结束时再次核实；读取旧日志不再误报为新构建。首次5分钟走打报告的环境监测误报与现场文件修改时间证据一起保留，不能直接引用为新采样器的基线。完整多场景回归入口为 `npm run test:perf:android:full -- --url <URL> --out <唯一目录>`，同样带构建干扰检查。

### 2026-11-13走打对照结果

同一Android14四核模拟器、相同画质与60帧配置，优化前V16、候选V17各连续运行5分钟。两份报告的环境、玩法及采样哈希相同，逐分钟移动／命中／击杀门槛、自然刷新、原生界面／图形、内存采样完整性与相对回退检查通过，未观测到并行Creator日志内容变化。

| 指标 | V16 | V17 |
| --- | --- | --- |
| 平均FPS／最低滑动1秒FPS | 59.78／54 | 59.70／51 |
| 全程进程族PSS观测峰值 | 533.44 MB | 531.89 MB |
| 四核归一化CPU | 25.62% | 25.64% |
| CPU×4核后的核心当量 | 102.47%，约1.025核 | 102.57%，约1.026核 |
| 主线程CPU | 4.421 ms/帧 | 4.433 ms/帧 |
| 实际移动／击杀／自然刷新 | 1027米／85／80 | 1013米／84／77 |

该单组走打对照没有测得明显CPU下降（核心当量约+0.10%、主线程约+0.28%），不能称为降温或降耗成功。此前H12自动挂机ABBA观测的约6.06%CPU下降只适用于自动挂机。V17通过的报告只作为H12／Lv17／BOW／300秒走打用例的基线，**不批准完整多场景基线**；此前完整回归失败与自动挂机长测中断记录仍保留。数据见 `test-results/performance/moving-hunt-v17-pair-summary.json` 与 `android-moving-hunt-v{16,17}-paired/`。

### 参考优化建议的适用范围

采用“采样定位→一次改变一类开销→相同走打负载复测”的流程，正式预算采样不挂CPU分析器。当前走打诊断中渲染提交、UI遍历与缓冲更新值得继续检查；相机拆分诊断约72次世界绘制、140次UI绘制/帧，不能只凭总DrawCall断定GPU瓶颈。

官方3.8文档中的 [`CC_USE_PROFILER`](https://docs.cocos.com/creator/3.8/manual/en/advanced-topics/profiler.html) 属于原生C++性能剖析器，不能直接当作TapTap小游戏的开启步骤。当前Android Chrome构建已观测到动态图集启用且atlasCount=1；这不证明小游戏构建也已启用，平台侧须按[动态合图文档](https://docs.cocos.com/creator/3.8/manual/en/advanced-topics/dynamic-atlas.html)核实初始化与内存。数字／倒计时已有CHAR缓存；静态文字是否用BITMAP须结合实际图集和绘制顺序，遵守[Label限制](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/editor/label.html)。

优先审查HUD的Mask、Graphics、纹理／材质与渲染顺序造成的[合批断点](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-batch.html)，再用CPU调用栈检查每帧分配和重复求值。UIStaticBatch已被官方弃用，且不适合包含Mask／Graphics的子树；不能盲目套用。资源池和引用释放复用已有实现；压缩纹理、LOD、实例化与分包必须分别核实平台兼容、视觉、内存和负载收益，不承诺固定百分比，也不改变当前画质或帧率目标。

## 既有多场景验证

主场景为用户 2026-11-12 截图中的 **U1-06／三誓供能线争夺／三刃守誓阵**，基准角色 Lv15，Seed19。v5驾驶器在生命≤60%且动作／冷却允许时按正常药水入口使用初始自带的3瓶生命药剂，消耗库存并保留伤害与死亡检查，不补库存、不改生命或敌人参数；终值血量、剩余药剂和实际消耗事件写入报告。旧v4站桩近战被新版首领击杀的窗口保留为无效证据，不得作为引用。保留跑动 5m/s、慢走 2m/s、60 FPS 配置，不能通过限帧消除失败。S13 是补充地图，不能代替 U1-06 的验收。

## 资源预算（2026-11-12用户要求）

统一配置在 [`budget.json`](../../src/cocos/tools/performance/budget.json)，当前协议为 `moving-combat-v6`。报告保存预算内容及哈希；旧协议和不同采样预算不能作为新版本的防劣化基线。

报告还指纹化实际加载的怪物战斗配置、全部技能、战斗规则和职业配装；两版玩法指纹不同会拒绝直接比较。采集脚本本身也有哈希，避免改变采样开销后继续沿用旧报告。玩法更新后先保留旧结果，再在新规则下重新验证绝对预算和建立经审阅的基线，不能自动把新玩法的差异算成性能优化。

Windows模拟器还记录其进程计时策略的实际ControlMask／StateMask并加入环境指纹。独立的 `Set-AndroidTimerPolicy.ps1` 只处理本项目专用AVD进程，支持查询、尊重已有计时精度请求以及恢复原策略；先写入PID／创建时间／原始掩码账本再操作，结束时读回核实。机制依据[Microsoft SetProcessInformation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation)。该开关本身不请求新的计时精度，也不修改系统电源计划或进程优先级。宿主调度假设必须通过单独的ABBA诊断验证；所有 `--diagnostic --diagnostic-reason <原因>` 报告都不能成为已批准基线，环境设置带来的变化不能计为游戏代码优化收益。

| 指标 | 硬门槛 | 优化目标或相对检查 |
| --- | --- | --- |
| 帧率 | 每个窗口平均FPS及最低滑动1秒FPS均≥50 | 继续保持60帧设置；原有长帧／p99门槛保留 |
| 进程内存 | 观测峰值≤1000 MB | 尽量≤800 MB；超出800提醒；同用例峰值比基线增加＞15%+32 MB失败 |
| CPU使用率 | 计数有效、核心数换算正确；主线程≤16.67ms/帧 | 核心当量比基线增加＞15%+3个百分点，或主线程增加＞15%+0.3ms/帧失败 |

这里1 MB＝1,000,000字节；原有堆／显存泄漏门槛仍以MiB（1,048,576字节）表示。进程内存从加载、预热到所有运行窗口每秒采样，报告保留观测峰值、各进程原始值与时间戳；采样间隔超过3秒或缺失取数会失败。周期采样记录的是观测峰值，不宣称捕获了采样之间的瞬时峰值。Android使用独立Chrome进程族的PSS，含浏览器和GPU进程开销；Windows桌面使用Chrome进程族工作集RSS之和，共享页可能重复计算。两种口径不可混比。JS堆和Cocos图形分配单独记录，不与进程占用相加，也不以GC后的堆大小代替整个游戏进程内存。

CPU同时显示整机归一化百分比、核心当量百分比与核数。未指定额外CPU绝对占用上限时，使用上述基线门槛，避免自行虚构固定百分比。模拟器结果仍不能替代TapTap容器或真机进程资源验收。

截图中的 31% 是系统给 TapTap 的当日用电统计，另有前台 36 分钟、后台 3 分钟；不是受控测试的设备电池起止差，不能据此计算本游戏每小时掉电或优化收益。

## Android模拟器执行入口

模拟器本身先做空WebGL画布刷新诊断；若空画布已经低于50FPS，该环境不能提供通过帧率预算的结论，也不能因此降低游戏门槛。2026-11-12长时间运行后曾测得空画布34.99FPS。Chrome在API30及以上默认使用Vulkan合成后端；Android官方列出的兼容性排查方式为 `-feature -Vulkan`，本项目启动器对应可选参数 `-DisableVulkan`，保留硬件GLES和游戏WebGL画质。依据：[Android Emulator图形故障排查](https://developer.android.com/studio/run/emulator-troubleshooting#cannot-open-webpage-correctly)。是否禁用Vulkan、宿主GPU模式及客体EGL/Vulkan/vsync属性一并写入环境指纹；不同图形环境拒绝直接比较。重新启动或切换后端的变化只能作为环境诊断，不计作游戏代码收益。

用户已明确指定Android模拟器。复用本机已有Android14 Google APIs x86_64镜像，创建项目temp中的独立测试AVD，4核／4GB、2412×1080横屏、480dpi、硬件GPU转译。启动脚本不下载镜像、SDK或依赖，不清理其他AVD。

```powershell
pwsh -NoProfile -File src/cocos/tools/performance/Start-AndroidEmulator.ps1 -DisableVulkan
adb -s emulator-5556 shell getprop sys.boot_completed
adb -s emulator-5556 root
pwsh -NoProfile -File src/cocos/tools/performance/Set-AndroidHostAffinity.ps1 -Action Set -PhysicalCoresOnly
npm run test:perf:android -- --profile smoke --url http://127.0.0.1:7495/ --out src/cocos/test-results/performance/android-smoke
npm run test:perf:android -- --profile regression --url http://127.0.0.1:7495/ --out src/cocos/test-results/performance/android-candidate --baseline src/cocos/test-results/performance/android-baseline/report.json
npm run test:perf:android:soak -- --url http://127.0.0.1:7495/ --out src/cocos/test-results/performance/android-soak
```

先等待boot_completed为1、adbd完成root重连。首次打开Chrome时选择不登录账号、关闭通知介绍，并确认没有原生弹窗覆盖游戏；原生界面可用ADB自带uiautomator读取，不需要下载Playwright Android UI驱动。脚本通过Playwright已有Android接口连接实际Chrome，并请求全屏。HTTP服务仍须按下节启动，ADB reverse把该本地端口接入模拟器。

本次专用AVD的蓝牙服务曾循环崩溃并弹窗，测试时在该AVD内临时执行 `adb -s emulator-5556 shell svc bluetooth disable`，原始 `settings get global bluetooth_on` 为1，结束后恢复启用。复跑时先记录原值；如需沿用本次环境，关闭服务后确认值为0，完成后按原值恢复。蓝牙设置也在环境指纹中，不能混用状态不同的报告。该操作仅针对本项目拥有的测试AVD，Windows蓝牙保持原状。

Android后端读取/proc中Chrome各进程utime＋stime，CLK_TCK由系统查询，PID＋启动计数防止PID复用；不重复累计子进程时间。窗口内出生的新进程经启动计数核实后，从零计入其全部CPU时间；无法确定起始值或窗口内退出的进程仍使测量失败，不能漏掉CPU后继续出报告。核心数读取模拟器实际online核，本机此配置为4核，不能用宿主24核代替。额外记录Chrome进程族PSS；它与Cocos显存计数存在重叠，不能直接相加。soak中预热后的PSS增长超过64MiB也失败。保留原始进程计数和单位，便于复核归一化CPU乘核心数后的负载。

异构宿主CPU会给模拟器带来明显调度波动。上面的宿主设置只把本项目拥有的QEMU进程固定到同一性能等级的宿主核心，`-PhysicalCoresOnly` 再按Windows CPU Set的CoreIndex选择每个物理核的一条逻辑线程，避免模拟器线程共享SMT执行资源。本机为宿主逻辑CPU0、2、4、6、8、10、12、14，亲和性21845；虚拟机仍是4核，CPU口径仍按这4核计算。不改变系统电源计划、游戏帧率、优先级或其他应用。报告直接查询实际进程亲和性并加入环境指纹；优化前后必须相同，不将调度变化带来的改善计入游戏优化收益。测试结束后执行 `Set-AndroidHostAffinity.ps1 -Action Restore` 恢复该进程原来的调度范围。原进程退出或被替换时脚本拒绝套用旧状态。

诊断原始CRP管线时可显式传入 `--expected-pipeline crp`。早期宿主调度下存在失败窗口，固定物理P核后则须重新建立同环境对照，不能混用较差的早期成绩计算收益。CRP报告用于 `--before` 优化归因；已批准的防劣化 `--baseline` 仍要求通过门槛且实际运行Legacy管线。源码模块配置、构建产物customPipeline标记和运行时Root.usesCustomPipeline三层检查共同阻止管线被恢复；Build-Local、Build-TapTap与check:tap都会验证相应状态。相关门禁随npm test执行。

优化归因使用 `--before path/to/before/report.json`：允许完整、有效的优化前测量暴露性能失败，但拒绝缺少窗口、未移动／未命中、运行异常或损坏计数。该选项不会放宽候选版门槛。未来防劣化的 `--baseline` 继续要求已通过性能门槛及Legacy策略的已验收版本；两种引用不能同时使用。

这是实际Android虚拟机里的Chrome测试，包含Cocos移动分支、Bullet、虚拟4核及宿主GPU转译；仍不等同TapTap客户端、ARM手机、实际电池功率或热降频。模拟器的电量图与虚拟温度不用于真实手机降耗结论。

### 图形有效性与缓存

协议 `moving-combat-v5` 沿用v4的资源预算及v3的原生图形及遮挡检查，在结束前读取独立AVD本次启动标记之后的Chromium原生日志，归档为 `android-chromium.log`。GL错误、上下文丢失、GPU进程重启、缺少日志窗口标记都会失败；页面没有console错误不能替代此检查。旧Android报告缺少这项检查，不能作为新版门禁的引用或已批准基线。

启动后及每轮结束，还通过ADB自带uiautomator确认原生界面只包含全屏Chrome，没有系统或浏览器引导／对话框遮挡。仅对已识别的Android首次全屏说明及其确认按钮自动关闭；其他弹窗直接失败。记录实际设备截图和UI层级；CDP网页截图可能看不到原生覆盖层，不能单独作为画面验收。此前v2结果在原生截图中发现首次全屏引导覆盖，因此保留作诊断，新版必须在无覆盖层条件下重建前后对照。

本轮查出箭袋与W11的静态网格序列化缓存失配：箭袋缓存为702顶点、源资源为732顶点，错误的索引偏移读出了65531等越界值。现有 `refresh-morph-build-cache.py` 已扩展到所有网格；先备份失配的生成缓存，再让Cocos重新生成，不改模型几何。309份网格缓存中修复2份，17份带形变的缓存保持原检查。五图正确性检查还会核实已载入网格的索引范围。

历史 `concept-2d-performance-v1-assets-repaired` 在原始CRP游戏／引擎代码上统一了修正资源；资源目录2793文件中，两份网格描述和配套清单变化，其他资源字节一致。来源及资源差异见 `repaired-reference-provenance.json` 和 `v1-v8-resource-diff.json`。后续静态模块审计发现，V1及V8仍是固定不动的三刃阵，V11已合入追击与守誓追斩；另有共享战斗逻辑更新。跨这些版本的差值包含玩法变更，不能全部归因于性能优化，已有报告保留为历史数据。

当前候选为Cocos原生构建的 `concept-2d-performance-v11`。最终管线对照改为隔离的当前工程副本：197份非生成脚本与V11逐字节一致，只在副本中将引擎模块从Legacy切回CRP，再由Cocos3.8.8构建。主工程Legacy策略和源码不变；该副本仅用于隔离管线开销，不是发布工程，也不把管线对照冒充所有优化的累计收益。构建、玩法模块、资源、原生图形及五图正确性均须复核后才能开始正式对照。跨场景回调保留旧地图的问题另有堆引用链与反复建销场景的证据。此前失败、未完成或旧预算下的报告不能替代新协议完整测量。

## 自动执行

复用已有 Cocos Creator 3.8.8、Playwright、Chrome 和规则测试依赖，不新增测试依赖。浏览器试验只在隔离的临时用户目录中写入测试存档。以下命令在仓库根目录执行：

```powershell
npm run check
npm test
pwsh -NoProfile -File src/cocos/Build-Local.ps1 -Platform web-mobile -OutputName concept-2d-performance-current
python src/cocos/tools/serve-web.py --port 7495 --directory src/cocos/build/concept-2d-performance-current
```

本机默认Creator用户目录曾反复在启动时出现 `UNKNOWN open engine.json`，未进入编译。可选传入 `-EditorUserData src/cocos/temp/creator-performance-cli-profile` 使用独立CLI用户目录；该路径沿用已有编辑器，不改引擎安装或渲染设置，构建仍须出现本次调用的完成日志并通过产物检查。

另一个终端执行：

```powershell
npm run test:perf -- --url http://127.0.0.1:7495/ --profile smoke --out src/cocos/test-results/performance/smoke
npm run test:perf -- --url http://127.0.0.1:7495/ --profile regression --out src/cocos/test-results/performance/candidate --baseline src/cocos/test-results/performance/baseline/report.json
npm run test:perf:soak -- --url http://127.0.0.1:7495/ --out src/cocos/test-results/performance/soak
```

首次建立基线时省略 `--baseline`，保留报告及整个构建；审核原始数据后显式将该报告作为后续 `--baseline` 输入。脚本不会自动覆盖或批准新基线。输出目录应每次唯一，原始帧间隔、截图和报告一起归档。只运行 smoke 不算完整性能验收。

默认是桌面Chrome＋横屏触控视口。使用 `--device iphone14` 可复用Playwright已有的iPhone14 UA进入Cocos实际移动端分支，并断言移动端CSM配置；报告记录UA、引擎移动标识和阴影尺寸。两种模式的基线不可混比。该选项仍运行于桌面Chrome／宿主GPU，不能仿真A15、iOS WebKit、真实TapTap容器或热降频。

| 配置 | 内容 | 计时窗口 | 重复 | 有效采样时长 |
| --- | --- | --- | --- | --- |
| smoke | U1-06 弓、火移动战斗 | 8秒 | 1轮 | 16秒 |
| regression | U1-06 静止、跑动、四职业原地战斗、四职业移动战斗；S13跑动 | 20秒 | 3轮，正反顺序 | 11分钟 |
| soak | U1-06 四职业移动战斗，反复进入真实新遭遇 | 30秒 | 10轮，正反顺序 | 20分钟 |

准备、资源预热、重建场景、强制 GC 和截图不计入帧耗时窗口；实际运行时间更长。soak 保持同一浏览器进程反复建销场景，用于泄漏及持续负载趋势，**不是同一存档连续20分钟战役，也不是手机热稳定结果**。

正常 `ChapterGame.update`、Cocos 渲染、Bullet、碰撞、敌人 AI、伤害、弹道、反馈及 HUD 均继续运行。浏览器外部输入脚本设定角色等级、职业和已看剧情等初始夹具，不修改敌人生命、伤害或游戏帧率，不使用无敌或无限资源。弓实际按下再释放；技能等待合法动作空隙再输入。移动、攻击、真实命中、技能释放和模拟时间都必须达到覆盖门槛，否则该窗口失败。初次定位可加 `--profile-cpu` 保存 CPU profile，另加 `--trace` 保存每窗口的Chrome主线程／合成／GPU／GC时间线及窗口时钟标记；丢失事件或标记会记为失败。诊断开销不可作为已批准的防劣化基线，也不能与未带同样仪器的数据混比。

## 指标与失败条件

最低滑动1秒帧率在绘制时间离开窗口的边界计算，包含下一次绘制前的低谷及超过1秒的无帧空窗；仅在新帧到达时计算会高估最低值。2026-11-12修正了该边界算法，保留原106个完整窗口及其原始报告，在 `android-gles-v5-*-windowfix` 中另存确定性重算结果。派生报告记录原报告、逐帧文件与分析脚本的SHA-256，以及未变更的采样脚本清单；其余采样代码必须逐字节匹配修正前快照。重算不是一次新的运行，失败记录继续保留，不能据此自动批准基线。

v6进一步记录真实采样起止、首末绘制偏移与实际绘制数量，检查首帧前和末帧后的空窗；最低1秒FPS不再截断于首末绘制之间。最长间隔及超过100ms的统计也包含首尾空窗。帧耗时分位数仍基于完整的相邻绘制间隔，平均FPS和主线程CPU/帧使用实际绘制数量。页面时钟覆盖须与外部计时相差不超过5%，缺失／不完整的时钟使窗口失败。原始时钟单独保存为 `*-frame-clock.json`。v5缺少这些边界信息，不能伪造边界重算为v6；已有失败继续保留，旧报告不作为v6基线。

v6的绘制调用与三角形改为每个完整帧间隔对应结束帧的序列，分别检查中位数和p95；首个绘制单独由时钟记录，不冒充一个完整帧间隔。原始序列保存为 `*-render-counters.json`，数量须与逐帧间隔严格对应。末帧快照继续记录供诊断。依据是同版WAR前20秒内单帧调用181–317、四次中位数197–198且p95为231–233；技能时相让单个末帧缺乏代表性。中位数及p95均沿用原绘制调用10%+5、三角形10%+1000的回退阈值，FPS／内存／CPU门槛不变。完整v5工具冻结在 `temp/performance-v5-frozen-before-series`，本次不是给历史失败改标成功。

原生条带继续使用Cocos `Line` 的几何、宽度、颜色和材质。针对3.8.8的生命周期适配见 `ManagedLine.ts`：释放自身模型、私有生成网格及材质实例，保留共享资源；未修改安装目录中的引擎。原始实现可核对 [Line](https://github.com/cocos/cocos-engine/blob/v3.8.8/cocos/particle/line.ts) 和 [LineModel](https://github.com/cocos/cocos-engine/blob/v3.8.8/cocos/particle/models/line-model.ts)。安卓实际运行检查覆盖6组原生／适配条带的顶点逐字节一致、销毁后的缓冲释放、无残留预热节点与原生图形日志；释放修复和材质预热的性能收益须另经完整回归与长测验证。

浏览器预览另使用 `BrowserPreviewFrameClock.ts` 适配3.8.8 Web Pacer。接近60Hz时，原生RAF正常而 `performance.now()` 分桶会重复时隙，导致部分回调未进入引擎更新；同页ABBA诊断中两段适配后均无额外丢帧。适配只把该Pacer的时钟原点映射到原生RAF时间戳，保留引擎自身限帧、取消和调度；不改全局RAF、游戏60帧设置或渲染质量。结构／函数签名不匹配时不安装，销毁时恢复；MINIGAME、NATIVE和EDITOR均直接跳过。该浏览器兼容修复不能作为TapTap小游戏容器已经修复掉帧的证据。依据：[3.8.8 Web Pacer](https://github.com/cocos/cocos-engine/blob/v3.8.8/pal/pacer/pacer-web.ts)、[HTML动画帧规范](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html)。

- 保留每帧间隔、FPS、p50/p95/p99、最长帧、超过 34.33ms/50ms/100ms 的计数，防止均值掩盖掉帧。34.33ms 为两帧 33.33ms 加 1ms 计时容差。
- CDP `Performance` 的 threadTicks `TaskDuration` 差值／真实渲染帧数为主线程 CPU ms/帧；专用浏览器所有进程的 CPU 秒增量另行累计。Android核实在窗口内出生的新进程从零累计；缺失尾部计数、无法核实出生时间或计数倒退均使该测量失败。
- **归一化CPU% × 逻辑核心数 = 核心当量CPU%**，再除100得到占用的核数。例如8核设备15%归一化占用＝120%核心当量＝1.2核。原始累计 CPU 秒已经包含各线程／核心，不能再乘核心数。主线程 ms/帧也不乘核心数。
- GPU 分配字节、模型数、逐帧绘制调用／三角形及GC后堆内存用于归因；绘制调用／三角形的末帧值另存为诊断快照。未测量 GPU 执行时间、物理功率或温度时，保留未测状态，不能用 CPU 代替功耗。
- 每窗口必须保留60帧设置、模拟时间≥墙钟85%、平均及最低滑动1秒FPS≥50、p99≤80ms、最长帧≤250ms、主线程CPU≤16.67ms/帧、观测进程内存峰值≤1000 MB。移动必须有实际位移及足够移动帧，战斗必须有命中和技能释放，弓必须确实发射。
- 同机同协议回归：CPU中位数增幅＞15%且超过噪声容差、p99增幅＞20%+2ms、长帧比例增加＞3个百分点、同用例累计超过100ms的帧比基线多出1次以上、FPS下降＞10%、提交数／三角形异常增加均失败。缺少用例、窗口、有效基线，或硬件／浏览器／实际画布／输入驱动不同，拒绝比较。
- soak：预热后保留堆增长＞12MiB、GPU分配增长＞8MiB、同职业最后3轮CPU中位数比前3轮增加＞20%+0.3ms，均失败。失败应先定位增长来源；禁止直接放宽门槛让报告变绿。

算法门槛由 `tests/performance.test.ts` 验证，纳入 `npm test`。报告记录 Git HEAD、实际已载入构建脚本哈希、浏览器／CPU／画布指纹、协议、输入脚本哈希和错误。不同提交允许比较，设备条件必须一致。报告中的桌面结果不能作为 TapTap 验收。

## 优化正确性用例

```powershell
npm run test:perf:world -- --reference http://127.0.0.1:7495/ --url http://127.0.0.1:7496/ --out src/cocos/test-results/performance/world-qa
```

两端分别提供优化前后构建。U1-06、S13、S02、旅店、H03各测试：3000个固定随机移动、障碍边缘±1e-8、不同角色半径、轴向滑动、后加障碍使快照失效。结果须与原 BoxCollider 实现逐值相同。每地图再用1200组普通／NPC视线及零长度射线检查复用对象没有改变查询结果。四职业×三种缩放×三个位置×普通／技能／终极瞄准的镜头坐标、旋转和高度须与旧构建逐值相同；保留S02发现镜头特例。加载结束后不得残留着色器预热节点。截图仅作画面复核，不能替代数值断言。

小地图雾层另在每张图的3种探索状态下，把保留池版本与引擎原始clear生成的顶点、索引逐字节比较，检查确实复用了原生Path/Point对象。小地图及顶部的首领／任务／出口文字提示已按用户要求移除，保留地图图形标记和原位的自动／挂机控件；历史参考构建仍检查稳定读数刷新不反复激活节点。该可选缓存只针对Cocos3.8.8 Web Graphics实现，内部保留上限为8192条路径／65536个点；原生或结构不匹配时执行普通clear。缓存上限不是平台限制，也不限制可绘制的地图内容。

## TapTap 真机完整验收矩阵

至少覆盖用户 iPhone 14、主目标 Android 中低端 ARM 真机。使用真实 AppID 下的测试包，记录版本及包体哈希，不能用安卓模拟器、游客网页或桌面 Chrome 替代。初始电量、亮度、音量、网络、画质、室温和充电状态一致；保持60帧目标，单窗口15分钟，先恢复到相同起始温度／电量，按 ABBA 各两次比较。电池健康和设备后台负载写入记录。

| 编号 | 操作 | 必须检查 |
| --- | --- | --- |
| DEV-01 | U1-06静止15分钟 | 稳态CPU／GPU可得指标、帧分布、内存、耗电、温度 |
| DEV-02 | U1-06正常跑动／绕障15分钟 | 初次指引和普通指引长帧、路径、碰撞、镜头；慢走再补一轮 |
| DEV-03 | 剑／弓／火／雷各原地普攻＋四槽技能15分钟 | 真实释放与命中、粒子／贴图预热、首用尖峰 |
| DEV-04 | 四职业各移动＋普攻＋技能15分钟 | 截图中的Lv15首领、真实8只增援、近战包围、远程弹道叠加；记录存活／击杀与输入录像 |
| DEV-05 | 从进入U1-06持续游玩30分钟，同一真实存档 | 后10分钟相对前10分钟帧率／CPU／内存趋势，热降频及资源累计 |
| DEV-06 | U1-06↔相邻区往返20次，再回U1-06战斗 | 首用／热缓存加载、贴图与模型释放、显存／进程内存是否回落 |
| DEV-07 | 战斗切后台3分钟，恢复10次；含锁屏与系统中断 | 后台无继续耗电计算／音频，恢复无大dt推进、无连发、资源和存档正确 |
| DEV-08 | U1-06战斗缩放／横屏安全区／手势同时操作 | 人物、怪物、预警与特效没有漏画；正常触控下复现长帧 |
| DEV-09 | S13首次移动与冷路线／热路线；S01、森林、地下过图 | 历史寻路、静态卡片剔除及资源复用不回退 |

温度记录外壳相同位置或系统热状态及测量工具；不能把不可得值填0。优先使用可归因到游戏的能量 mWh／功率积分；只有设备电池起止百分比时标注估算和电量分辨率，不能用系统“App用电占比”。所有物理设备结果必须带原始取数来源，CPU已按整机归一化时乘实际核心数；不确定口径时先核实工具定义。

复制 `src/cocos/tools/performance/device-template.json` 填写原始采样，再执行：

```powershell
npm run test:perf:device -- path/to/physical-device.json
```

此门禁拒绝空记录、少于15分钟、App用电占比、条件不一致或缺少ABBA重复。有效对照的耗电率增加＞5%、FPS下降＞5%或p99回退将失败。它只审查DEV-01至04结构化对照，DEV-05至09仍需附独立日志／视频／取数证据并人工验收。报告通过只说明未劣化；宣称降耗还必须由相同口径的有效下降数据支持。

## 触发与留档

修改主循环、物理、导航、角色动画、特效、HUD、地图组织、资源加载或渲染配置时，先运行规则＋smoke，再在固定机器运行regression。合入候选和发布前运行soak；涉及平台生命周期／渲染或新资源时执行对应真机矩阵。基线只由相同条件下已验收的版本产生；失败保留报告、帧明细、构建哈希及复现条件，不覆盖成成功。测试运行期间避免同时编译、录屏、CPU profile或其他重负载任务，记录无法避免的干扰并重测受影响窗口。

依据：[CDP Performance](https://chromedevtools.github.io/devtools-protocol/tot/Performance/)、[CDP进程CPU累计时间](https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/)、项目内Cocos3.8.8节点／碰撞接口定义。平台资源与生命周期验收沿用 `src/cocos/AGENTS.md`。

模拟器与管线依据：[Android模拟器命令行](https://developer.android.com/studio/run/emulator-commandline)、[Playwright AndroidDevice](https://playwright.dev/docs/api/class-androiddevice)、[Cocos3.8新旧渲染管线](https://docs.cocos.com/creator/3.8/manual/en/render-pipeline/overview.html)。

## 2026-11-12 V14执行记录

使用同一4核Android14模拟器、Chrome113、硬件GLES、关闭模拟器Vulkan、宿主P核亲和性21845及原始计时策略0/0。Web构建为0.3.27，游客交付包为自动递增后的0.3.28；199份跟踪脚本（其中2份为生成的资源表，197份业务脚本）打包前后逐字节一致。保留60帧设置与原画质。对照为当前相同玩法规则下的CRP构建，比较范围包含整个应用版本变化，不能把全部收益单独归因于管线、条带或时钟适配。

| 检查 | 33窗口回归 | 40窗口／20分钟长测 |
| --- | --- | --- |
| 观测进程内存峰值 | 566.65 MB | 559.18 MB |
| 最低窗口平均FPS | 56.28 | 55.43 |
| 最低滑动1秒FPS | 44，失败 | 46，失败 |
| 原生图形错误 | 0 | 0 |
| 结论 | 2个FPS失败窗口，另有末帧drawCalls 192→224回退 | 4个FPS失败窗口，其余CPU／内存趋势门槛通过 |

移动战斗WAR／BOW／FIR／THU的主线程CPU中位数较对照分别下降20.64%／18.93%／26.02%／30.22%；进程族核心当量分别下降7.31%／6.60%／18.70%／26.46%。后者已包含实际4核换算，不再重复乘核心数。长测预热后保留堆增长9.00 MiB、图形分配增长4.96 MiB、进程族PSS增长20.33 MiB，均在既定增长门槛内。

原始数据为 `src/cocos/test-results/performance/android-v14-{regression,soak}/report.json`，原始逐帧、截图、原生日志与失败记录保留。长测在帧率失败出现之后另执行了只读top／SurfaceFlinger列表取证，不能忽略这些观察操作的潜在开销；前面的失败窗口不由后续取证引起。当前没有批准的防劣化基线，不以均值达标覆盖最低FPS失败，也不放宽预算。

独立补充诊断 `near60-pacer-v14-extended/report.json` 覆盖四系共12×30秒：每段原生RAF回调数、引擎更新数与绘制数相同，额外跳帧均为0。两段WAR最低原生回调／绘制FPS分别49／49、47／47，最长回调空隙152.9ms；因此这些低谷已经出现在浏览器原生回调交付层。观察器未记录对应的≥50ms主线程长任务，但该数据没有单独记录API支持标记，不能据此排除所有脚本／渲染阻塞，也不能将剩余问题直接归咎于宿主。具体图形合成、调度或游戏渲染阻塞仍待定位。诊断不作为批准基线。原生图形日志无错误，诊断内存峰值553.89 MB。

本轮结束已核实恢复QEMU原亲和性16777215、原计时掩码0/0及专用AVD蓝牙原值1，再正常关闭本项目AVD；未终止其他Cocos进程或更改用户应用。

类型检查、139项既有及预算检查、31,126个碰撞查询以及视线／镜头／雾层一致性检查通过。小游戏编译产物中浏览器时钟安装器已静态裁为无操作，未向TapTap运行环境引入window／RAF依赖。交付记录见 `src/cocos/release/taptap-u1-06-performance-validation.json`；0.3.28游客包的本地转换、CRC、SHA-256及体积审计通过，未上传。完整ZIP 219,801,980字节；离线主包ZIP 1.29 MiB仅为本地测量，平台首包及可玩前下载量仍未测得。

## V16资源复用与v6协议验收记录

原生分配调用栈把持续创建缓冲定位到 `Effects.line` 的材质／Pass复制、`SkillFireSprites.sprite` 的五档尾焰网格切换，以及 `FlatActors.show` 的图集帧网格切换。代码改为原六类材质分组复用条带、每张尾焰卡片持有动态网格并仅在切档时更新原顶点，以及每个角色用独立 `tilingOffset` 采样原SpriteFrame区域。条带160、火焰卡片64的上限保持，原图、帧号、UV区域、几何拓扑、缩放与脚部锚点保持。动态网格复用的是Cocos官方 [Mesh.updateSubMesh](https://docs.cocos.com/creator/3.8/api/en/class/Mesh)／MeshUtils与3.8.8 `MeshRenderer.onGeometryChanged`，未另建渲染引擎或引入依赖。

原生正确性数据：`vfx-resources-v15-qa/report.json` 的条带活跃顶点逐字节一致、预热后材质重绑0、160容量借用及资源释放通过；尾焰五档的顶点／UV／索引相同，网格、SubModel与顶点缓冲身份稳定。动态AABB与静态计算的最大差异为2.78e-17，边界比较明确采用1e-12数值容差。`flat-uv-v16-qa/report.json` 覆盖9个模型、1616姿态，原主体／描边位置、法线、索引、缩放、锚点和实际渲染uniform通过；最大UV差5.96e-8，约0.000105纹理像素。`webgl-resource-v16-ready/actor-uniform-isolation.json` 另通过实际修改一个角色uniform、读取另一个角色uniform的隔离检查。

V15与V16的Cocos引擎二进制SHA-256相同；条带和尾焰两份业务源码也相同，因此上述V15原生几何／释放检查继续适用，V16补充角色UV检查。当前完整类型与140项检查通过。源边界为 `v16-source-boundary.json`：199份跟踪脚本／197份业务脚本，相对V14只改动三份呈现代码。

30秒带计数钩子的诊断中，V14→V16观测到WAR uniform-buffer分配1165→496、缓冲删除889→19；FIR分配697→130、删除580→8。已有条带材质重绑均降为0。真实战斗的命中／特效峰值会随帧时序变化，这些是版本级诊断计数，不能直接宣称相同比例的CPU或物理耗电下降。两段最低FPS为55／58。正式验收使用不带这些钩子的v6协议；旧失败与诊断报告不覆盖成成功。

本轮正式优化前对照选择冻结V14 Legacy，确保与V16的玩法、管线及预览时钟相同；先运行40×30秒soak，通过后采集33窗口V14对照与33窗口V16候选。仍要求平均与完整滑动1秒FPS≥50、800MB目标／1000MB硬上限及原CPU回退门槛。开始前冷启动专用AVD并记录进程创建时间，避免诊断跟踪与压力夹具的残留；环境重置不计为代码收益。任一硬门槛失败即保留原始数据，不批准基线。

首轮v6采样在雷法窗口因采样器错误地要求三角形统计为整数而中止，前三个完整窗口最低57／58／58FPS。原始序列与失败报告保留在 `android-v6-v16-soak/`；Cocos3.8.8 `webgl2-primary-command-buffer.ts` 对TRIANGLES直接累加 `indexCount / 3`，原始计数包含198780.33333333334。采样器已保留该有限非负原值，绘制调用数继续要求整数；未舍入计数、改动游戏几何或放宽任何性能预算。140项检查及类型检查再次通过，修正后采样器哈希为 `181365cbcfea366fa143506ba74f713eb12b1e0bd1567a1698d06e55846278b1`，完整验收另写 `android-v6b-v16-*`，不会混用旧哈希数据。

0.3.29游客包已完成官方转换、本地体积／CRC／SHA-256检查，完整ZIP 219,802,464字节，离线主包ZIP 1,352,985字节；199份跟踪脚本与V16构建边界一致。包体位于 `artifacts/taptap-u1-performance-v16/`，未上传。

2026-11-13完成 `android-v6b-v16-*` 全序列：候选40×30秒长测全部通过，最低完整滑动1秒57FPS，全过程PSS峰值548.78208MB；保留堆／图形／PSS增长分别8.65／3.45／40.85MiB，后期CPU变化及原生图形检查通过。随后同一AVD中的33窗口优化前对照保留两处低帧失败，完整性检查通过；33窗口候选回归出现5个低帧窗口：首轮idle39、run1，第二轮moving-BOW47，第三轮stationary-WAR25、stationary-BOW4FPS。最长绘制间隔989.6ms；全过程PSS峰值566.29248MB。CPU、进程内存及时间序列绘制调用／三角形数相对回退检查通过，但FPS、单帧与重复长停顿门槛失败，**不批准防劣化基线**。汇总在 `v16-v6-acceptance-summary.json`，逐帧、完整窗口时钟、逐帧渲染计数及全部失败保留。

在相同已持续运行的AVD中补做无Cocos／无游戏逻辑的原生WebGL2空画面对照，按system-managed／honor／honor／system-managed执行四段30秒。四段最低1秒均59FPS，最大间隔20.1–20.4ms，无longtask，未发现只改该模拟器进程计时策略的收益；原计时策略0/0已恢复。该诊断不证明游戏长停顿来自环境，下一步记录混合场景的原生回调、主线程和GPU阶段。报告 `empty-gles-timer-v16/report.json` 不作验收基线。
