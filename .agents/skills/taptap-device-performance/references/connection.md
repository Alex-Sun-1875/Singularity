# 连接准备与排错

| 手机 | 电脑 | 调试入口 |
| --- | --- | --- |
| Android | macOS | Platform-Tools / ADB + Chrome DevTools，终端用 zsh/bash。 |
| Android | Windows | Platform-Tools / ADB + Chrome DevTools，以下命令用原生 PowerShell 5.1 或 7。 |
| iPhone | macOS | Safari Web Inspector；可选本技能的 USB 采样脚本。 |

先区分手机系统与电脑系统。Android 的两条路径具有相同的调试与采样流程，差异主要在工具路径、USB 驱动和 shell 命令。

## 共同准备

1. 准备能传数据的 USB 线，解锁手机并保持游戏在前台。记下设备型号、系统和 TapTap 版本；接入前先询问或枚举设备，不根据项目偏向 Android 推断当前手机。
2. 使用真实小游戏 AppID 和有自测权限的 TapTap 账号。开发者可以在后台小游戏的包体管理中配置自测用户。检查待测包版本与本地改动是否一致。
3. 加载游戏有两条路径：已有后台测试包的二维码；或 VS Code 的 **TapTap MiniGame Debugger**。插件应打开转换后含 `game.js`、`game.json` 的小游戏代码包根目录（本项目通常为 `src/cocos/build/<name>-package/game`），输入调试端口、真实小游戏 ID、名称并生成二维码。插件扫码路径要求手机和电脑在同一局域网，且本地服务端口可达；USB Inspector 连接与局域网资源下载是两件事。
4. TapTap 文档截至 2026-11-15 标注：插件扫码调试要求 Android ≥2.83.2 / iOS ≥4.58.0；后台测试包入口要求 Android ≥2.83.0 / iOS ≥4.55.0。执行时重新核对官方文档，不把这些历史最低值当作当前推荐版本。
5. 开启小游戏菜单中的开发调试并按提示重启。先确认加载和登录成功，再进明确场景。调试日志会产生性能开销，记录开关状态；正式体验结论要在对应日志配置下复核。

