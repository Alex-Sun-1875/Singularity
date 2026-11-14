# 安卓模拟器石场跑动 CPU / GPU 实测与寻路优化

后续参数更新：用户将默认跑动设为5.0米/秒、慢走2.0米/秒，[功能复核已通过](../../src/cocos/release/taptap-movement-speed-v4-validation.json)。下文保留当时4.0／5.2米/秒的安卓性能采样，不作为新参数的真机温度结论。

2026-11-12，Cocos3.8.8 / 0.3.21，本轮保留60帧设置和默认4.0米/秒跑速。使用本机已有Android14镜像，没有下载运行环境或依赖。

**模拟器复现了移动初期的 CPU 尖峰，已确认主要来自任务指引寻路，并完成源码修复。** 速度越快，越容易在更短时间内进入新的起点网格；真正昂贵的是每次搜索反复解析坐标字符串、扫描候选并重复检测相同的障碍边。CPU剖析中的一次普通跑动：游戏更新35.28毫秒/帧，其中指引33.61、寻路33.60；单次寻路约1100毫秒。

## 空缓存受控对照

同一新构建内，切换优化前的方法与Cocos实际编译的优化后方法，其他游戏逻辑一致。每种速度按正反序各测两段8秒，每段开始清空路线及网格缓存。下表为两段均值，最长指引为两段最大值；这是首次计算的压力对照，不能当作全程游玩平均帧率。

| 跑速 | CPU毫秒/帧，前→后 | FPS，前→后 | 最长指引毫秒，前→后 | CPU均值减少 |
| --- | ---: | ---: | ---: | ---: |
| 4.0米/秒 | 69.19 → 4.85 | 12.0 → 57.5 | 979.0 → 56.4 | 93.0% |
| 5.2米/秒 | 59.60 → 4.72 | 13.7 → 57.8 | 1051.5 → 43.9 | 92.1% |

优化后仍有约44–56毫秒的首次指引计算，尚不能声称完全消除了长帧。现有A*、网格步长、碰撞半径、20,000次搜索边界和路径规则保留。

## 正常缓存下的复核

在编译后的优化版本中，不注入方法，先交替预热12秒，再按静止／跑动／快跑与逆序各测一轮，每段8秒。

| 模式 | 主线程毫秒/帧 | 实测FPS | 模拟器进程的宿主GPU 3D占用 | 绘制调用/帧 |
| --- | ---: | ---: | ---: | ---: |
| 静止 | 3.57 | 60.0 | 10.62% | 176.0 |
| 跑动4.0 | 4.04 | 59.4 | 10.22% | 173.9 |
| 快跑5.2 | 3.95 | 59.8 | 10.36% | 174.2 |

当前跑动与原快跑的CPU范围重叠，GPU差约0.14个百分点，不能认定存在持续的大幅上升。快跑只用于对照，默认速度没有恢复到5.2。CPU瓶颈缓解后绘制帧数增多，所以空缓存A/B中GPU占用高于旧逻辑的低帧率样本；这不代表每帧GPU工作变重，也不能据此推断手机更凉。

## 实现与验证

- 复用项目现有A*和碰撞足迹；节点只计算必要的坐标及f分数，候选比较不再制造大量临时字符串／数组／点对象。检索了PathFinding.js、FastPriorityQueue及现有依赖／引擎能力后，本轮保留已有算法并优化数据处理，没有引入新的寻路库或自行新增堆算法。
- 静态网格边按需记录已检查和可通过位，主导航实例为149×137×2＝40,826字节。其他调用path的Navigation实例各自分配；仅用于可视性的实例不会分配。SceneBuilder改变场景布局时重建Navigation，缓存随实例失效。
- 路线缓存有界200项，失败路径也复用，到限额淘汰最旧一项，避免整表清空后重算。
- 完整／核心TypeScript检查、116项既有检查及独立Cocos Web构建通过，包含绕障、不可达、窄间隙、地形与跨区路线检查。最终8段空缓存A/B及6段正常缓存复核均无应用错误。
- 单独的CPU剖析在19.92FPS触发了最初设置的20FPS诊断下限，已保留剖析文件和日志；这是复现低帧率时的采样脚本阈值，不计入最终A/B均值。

## 环境和结论边界

Android14 / API34 / x86_64，4个虚拟CPU、4GB内存，WHPX虚拟化，宿主i9-12900KF / RTX3080。Chrome113.0.5672.136，实际WebGL2渲染器为Android Emulator OpenGL ES Translator (NVIDIA GeForce RTX3080)，画布1608×768。显示器设为2412×1080横屏，Chrome的页面视口报告804×384／DPR3；按浏览器实际画布采样，不把它当成TapTap全屏布局验收。

CPU使用CDP threadTicks增量／实际帧数，另留安卓/proc的Chrome进程CPU计数。安卓Chrome没有GPU计时扩展，GPU列来自Windows对整个模拟器进程的WDDM计数，包括安卓合成开销，不是手机GPU百分比。计数窗口含取数开销，期间保持同一模式。

场景为S13断镐石场，Seed19、Lv40，实际碰撞与正常输入循环，距敌人至少约74.8米的26米畅通路线，未包含近距离怪群、战斗和特效叠加的最坏情况。最初发现记录与最终独立构建属于不同采样流程；两者绘制数差异不计入本次优化收益，因果对照使用同构建内的方法切换。

这是Android Chrome测试，尚未在TapTap客户端／荣耀X60i ARM真机中验证，未测物理手机温度、功耗或降频。40KB缓存不是游戏总内存减少量；Chrome量化堆快照和仅浏览器进程的meminfo也不能替代原TapTap内存指标。此前0.3.21游客ZIP尚未包含本次寻路优化；本轮未打新TapTap包、未上传。

[结构化结论](../../src/cocos/release/taptap-android-quarry-cpu-gpu-validation.json)、[空缓存原始对照](../../src/cocos/test-results/android-quarry-v1/cold-ab.json)、[正常缓存复核](../../src/cocos/test-results/android-quarry-v1/steady.json)、[CPU剖析](../../src/cocos/test-results/android-quarry-v1/quarry-run.cpuprofile)、[源码差异](../../src/cocos/test-results/android-quarry-v1/navigation.patch)。独立预览：[7492](http://127.0.0.1:7492/?view=2d&player=3d)。

![安卓模拟器石场实拍](F:/workspace/Singularity/src/cocos/test-results/android-quarry-v1/android-quarry-preview.png)

方法依据：[Android模拟器硬件加速](https://developer.android.com/studio/run/emulator-acceleration)、[Playwright Android](https://playwright.dev/docs/api/class-androiddevice)、[Chrome Performance协议](https://chromedevtools.github.io/devtools-protocol/tot/Performance/)、[Microsoft计时计数器](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types)。
