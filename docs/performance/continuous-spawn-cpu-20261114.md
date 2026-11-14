# 连续刷怪 CPU 定位与分配／渲染提交优化（2026-11-14）

用户确认原问题发生在**手机 TapTap 小游戏 0.3.39**，随后明确要求本阶段先在 Android 模拟器优化，暂不处理手机版本。本轮对当前源码重新构建，使用现有 Android 14 专用模拟器定位与验收；以下数字不能替代手机的 CPU、GPU、功耗或温度结论。保留 WebGL 2、Legacy forward、60 FPS 设置、分辨率、怪物数量、攻击规则与原画。

## CPU 时间花在哪里

在当前构建上分别采集 30 秒的 20 怪训练战斗和 H12 弓系连续移动战斗。原生训练夹具每 6 秒重置一波，不能替代野外自然刷新；H12 使用现有 `farm-driver.cjs` 的正常移动、普攻和技能输入。

V8 采样按调用栈归属，保留 idle、未归因 VM 和垃圾回收样本。表中是抽样估算的包含子调用时间，兄弟项可比较，父子项不能重复相加；不是函数的精确 CPU 计时。

| 主线程阶段 | 20 怪训练，约 ms/帧 | H12 走打，约 ms/帧 |
| --- | ---: | ---: |
| Cocos `Root.frameMove` 渲染阶段 | 1.007 | 1.215 |
| `GameSession.advance` 规则推进 | 0.428 | 0.389 |
| `Player3DActors.update` 角色呈现 | 0.242 | 0.166 |
| `Hud.update` 界面数据更新 | 0.145 | 0.205 |
| `Effects.update` 特效呈现 | 0.118 | 0.084 |
| `EnemyCombatFeedback.update` 血条／浮字更新 | 0.117 | 0.061 |
| 垃圾回收抽样 | 0.167 | 0.366 |

渲染阶段内，H12 的 `UI.update` 约 0.314 ms/帧，`ForwardStage.render` 约 0.423 ms/帧，`ShadowFlow.render` 约 0.088 ms/帧。UI 遍历、材质／缓冲绑定和绘制命令提交仍是重点，不能将所有 CPU 占用归结为刷怪 AI 或血条规则。

H12 的线程快照中，`CrRendererMain` 约 20.64% 单核，`CrGpuMain` 约 20.29%，`CompositorGpuTh` 约 5.61%；100% 表示一个 CPU 核心。这些是模拟器 Chrome 的 **CPU** 线程统计，包含图形命令与合成，不能称作硬件 GPU 利用率。采样窗口与进程快照边界不同，不将上述线程百分比直接相加替代进程计数。

H12 带分析器诊断出现平均 54.57 FPS、最低完整滑动一秒 42 FPS；明确保留为诊断结果，不能用它通过帧率回归。正式回归不挂分析器。

证据位于 `src/cocos/test-results/performance/`：

- `cpu-current-training-profile-v2-20261114/`：训练调用栈、实际加载脚本、`attribution.json` 与 `cpu-summary.json`。
- `cpu-moving-profile-current-20261114/`：野外调用栈、原生线程前后快照、逐帧计数、实际加载脚本与 `attribution.json`。引擎语义名以已安装 3.8.8 方法的完整函数代码匹配，非凭压缩后的短变量名猜测。

## 本轮代码改动与边界

`FlatActors.frame` 原本已缓存 SpriteFrame 和网格，但每次调用仍重新解析图集名、行列、裁切矩形、原点与缩放，并分配返回对象。血条的 `enemyHeadPoint` 每个可见怪物每帧都走这一流程，默认还创建头部定位用不到的 UV 网格。

复用现有 SpriteFrame／Mesh 缓存，进一步按本场景已加载的不可变 action、方向、帧序号缓存精确采样结果。普通四边形与确需 UV 网格的调用分别保留结果，后者仍按原路径懒创建网格。头部和肖像的元数据查询不再请求网格。缓存随所属 FlatAsset／场景释放，未按时间或敌人 ID 无限积累；动画时钟、实时位置、朝向、反应和投影仍按原帧更新。

怪物血条的边框、背景、当前血量与延迟扣血仍由代码绘制。死亡淡出保留的矩形填充使用引擎自带白色纹理，无新增血条图片；这里缓存的是怪物图集定位数据。

**整体 CPU 收益未被证实。** 同一进程按 A-B-B-A 各 60 秒连续战斗，四段分别为 54.20%、52.91%、53.63%、52.92% 单核。按实测时间／帧数汇总：

| 指标 | 原版 | 缓存候选 |
| --- | ---: | ---: |
| Chrome 进程族 CPU，100%=1 核 | 53.564% | 53.271% |
| 主线程 ms/帧 | 2.6340 | 2.6107 |
| 绘制帧 | 7,200 | 7,200 |
| 实际技能释放／命中事件 | 40／140 | 40／140 |

CPU 观测差约 -0.55%、主线程约 -0.88%，小于原版两段之间的漂移；不能据此宣称稳定整体降耗，更不能换算手机降温。保留本改动的依据限于消除已确认的重复解析／分配与无用网格、且输出精确一致。没有减少绘制次数或 GPU 执行工作量的证据。

`flat-frame-cache-abba-v1/` 保存完整四窗口、事件、逐帧数据和 `comparison.json`。测试过程未改帧率、隐藏 HUD、冻结玩法或减少怪物／投射物；每段实际释放、命中、投射物和受击事件完全相同。未观测到 Creator 构建日志内容变化。

## 后续对象分配定位与循环减负

另用 32 KiB 间隔的 V8 分配采样，明确包含已被 minor／major GC 回收的对象。H12 30 秒走打估算累计分配 458.43 MiB；这是统计估算的**累计临时分配量**，不是常驻增长或内存泄漏。按脚本模块与调用栈归属，Terrain 约 35.0 MB、FlatWorldLayers 约 25.1 MB。Graphics 雾边缘重建也有较大分配，本轮没有改其羽化／混合算法。

实际 Creator 编译代码中，数组 `for...of` 被转译为迭代器帮助函数，为每次循环创建局部函数和返回对象。高度查询被角色、碰撞、视线和特效高频调用；环境遮挡循环还会遍历当前区域的卡片。这些临时对象不改变游戏内容，却增加分配和回收压力。

- `Terrain.height` 的数组循环改为相同顺序的索引循环；坡道累计值保留原运算顺序，岸坡函数移到模块级。97 区域的 106,270 个随机／岸坡／桥面／坡道边界点逐一 `Object.is` 相同，包含有符号零。实际编译的 H12 另有 1,000 点对照通过。见 `terrain-height-equivalence-20261114.json`。
- `FlatWorldLayers.update` 与常用分组剔除循环去除数组迭代器；遮挡差向量使用实例内暂存，卡片偏移向量仅在相机旋转确需重排时创建。卡片集合、遍历顺序、剔除条件、材质、透明度与绘制内容保持原逻辑。
- 实际编译的两项循环改动已完成 6 组相机角度原生对照，755 个卡片、182 个分组的逐项变换／显隐／遮挡状态和绘制计数一致；每组 2,778,624 像素，最大差异均为 1 色阶，无大于 3 色阶的像素。见 `allocations-loops-native-qa-v2/`。V1 为隔离诊断加载器漏回传模块导出值而失败，修正只在忽略的临时诊断脚本中，未加入游戏。
- 首组真实编译函数的固定 100,000 次高度查询，A-B-B-A 原版 27.6／36.8 ms，候选 5.3／6.5 ms，校验和相同。但最终构建的反向函数替换诊断中，已在真实游戏中运行的新函数约 23 ms，隔离加载的旧函数约 9 ms，方向相反。两者的 JIT 历史／输入对象形态未受控，因此**这些微基准时间不作为稳健 CPU 收益依据**，也不换算完整游戏收益；保留所有原始数值。
- `terrain-height-moving-abba-v2/` 的整进程对照与一次 TypeScript 检查重叠，已终止并标为 `invalid-concurrent-typecheck`，不引用其 CPU 差额。V1 为诊断模块依赖解析失败，同样保留失败记录。

相同 H12 夹具分别采集 30 秒分配，按绘制帧归一后的累计估算分配由 267,349 降至 243,018 字节/帧，约少 **9.1%**。Terrain 归属由约 35.01 MB 降至 5.67 MB，FlatWorldLayers 由约 25.08 MB 降至 0.098 MB。两窗口帧数为 1,798／1,801，击杀为 9／10，不能将采样估算当作精确字节计数，也不能将分配降幅换算成 CPU 降幅。

无分析器、真实持续走打的同进程 A-B-B-A 中，两项循环候选与原版按时长汇总 CPU 为 68.769%／66.008% 单核，按帧数汇总主线程为 3.139／3.198 ms/帧；候选命中／击杀 177／34，原版 170／31。主线程观测约少 1.85%，但小于原版前后约 4.1% 的主线程漂移，且整进程 CPU 反而较高约 4.18%。因此仍**没有稳定的完整进程 CPU 降幅结论**；不能忽略图形线程开销或自然战斗量差异，只报主线程小幅差额。两项普通代码改动保留的依据为局部计算／临时分配减少、精确结果／原生画面一致，完整目标尚未达到。

证据：`cpu-moving-allocations-{current,final}-20261114/` 的 heapprofile、加载脚本与 `attribution.json`，`allocation-loop-comparison-20261114.json`，以及 `allocations-loops-moving-abba-v1/` 的四个完整窗口、`comparison.json` 与无并行 Creator 构建记录。前一阶段帧采样缓存的五分钟结果不挪作最终三文件候选的验收。

## 正确性与回归

- 原型及实际 Creator 编译候选均通过本夹具加载的近战／盾兵／远程三种怪物的 156 组采样元数据、156 组网格引用、80 组头部位置对照；不扩大为全部角色画面验收。
- 两组完整固定画面均为 2,778,624 像素，最大像素差为 0；绘制计数一致，无原生图形错误。见 `flat-frame-cache-qa-v1/`、`flat-frame-cache-compiled-qa-v1/`。
- 完整 TypeScript、核心 TypeScript、现有 140 项测试和 Creator Web 构建通过；未新增测试依赖或常驻测试框架。
- 实际编译候选的 H12／Lv17／BOW 300 秒连续走打回归通过：平均 59.866 FPS、最低完整滑动一秒 57 FPS、P99 22.3 ms，实测移动 1,019.46 米、击杀 87、自然刷新 80、真实技能释放 85，角色持续存活。全过程 Chrome 进程族 PSS 峰值 512.48 MB，测量窗口峰值 505.39 MB，301 次窗口内存观测，无原生图形错误或并行 Creator 构建干扰。
- 该五分钟窗口主线程为 3.305 ms/帧、进程族 CPU 为 65.364% 单核。没有同协议配对的五分钟原版窗口，因此只作功能／帧率／内存回归，不用来计算 CPU 优化比例。完整数据见 `flat-frame-cache-moving-300s-v1/`。
- 最终三文件候选另跑 `allocations-loops-final-moving-300s-v1/`：平均 58.604 FPS、最低一秒 48 FPS、P99 30.6 ms，因最低一秒低于 50 而失败；主线程 3.278 ms/帧、CPU 63.001% 单核，峰值 PSS 537.56 MB、移动 999.80 米、击杀 81、自然刷新 75，玩法／内存／图形检查通过。保留失败，尚不能批准最终五分钟结果。原版与候选均保持 TSC、亲和性 21845、WebGL 2 和 60 FPS 设置。
- 该失败的低帧窗口约在第 282 秒，WDDM GPU 计数采集在第 81.308～111.718 秒，两者不重叠，不能将其归因于 GPU 计数采样。逐帧归因见同目录 `low-fps-attribution.json`；在同一模拟器追加对照版与候选版复核，不在取得证据前自行宣称环境原因。
- 随后的同模拟器对照版 60 秒走打 `allocations-loops-late-control-smoke-v1/` 通过，平均 59.948 FPS、最低一秒 57 FPS、P99 22.5 ms；该时段未复现对照版本身持续退化。最终候选再做独立 300 秒无附加采样复核，结果另录，不能用短对照通过覆盖长候选失败。
- 无附加采样的最终候选第二次 300 秒 `allocations-loops-final-moving-300s-v2/` 平均 58.547 FPS、最低一秒 50 FPS，绝对预算通过；P99 30.5 ms，主线程 3.281 ms/帧、进程族 CPU 63.814% 单核，全过程峰值 PSS 524.15 MB、测量窗口峰值 500.26 MB。实际移动 1,028.96 米、击杀 85、自然刷新 77、技能释放 84，角色存活，无图形错误或 Creator 构建干扰。
- 与前一阶段五分钟报告的环境指纹、测量协议和 farm harness 哈希全部相同，复用现有 `metrics.compare` 后仍报 **P99 22.3→30.5 ms 回退**。所以第二次绝对预算通过并不等于相对回归通过，**不批准最终性能基线**。机器可读结论见该目录 `reference-comparison.json`。
- `allocations-raf-reverse-diagnostic-v1/` 在最终构建中只观察原生 RAF，并反向切换旧／新循环函数，没有修改帧率或 pacer。两种函数均存在 RAF 已回调但没有新增 Cocos 绘制的帧，提示预览帧调度／门控因素；但不足以证明全部五分钟 P99 回退与循环改动无关，也不解除失败。计数与边界见 `raf-summary.json`，后续继续查帧调度及图形提交，不重新引入已撤回的浏览器帧时钟桥接。