依据：[TapTap 真机调试](https://developer.taptap.cn/minigameapidoc/dev/dev-support/debugging/)。

## iPhone + Mac：官方 Safari 路径

1. 手机通过 USB 连接 Mac；如出现“信任此电脑”，由用户在手机确认并输入设备密码。Finder 可确认系统已识别手机。
2. iPhone 设置中搜索 **Safari → 高级 → 网页检查器** 并打开；新系统可能把 Safari 放在“App”列表内，以系统搜索为准。
3. Mac Safari → 设置 → 高级，打开“显示网页开发者功能”（旧版名称为“在菜单栏中显示开发菜单”）。这是 Web Inspector；不要误要求安装完整 Xcode 或开启远程自动化。
4. 在 TapTap 小游戏中打开开发调试并重启。出现调试提示后，Mac Safari → 开发 → 该 iPhone → 对应小游戏容器；连接后，在手机点击提示中的“确定”进入游戏。
5. 在 Inspector 中确认游戏 JS 和 Cocos 执行上下文。当前项目的 iOS 运行时在 `GameGlobal` 下；`typeof cc === 'undefined'` 不代表引擎没加载。先查看 `globalThis.GameGlobal?.cc`，需要全部引擎导出时才使用 `GameGlobal.System.import('cc')`。
6. Console 观察错误；Timelines 录制 JS/CPU 等可用轨道；不要在录制过程中暂停断点。设备级日志可在 macOS“控制台”选中手机，筛选子系统 `com.taptap.instantGame`。

依据：[WebKit 开启 Web Inspector](https://webkit.org/web-inspector/enabling-web-inspector/)、[Timelines](https://webkit.org/web-inspector/timelines-tab/)。

### iPhone：可重复的命令行采样

优先使用已经安装的 `pymobiledevice3` 环境。辅助工具通过已配对的 Apple USB WebInspector 服务连接，`autopair=False`，不会替用户确认信任。Safari 与脚本不能同时占用同一目标；使用脚本前关闭该目标的 Safari Inspector。

本项目已实测 `pymobiledevice3 11.55.0`。它是宿主调试依赖，GPL-3.0-or-later，不放入 Cocos 或小游戏包。安装前查看其[官方项目](https://github.com/doronz88/pymobiledevice3)及当前 Python 版本要求。使用独立 venv；以下环境名可调整：

```sh
python3 -m venv ~/.cache/taptap-device-performance/venv
```

本仓库禁止依赖下载走代理/TUN。下载前检查 `scutil --proxy`、代理环境变量及实际到包源的路由（如 `route -n get <源站解析的IP>`）。系统代理关闭仍可能经 `utun`；单独设置 `NO_PROXY` 不能绕过透明路由。确认直连后才运行安装，保留 pip report 中的来源和哈希；直连不通不自动切换代理，仍可用 Safari：

```sh
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy NO_PROXY='*' no_proxy='*' ~/.cache/taptap-device-performance/venv/bin/python -m pip install --index-url https://pypi.org/simple --only-binary=:all: --report /tmp/taptap-profiler-install.json 'pymobiledevice3==11.55.0'
```

以下命令在项目根目录执行，`TAP_PERF_PY` 改为实际已验证环境：

```sh
TAP_PERF_PY="$HOME/.cache/taptap-device-performance/venv/bin/python"
TAP_PERF_SKILL="$PWD/.agents/skills/taptap-device-performance"
"$TAP_PERF_PY" "$TAP_PERF_SKILL/scripts/ios_capture.py" list
"$TAP_PERF_PY" "$TAP_PERF_SKILL/scripts/ios_capture.py" snapshot
"$TAP_PERF_PY" "$TAP_PERF_SKILL/scripts/ios_capture.py" capture --seconds 20 --label standing-A --out src/cocos/test-results/performance/iphone-standing-A
"$TAP_PERF_PY" "$TAP_PERF_SKILL/scripts/ios_capture.py" capture --seconds 10 --label standing-profile --profile --sources --out src/cocos/test-results/performance/iphone-profile
python3 "$TAP_PERF_SKILL/scripts/analyze.py" src/cocos/test-results/performance/iphone-standing-A
```

输出目录须为新目录。多设备使用 `--udid`；多目标使用刚枚举的 `--page`，必要时加 `--application`。默认只选 `com.easyplay.taptap.now` 中未被占用且 URL 以 `tjapp://game-runtime` 开头的唯一容器；App bundle 改变时核实后使用 `--bundle`。脚本会对初次页面枚举做一次限时补查，以处理 App/页面列表到达顺序不同的情况；仍无目标时，进行一次有明确手机操作变化的重试，不无限轮询。

## Android + macOS / Windows：ADB + Chrome DevTools

两种电脑都准备 Chrome 和 Android SDK **Platform-Tools**。先检查已有 `adb`；缺失时从 [Android 官方 Platform-Tools](https://developer.android.com/tools/releases/platform-tools)选择对应系统的压缩包并解压，独立 Platform-Tools 即可使用。只用 Chrome 调试不需要 Python；下面生成表达式和分析 JSON 的辅助命令需要 Python 3 标准库，不需要 `pymobiledevice3`。

下载遵守仓库直连要求：检查系统代理、代理环境变量及实际到下载源的路由，排除透明代理/TUN。macOS 可用 `scutil --proxy`、`route -n get <源站IP>`；Windows 检查系统“代理”设置、`netsh winhttp show proxy`、代理环境变量和 `Find-NetRoute -RemoteIPAddress <源站IP>`，不能仅凭其中一项认定直连。使用明确禁用代理的下载方式，直连失败不切代理。

手机设置 → 关于手机，通常连续点击版本号启用开发者选项，再打开 **USB 调试**。用数据线连接电脑，解锁手机，出现 RSA 指纹提示时由用户确认“允许 USB 调试”；部分机型还需切换 USB 数据模式。

### macOS：终端准备与转发

macOS 通常无需额外 USB 驱动。先用 `command -v adb` 检查现有安装；下方 PATH 两行仅在需要时执行，目录换成实际 SDK 或独立解压目录。它只影响当前终端，不修改全局配置。

```sh
TAP_ADB_DIR="$HOME/Library/Android/sdk/platform-tools"
export PATH="$TAP_ADB_DIR:$PATH"
adb version
adb devices -l
```

从输出选择状态为 `device` 的目标，把 `SERIAL` 替换为真实序列号；`unauthorized` 或 `offline` 时先处理连接。

```sh
TAP_DEVICE_SERIAL='SERIAL'
adb -s "$TAP_DEVICE_SERIAL" get-state
adb -s "$TAP_DEVICE_SERIAL" shell getprop ro.product.model
adb -s "$TAP_DEVICE_SERIAL" shell getprop ro.build.version.release
adb forward --list
adb -s "$TAP_DEVICE_SERIAL" forward --no-rebind tcp:9229 tcp:9229
```

### Windows：PowerShell 准备与转发

使用 Windows 原生 PowerShell 和 Windows 版 `adb.exe`。先用 `Get-Command adb -ErrorAction SilentlyContinue` 检查已有安装。目录以实际安装为准；只有需要时才执行下方 PATH 两行，仅影响当前 PowerShell。路径中含空格也可使用。

```powershell
$TapAdbDir = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools'
$env:Path = "$TapAdbDir;$env:Path"
adb version
adb devices -l
```

也可不改 PATH，用 `& (Join-Path $TapAdbDir 'adb.exe') version` 这样的完整路径调用。若设备列表为空，检查 Windows **设备管理器**中的未知设备或 Android ADB 接口；按手机厂商安装适配的 [OEM USB 驱动](https://developer.android.com/studio/run/oem-usb)。MTP 文件传输可用不代表 ADB 接口驱动已正确安装。

从输出选择状态为 `device` 的目标，把 `SERIAL` 替换为真实序列号：

```powershell
$TapDeviceSerial = 'SERIAL'
adb -s $TapDeviceSerial get-state
adb -s $TapDeviceSerial shell getprop ro.product.model
adb -s $TapDeviceSerial shell getprop ro.build.version.release
adb forward --list
adb -s $TapDeviceSerial forward --no-rebind tcp:9229 tcp:9229
```

### 两种电脑共用的 Chrome 流程

上面的转发对应 TapTap 官方的 `adb forward tcp:9229 tcp:9229`，加 `--no-rebind` 防止覆盖已有转发。先看 `adb forward --list`：完全相同的映射可复用并记为非本次创建；9229 已占用时，选择空闲本机端口，例如 `tcp:9230 tcp:9229`，在 Chrome Configure 中添加 `localhost:9230`。设备端仍是官方 9229。

1. 手机打开 TapTap 小游戏 → 右上角菜单 → 开发调试 → 打开调试 → 重新进入游戏。
2. Chrome 打开 `chrome://inspect/#devices`，启用 Discover USB devices；必要时在 Configure 添加 `localhost:9229`。找到对应小游戏目标，点击 **inspect**。检查实际游戏源码，避免采到 Chrome 普通网页或其他 WebView。
3. 在 Console 的上下文选择器找到可访问 `globalThis.GameGlobal?.cc ?? globalThis.cc` 的游戏上下文。用下方短窗口采集帧数据；另开一轮 **Performance → Record → 在手机操作 → Stop** 查主线程、调用栈与长帧，保存导出的 trace。Memory 面板用于按需排查堆，不能用 JS heap 代表整个 TapTap 进程内存。
4. 采样时关闭 DevTools screencast，避免投屏改变负载。录制移动/战斗时说明操作路线、技能、敌人数量与持续时间，保持前后对照一致。

USB ADB 转发不要求手机与电脑同一 Wi-Fi；通过 VS Code 插件扫码下载电脑上的包时，仍需满足共同准备中的局域网条件。Windows 若此下载被防火墙阻止，只按需放行实际本地服务的专用网络入站端口。

依据：[Android ADB](https://developer.android.com/tools/adb)、[Chrome 远程调试 Android](https://developer.chrome.com/docs/devtools/remote-debugging)。这里不假设 Android 支持 iOS 的 `ScriptProfiler`/`CPUProfiler` 域。

## 共用帧采样：macOS / Windows

从项目根目录执行。`console_snippet.py` 只生成代码，不连接或执行设备。`--out` 直接写 UTF-8，避免依赖 shell 重定向的编码；尤其 Windows PowerShell 5.1 的 `>` 默认写 UTF-16LE，见 [PowerShell 编码说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding)。生成后先阅读，再把对应文件内容粘贴进小游戏 Console；不通过脚本自动关闭浏览器的反诈骗粘贴保护。

### macOS（zsh/bash）

先确认 `python3 --version`，再生成四个表达式。用本轮临时目录避免覆盖其他采样文件：

```sh
TAP_PERF_SKILL="$PWD/.agents/skills/taptap-device-performance"
TAP_PERF_TMP=$(mktemp -d "${TMPDIR:-/tmp}/taptap-perf.XXXXXX")
python3 "$TAP_PERF_SKILL/scripts/console_snippet.py" snapshot --out "$TAP_PERF_TMP/snapshot.js"
python3 "$TAP_PERF_SKILL/scripts/console_snippet.py" start --seconds 20 --label android-standing-A --out "$TAP_PERF_TMP/start.js"
python3 "$TAP_PERF_SKILL/scripts/console_snippet.py" take --copy --out "$TAP_PERF_TMP/take.js"
python3 "$TAP_PERF_SKILL/scripts/console_snippet.py" cleanup --out "$TAP_PERF_TMP/cleanup.js"
```

可用 `pbcopy < "$TAP_PERF_TMP/snapshot.js"` 复制表达式；按顺序换成 start、take。Chrome 执行 take 后，剪贴板已变成采样 JSON，先保存它再复制其他内容：

```sh
pbpaste > "$TAP_PERF_TMP/frames.json"
python3 "$TAP_PERF_SKILL/scripts/analyze.py" "$TAP_PERF_TMP/frames.json" --out "$TAP_PERF_TMP/analysis.json"
```

### Windows（PowerShell 5.1 / 7）

先确认 `py -3 --version`。若安装未提供 `py`，使用已确认是 Python 3 的 `python` 或解释器完整路径替代以下 `py -3`。读取的是仓库实体目录，不依赖 Mac 上的个人目录链接。

```powershell
$TapPerfSkill = Join-Path (Get-Location).Path '.agents\skills\taptap-device-performance'
$TapPerfTemp = Join-Path $env:TEMP ('taptap-perf-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $TapPerfTemp | Out-Null
py -3 "$TapPerfSkill\scripts\console_snippet.py" snapshot --out "$TapPerfTemp\snapshot.js"
py -3 "$TapPerfSkill\scripts\console_snippet.py" start --seconds 20 --label android-standing-A --out "$TapPerfTemp\start.js"
py -3 "$TapPerfSkill\scripts\console_snippet.py" take --copy --out "$TapPerfTemp\take.js"
py -3 "$TapPerfSkill\scripts\console_snippet.py" cleanup --out "$TapPerfTemp\cleanup.js"
```

可用 `Get-Content -Raw -Encoding UTF8 "$TapPerfTemp\snapshot.js" | Set-Clipboard` 复制表达式；按顺序换成 start、take。Chrome 执行 take 后，立即保存剪贴板中的 JSON：

```powershell
Get-Clipboard -Raw | Set-Content -Encoding UTF8 "$TapPerfTemp\frames.json"
py -3 "$TapPerfSkill\scripts\analyze.py" "$TapPerfTemp\frames.json" --out "$TapPerfTemp\analysis.json"
```

分析脚本接受 UTF-8 与 UTF-8 BOM；输出文件使用 UTF-8，支持中文标签和含空格的路径。最终把本轮数据、报告和 Performance trace 保存到 `src/cocos/test-results/performance/<本轮名称>/`，记录电脑系统、shell 与工具版本。

### 控制台执行顺序与回收

执行 snapshot 核对版本/画布；执行 start 后按场景操作，20 秒到期自动停止；在结束后的 20 秒内执行 take。Chrome 的 `--copy` 会把 JSON 复制到剪贴板。Safari 生成 take 时省略 `--copy`，保存控制台返回的 JSON 字符串内容，再运行分析脚本。

take 会释放采样数据，cleanup 可随时取消；失联后看门狗自动移除监听并在“采样时长 +20 秒”清除临时对象。每轮可用 `--key` 区分，但 start/take/cleanup 必须同一个 key；同一个 key 未释放时不会重复注入。

### 排错速查

| 现象 | 下一步 |
| --- | --- |
| iPhone 已连接但 targets 为空 | 解锁、把 TapTap 游戏置前台、确认 Safari 网页检查器和游戏开发调试都已开启，按官方流程重启并保留调试提示；确认没有其他 Inspector 占用。 |
| iPhone 握手超时/未配对 | 检查数据线、Finder 识别和手机信任确认；已有配对失效时由用户重新建立，不伪造配对记录。 |
| Safari 能连、脚本不能连 | 先断开 Safari Inspector；核对脚本依赖版本与目标类型，保留报错，可继续走官方 Safari 路径。 |
| ADB unauthorized | 解锁手机并确认 RSA 提示；如没出现，重新插线/重新启用 USB 调试，再看设备状态。 |
| Windows 找不到 adb / Python | 确认 Windows 版工具实际安装目录和当前 shell PATH；带空格的完整程序路径用 `& '实际路径'` 调用。`py` 不存在时改用已确认的 Python 3 解释器。 |
| ADB offline/列表为空 | 检查线缆、USB 数据模式、驱动及 Platform-Tools；先处理设备识别，转发不能修复 USB 连接。 |
| Windows 能浏览手机文件但 ADB 列表为空 | 在设备管理器核对 Android ADB 接口与 OEM 驱动，再确认手机 USB 调试和 RSA 授权。 |
| ADB device 但 Chrome 无小游戏 | 检查转发、Chrome Configure、游戏开发调试后是否重启、测试包权限和 TapTap 版本；确认手机没有停在别的 App。 |
| 端口占用/转发失败 | 查看现有转发与本地监听，复用相同映射或换本机端口，不删除他人映射。 |
| cc 未定义/没有帧 | 选择正确上下文，检查 GameGlobal.cc，确认场景已完成加载、游戏未被断点暂停或挂到后台。 |
| 电脑能打开本地服务但手机下载失败 | 检查同一局域网、防火墙、服务监听地址和二维码中的主机地址；不要在手机 URL 中使用电脑的 localhost。 |

## 结束

先保存记录并停止 profiler，再执行采集 cleanup，确认监听与临时对象已移除，关闭自己的 Inspector 会话。如果本轮创建了 ADB 转发，只移除这一条（换过本机端口则用实际值）：

```sh
# macOS，沿用本轮设备变量
adb -s "$TAP_DEVICE_SERIAL" forward --remove tcp:9229
```

```powershell
# Windows，沿用本轮设备变量
adb -s $TapDeviceSerial forward --remove tcp:9229
```

不要移除复用的映射、`--remove-all` 或无必要地 `adb kill-server`。需要测普通玩家表现时，在手机关掉游戏调试/日志并重启后复测，记录配置变化。

当前已有 iPhone + Mac USB 实测记录；Android + macOS / Windows 的连接与 DevTools 步骤依据官方文档整理。本次没有 Android 真机或 Windows 主机，不能把脚本本地检查标记为这两条连接路径已实机验收。
