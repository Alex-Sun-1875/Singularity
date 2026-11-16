# TapTap 与 HTML 平台隔离规范

当前主工程为 `src/cocos/`，目标为 TapTap 小游戏，HTML 用于浏览器试玩和验证。2026-11-15 按实际业务脚本、平台适配、Web 模板和打包入口检查后维护本规范。

## 平台、档位与资源模式

- **运行平台**：统一从 `platform/RuntimePlatform.ts` 读取。Cocos `MINIGAME` 对应本项目的小游戏构建，`!MINIGAME && sys.isBrowser` 对应 HTML。`MINIGAME` 本身不是通用的 TapTap 身份证明；本项目的发布链还必须完成官方 TapTap 转换并校验真实 AppID。增加其他小游戏平台时须新增明确目标选择，不复用 TapTap 实现。
- **玩法档位**：`BUILD_PROFILE` 的 dev / test / release，决定开发加速、存档前缀与交付要求，独立于运行平台。HTML 与 TapTap 都遵守同一份档位规则。
- **资源模式**：`GameResources.usesAssetBundles` 决定资源路径路由。HTML 的 `__SINGULARITY_BUNDLE_PREVIEW__` 仅复现分包资源图，不启用 TapTap 登录、存储、更新或正式发布身份。旧 `__TAP_RELEASE__` 标记已从当前源码与构建注入中移除。

不得用 `tap` / `wx` / `window` 对象是否存在、URL 参数、dev 档位或资源预览标记猜测运行平台。引擎或工具可能注入同名对象；先选择平台，再检查该平台的能力是否存在。

## 当前差异与适配入口

| 能力 | TapTap 小游戏 | HTML | 项目入口与处理 |
| --- | --- | --- | --- |
| 启动与人物模式 | 发布场景和构建配置，不读取网页 URL | Web 模板和显式试玩参数 | `ChapterGame` 组合；`HtmlPreview` 封装 URL，小游戏固定使用构建资源与人物模式 |
| 登录 | `tap.checkSession` / `tap.login`，失败保留门禁 | `preview`，不模拟 TapTap 登录成功 | `PlatformServices` / `TapLogin`；游客仅为明确的小游戏 test 构建开关 |
| 存档与偏好 | `tap.getStorageSync` / `setStorageSync` 等 | Cocos `sys.localStorage` 的浏览器实现 | `PlatformStorage` 共用键接口与档位前缀；能力缺失不换后端，存档错误交给现有保护机制 |
| 地图迷雾、发型、技能名称 | 与主存档使用相同平台和档位命名空间 | 同样通过公共存储；发型可使用 HTML 试玩参数 | 已移除功能层直接使用 `sys.localStorage`；test / release 保留原键，dev 独立，不删除历史正常数据 |
| 屏幕常亮 | `TapScreenAwake` → `tap.setKeepScreenOn` | `HtmlScreenAwake` → `navigator.wakeLock` | `ScreenAwake` 契约；前台申请、后台／销毁释放；HTML 额外处理可见性、安全上下文和权限 |
| 窗口与系统菜单 | Cocos 窗口信息，补充 TapTap 菜单矩形及变化事件 | Cocos 窗口信息，不读取 TapTap 菜单 | `ViewportMetrics` 缓存，尺寸变化／回前台失效；继续使用原 Cocos 安全区布局 |
| WASM | 先 `tap.loadSubpackage`，再按包内路径实例化 | Cocos 下载字节，再用 WebAssembly 实例化 | `WasmModule`；小游戏缺接口不走浏览器下载，失败由现有 JS 算法降级处理 |
| 资源加载与缓存 | Cocos Asset Bundle 配合官方分包适配 | 普通 resources 或显式分包资源图预览 | `GameResources` / `AssetBundles`；复用依赖、引用计数与缓存，不在玩法里手写平台下载 |
| 前后台与输入 | Cocos 官方适配的生命周期与触控 | Cocos 生命周期、键鼠与触控 | `PlatformServices.lifecycle` / Cocos `Input`；共享输入归属、取消和恢复，不重复订阅 `tap` 触控 |
| 音频 | Cocos 官方适配播放器 | Cocos 播放器，遵守浏览器音频解锁限制 | `BackgroundMusic` / `AudioSource`；保留真实输入重试与后台暂停，不另造第二套播放器 |
| 自动更新 | `tap.getUpdateManager` | 不接入小游戏热更新管理器 | `TapUpdates`；HTML 标为 unsupported，不伪造已更新 |
| 内存告警 | `tap.onMemoryWarning` / `offMemoryWarning` | 不模拟小游戏原生告警 | `PlatformServices.memoryPressure`；支持时注册和成对清理，缺失时明确不支持 |
| 页面、文件与调试入口 | 不依赖 DOM/BOM、网页服务器或桌面文件路径 | DOM、URL、history 只存在于 HTML 适配／Web 模板 | `HtmlPreview`、Web 构建模板及 `serve-web.py`；Cocos 官方适配内部的垫片不作为业务可用 DOM 的依据 |
| 构建与交付 | 官方转换、身份和分包审计，ZIP 交付 | Web 导出和浏览器服务 | 共用构建锁与档位生成器；Web 试玩不升版、不冒充 TapTap 验收，具体版本规则见 `build-profiles.md` |