## 预览帧调度与渲染提交补充定位

通过公开的 `game.pause()` / `game.resume()` 在原生 RAF 后不同延迟恢复，保持同一源码、相同 60 FPS 设置和实际 H12 走打，仅改变恢复时刻。对照版六个 10 秒诊断窗口的 P99 为 27.7～34.3 ms，最终三文件版为 23.7～29.0 ms；对照版本身能够出现与先前候选相同或更差的帧间隔。这里不是 CPU 验收或优化收益，不从中挑一个好相位替代默认验收。

原生 RAF 观察器在恢复后排于引擎回调之前。除每窗口第一对缺少前序帧边界外，所有“已有 RAF、没有新增 Cocos 绘制”都对应前一个观察点满足 `floor((now-start)/frameTime)<frameCount`，与已安装 3.8.8 Web Pacer 的原生跳帧门控一致。对照版共 120 个可判定跳帧、候选共 34 个，逐点判断保存于 `pacer-phase-sweep-{control,final}-v1/gate-summary.json`，原始回调亦保留。先前用当前点而非前一个点判断的临时摘要已纠正；第一对每窗仍单列，未强行归因。

这表明跨启动的 P99 差异受原生预览调度相位影响，不能直接证明循环优化造成全部回退；原始失败和未批准结论继续保留。没有修改 Pacer、帧率或计时源，也没有重新引入浏览器帧时钟桥接。

`render-submit-census-v1/` 在冻结的真实 H12 画面透明计数 10 个渲染帧：每帧 158 次 draw，其中 UI 精灵／文字 63 次、Graphics 31 次、特效 Ribbon 11 次。计数期间仅包装并原样调用 WebGL 实例函数，结束后恢复；不使用包装下的计时证明 CPU 收益，也不当作所有战斗状态的平均绘制量。

使用原生 Label 的 `CacheMode.BITMAP` 只缓存罗盘四个不变的 N/E/S/W 字形，让其参与原生动态图集合批；字体、SHRINK、轮廓、位置和朝向继续按原逻辑。`ui-batch-trial-v1/` 同帧由 158 降至 154 draw，三角形计数相同；2,778,624 像素最大差异 1，无大于 3 色阶差异。还尝试了全量文字／白色填充入图集，只作诊断，没有采用：动态文字会反复占用图集，白色填充在该顺序下没有额外收益。

## 寻路查询减负与后续候选

分配采样中 Navigation 归属约 29.96 MB/30 秒。复用已有实现做三项局部调整，没有引入新的寻路库或改变算法：`visible` 直接向现有 `blockedAt` 传坐标，取消每 18 厘米一个临时 Point；碰撞扫描的数组循环取消转译后的迭代器／临时闭包；A* 邻居只复用一个不逃逸的坐标对象，新发现的搜索节点仍独立保存坐标。采样间距、严格碰撞不等式、邻居顺序、分数比较、迭代上限和路线简化顺序保持原值。

场景寻路与探索视线的障碍物在重建前保持不变，启用项目原已用于移动碰撞的空间索引。索引只是缩小候选集，仍使用原矩形判断；不足 8 个障碍物、非有限数值或负半径沿用完整扫描。场景／探索布局变化时继续重建 Navigation，未按敌人、帧或位置无限缓存。

`navigation-allocation-equivalence-20261114.json` 覆盖 97 区域，以原版未索引查询分别对照两种候选模式：280,112 次碰撞、46,560 次视线、96 组冷／缓存路径全部一致。`navigation-cache-moving-abba-v2/` 另在真实 Cocos 编译结果中比较 3,648 项，含 H12 内容定义、场景附加碰撞与探索遮挡，零差异；实际场景查询障碍物为 21，探索遮挡为 3，后者按原阈值完整扫描。V1 因临时提取包尚未生成而加载失败，未进入计时，保留失败记录。

完整 TypeScript、核心检查和现有 140 测试再次通过。新 Web 产物为 `perf-cpu-navigation-20261114`。第一次 CLI 启动因宿主日志管道 EPIPE 异常未形成构建，已验证进程身份并停止该任务；独立日志重跑完成（Creator Finished，退出码 36），没有在其运行时进行 CPU 验收。未创建新的预览端口，复用原任务已有的本地 HTTP 服务读取候选产物。

罗盘缓存单独的 H12 A-B-B-A 各 60 秒对照，原版／候选 CPU 为 73.529%／74.005% 单核，主线程 3.227／3.273 ms/帧，击杀同为 34，命中 174／172。没有整体 CPU 降幅证据；固定画面的 4 次 draw 减少不换算成 CPU 百分比。见 `compass-cache-moving-abba-v1/comparison.json`。导航加缓存候选的真实连续战斗对照和最终完整构建回归另录，不用早期三文件结果替代。

导航加缓存的同进程四窗口 `navigation-cache-moving-abba-v2/` 均约 59.93～59.96 FPS，P99 24.2～24.6 ms。汇总原版／候选 CPU 为 82.301%／79.097% 单核，主线程 3.179／3.077 ms/帧；候选表面上约少 3.9% CPU、3.2% 主线程，但原版前后主线程由 3.383 降至 2.975 ms/帧（约 12.1% 漂移），且命中 170／160、击杀 31／33。因此**仍未证实稳定整体 CPU 收益**，不能把候选窗口数值直接当作最终优化百分比。逐窗与加权汇总见该目录 `comparison.json`。

完整新构建的首轮五分钟入口发现两条 404：直接 Creator CLI 构建未运行既有 `copy-branding.cjs`，缺少 index 配置的 favicon/web icon。已提前停止并标为 `aborted-missing-web-branding`，不批准性能结果；补跑现有图标复制步骤后用独立 V2 目录重新计时，加载日志不再出现该错误。游戏源码／规则／测量工具均未因这次修复改变。

`navigation-cache-final-moving-300s-v2/` 的完整新构建五分钟绝对预算通过：58.547 FPS、最低一秒 51 FPS、P99 29.4 ms、主线程 3.239 ms/帧、CPU 73.001% 单核（4 核归一为 18.250%），全过程 PSS 峰值 518.93 MB。移动 1,037.54 米，击杀 83、自然刷新 74，角色存活，无控制中断／图形／加载错误，无并行 Creator 构建。**不能据此批准相对基线**：早先报告使用 farm-routine，本次使用 farm-regression，尽管两者脚本计划同为 300 秒×1、除 soak 外执行代码相同，现有严格比较仍因 profile 标签拒绝；保留此拒绝，不改写原报告。且 P99 29.4 ms 仍高于前一阶段参考 22.3 ms 的 20%+2ms 阈值（28.76ms），未解除已记录的预览节奏问题。见 `reference-comparison.json`。

`cpu-moving-allocations-navigation-20261114/` 重新进行 30 秒统计采样：估算 426,798,952 字节／1,788 绘制帧，即 238,702 字节/帧。较缓存阶段的 267,349 约少 10.7%，较三文件循环阶段的 243,018 约少 1.8%。Navigation 归属由三文件阶段的 29.96 MB 降至 26.45 MB；两窗口技能释放同为 8、自然刷新同为 4，击杀 10／9，采样误差和战斗量差异均保留。不是常驻内存降幅或 CPU 百分比，见 `allocation-navigation-comparison-20261114.json`。

本次诊断原生线程快照中 `CrRendererMain` 约 20.81% 单核，与早先 20.64% 接近，而 `CrGpuMain` 约 33.58%，高于早先 20.29%。两次不同窗口不能直接作优化对照，但说明整体 CPU 波动并不全在玩法／主线程；继续定位原生图形命令／模拟器提交工作，而非把主线程微优化外推成总体 CPU 收益。

## 模拟器 GPU 与后续手机验证

当前 WebGL 2 环境不提供 `EXT_disjoint_timer_query_webgl2`，没有 Android 来宾渲染帧／具体绘制的 GPU timer 数据。另按用户的模拟器范围，使用 Windows WDDM `GPU Engine` 的 `Timer100Ns` 计数器，只筛选本任务 qemu PID 30532。在最终候选真实 H12 走打内取得 31 次一秒观测、30.410 秒跨度：RTX 3080 的该进程 3D 引擎累计忙碌 3.640 秒，平均 **11.971%**，一秒区间约 7.98%～15.08%；其他引擎区间增量为 0。该窗口没有宿主 GPU 饱和证据，CPU 图形命令线程仍值得继续定位。

这是**宿主硬件、归属 qemu 进程的引擎忙碌度**，包含模拟器／Android 合成，既不是手机 GPU 占用，也不是游戏每个绘制的 GPU 时间；不把用户桌面视频的 GPU 占用合计进来，不据此宣称 GPU 优化降幅。原始实例、计数类型、计时值与逐秒观测见 `owned-avd-gpu-20261114.json`。计算采用 `100×ΔRawValue/ΔTimestamp100NSec`，本机实际计数类型为 542180608（[Microsoft Timer100Ns 定义](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.performancecountertype)）；采集使用公开的 [Get-Counter](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-counter)。该只读 31 次宿主采样与最终五分钟回归的中段重叠，CPU 回归未挂 V8／原生分析器。

