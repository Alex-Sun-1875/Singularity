# 启动资源分包

2026-11-17：TapTap 下载的是完整分包。Cocos 单张纹理的低优先级不能阻止首次访问触发整包下载，因此不能用普通 HTML 的传输量或启动秒数代替小游戏结论。

`release/taptap.json` 的 `selectivePacks` 定义开局界面、HUD 图标、公共特效、战士特效／声音和首发武器。`prepare-taptap.py` 从原始 `.meta` 收集 UUID，在 `assets/bundle-groups/` 生成带 `Asset[]` 引用的入口 Prefab。Cocos 依赖收集与更高的 Bundle 优先级负责导出和去重；入口不在游戏中实例化，不移动或改写原画、模型及其 importer UUID，也不使用嵌套 Asset Bundle。

`ResourcePacks.ts` 同时生成目录路由与精确 UUID 路由。`GameResources` 只在明确的小游戏／分包资源图模式下使用精确路由，通过原生 `loadBundle`、`loadAny` 和公共缓存加载原资源；普通 HTML 保留原 resources 路径。加载失败沿用错误回调，不静默切换资源后端。`report-taptap.py` 对每个精确路由核对最终分包配置中的 UUID，缺失或空包必须阻止交付。

小游戏不在开局预热整套管理页面；按实际打开的页面加载。主菜单尚未开始游戏时不预取相邻地图和不播放的音乐，点击开始／继续后沿既有入口启动。可选寻路 WASM 等首帧完成后再准备，期间保留原 JS 算法。`[Startup]` 日志分别记录应用开始、基础分包、场景资源、人物与地图、战斗准备和可交互阶段，计时从应用组件开始，不代表平台总启动耗时，也不提前上报平台完成指标。

验证顺序：普通 HTML、`Build-Local.ps1 -ResourceBundles` 的资源图预览、统一 `npm run pack:taptap` 的正式转换与 ZIP 检查、真实 TapTap 包复测。分别记录完整上传包、首包、当前开局需要的完整分包量及实机耗时；完整 ZIP 的资源去重不等于可玩前资源已足够小。改动玩法或换存档、机型、网络后不能直接复用上一轮秒数。

## 加载预览与外观资源

`prepare-startup-preview.py` 使用 Pillow 从保留的加载背景 PNG 生成 1280×720、JPEG quality 90 的加载专用预览。`boot-loading.aliases` 仅在小游戏／资源图模式将原逻辑路径解析到该预览的原生 UUID；普通 HTML 仍使用原图。此替换只影响临时加载画面，不压缩人物或场景贴图。原图与其 UUID 不变，派生过程和哈希登记在 `source-art/ui/loading-taptap-preview-v1/provenance.json`。

四种发型贴图与四种头像分别打包，按实际保存的发型加载；角色 manifest 的发型材质声明 `parts: ['hair']`，避免身体材质预热同时拉取所有发型。`prepare-runtime-actor.cjs` 保留此声明。备用头像、骰子与 Boss 面板独立分包，开局真正使用的肖像和 HUD 图标进入 `boot-ui`，避免普通头像目录的依赖再次拉齐四种发型头像。保留发型切换与按需加载失败处理。

根目录音效明确从 resources 包过滤，由 `boot-sounds` 持有原始 UUID，防止目录级自动依赖反向扩大基础包。启动 UI 只保留当前控件版本及主菜单／设置公共组件，旧版本仍可在后续页面需要时通过原目录加载。

0.3.57 正常 test 包与 0.3.56 同一新旅程、S01-T1 起点、默认 curly 发型对照：包含基础文件、引擎分包和完整依赖分包的文件量从 50,561,981 降至 39,753,323 字节，减少 21.4%。保存 vergil／dante 发型的独立启动分别为 39.93／39.60 MB，均只请求对应外观。首包离线压缩约 1.65 MiB，完整上传 ZIP 251.82 MB；后续内容和加载原图仍保留在完整包中。这些数值不是平台传输量或实机秒数。证据见 `src/cocos/release/taptap-startup-resource-v3-validation.json` 与 `src/out/0.3.57/logs/`。