本轮没有新增云存档、网络服务、广告、支付或桌面入口能力。这些能力后续接入时，分别核对官方 API 和对应 HTML 需求，不能用本地存储、浏览器请求或模拟回调宣称已接入。

## 实现约束

1. 共用玩法、数据和状态契约；平台差异集中放入 `platform/`。已有 Cocos 适配足够时直接复用；确有差异时使用共同契约和各平台实现。不要为目录对称重复实现引擎已经适配的输入、音频或生命周期。
2. `tap.*` 仅从显式小游戏分支取得，统一使用 `readTapAPI`，再判断当前宿主是否支持。DOM、navigator、location、history 和 URL 解析只在 HTML 适配或 Web 模板中使用，模块导入本身不得读取这些全局对象。
3. 所有持久化数据通过 `PlatformStorage` 或转发它的 `PlatformServices`，包括 UI 偏好、地图探索、音频设置与诊断。dev 前缀统一应用于读取、写入、枚举和删除；不得回退读取或清除正常档位的数据。test / release 现有键保持兼容。
4. 能力不可用时，按功能语义返回“不支持”、降级或报错；禁止跨平台静默回退、模拟登录成功或以另一后端写入代替存档成功。可选常亮／偏好失败不阻断游玩；真实存档失败沿用双槽、写后校验与旧档保护。
5. 每项能力负责失败、异步结果、后台中断、前台恢复及监听清理；不因恢复而重复计奖、重复保存或重复注册事件。保留现有 JS 降级和资源生命周期。
6. 新增平台能力先核对当前官方文档、已安装官方插件声明及 Cocos 适配；不套用其他小游戏 API，不自行绕过引擎缓存或把平台分支散落到玩法层。

## 验证与证据

复用现有类型检查和规则检查，按改动检查平台隔离、前后台、存读档、档位命名空间与资源恢复。专项验证可用临时探针：HTML 放置会抛错的 `tap` getter，小游戏放置会抛错的 DOM／URL／浏览器存储 getter，确认错误平台的接口从未读取；这属于边界验证，不是平台验收。

分别记录 HTML 实际浏览器、Cocos 导出／官方转换、TapTap 平台和目标真机结果。不支持、权限拒绝、接口缺失及未验证项均如实记录。浏览器常亮受到安全上下文、权限及系统策略限制；浏览器接口请求或模拟回调通过，不能证明物理屏幕不会熄灭。

本轮源代码检查与验证见 `src/cocos/release/platform-adapters-validation.json`。未打包或上传时，不把已有 ZIP 标为包含本次修复。

## 官方依据

- [TapTap Cocos 官方适配与运行环境差异](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)
- [TapTap 分包加载](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/subpackage/)
- [W3C Screen Wake Lock](https://www.w3.org/TR/screen-wake-lock/)
- 已安装官方插件声明：`src/cocos/extensions/taptap-minigame-tools/tap-minigame.d.ts`（本轮版本 1.2.2）。