本阶段继续以模拟器的图形提交与完整进程 CPU 为重点，用户已暂缓手机版本处理。将来回到手机验收时，按 [TapTap 官方性能测试流程](https://developer.taptap.cn/minigameapidoc/dev/tutorial/performance/performance-test/)采集：iOS 可在 macOS Instruments 中观察小游戏的 `com.apple.WebKit.WebContent` 进程；Android 使用测试包的开发调试性能信息，并结合可取得的原生跟踪。官方列出的 iOS 日志面板提供 FPS，不能假定它也提供 CPU 或 GPU 调用栈。当前目标仍保持未完成，未宣称手机降温。

引擎依据：[Cocos UI 合批规则](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-batch.html)、项目已安装 3.8.8 的 SpriteFrame、Mesh、Node 和渲染实现。本轮不新增依赖或引擎私有接口适配，也未制作、上传新的 TapTap 包。

## 按组件开关定位与卷发减面

按用户要求，在模拟器真实 H12 连续走打中分别保留／隐藏组件，采用 A-B-B-A 各 30 秒、切换后留 6 秒稳定期。这里只将隐藏组件作为定位手段，计时窗口没有截图或分析器。

| 隐藏组件 | 保留时主线程 ms/帧 | 隐藏时主线程 ms/帧 | 定位含义 |
| --- | ---: | ---: | --- |
| 卷发 | 3.239 | 3.062 | 主线程净差约 5.5%；原卷发 18,366 三角形 |
| 主角全部渲染器 | 3.193 | 2.864 | 包含卷发，不能与卷发差值相加 |
| 特效根节点 | 3.173 | 3.069 | 命中数 97／73，战斗量有混杂 |
| HUD | 3.139 | 2.527 | 主线程影响较明显，绘制约 149→63 次 |

原始记录：`hair-component-ablation-moving-v1/`、`render-component-ablation-moving-v1/`。整进程 CPU 前后控制窗漂移较大，WDDM qemu GPU 忙碌度也无稳定差异；不能把上述主线程差值当作隐藏后的整体 CPU／硬件 GPU 降幅，更不能当作最终减面收益。卷发开关的固定画面为 141→139 draw、139,294→102,562 三角形，头发在主画面与阴影各绘制一次。

原生图形命令跟踪显示较多 BufferSubData 提交。后续逐缓冲只读计数确认，多个 12,288 字节上传属于角色部件的蒙皮 uniform 缓冲，包含卷发；此前关于这些大上传来自线条顶点缓冲的猜测不成立。跟踪命令跨度包含驱动等待，不是纯线程 CPU 或硬件 GPU 时间。证据保留于 `native-gpu-decoder-trace-v1/command-spans.json` 与 `buffer-upload-census-v1/`，不改引擎私有蒙皮容量。

曾试验原生骨骼挂点加普通 MeshRenderer，用户随后明确希望头发本身简单一些，因此已将 `HairstyleGeometry.ts` 与 `CharacterPreview.ts` 恢复到试验前内容，挂点试验不进入本轮实现。

本轮复用已安装 Blender 4.5.15 LTS 与项目已有的 Decimate Collapse/Triangulate 流程，把默认卷发由 **18,366 减为 4,500 三角形（减少 75.5%）**，顶点 14,193→4,300，GLB 982,620→274,880 字节（减少 72.0%）。Blender 负责减面，适配脚本只重新打包几何；原节点、共享骨骼顺序、逆绑定矩阵、材质、网格名与 Head 权重保持原值。模型边界最大变化约 0.21 毫米；资源 `.meta` 的 UUID 不变，仅由 Creator 更新 triangleCount。减面方法依据 [Blender 官方 Decimate 文档](https://docs.blender.org/manual/en/5.0/modeling/modifiers/generate/decimate.html)。

完整原模型、几何报告与复现说明保留在 `source-art/characters/3d-hair-lod-v1/`，减面适配器为 `tools/model-pipeline/simplify_rigid_hair.py`。新 Creator Web 编译 `perf-render-hair-lod-20261114` Finished、退出码 36，并补跑既有品牌图标复制步骤。运行时仍使用原生 SkinnedMeshRenderer，维持 60 FPS、原材质与阴影设置。

新旧 Web 构建的 `src/**/*.js` 与 `cocos-js/**/*.js` 分别 3／6 个文件，SHA-256 清单完全一致。几何校验确认节点、骨骼、材质、场景、逆绑定矩阵不变，各浮点属性有限。固定真实场景以公开 `Mesh.reset` 重建原编译网格并切换 renderer.mesh：同姿势 147 draw 不变，139,156→111,424 三角形；换回原网格，头部 ROI 13,560 像素逐像素完全恢复。简化版该 ROI 平均绝对 RGB 差约 0.282，418 像素有大于 3 色阶差异，不能以此代替近景美术检查。

`hair-lod-moving-abba-v1/` 在近景截图之后运行 A-B-B-A 各 45 秒，原版／简化版加权主线程 3.980／3.987 ms/帧，整进程 CPU 97.844%／98.139% 单核，**没有整体收益证据**。但两版仅约 35～37 FPS，低于此前约 60 FPS，另原网格跨预览克隆时未显式持有 ref，后续已补持有／有效性断言，因此本轮不作性能验收。原记录不改，`comparison.json` 单列 `approved:false`；原网格释放故障并未实际观察确认，不将其当作已证实原因。

另起无截图／无预览的计时流程 `hair-lod-moving-abba-v2/`，仍确认原生 frameRate=60。其首窗与工作区另一轮 `perf-navigation-heap-20261114` Creator 构建重叠（15:10:02 完成），最低一秒 2 FPS，属于受干扰窗口，不能解释为头发减面回归或收益。同步观察构建日志的拒绝结果保留，不停止／覆盖其他任务改动；不挑选受干扰报告中的某个好窗口作为最终批准。

最终独立画面检查 `hair-lod-neutral-qa-v1/` 完成 3 个真实游戏姿势×原／简化／恢复共 9 张，以及原生烘焙动画头像 4 个方向×两种网格共 8 张，零脚本／图形错误。头像原灯光会过曝，诊断中只将两版头像各点光源设为相同的 2% 光通量来显露网格细节，没有改游戏源码／实际灯光配置。已实际查看多方向近景与游戏裁切图：发际线、鬓角、后脑整体卷发轮廓保留，细纹有简化，近看少量棱角可接受，未见明显破洞或穿头。三种游戏姿势恢复原网格的头部 ROI 均逐像素一致，每次简化均少 27,732 三角形、draw 数不变。

**保留这版默认卷发减面，几何与本地视觉检查通过；整体 CPU/GPU 性能收益仍未批准。** 完整记录分别见 [几何报告](../../source-art/characters/3d-hair-lod-v1/geometry-report.json)、[视觉检查](../../source-art/characters/3d-hair-lod-v1/art-review.json)、[近景对比](../../source-art/characters/3d-hair-lod-v1/head-comparison.jpg) 与 [游戏姿势对比](../../source-art/characters/3d-hair-lod-v1/game-comparison.jpg)。当前未打新 TapTap 包，平台与手机表现待后续验证；CPU/GPU 排查目标继续保持未完成。

## 其余三款可选发型

用户续要求“其他的也一样”，沿用已验证的 Blender 减面适配器处理 Dante／Nero／Vergil，各保留约四分之一三角形：

| 发型 | 三角形原版 → 简化版 | 顶点原版 → 简化版 | GLB 字节原版 → 简化版 |
| --- | ---: | ---: | ---: |
| Dante | 10,796 → 2,700 | 9,159 → 2,901 | 630,012 → 191,336 |
| Nero | 6,452 → 1,600 | 4,814 → 1,509 | 351,936 → 112,344 |
| Vergil | 8,434 → 2,100 | 6,303 → 1,930 | 453,152 → 137,244 |

逐个确认节点、骨骼顺序、逆绑定矩阵、材质、场景一致，浮点属性有限；模型边界最大变化分别约 0.38／0.36／0.21 毫米。原始高模另存源素材目录，几何报告按发型单列。Creator 只更新各 `.meta` 的 triangleCount，UUID 与其他导入选项不变。

首次多发型 QA 在旧 `navigation-candidate` 上切换第一个发型时，尚未加载新减面候选，便触发原有的蒙皮局部描述符空引用。原因是 `HairstyleGeometry.destroy` 手动先清 skeleton／skinningRoot，再清 sharedMaterials，后者重建材质时依赖仍有效的蒙皮描述符。最小修复为禁用 renderer 后调用其标准 `destroy()`，由 Cocos 原生 onDestroy 统一注销动画与模型，再按原逻辑释放本类持有的 Asset 引用；没有修改挂点、动画模式或引擎内部代码。首轮失败原样保留于 `all-hair-lod-neutral-qa-v1/`。

修复后 Creator 构建 `perf-render-all-hair-lod-v2-20261114` Finished、退出码 36，补跑既有品牌图标复制。`all-hair-lod-neutral-qa-v2/` 实际通过三款切换、每款 3 个游戏姿势×原／简化／恢复共 27 张、每款 4 个烘焙动画头像方向×原／简化共 24 张；零脚本／图形错误。实际查看三款四方向近景与游戏裁切图：保留刘海、发际线、鬓角与后脑轮廓，细节略减、近看少量棱角可接受，未见明显破洞、穿头或脱离。9 组恢复原网格的头部 ROI 都逐像素一致；Dante／Nero／Vergil 含阴影分别少绘制 16,192／9,704／12,668 三角形，draw 数不变。

**三款减面与本地视觉检查通过并保留。** [检查记录](../../source-art/characters/3d-hair-lod-v1/other-art-review.json) 与 [游戏对比](../../source-art/characters/3d-hair-lod-v1/other-game-comparison.jpg) 分开保存几何生成与视觉验收结论。四款源 GLB 合计 44,048→10,900 三角形，2,417,720→715,804 字节；这是资源合计，运行时只选一款，不等于每帧同时减少此数。此轮只验收模型、动画显示与切换，没有新增整体 CPU/GPU 降幅结论，也未制作或上传新 TapTap 包。

## HUD 原生分层合批与禁用圆片

此前隐藏 HUD 的主线程差值较大，继续定位其渲染提交。原生 [Sorting2D](https://docs.cocos.com/creator/3.8/manual/en/engine/rendering/sorting-2d.html) 可以调整绘制顺序而保留节点树、触控、按压目标和变换；原生 Mask 遇到批次边界时仍由引擎处理模板状态，没有改 batcher 或队列内部实现。

`Hud.ts` 给技能底框、禁用圆片、图标和冷却遮罩分别使用 -30／-20／-10／-5 的默认层顺序。普通 HUD／弹窗继续使用默认顺序。启用现有 3.8.8 的 sorting-2d 裁剪模块，两个现有配置均保留原选择，只增加此模块。分组不改变控件位置、尺寸、按压目标、交互逻辑、图片或采样方式。

禁用遮罩原来是纯色 `mask-disabled` Sprite 加圆形 Mask。原图中心为 RGBA(18,13,10,158)，在现有圆孔覆盖区域内保持纯色；用原生 CompactGraphics 的同样 64 点多边形直接填充，取消这层不必要的模板进入／退出及图片绘制。颜色集中新增到 FeedbackPalette 的 `control.disabled`，透明度沿用 158。只在创建时生成几何，显隐继续走原有状态；没有每帧重画、运行时画布或额外图片。

`hud-overlay-prototype-v1/` 的强制禁用状态 172→158 draw，像素最大差 2，但正常刷怪夹具中这些遮罩很少出现，因此不把此差值外推成常态 CPU 收益。`hud-sort-prototype-v1/` 原生分层原型继续检查正常、禁用、按压、技能说明、补给和设置六种状态，正常 151→145 draw；禁用时联合方案 172→152。

正式源码的 TypeScript 检查通过，新 Creator Web 构建 `perf-ui-controls-20261114` Finished、退出码 36，并补跑品牌图标复制。`hud-native-controls-qa-v2/` 在正式编译结果中重建原版 Mask+Sprite／默认优先级，对照新实现：

| 固定画面状态 | 原版 draw | 新版 draw |
| --- | ---: | ---: |
| 正常 | 149 | 143 |
| 全部禁用 | 170 | 150 |
| 按压 | 149 | 143 |
| 技能说明 | 158 | 152 |
| 补给展开 | 167 | 159 |
| 设置弹窗 | 188 | 182 |
| 多技能冷却 | 158 | 146 |

七种状态各原版／候选／恢复，共 21 张全画面；最大像素差 2，无超过 3 色阶的像素，原版恢复最大差 1。所有按钮的父节点、局部／世界变换、尺寸及 interactable 状态严格相同，零脚本／图形错误。V1 对照重建遗漏了 GRAPHICS_ELLIPSE，使用默认矩形导致无效视觉差异；已停止对应计时，在 V2 修正对照后复核，未为掩盖错误调整候选外观。失败记录与说明原样保留。

另确认当前模拟器的低帧率不能一概归为引擎主动跳帧：重启前只读原生 RAF 观察 120 个间隔，约 24.08 FPS、Cocos 绘制 119 次，主要是原生回调供给变慢。本任务专用 emulator-5556 按原配置重启后，恢复 root 与原有 TSC（未修改系统时钟源），原生 RAF 约 59.50 FPS；该短观察 Cocos 仅绘制 92 次，预览门控／启动节奏问题仍保留。没有修改帧率、Pacer、时间源或引入浏览器时钟桥接。固定画面的 draw／像素结果不换算成 CPU/GPU 收益，连续走打原生计时另录。

### 连续战斗计时与干扰排除

`hud-controls-moving-abba-v3/` 首次完成无并行构建的 A-B-B-A 各 45 秒窗口。原版／候选加权 FPS 为 49.063／48.592，Chrome 进程族 CPU 为 92.117%／85.366% 单核，CPU 每绘制帧 18.775／17.568 ms，主线程每绘制帧 3.598／3.463 ms。该次观察到 CPU 少约 7.33%，按帧折算少约 6.43%，主线程少约 3.77%；命中 127／121、击杀 24／25、自然刷新 26／24。两版绝对帧率预算均未通过，且独立反序确认尚未完成，`comparison.json` 保持 `approved:false`，不发布稳定整体降幅。

这里更正夹具标签：上述 V3 与后续 `hud-controls-moving-baab-v1/` 的脚本 scope 文案误写 Lv17，实际调用漏传 level，`fixture.level` 均为 **15**、初始生命 190。两条件等级一致，仍能作该场景内部对照，但不能与 Lv17 的五分钟回归直接比较。原始报告保留不改；重新计时显式传入 level=17。

反序 `hud-controls-moving-baab-v1/` 的最后窗口与 `perf-navigation-wasm-v2` Creator 构建重叠，状态 failed，不能作为复现确认。随后 `current-combined-final-moving-300s-v1/` 的 Lv17、300 秒实测又与 default／enabled 两次外部 Creator 构建重叠；虽完成移动 1,034.88 米、击杀 86、自然刷新 74，仍因并行构建、FPS 和长帧预算拒绝。其约 41.37 FPS、113.71% 单核 CPU 不用于证明代码回归或收益。

用户随后明确同意“先暂停其他构建做对照”。已向同机的“评估密集运算迁移至 WebAssembly”会话传达临时无构建／压力测试窗口；已有任务可正常收尾，不强停，不取消对方目标。计时复用完成的不可变 Web 构建，保持原生 60 FPS、原画质、怪物与规则；完成后通知恢复。

### 原生采样定位图形进程 CPU

`native-gpu-cpu-sample-v1/` 使用模拟器已安装的 Android simpleperf，按[官方 record/report 用法](https://android.googlesource.com/platform/system/extras/+/refs/heads/main/simpleperf/doc/executable_commands_reference.md)对本任务 Chrome GPU 进程进行 15 秒 cpu-clock 采样，500 Hz、DWARF 调用栈。实际记录 14.9903 秒、1,387 样本、零丢失，无并行构建。保留 perf.data、命令日志、self／inclusive CSV 和调用栈；该诊断含分析器，不能作无分析器性能验收。

GPU 进程样本中，Goldfish 传输驱动 `goldfish_pipe.ko` 的 self 权重为 **57.39%**，含该驱动的全部内核 self 权重为 81.69%。`CrGpuMain` 与 `CompositorGpuTh` 均出现传输开销，调用栈明确包含 `glBufferSubData_enc → qemu_pipe_write_fully → write → goldfish_pipe_read_write`。inclusive 项存在包含关系，不能相加。采样期间正常移动约 51.38 米、29 命中、4 击杀，未隐藏场景组件。

这些比例只描述**模拟器 Chrome GPU 进程的采样 CPU 分布**，不是整个游戏 CPU、硬件 GPU 时间或真实手机内核归因。已核实模拟器使用 RTX 3080 的宿主 OpenGL 翻译器，并非 SwiftShader；低硬件 GPU 忙碌度与较高图形进程 CPU 可以同时出现。当前证据指向图形缓冲上传／命令传输，后续应继续减少实际提交，不能把头发减面数量直接换算成 CPU 降幅，也不通过修改模拟器时钟或私有上传逻辑制造收益。

### 用户授权的无构建窗口结果

`hud-quiet-window-abba-final-v1/` 复用冻结的 `perf-navigation-wasm-v2-20261114`，先运行显式 Lv17 的 HUD A-B-B-A 各 30 秒，再销毁临时原版 Mask／Sprite 对照组件、恢复正式候选，执行现有 farm.cjs 的 300 秒移动战斗测量。临时包装器只在最终循环前增加对照；记录包装器与原测量工具各自哈希，没有修改正式测量工具。此构建包含本轮 HUD 与当时的导航实现，不能当作另一会话随后 enabled／default 构建的结果。

| Lv17 ABBA 加权指标 | 原版 HUD | 候选 HUD |
| --- | ---: | ---: |
| FPS | 49.192 | 48.415 |
| CPU，单核 % | 104.980 | 102.995 |
| CPU，ms/绘制帧 | 21.341 | 21.273 |
| 主线程，ms/绘制帧 | 3.862 | 3.893 |
| 击杀／自然刷新 | 17／16 | 17／14 |

候选总 CPU 少约 1.89%，但按实际绘制帧折算只少约 0.32%，主线程反而高约 0.81%；原版首尾主线程也存在漂移。**没有复现早先约 7.33% 的稳定整体 CPU 收益**，`comparison.json` 保持 `approved:false`。保留本轮原生合批／取消冗余遮罩的绘制减少与外观等价结论，不将 draw 数降幅当成 CPU/GPU 降幅。

随后正式候选五分钟测量实际覆盖 302.195 秒、14,512 绘制帧：48.022 FPS，最低一秒 32 FPS，P99 50.8 ms，最长帧 84.4 ms、无超过 100 ms 的帧；主线程 3.952 ms/帧，CPU 101.938% 单核（4 核归一为 25.484%）。移动 1,029.54 米、击杀 85、自然刷新 75，角色存活，正常输入控制与持续战斗检查通过。

计时窗口 Chrome 进程族 PSS 峰值 503.78 MB、最大采样间隔 1,049 ms；包括加载和前置对照的全过程峰值 533.96 MB，现有内存预算与采样覆盖检查均通过。没有脚本、资源或原生图形错误，没有并行 Creator 构建日志变化；编译主包前后指纹相同，另存 `build-immutability.json`。完整报告仍为 **failed**，拒绝项是平均 FPS 与最低一秒 FPS 低于现有 50 FPS 底线，未降低预算或限帧。

无构建窗口在 16:45:18 结束，已立即通知另一会话恢复构建与性能测试。之后重新执行完整 TypeScript、核心 TypeScript 与现有 140 项测试，均通过；本轮源码差异检查通过并保留原 CRLF。未新增测试依赖，未制作／上传 TapTap 包。连续刷怪 CPU/GPU 目标继续保持未完成。

最终截图原件 `1-farm.png` 为 2412×1152，其中底部 72 行逐像素重复顶部 72 行（向下偏移 1080，最大差 0），不能据此判定 HUD 又生成了一份。保留原始图，另用前 1080 行生成显示区域缩略图；截图边界现象与运行时 viewport 的关系尚未独立确认，不改游戏布局来补偿截图。

## 共享骨骼上传原型与全进程归因

继续读取原生上传清单，确认主角每帧有 9 个 12,288 字节的骨骼 uniform 上传。候选试验将兼容的不透明部件放入一个原生多子网格 SkinnedMeshRenderer，各材质槽、顶点／索引、阴影与姿势保留。Cocos 的[普通蒙皮组件](https://docs.cocos.com/creator/3.8/manual/en/module-map/mesh/skinnedMeshRenderer.html)支持多材质；现成的[蒙皮合批组件](https://docs.cocos.com/creator/3.8/manual/en/module-map/mesh/skinnedMeshBatchRenderer.html)还要求定制合并 effect／材质与贴图，因此此处只用已有 Mesh.reset 拼接公共网格结构，不改 shader、渲染器内部缓冲或上传策略。

临时原型在 `src/cocos/test-results/performance/skin-share-prototype-qa-v2/` 完成三个实时姿势和烘焙 idle／walk／attack_bow 共 18 张原／候选／恢复图，六组的 draw 与三角形数相同，最大像素差 1，无超过 3 色阶的像素，无脚本／原生图形错误。V1 把附加灯光 pass 的 additive 状态误当作表面透明，先于候选安装拒绝；V2 按原有 HeroBodyBatches 的主 pass 判断，未调整材质。上传清单 V1 及计时夹具另逐项核对 8 个子网格的全部属性与索引，均相同。

`skin-share-upload-census-v1/` 记录原／候选／恢复各 120 个移动帧，骨骼上传稳定为 **9／2／9 份**：头发仍独立一份，其余共用一份，每帧确定少传 86,016 字节（84 KiB）。整帧上传调用约 73.3→59.9 次、总字节约 176.6→82.6 KB；总数还包含动态 UI／战斗差异，只有骨骼的固定差值可以直接归因。该清单含调用计数，仅作诊断，不作 CPU 验收。

`skin-share-moving-abba-v1/` 的显式 Lv17、A-B-B-A 各 45 秒无分析器计时没有证实整体收益：原／候选 FPS 为 45.712／45.531，CPU 98.510%／99.494% 单核，CPU 每绘制帧 21.550／21.852 ms，主线程 3.934／4.010 ms。击杀 23／24，计时阶段未记录到 Creator 构建日志变化，但既有 `perf-computation-wasm` 构建在热身阶段结束（16:56:50）；短原生 RAF 观察约 51.43 FPS，不能当作稳定 60 FPS 环境。`comparison.json` 保持 `approved:false`。**该共享蒙皮原型与准备稿留在忽略的 temp 目录，没有写入正式 HeroBodyBatches.ts**，不以传输字节减少冒充整体 CPU 优化完成。17:00:43 已通知另一会话恢复构建。

随后对全部 Chrome 进程族做一次 simpleperf 原生采样，原始记录在 `test-results/performance/native-all-cpu-sample-v1/`。正常 H12/Lv17 移动战斗，记录 14.9758 秒、1,901 样本、零丢失；另保留前后所有线程的 `/proc/.../stat`，该快照跨度包含记录后的展开工作，约 18.22 秒，仅汇总两端仍存在的相同 PID/TID/starttime，不与无分析器性能验收混用。

线程 CPU 增量中，GPU 进程占约 **69.72%**，CrRendererMain 主线程约 **17.72%**；独立采样权重中 GPU 进程约 73.17%，Goldfish pipe 驱动 self 约占全部进程采样的 **39.14%**。这是 CPU 线程／采样分布，仍不是硬件 GPU 利用率。采样权重不换算成精确核占用；完整范围进一步支持原生图形提交／合成是当前模拟器 CPU 的主要方向，不把后台线程自动归因为 GC。


## 固定本地浏览器基准（用户于 2026-11-14 明确调整）

用户要求“固定一种”“测试用同一基准”，并优先在本地浏览器定位。已在 17:27 停止 Pipe/ASG 切换，恢复原始 Pipe 配置（SHA256 `3f82145e59e775767cd70eb3d1b5e5c9660d67bb23de57041d57dec4ff67224c`），关闭本任务的 emulator-5556，并解除另一会话的构建暂停。本地 CPU 对照不再依赖模拟器；TapTap 手机表现留待阶段复核。

此前 ASG 预试验不是可用 A/B：冷启动后的时钟环境改变，且一次测量与另一模拟器压力任务重叠。原始结果保留并明确拒绝；用户叫停后排队的受控 ASG 阶段没有执行，不继续调整时钟或传输。

固定浏览器：Windows Chrome 157.0.8103.51、headless、RTX 3080 的 ANGLE D3D11 硬件渲染，1608×768、DPR1，Pixel 7 Android UA、触控与实际 Cocos mobile 分支，CSM1、legacy forward、60 FPS。场景为显式 H12/Lv17/BOW、19 敌人及 4 远程怪，正常移动输入、真实伤害、有限补给和自然刷新。原／候选使用相同页面与渲染参数；桌面 Chrome CPU、Windows RSS、硬件 GPU 时间与 Android PSS／手机发热分开解释。

现有 `tools/performance/farm.cjs` 增加 `--backend desktop`，复用 page-driver、farm-driver、采样与战斗检查；安卓仍为原默认。桌面固定上述分辨率及 UA，额外预热 60 秒，正式计时不启用 CPU/分配分析器。桌面不伪造 Android 的 UI／图形日志验收标记。Windows 进程族 RSS 求和可能重复计算共享页，保留现有预算原判定，不能把其数值当成 Android PSS。

### 本地 CPU 与分配热点

`test-results/performance/desktop-moving-diagnostics-v1/` 对旧冻结页面 `/ui-current-combined/` 单独运行各 30 秒 CPU 及分配采样。采样结果用于归因，不作无分析器性能验收；该页面早于另一会话的小地图更新，不能据此重新优化已变更的小地图代码。

分配样本估计约 209 KB/帧；Bullet 约 35.96 MB，其中视线 `SceneBuilder.visible → raycastClosest` 约 30.15 MB，显式胶囊移动约 3.94 MB，自动 Physics.postUpdate 约 1.87 MB。采样量是统计分配估计，不是保留内存或泄漏结论。后续先消除无动态刚体时的自动世界步进，再对确定不可能碰到静态遮挡物的视线增加保守范围预判，保留原生射线处理所有可能相交情况。

### 静态场景的物理步进对照

最新源码基线为 `perf-desktop-cpu-baseline-20261114`（17:45:27 完成，已执行 render-policy、导航 WASM 及 branding 后处理）。120 帧原生公共接口计数：`syncSceneToPhysics=241`、`step=120`、`emitEvents=120`；0 动态刚体、22 碰撞体、1 胶囊控制器。Cocos 3.8.8 的胶囊 `move` 同步执行原生移动及位姿回传，无需额外动态世界步进；保留全部胶囊移动、碰撞、射线和 60 FPS 设置。

先前简单 ABBA 每窗 30 秒未稳定改善总 CPU，因此不采纳其总 CPU 收益。改用 60 秒预热、逐窗重置同一夹具、B-A-A-B 各 30 秒，GC 仅在窗外执行：

| 加权指标 | 原版自动步进 | 显式胶囊／静态查询 |
| --- | ---: | ---: |
| 实际 FPS | 约60.01 | 约60.00 |
| 主线程 ms/帧 | 约4.980 | 约4.817 |
| CPU 单核 % | 约81.86 | 约80.13 |

主线程少约 3.26%，进程族 CPU 少约 2.11%，CPU/绘制帧少约 2.10%。这是固定本地 Chrome 的小幅收益；没有把它扩大成手机功耗或 GPU 降幅。完整原始报告在 `desktop-physics-moving-baab-reset-v1/`。

正式源码仅在 flat 场景关闭公共 `PhysicsSystem.autoSimulation`；SceneBuilder 在静态碰撞体变化后按需同步，移动和射线前保证查询可见，胶囊移动仍保留原同步。ChapterGame 保存原自动步进状态并在销毁时恢复。

`desktop-physics-collision-replay-v1/` 在 H12、H03、U1-06、S13、S02、S01-T1 六区进行 25,272 次原生胶囊查询（原／候选／恢复），XZ 及胶囊 XYZ 的最大差均为 0。编译候选 V2 再次全部一致，各区闲置射线在显式步进前后相同，晚加入碰撞体可立即命中。

### 构建与退出验证中的实际问题

原工程构建偶发 Creator 对 settings/engine.json 的 UNKNOWN 写入错误；未改安全设置或引擎安装。第一份含源码／library 目录链接的隔离构建虽 Finished/exit36，却缺失 ChapterGame 类，主包仅 2,422 字节，已拒绝。第二份使用实体文件及独立 library 的隔离项目，在 18:24:32 完成；核对主包 2,160,766 字节及新增方法、源码哈希一致，再复制到 `perf-desktop-manual-physics-verified-20261114`，通过渲染策略和 WASM 后处理。

V2 编译查询检查在退出阶段发现既有 TapLogin.dispose 的 Set 展开被发布编译转为 concat，导致取消回调不是函数，阻断后续清理；因此 V2 报告保持 failed，不能称完整通过。修复为 `Array.from(Set)` 保持取消回调快照语义，同时将新增全局物理状态恢复移到 ChapterGame.onDestroy 开头，避免依赖其他清理先成功。最后的编译、退出及连续运行验证另记结果。


### 本地连续测量及边缘用例修正

`desktop-manual-physics-moving-300s-v1/` 完成第一轮五分钟：56.725 FPS，最低一秒 55，P99 22.3 ms、最长帧 37.2 ms，主线程 3.354 ms/帧、CPU 55.86% 单核；移动 1,006.41 米、击杀 80、自然刷新 76，角色存活，未记录并行构建。该报告保持 failed：Windows 进程族 RSS 求和峰值 1,334.63 MB，超过既有 1,000 MB 预算；另有四次短生命周期 Chrome 进程退出导致内存快照失败。没有将这些问题从报告中去除。

第一轮桌面采样复用的旧 resources.windowsChromeMemory 每秒新开 PowerShell，既增加宿主干扰，又存在 PID 列表与读取之间的竞态。现新增常驻计数器读取器，仅桌面 farm 使用；复用同一 PowerShell 进程，通过 stdin/stdout 传递 PID／完整快照；若进程恰好退出，重新获取完整族列表后重试一次，仍失败则保留错误，不静默跳过。手动连续读取 10 次，均为完整快照，读完已关闭助手进程；最终对照使用同一新采样工具。未更改资源预算或帧率设置。

`desktop-cpu-final-world-qa-v1/` 的现有验证通过 31,126 次移动碰撞对照、各区 1,200 次随机及零长度视线对照、镜头姿态／地图稳定性／索引检查。但新增更密的障碍物边缘用例在 U1-06 柱子周围找到约 1 mm 的视线误判，因此含最初 1 mm 包围盒余量的编译候选不能采纳。失败报告为 `desktop-cpu-final-compiled-qa-v1/`。

进一步直接复现发现：新静态体首次进入 Bullet 后，执行一次世界步进会更新 broadphase 范围，极近边缘的射线结果随之改变。Cocos 公共 collider.worldBounds 是形状范围；Bullet [updateSingleAabb](https://github.com/bulletphysics/bullet3/blob/master/src/BulletCollision/CollisionDispatch/btCollisionWorld.cpp) 还会增加接触阈值，原生凸体射线也存在数值容差。上游源码用于解释机制，具体行为以项目所带 Bullet 二进制的复现为准。

修正为：静态几何变化后在手动模式执行一次公共 physics.step 初始化查询范围，稳定帧仍不执行世界步进；粗判保留 5 cm 的保守带，所有可能相交或近边缘的情况仍走原生射线。扩大边缘用例至边界内外 0.1 mm 至 10 cm 多档，不以随机样本通过代替边缘正确性。新源码完整 TypeScript 检查通过；修正后的实际编译和性能结果另记。


### 修正后编译与正确性结果

`perf-desktop-cpu-final-v2-20261114` 于 18:42:30 完成 Creator 构建（Finished、exit36），复制产物后通过 legacy render-policy、33561 字节 ABI3 WASM 校验／导出及 branding。独立项目的 ChapterGame、SceneBuilder、TapLogin 与主工程源码哈希一致，未通过改编译产物代替源码修复；Web 构建不递增版本。

`desktop-cpu-final-compiled-qa-v2/` 完成六区 **21,340 组视线对照、25,272 次胶囊查询**，全部与原生参考一致。包含边界内外多档距离及 NPC 高度，闲置时 1,718 条射线在再次世界步进前后相同；各区晚加入碰撞体可立即命中。退出时自动模拟原值 true、实际恢复 true，脚本及原生图形错误为 0，完整报告 completed。TapLogin 清理修复也已实际编译验证。

`desktop-cpu-final-world-qa-v2/` 再次通过现有工具的原／候选合计 31,126 次移动查询、随机与零长度视线、镜头一致性、地图稳定绘制及网格索引检查。完整 TypeScript、核心检查及现有 140 项测试通过；最后的几何容差／初始化修正后再执行完整 TypeScript，通过。没有新增测试依赖。

正式候选预热后的 120 帧计数为 `syncSceneToPhysics=121`，`step=0`、`emitEvents=0`，仍为 22 碰撞体、1 胶囊、0 刚体。与原版 241/120/120 对应：稳定帧省去自动更新，保留显式胶囊同步与移动；新几何的一次初始化位于计时窗外。

粗判复用 Cocos [geometry.intersect.aabbWithAABB](https://docs.cocos.com/creator/3.8/api/en/namespace/geometry)，静态范围仅在几何改变后重建；单帧精确视线缓存、视线高度和原生精判保持原规则。后续 B-A-A-B 与最终五分钟结果另记，不以查询次数变化替代 CPU 实测。


### 视线粗判未获得总 CPU 收益，已撤回

`desktop-physics-visibility-baab-v1/` 在同一不可变编译包上，以精确原版单帧缓存视线函数＋自动步进作 A，编译后的包围盒预判＋手动物理作 B。60 秒预热，每窗重新创建 H12/Lv17/BOW 夹具，B-A-A-B 各 30 秒；无 CPU／分配分析器、无构建日志变化、无脚本错误。GC 仅在窗外。

| 加权指标 | A 原版查询／自动步进 | B 粗判／手动物理 |
| --- | ---: | ---: |
| 实际 FPS | 56.822 | 56.761 |
| 主线程 ms/绘制帧 | 3.780 | 3.709 |
| Chrome 进程族 CPU 单核 % | 61.533 | 62.022 |
| CPU ms/绘制帧 | 10.829 | 10.927 |

主线程只少约 1.90%，总 CPU 高约 0.80%，按绘制帧约高 0.90%。因此 `comparison.json.approved=false`，**没有把该视线粗判写入最终方案**。已从正式源码删除新增 AABB 字段、范围快照及预判方法，恢复原精确缓存＋原生 raycastClosest。通过大量正确性测试不代表性能方案值得保留。

保留独立对照中已有小幅收益的静态场景手动物理，及首步初始化、按需同步／销毁恢复的正确性修正。新几何初始化只发生于 dirty 状态，常规帧保留胶囊碰撞。最终源码另编译为 `desktop-physics-final`；上述粗判产物、报告和准备稿保留用于审计，但不作为最终方案。最终 TypeScript 检查再次通过。


### 最终物理单项复测：只确认小幅主线程变化

最终编译 `perf-desktop-physics-final-20261114` 在 18:51:04 完成（Finished、exit36）并通过同样后处理；其三个变更源文件与隔离项目快照哈希一致。`desktop-physics-final-compiled-qa-v1/` 再次完成六区 21,340 视线、25,272 胶囊查询，最大差 0、迟加入碰撞体正常、首次同步后的闲置射线再步进结果一致、退出恢复 true，脚本／图形错误 0。正式源码不含被拒绝的 AABB 预判。

最后测量复用 canonical farm 的桌面后端，只在同一页的 60 秒预热后、正式五分钟之前增加 B-A-A-B 各 30 秒的物理开关对照。忽略目录的 `desktop-physics-final-combined.cjs` 包装器及 canonical 文件哈希均记录在报告，未假装未修改测量工具。使用常驻 Windows 内存计数器，两种模式条件相同，正式窗口无分析器。

原／候选实际 FPS 约 56.862／56.793，主线程约 3.858／3.807 ms/帧（少约 1.32%）；Chrome 进程族 CPU 约 62.955%／63.268% 单核，候选略高约 0.50%，属于小幅波动，**不能宣称整体 CPU 已降低**。此前另一时段约 60 FPS 下的 2.11% 进程族收益没有稳定复现；不同时间／实际帧率结果不混合作最终收益。原始四窗及 `physics-comparison.json` 保留，后者明确 `overallCpuBenefitConfirmed:false`。

保留的源码减少了已确认不需要的自动世界步进，功能验证通过，测得的小收益仅归于主线程；连续刷怪整体 CPU/GPU 的改善目标继续保持未完成。日常固定本地浏览器，后续围绕当前图形提交热点继续验证，不重启传输／模拟器时钟试验。


### 最终五分钟与采样器修正

`desktop-physics-final-moving-300s-v2/` 的正式窗口为 300.138 秒：**56.817 FPS，最低一秒 55，P99 22.5 ms，最长帧 38.5 ms**；主线程 3.751 ms/帧，Chrome 进程族 CPU 62.160% 单核（24 线程归一约 2.590%）。移动 1,010.93 米、击杀 80、自然刷新 73、真实受伤 1 次，结束 HP184/200、有限药水 15，持续移动／战斗、场景、60 FPS 设置及帧率底线检查通过。没有并行构建；编译主包计时前后指纹相同，三份拥有改动的源码与编译快照一致，见 `build-immutability.json`。

**完整报告仍为 failed。** 正式窗口 Windows Chrome 族 RSS 求和峰值 1,204.36 MB，全程含预热／ABBA 峰值 1,277.15 MB，超过既有 1,000 MB 预算；共享页可能重复计算，不能当作 Android PSS，也未放宽预算。此外，预热期有一次短进程退出的采样失败（PID3332）。正式五分钟有 301 条内存观测，最大间隔 1,105 ms；全程最大间隔 2,009 ms 在 warmup，未伪造为零错误。没有脚本／资源／图形错误或角色死亡。

预热的竞态说明立刻重取 CDP 列表仍可能得到刚退出的 PID。测量结束后，常驻计数器改为最多三次完整快照、重试前等待 100 ms，始终不静默舍弃 PID。用真实 Chrome 连续创建／关闭 30 个页面进行 60 次读取，触发 30 次重试、全部快照完整、0 失败，随后关闭计数器和浏览器。此改动发生在长测之后，旧计数器源码另存 temp 快照；**没有把旧报告改称新计数器已通过长测**。新旧工具的 measurementHash 会不同，不能直接混成同一基线。未再扩写测试或重跑没有必要的长测。

最终保留：公开物理接口的静态场景调度、几何初始化与按需同步、销毁恢复，以及 TapLogin 的 Set 快照清理修复；新增的视线包围盒预判已撤回。完整 TypeScript、核心检查、现有 140 项测试与实际编译正确性已完成；最新 JS 工具语法检查及上述采样压力验证通过。根版本仍为 0.3.40，未制作或上传新的 TapTap 包。后续日常基准固定本地 Chrome，整体 CPU/GPU 优化目标继续进行；手机／TapTap 的绝对占用与温度按用户要求留待阶段复核。


## 当前浏览器的渲染开关定位与怪物头顶精简

`desktop-render-components-v1/` 在已固定的 Chrome／RTX3080／1608×768 DPR1／H12 Lv17 BOW 页面上，对头顶反馈、HUD、主角、头发、特效分别做保留—隐藏—恢复的短时筛选（每窗 10 秒，原生渲染开关，规则继续运行）。这是筛选，不是修改后收益验收；自然战斗量没有逐窗重置，尤其头发窗口的命中与绘制量差异明显，不据此宣称头发隐藏更快或更慢。没有将这些隐藏写入游戏。

HUD 隐藏时约从 144 降到 64 draw，总 CPU 约 64%→46% 单核；主角隐藏时约从 141 降到 109 draw、CPU 约 63%→51%；头顶反馈隐藏约从 142 降到 128 draw、CPU 约 64%→58%。筛选中 Chrome renderer 与 GPU 两类进程各约占一半 CPU。这里的 GPU 进程数值是图形驱动／提交的 CPU，不是硬件 GPU 利用率，下一步应优先减少实际绘制提交，而非继续把 1% 级的逻辑变化扩大解释。

### GPU 计时的独立控制

初次 Director.BEFORE_DRAW—AFTER_DRAW 的 TIME_ELAPSED 区间中位数约 14 ms，不能直接当作 GPU 忙碌时间。另用 `desktop-gpu-control-census-v1/` 对照零工作查询、原生完整绘制查询及明确提交结束标记的诊断查询：零工作中位数 0 ms；完整未显式提交的中位数约 4.91 ms，提交结束标记后约 3.05 ms。后者 P95 5.48 ms、无 disjoint／GL 错误。单独的 Windows WDDM 计数显示，本任务 Chrome GPU 进程的 3D 引擎忙碌约 19.9%–22.5%，copy 引擎约 0.03%–0.05%。

GPU elapsed 覆盖命令执行区间，可以包含等待／批次提交间隙；初次 14 ms 不能作为硬件瓶颈结论。所有查询／flush 仅在忽略的诊断脚本中，未修改引擎、帧时钟或正式上传策略；这些窗口不作 CPU 优化验收。方法依据 [WebGL EXT_disjoint_timer_query_webgl2](https://registry.khronos.org/webgl/extensions/EXT_disjoint_timer_query_webgl2/)。

### 按用户最新要求，常驻名称与攻击飘字分开

用户要求怪物头顶只保留一份名称和血条，去掉重复的名称与距离；随后明确要求保留普通掉血、暴击等攻击飘字，并保留独立的野外怪群提示。最终范围以这些澄清为准。

源码统一由 EnemyCombatFeedback 负责普通怪、精英、首领的常驻名称／血条；任务标识不再叠到敌人头上，ChapterGame 不再创建另一套 BossPresence。名称共用同一身份解析，去掉常驻等级行。伤害、暴击、MISS 的原 onEvents／showText 逻辑、样式、时长、字形预热与池上限已恢复并保留；浮字位于名称／血条上方，玩家受伤、吸收、治疗沿用原逻辑。

独立的野外怪群方向／距离提示保持原样：`encounterDirection`／`calculateEncounterDirection` 与变更前逐字节相同。曾考虑移除这条提示，但编辑未落盘，已按用户澄清保留。早先不含攻击飘字的候选 v1／v2／v3 验证另存 `acceptance.json` 标注不采纳，不用它们证明最终版本正确。

实际采用 `perf-desktop-monster-heads-v2-20261114`（Creator Finished／exit36，通过 legacy policy、33561B ABI3 WASM 与 branding 后处理）。五个变更源文件与编译快照一致，见 `monster-heads-candidate-qa-v4/source-verification.json`；该记录还核对攻击浮字呈现方法及字形预热与原版一致、野外怪群提示方法不变。之后的 v3 为同内容重复构建，未替换已验收的 v2 预览。

`monster-heads-{reference,candidate}-qa-v4/` 在 844×390 逻辑横屏、请求 DPR3 下完成普通怪、任务敌人、首领三种实际编译场景；引擎现有像素比限制使实际画布为 1688×780，此规则未修改。每个敌人恰有一套常驻名称／血条，HP 比例与权威 HP 一致；任务敌人及首领无第二套标识。同时明确验证普通伤害、暴击、MISS 三类浮字都可见（10／暴击15／MISS），玩家 -12 受伤、吸收4、闪避均保留，非敌人出口导航也正常。UI夹具重建后的玩家等级为默认15，单独记录；不把初始 Lv17 计时夹具误标到这些 UI 截图。已检查完整画面与头顶局部，截图在 `monster-heads-ui-review/`。

完整 TypeScript、核心检查与现有 140 项测试通过；恢复攻击飘字后再运行完整 TypeScript，通过。复用 farm.cjs 的显式 H12/Lv17/BOW 60 秒连续移动战斗已完整测量：约 56.833 FPS、最低一秒55，主线程3.768 ms/帧，CPU62.318%单核，移动约202米、击杀15、自然刷新9，角色存活。没有脚本／图形／并行构建错误，内存采样完整，窗口最大间隔1015ms。完整报告仍因 Windows 族 RSS 峰值约1216MB超过既有1000MB预算而 failed；不宣称总体 CPU 已明显改善，不用它代替手机验收。测量在范围澄清的收尾阶段已完成，原始完成状态与数据保留，见 `scope-review.json`。

游戏版本仍0.3.40，本轮只生成本地 Web 预览，没有制作或上传 TapTap 包。整体 CPU/GPU 优化目标继续保持进行中。


## 无画面退化的原生 HUD 图集

用户进一步明确：没有画面或功能退化的改动可以保留，但避免过度 hack。此项沿用 Cocos Texture2D、SpriteFrame、Sorting2D 与已有 GameResources／FrameCache；没有新增全局引擎补丁、渲染器私有写入、帧时钟修改、DOM 画图或运行时拼图。图集是现有 Pillow 工具的确定性离线输出，原始美术继续保留。

先用忽略目录中的七图原型做 1024×1024 同页 ABBA：七种冻结状态均少 6 draw，像素最大通道差 2/255，按钮位置／尺寸／缩放／可用状态相同。30秒四窗加权：原版约61.535%单核／3.749ms主线程每帧，候选59.324%／3.634ms，均值低3.59%／3.06%；但两个候选 CPU 窗口相差约5个百分点，不把初次均值当作稳定的整体收益。原始记录保留在 `hud-icon-atlas-{qa,abba}-v1/`。

正式接入按 WAR／BOW／FIR／THU 默认技能栏各生成一张 **1024×512** 图集，每张只包含七个原始256×256 RGBA图块，无缩放、裁边、旋转或像素生成；沿用原 `.047` 分数裁切、双线性／Web mip 规则及原生 Sprite 渲染。切换到其他可选技能时继续使用原来的圆形图片，不限制技能配置。流派进入图标缓存键，公共闪避／普攻也随当前流派更新；换图先清除旧 SpriteFrame，再释放旧节点租约，沿用 FrameCache 的最后绘制帧后回收与异步请求校验。

每张带Web mip的实际GFX纹理为2,796,204字节，原七图合计2,446,668字节，增加349,536字节（约0.333MiB），不是内存优化。四张新增PNG合计3,144,455字节（约3.00MiB）进入资源目录；本次Lv17默认七图夹具所需PNG相对原七图只增约9.7–16.4KB；较低等级也会加载完整当前流派图集，初次可玩下载变化须另验，完整上传包／首包／分包的最终变化尚未重新制作TapTap包验收。上述9.7–16.4KB仅为本地Web逐图请求对照，不作为TapTap可玩前下载量；现有 `ui/combat-relief/` 路由仍进入 skill-icons 包，TapTap按完整分包重新统计。

实际编译 `perf-desktop-hud-atlas-20261114`，Creator于20:12:59记录Finished；通过legacy forward、ABI3 WASM与branding后处理。`hud-icon-atlas-compiled-qa-v1/source-verification.json` 核对三份源码及四张图集与独立编译快照一致。完整TypeScript和生成工具语法检查通过，没有新增测试框架。

四个流派各七种状态（normal／disabled／pressed／description／supplies／settings／cooldowns）共28组都少6 draw、三角形数相同，原生按钮位置、尺寸、缩放和可用状态相同。v1 的 THU/settings 首张参考截图遇到设置页滑块与图标尚未加载完成；候选与恢复后的参考相差最多1通道，差异范围也在设置页。其原始像素报告仍保留failed。v2在网络空闲及额外300ms后只补验这一组，通过。另两组WAR/settings、BOW/settings的截图像素通过，但截图前的draw计数同样遇到异步加载；v3等待就绪后补验这两组，像素与计数均通过，原始计数未覆盖。汇总验收见 `hud-icon-atlas-compiled-acceptance.json`，28组最大通道差2/255，已检查弓系原／候选技能栏局部。

WAR→BOW→FIR→THU 的每张前一个图集均实测 refCount=0、isValid=false、GFX字节=0，未逐流派常驻累积。另验证 BOW_03 使用原256px图片；快速切换 BOW_04／BOW_03／空槽／BOW_01 后，最终仍为 BOW_01 正确图集区域，旧异步请求没有覆盖新选择。怪物头顶的一份名称／血条、攻击飘字和独立野外怪群提示未改动。

最终接入版本另做同一不可变包 B-A-A-B，每窗45秒，60秒预热、显式H12/Lv17/BOW/普通输入连续移动战斗、固定本地硬件Chrome；计时不运行分析器、截图或GPU计时查询。结果随后补记，不以draw数直接代替总体CPU或手机发热结论。


最终原生接入版 `hud-icon-atlas-native-baab-v1/` 于20:22:12完成。四窗各45秒、无脚本／图形错误、无Creator日志写入；均持续移动约145–146米、命中66–70次、击杀12–14，保持H12/Lv17/BOW、19敌人／4吐毒者及60FPS设置。原／候选实际FPS为56.797／56.799，最低一秒与完整帧数据保留。加权Chrome族CPU为62.708%／60.807%单核，按帧11.041／10.706ms（低约3.03%）；主线程3.735／3.703ms（低约0.88%）。两个候选CPU窗口仍相差约5个百分点，故 `stableWholeGameCpuGainConfirmed=false`；初次原型与最终接入均值方向一致，但不宣称总体高占用或手机发热已解决。

按用户授权，保留这一无画面／交互退化、采用原生接口的提交次数优化及已验证的旧图集释放。`hud-icon-atlas-compiled-render-checks.json` 对最终采用的28组逐项核对A/B/A：候选恰少6 draw，恢复回原数，三角形数相同。图集约0.333MiB额外纹理内存及约3.00MiB新增资源文件均如实记录；平台分包／真机表现留待阶段验收。版本仍0.3.40，没有TapTap新包、版本递增、上传或模拟器配置改动。


## 主角蒙皮重复上传的独立定位

上一轮属于实际进展：原生技能图集已接入并完成四流派画面／交互／资源释放验证，绘制提交减少但CPU整体收益仍有波动。本轮从现有主角渲染器继续定位，不重启模拟器、不改变固定浏览器／H12 Lv17 BOW／60FPS／怪物规则。

现有HeroBodyBatches仅合并相同材质服装；可见主角仍有手臂、眉毛、眼睛、头部及三个服装批次，共7个兼容不透明渲染器、8个材质槽，另有独立发型。它们共享同一67关节骨骼与蒙皮根、相同局部变换和渲染设置；手臂另有两个关节映射。因此原生蒙皮缓冲仍有9份（含发型）。

Cocos原生SkinningModel每次updateUBOs遍历当前关节并上传其各关节缓冲，updateTransform也逐关节变换包围盒；相同骨骼拆为多个模型会重复处理。此依据为本机Creator3.8.8的skinning-model.ts，而不是跳过任何引擎更新的修改。

使用[公开的Mesh.IStruct／jointMaps](https://docs.cocos.com/creator/3.8/api/en/interface/Mesh.IStruct)和[多材质SkinnedMeshRenderer](https://docs.cocos.com/creator/3.8/manual/en/module-map/mesh/skinnedMeshRenderer.html)做忽略目录中的原型：复制原始顶点／索引，保留8个原材质槽，以一个原生Mesh／SkinnedMeshRenderer和关节索引并集共享一份调色板。61个被引用的关节索引，数据2,197,176字节；每项属性与索引逐值核对一致，发型不合并。官方SkinnedMeshBatchRenderer要求定制合批材质，本次保留原材质，未引入该材质／着色器流程，也没有写渲染器私有状态或修改全局引擎。

`desktop-skin-share-union-qa-v1/` 在当前不可变图集构建中完成3个运行时冻结画面与idle／walk／attack_bow三种烘焙动画状态，共18张原／候选／恢复图；6组全部像素通道最大差1/255，绘制次数、三角形数相同，无页面错误。不同烘焙状态的原始画面也实际不同，不用重复的同一张姿态冒充多种状态。此为局部原型验证，尚未替代换装、隐藏部件与最终构建验收。

`desktop-skin-share-union-census-v1/` 在3个各120绘制帧的诊断窗口中，完整转发每次WebGL调用，仅记录上传：原版9个骨骼UBO各每帧上传12,288字节；候选只剩发型和共享模型2个，恢复后回到9个，确定少7次／84KiB每帧。总bufferSubData调用与字节受自然战斗/UI变化影响，只用固定的骨骼缓冲计数作此结论。诊断计数器未进入正式CPU计时窗口或业务代码。

另外运行同包ABBA、每窗重建显式H12/Lv17/BOW夹具并重新创建相同原型、各45秒。所有原／候选窗口都先创建原型，使窗外分配一致；原型只通过渲染器enabled选择，规则和普通输入继续运行。60秒预热，计时不带上传计数器、分析器、截图或GPU查询；结果随后补记。正式源码尚未接入此蒙皮原型，是否值得增加这部分接入复杂度以实测CPU为准。


蒙皮原型ABBA于20:36:03完成：原／候选实际FPS56.753／56.754，总CPU59.575%／58.795%单核（均值低1.31%），主线程3.621／3.562ms每帧（低1.62%）。两个候选窗口58.925%／58.665%，末个恢复原版58.632%，整体差异与时段波动相近；自然战斗命中量64–71、击杀13–14，也未强行解释为纯实现收益。无脚本／图形错误、无并行构建。

因此 `desktop-skin-share-union-abba-v1/comparison.json.retained=false`：保留公开API原型、准确的84KiB上传削减证据和画面对照供后续复用，**不把新增的网格拼接与关节索引管理写入正式源码**。HeroBodyBatches仍为原先只合并相同材质服装的实现。这次定位解释了重复蒙皮上传，但并未证明它足以解决整体高占用；下一步继续从剩余原生UI绘制批次筛选更直接的改动。


## 文字缓存筛选与启动策略边界

`desktop-ui-batch-census-v1/` 的冻结画面把当前未缓存标签改成BITMAP后135→126 draw，整屏最大通道差2/255；改成CHAR后123 draw，但27,652个像素通道差超过3，最大228。分组的 `desktop-ui-cache-groups-v1/` 进一步确认：敌人名称单独BITMAP不减draw；其他标签BITMAP少9 draw；技能槽数字CHAR少4 draw却有370像素超过3（最大70），罗盘CHAR还多1 draw且有明显像素变化。已查看数字局部；这些模式均未写入业务源码。“static-bitmap”只是冻结诊断的模式名，实际含距离、提示等动态文案，不能按名称推定适宜永久缓存。

这里的重要边界来自[官方动态图集说明](https://docs.cocos.com/creator/3.8/manual/en/advanced-topics/dynamic-atlas.html)：小游戏默认关闭动态图集；强制启用要求在加载前保留图片缓存，不能在部分图片已释放后随意开启。当前未改变全局图片缓存策略，也未把浏览器的9 draw收益当成小游戏收益。后加载关闭动态图集的 `desktop-ui-atlas-off-census-v1/` 只作诊断：已有Label／Sprite渲染数据未全部重新建立，不等价于小游戏启动状态，另存measurement-notes说明。早期在AFTER_DRAW读到空batch数组则是读取阶段已清空，不能据此说没有UI批次。

采用官方Cocos启动settings.engine.macros字段，通过本地Playwright请求响应把CLEANUP_IMAGE_CACHE设为true，从引擎初始化起关闭动态图集；不改磁盘构建、业务设置、帧率或日常固定基准。它覆盖该图片缓存／动态图集策略，仍不是完整MINIGAME编译、TapTap适配器、AppID或真机验收。正确的render-frame-begin阶段可读到完整UI绘制批次；额外确认只有WorldCamera和UICamera两个可见相机。

### 缓存清理下的纹理保护修正

该启动对照前两次失败记录 `desktop-ui-startup-policy-census-v1/v2` 保留：7个技能图标虽持有有效纹理对象，但宽高均0、refs=8，等待20秒也未恢复。Web的MINIGAME常量为false，旧UiSkin的mip重上传条件没有检查CLEANUP_IMAGE_CACHE；源码路径仍可能借用正在清理的ImageAsset重新赋给Texture2D。小游戏分支本来跳过这一步，**不把此Web配置问题写成已在TapTap手机复现的缺陷**。

UiSkin现在仅在图片缓存保留且ImageAsset有效时进行Web mip重上传；缓存清理开启时保留Cocos已经上传的单层纹理及原双线性采样。新增检查是公开引擎宏和Asset有效性判断，没有修改渲染器或资源管理器内部。完整TypeScript通过，Creator于20:57:53 Finished生成 `perf-desktop-texture-policy-20261114`，通过legacy forward、ABI3 WASM和branding后处理；没有新TapTap包、版本递增或上传。

`desktop-ui-startup-policy-census-v3/` 在同一启动配置下通过：imageCleanup=true、dynamicAtlasEnabled=false、atlasCount=0，七个图标均1024×512、mip1，纹理不再为零尺寸。当前静态图集150 draw，独立原七图156，恢复150；三角形数同为110,602，整屏最大通道差1/255。全标签BITMAP仍150 draw，直接证明此时没有原先浏览器的合批收益。该配置下图集GFX为2,097,152字节，原七图1,835,008字节，增加0.25MiB；这仍仅是本地该渲染策略下的GFX计数。

默认Web策略也复验 `texture-policy-default-qa-v1/`：四流派共12张原／候选／恢复图，像素检查通过，每组恰少6 draw、三角形数相同，旧图集引用归零并销毁，其他技能与异步切换验证通过。三份当前源码与独立编译快照一致；磁盘settings的macros仍为空，路由覆盖原文件哈希已核对。源文件保护只影响加载阶段，本轮不新增声称每帧CPU收益的数字。

canonical page-driver仅新增texturePolicy只读元数据（图片清理开关、动态图集开关／数量／尺寸），使后续报告显式记录这个差异。其计时、普通输入、帧率、规则及质量未改；修改前工具另存temp供复现旧测量。已通过工具语法和上述实际运行检查，无新增测试框架／依赖。整体CPU/GPU目标仍未完成，后续优先从小游戏对应策略下的静态UI资源与装饰提交继续优化，保持攻击浮字和野外怪群提示。


## 原样像素的面板／血条图集合批

按用户“无退化可保留、避免过度 hack”的要求，先试验了将 HeroStatus 的原生背景、边框与细金线预合成为单图。原型虽少2 draw，但细线抗锯齿发生明显像素差异，因此未写入源码。Graphics 装饰、文字、布局与交互均继续使用原实现；原型与拒绝记录保留在忽略目录。

最终只把7张已有面板／血条 RGBA 图片离线排进512×512静态图集，不缩放、不旋转、不生成新像素。所有内部区域与原图逐字节相同，2像素边缘复制也逐项验证；512宽的 bar-track 横向直接使用纹理边界以保持原 CLAMP_TO_EDGE。UiSkin 通过公开 Texture2D／SpriteFrame.reset／Rect／Size 和原有资源缓存创建区域帧，九宫格 inset、Sprite 类型、透明度和节点均保持原状。仅在原生动态图集禁用时采用该图集；默认Web启用动态图集时仍走既有路径，不全局改引擎策略。

实际编译 perf-desktop-panel-atlas-20261114 于21:36:44 Finished，执行 legacy forward、ABI3 33561B WASM 与 branding 后处理；当前四份源码／资源与独立编译快照 SHA256 相同，见 panel-atlas-compiled-qa-v2/source-verification.json。根版本仍0.3.40，无新TapTap包。新增PNG108,367字节，原7图未删除；完整上传包／首包变化尚未重新打包统计。

在引擎启动即 CLEANUP_IMAGE_CACHE=true／dynamicAtlas=false 的独立队列，1608×768 DPR1及844×390请求DPR3（实际画布比2）分别完成 normal／partial-health／empty-health／tinted／supplies／description／settings 七种原／候选／恢复对照。两个视口共14组最大差1/255、0个像素差大于3，按钮几何／可用状态与三角形数相同；通常少5 draw，补给弹窗少6 draw。中文“生命”标签明确保留。v1忽略目录中的QA夹具曾因Python默认GBK写入而乱码，其验收已撤销，改为UTF8并复用现有本地化标签的v2才是正式结果。源码UI文字未受影响。默认Web烟测也通过，未分配该静态图集。

原7纹理GFX合计511,744字节，图集1,048,576字节，净增536,832字节（约0.512MiB），并非显存优化。编译版本在加载参考纹理之前已确认原7图GFX均为0；引用对照则给两组保留相同纹理集合，避免额外内存压力偏置。

panel-atlas-native-baab-v1 于21:52:04完成同页B-A-A-B四个45秒连续移动战斗窗口，每窗重置H12／显式Lv17／BOW／19怪4远程，保留实际伤害、有限药水与自然刷新。固定Chrome／RTX3080／1608×768 DPR1／移动分支／60FPS设置，60秒热身，计时内无分析器、截图或GPU查询；无脚本／图形／并行构建错误，均保持playing。原／候选加权FPS56.743／56.816，总CPU62.682%／62.089%单核（均值低0.95%），主线程3.747／3.725ms每帧（低0.60%），CPU每帧11.047／10.928ms。GPU进程的驱动／提交CPU29.802%→29.242%单核，renderer CPU31.119%→31.130%基本不变。该项是小幅提交收益，不称作整体高占用已解决，也不是硬件GPU忙碌或手机降温结论；不与默认Web策略报告混算。逐窗、进程类型与加权结果均保存，comparison.json.retained=true。

完整TypeScript、生成工具Python语法与本轮文件空白检查通过。保留原生静态图集，拒绝预合成细线方案；下一步核对优化前原始构建与当前所有保留改动的整体同机对照，不再用单项1%差异替代最终验收。


## 所有保留改动与最初构建的整体对照

原始参考为11:51完成的不可变 perf-cpu-base-20261114（7580），候选为21:36的 perf-desktop-panel-atlas-20261114（7582/desktop-panel-atlas/）。预检 overall-baseline-preflight-v1 已逐项确认：编译后战斗常量SHA256相同（f5fd1c0feb57361c2e75c236e979fe59ef0887a8d99cdec6f75e793511cfd153），H12完整区域数据SHA256相同（0f054fb8b654fc4b755b5691e27c10b9ed1d1afb56fec493b544c1d10aa69905），H12/Lv17/W07/BOW/19怪/4远程/HP200/正常移动输入的实际夹具逐字段相同。浏览器版本、RTX3080、1608×768 DPR1、移动分支、CSM1、legacy和60FPS设置也一致。两者均保持默认Web启动策略 imageCleanup=false、dynamicAtlas=true；图集数量不同属于被测改动，未强行改成同值。此队列中新增面板静态图集不启用，其收益单独见前节。

复用现有 page-driver、farm-driver、metrics、Windows常驻内存计数与构建干扰监视，整体按原—新—新—原各60秒；每窗新建独立浏览器上下文，实际战斗预热60秒，再重置同一夹具。量测期间没有替换源码函数、隐藏对象、截图、Profiler或GPU查询。每窗校验主脚本和settings内容仍与预检哈希一致。

| 窗口 | Chrome族CPU，100%=1核 | 主线程ms/帧 | FPS | 绘制p50 | 三角形p50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原0 | 63.729% | 3.855 | 56.739 | 149 | 139339 |
| 新1 | 62.959% | 3.760 | 56.743 | 133 | 111857 |
| 新2 | 62.860% | 3.797 | 56.797 | 133 | 111978 |
| 原3 | 68.785% | 4.072 | 56.836 | 149 | 139493 |

按实测时间／帧数加权，原／新CPU66.257%／62.909%单核（观察均值低5.05%），主线程3.964／3.778ms每帧（低4.68%），CPU每帧11.668／11.081ms（低5.02%），FPS56.788／56.770几乎相同。两组均35击杀、173次普通命中，自然刷新19／18，四窗最低一秒均55FPS、P99约22.3–22.6ms，玩法／输入／采样／脚本校验通过，无并行Creator日志变化。总CPU仍不能批准稳定5%收益：原版首尾CPU自身漂移约7.93%、主线程漂移约5.62%，大于相邻第一组的差额；comparison.json.overallCpuBenefitConfirmed=false。原始结果完整保留，不把均值包装成手机降温结论。

可稳定复现的是每帧绘制p50从149降到133（少16次，约10.7%），三角形约139416降到111918（约少19.7%）；伤害／暴击／MISS飘字与野外怪群提示均保留。renderer与GPU进程CPU按类型分别记录，GPU进程仍只是提交／驱动CPU。四窗现有1000MB进程族RSS硬预算均失败，因此仅记CPU对照测量completed，不能称完整性能预算passed；没有放宽预算或修改原始失败。


### 独立硬件GPU整体对照

overall-retained-gpu-abba-v1 在CPU计时完全结束后另起浏览器，仍使用原—新—新—原、相同默认Web策略与H12/Lv17/BOW正常移动战斗。每窗新上下文实际战斗预热30秒、重置夹具并稳定4秒，再量测30秒；不用WebGL计时查询或flush，也不采纳本诊断的CPU值。通过已有read-chrome-gpu.ps1验证PID确为本任务Chrome GPU进程，读取WDDM GPU Engine原始100ns活动计数差。四窗GPU进程身份、引擎实例集合、计数类型与时间戳均完整，0脚本／图形／构建干扰错误。

| 窗口 | 所属Chrome的3D引擎忙碌度 | 实际FPS | 绘制p50 | 三角形p50 |
| --- | ---: | ---: | ---: | ---: |
| 原0 | 24.692% | 56.777 | 148 | 138755 |
| 新1 | 21.138% | 56.510 | 131 | 110845 |
| 新2 | 21.223% | 56.643 | 131 | 110908 |
| 原3 | 24.758% | 56.813 | 148 | 138640 |

按计数区间时间加权，原／新3D忙碌度24.725%／21.180%，相对减少14.337%；实际FPS56.795／56.577，相差0.385%，60FPS设置未改。两个候选窗口均下降，末段恢复原版也恢复到24.8%，本机硬件GPU活动减少已复现。这里是拥有的GPU进程引擎活动计数，既不是Chrome GPU进程CPU，也不是手机GPU／功耗／温度。WDDM前后读数包含工具读取的短边界，计数区间约32.6–33.4秒，原始帧时钟为30秒；不伪装成逐帧精确GPU毫秒。自然战斗量有小差异，原／新普通命中87／86、击杀15／17，原始事件未调整。

最终57份变更源码和资源全部与独立编译快照逐字节相同，根版本0.3.40，见 overall-retained-abba-v1/source-verification.json；整体候选也包含同期已有导航／WASM工作，因此14.3%仅归于完整保留版本，不能分拆归因给某一项。保留缓存、索引循环、原生静态资源图集、原生绘制排序、已验收头发LOD与静态物理调度；无渲染器私有补丁、修改帧钟、跳传GPU缓冲或运行时拼图。共享蒙皮联合网格、改变细线的背景预合成与改变文字外观的标签缓存方案均未进入正式源码。

本轮本地定位、源代码优化、画面／交互检查与整体CPU／硬件GPU对照已收尾。CPU均值改善仍带有原版控制漂移，保持未批准稳定百分比；既有RSS硬预算失败也继续登记。攻击伤害、暴击、MISS和野外怪群方向提示均保留。没有制作／上传TapTap包，用户已推迟的手机0.3.39现象与TapTap真机功耗另行验证，不以此次本地结果替代。


后续原生合批复查与本轮新增3／4次提交减少，见[原生合批记录](native-batching-20261114.md)。这轮尚未新增整体CPU／GPU百分比，空间地形合批仍在评估。


## 2026-11-15 持续发热复查与手机比例可视范围

用户反馈连续刷怪仍热，继续固定本地 Chrome／RTX3080／1608×768 DPR1／移动分支／legacy／CSM1／60FPS，不把已有合批收益称作手机降温验收。当前不可变构建为 desktop-native-frame-atlas-v3。此次没有创建新的TapTap包，仓库已由其他打包流程升至0.3.41，未修改其版本或产物。

`continuous-heat-profile-20261115-v1`：实际H12／Lv17／BOW／19敌人4远程，60秒战斗预热后重置夹具，采样30秒、1800帧、59.975FPS。V8抽样的Director.tick包含2977.07ms，其中Root.frameMove1533.41ms、GameSession.advance213.91ms。约51.5%和7.2%是这些调用栈相对tick的抽样包含时间比例，不能当作全部进程CPU或手机功耗分解；保留idle、program、GC和未归因样本。原始profile、脚本、attribution及CPU进程分类均保存；无脚本错误或并行Creator构建。

采用公开geometry.AABB.transform／intersect.aabbFrustum与MeshRenderer.enabled做忽略目录中的画面外角色呈现原型，所有规则、动画时钟、变换、血条和攻击飘字仍按原流程更新。7个冻结镜头原／候选／恢复最大通道差1/255，draw和三角形相同；可减少11–19个注册渲染模型。原生视锥剔除此前已避免它们的实际绘制，原型只尝试减少前置模型更新。

`offscreen-actors-baab-20261115-v1`四窗各45秒实际移动战斗，B-A-A-B，均约60FPS、角色存活并持续击杀／自然刷新，无脚本、图形或并行构建错误。候选CPU34.697%、49.262%单核，原版42.444%、41.524%；加权候选41.980%、原版41.984%，没有一致净收益。主线程均值虽低6.7%，同样受候选首尾大幅漂移影响。comparison.json.retained=false，原型未进入正式源码，不能据此宣布降温或整体性能改善。

用户追问手机实际渲染范围，`phone-camera-footprint-20261115-v1`另在844×390／请求DPR3比例复测，同一H12默认镜头。实际Web画布1688×780，orthoHeight4.6，屏幕平面宽19.910米、高9.2米；对玩家脚下同一水平面的四角射线交点给出地面宽19.910米、进深14.448米。地形起伏及手机实际比例、镜头缩放会改变此数值；不是手机当前帧的远程采样。

H12地图逻辑范围144×128米；普通地形网格另有边缘延伸。81个地形块仅4块包围盒与当前视锥相交，每块约23.944×24米、512三角形，合计2048三角形。4块的外接范围71.832×48米，布局并不填满此外接矩形。地形以16×16个约1.5米网格单元分块，不能误写成16米一块。整块相交便提交其顶点，屏幕外部分由GPU裁剪；这不表示整张地图被逐像素绘制。当前19个平面怪物中8个包围盒与镜头相交，画面外角色仍有规则／动画／模型更新。near0.1／far160是相机纵深裁剪参数，不是160米半径地图绘制范围。阴影另有独立投影范围，不能把主相机之外一概视为完全没有渲染工作。

依据为本机Cocos3.8.8的AABB、Camera和场景更新源码、项目既有FlatWorldLayers分组剔除，以及官方相机／几何接口文档。此次仅诊断和拒绝无稳定收益的原型，没有限帧、删怪、删伤害反馈或生产引擎补丁；真实TapTap手机功耗／温度仍未验收。


## 2026-11-15 安卓模拟器当前CPU实测

按用户明确要求重新启动既有专用emulator-5556，Android14／4核／2412×1080／hostGPU／Pipe／禁用Vulkan，AVD配置SHA256仍为3f82145e59e775767cd70eb3d1b5e5c9660d67bb23de57041d57dec4ff67224c。没有调整宿主亲和性、计时器、客户机时钟或图形传输；本次冷启动实际clocksource为hpet，宿主亲和性为默认16777215，不能假定等于更早TSC／21845的模拟器计时环境。结束后已关闭本次启动的专用模拟器，保留之前的Web服务。

主记录 `test-results/performance/android-current-cpu-20261115-v1`：当前74项优化源码／资源与不可变V3构建一致。Android Chrome113，实际引擎画布1608×768，CLEANUP_IMAGE_CACHE=true／dynamicAtlas=false，与小游戏图片策略对齐，但仍不是TapTap App运行。复用farm脚本，忽略包装器只增加Android也先预热60秒；H12／Lv17／BOW／19敌人4远程／普通移动输入／真实伤害／有限药水／自然刷新，随后计时304.2494秒、11313绘制帧。

Chrome进程族CPU时间519.52秒，即170.7547%单核／1.70755核，4核折算42.6887%；逐分钟175.94%、172.54%、166.00%、168.41%、170.82%。实际37.1833FPS，最低完整一秒16FPS，P99 76.4ms，主线程8.5473ms／帧。80击杀、75自然刷新、561次普通／技能命中，移动1028.88米。战斗PSS峰值469.71MB、全过程507.05MB，结束回收后430.21MB。无脚本／图形错误，无并行Creator构建；原报告保持failed，只有平均FPS及最低一秒低于50的两项预算失败，不能称完整性能检查通过。

CPU校验发现/proc/stat聚合tick的等效时间与/proc/uptime及进程CPU不一致，拒绝把其57.15%原始busy比例作为可靠系统占用，也不使用该聚合tick总量给进程归一。另在相同构建／启动策略做20秒simpleperf stat -e task-clock独立核对，记录 `android-current-cpu-stat-20261115-v1`：同窗口/proc PID口径1.87506核，task-clock1.871791核，相差0.175%，进程CPU时间算法得到独立复核。此短窗口不混入五分钟170.75%的均值；未采样调用栈，也未更改时钟或计账方式。原始CPU、内存、帧数据、counter-cross-check及result-summary均保留。

用户问昨天为何约80%。已核对昨晚desktop native-frame-base为81.509%／59.977FPS，最新desktop native-frame-atlas-cleanup为77.555%／59.979FPS；均Windows Chrome157／ANGLE D3D11。今天是Android Chrome113／模拟器OpenGL Translator。最新77.555%那次与本次170.755%加载的主脚本哈希完全相同（2fa1904973d01b5865234fb4d837df2670a26874f78abf4f1e0d161a077e278e），这两次不是代码前后对照，不能判断代码负载翻倍。更早也存在安卓83.226%的20怪训练夹具及82.816%的H12／TSC记录；不可把不同夹具、构建或模拟器状态混为统一基准。逐项核对保存在baseline-context.json。这里确认当前模拟器环境负载仍高、帧率不足，不替代手机TapTapCPU或温升结论。


## 2026-11-15 排查83%与171%的变化：同次安卓启动交叉对照

用户要求检查近期改动是否造成大幅增加。找到凌晨01:52那份82.816% H12报告的原构建 `C:/Users/Alexa/AppData/Local/Temp/Singularity-memory-audit-20261113/src/cocos/build/taptap-texture-preloaded`，加载后的主脚本fingerprint仍为851e7a413011649748865af4a9bb4ef40e7437fadf05837adf983b23b6934939，旧二进制未修改。预检old-v2和current-v1均通过：完整战斗规则、H12区域数据、显式Lv17／BOW／19怪4远程／HP200／正常输入起点逐项相同，legacy／mobile／CSM1／60FPS设置相同。第一次old-v1在游戏加载前因7582预览服务未运行而失败，原记录保留；恢复本地服务后重新预检，没有篡改旧构建。

源码审计覆盖新增／变更的实际编译模块。主要为sorting-2d及HUD原生合批、静态图集与预热、头发LOD和服装同材质合并、平面角色采样缓存、静态物理同步和寻路/WASM，以及用户要求的头顶反馈精简。战斗规则和地图未改。旧留存工作区中的farm-driver、farm-metrics及android.cjs与当前逐字节相同；CPU运算未改，metrics只调整fingerprint对象键排序，page-driver只增加启动纹理策略元数据，因此没有通过统计口径改变制造CPU倍增。

使用同一次专用Android14模拟器启动、同一个Chrome113上下文，序列C-A-B-B-A-C，每段60秒实测；首段60秒、其余30秒真实战斗预热，随后每段重置同夹具。A为旧版默认Web策略，B为当前默认Web策略，C为当前CLEANUP_IMAGE_CACHE=true／动态图集关闭策略。每段画布1608×768，原始AVD／Pipe／hostGPU／禁Vulkan配置不变；不改时钟、亲和性、计时器或传输。该次冷启动自动选TSC，六段前后均未变化。无分析器、截图或额外图形查询进入计时窗口；1秒PSS监测与原有方法一致。

`test-results/performance/android-recent-changes-cabbac-20261115-v1/comparison.json` 的时间／帧数加权结果：

| 条件 | CPU单核口径 | 实际FPS | 累计CPU ms/绘制帧 | 主线程ms/帧 | draw p50 | 三角形p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A旧版默认 | 141.407% | 49.382 | 28.635 | 6.033 | 166 | 139745 |
| B当前默认 | 128.467% | 51.177 | 25.103 | 5.438 | 130 | 111986 |
| C当前清理图片 | 123.809% | 49.229 | 25.150 | 5.491 | 133 | 112159 |

A两段146.802%／136.011%，B为131.409%／125.526%，C为121.739%／125.878%。同策略A/B观察CPU均值低9.15%、累计CPU每绘制帧低12.34%、主线程低9.85%、FPS高3.64%；样本短且存在时段波动，不宣称稳定精确9%收益。没有复现近期改动造成CPU翻倍回退。B/C累计CPU每帧仅差约0.188%，该图片策略差异也不能解释原先约2倍的读数。此处CPU时间为多线程累计，不能把25ms解读为单线程帧时长。

同一旧二进制此前82.816%／59.249FPS，此次同会话复测136.011%至146.802%／约49FPS；同一当前清理图片二进制此前170.755%／37.183FPS，本次121.739%至125.878%／约49FPS。跨启动／运行状态波动已由不变二进制实测确认。此前171%那次为HPET、本次TSC，但旧82.8%记录本来也是TSC，因此不能把全部差异唯一归因时钟名称；具体调度、图形桥与客户机计账影响尚未逐项隔离。/proc/stat聚合tick与进程CPU／uptime存在覆盖差异，不使用聚合tick总量重新归一进程数值；原始计数完整保留。

六段协议、持续移动／伤害／击杀／自然刷新与进程计数检查完成，0脚本、图形和并行Creator构建错误；当前74项源码／资源仍与实际V3构建一致。报告的诊断状态completed，性能预算仍为failed：所有段最低一秒42至45FPS，未通过50FPS下限；不把相对工作量下降当作发热已解决。此次无生产源码改动、TapTap新包或版本变更，结束后关闭本次启动的专用模拟器。
