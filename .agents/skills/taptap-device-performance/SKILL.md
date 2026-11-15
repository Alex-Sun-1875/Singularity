---
name: taptap-device-performance
description: 为剑与火（singularity）的 Cocos Creator / TapTap 小游戏连接 iPhone（macOS）或 Android（macOS / Windows）真机，采集帧时间、渲染计数与 JS 热点，分析并验证性能优化。用于真机卡顿、发热、内存和调试连接问题；旧 Maker / UrhoX / Lua 工程不适用。
---

# TapTap 真机性能调试

从当前项目根目录工作，先读该项目的 `AGENTS.md` 与 `src/cocos/AGENTS.md`。主工程是 `src/cocos/`、Cocos Creator 3.8.8；不把旧 Maker 的 Lua 调试代码接入主工程。

## 选择接入路径

- 首次连接、环境缺失或连接失败：读 [连接准备与排错](references/connection.md)，含共同准备、iPhone + Mac、Android + macOS / Windows、工具安装和结束清理。
- iPhone + Mac：按 TapTap 官方 Safari 流程打开可检查的运行容器；需要可重复采样时使用本技能 `scripts/ios_capture.py`（USB WebInspector）。这是辅助工具，不是 TapTap 官方 SDK。
- Android + macOS 或 Windows：均按官方 `adb forward` + Chrome DevTools 流程连接；按宿主系统选择连接指南中的 zsh/bash 或 PowerShell 命令。在小游戏执行上下文使用 `scripts/collect.js`，需要完整分析时录制 DevTools Performance。Android 不需要 iPhone 的 Python 依赖。
- 指标口径、A/B 对照、源码映射与报告：读 [采样和分析](references/measurement.md)。
- 排查本项目已有热点时：读 [项目定位与已验证案例](references/project.md)。案例只是查找线索，每次仍需新的证据。

## 工作顺序

1. 读取本机现有工具、连接设备和目标游戏版本。设备连上 USB 不等于游戏已暴露调试目标。只连接目标 TapTap 容器，页 ID 每次重新枚举；有多个候选时选明设备和目标。
2. 记录手机型号、系统、TapTap/小游戏版本、画布像素、帧率设置、场景、角色移动/战斗状态以及调试日志开关。确认手机运行包是否包含当前源代码。
3. 先采集不启用 JS profiler 的 15–30 秒帧基线，再单独录制热点。需要结论覆盖移动、战斗和长时间发热时，分别采样这些场景；静止采样不能代替它们。
4. 将热点关联到实际游戏源码或平台桥接。优先复用引擎和项目适配层解决重复计算/分配/桥接；不改帧率上限来降低负载。
5. 以相同设备、场景、画布和帧率做 A/B/A 或重新打包的前后对照。临时注入只能证明候选原因，不能证明新包已验收。改源码后运行现有 `npm run check`、`npm test`，并验证受影响的生命周期与触控。
6. 保存原始数据、结论、恢复结果和未验证项，明确 CPU/GPU/内存指标的范围。最后释放自己创建的采样监听、profiler、调试连接和 ADB 转发。

脚本采样限制为 1–60 秒，不生成测试角色、不改存档、不强制 GC，也不覆盖引擎 getter。需要人工操作手机时，提出具体操作，同时继续不依赖该操作的分析。已有授权内的代码优化和本地验证直接完成；本技能本身不授予上传、发布或修改真实存档的额外授权。

## 脚本

- `scripts/ios_capture.py list|snapshot|capture`：已配对 USB iPhone 的目标发现、快照、限时帧采样、可选 WebKit profiler 与源码导出；有超时和采样看门狗。
- `scripts/console_snippet.py snapshot|start|take|cleanup`：生成可粘贴至 Chrome/Safari 控制台的相同采集表达式。`--out` 直接保存 UTF-8 文件；`--copy` 仅用于 Chrome DevTools 的复制导出。
- `scripts/analyze.py <capture-directory-or-frames.json>`：统计 FPS、p50/p95/p99、draw calls、三角形和可用 JS/CPU 数据。输出 JSON，`--out` 可保存报告。
- `scripts/collect.js`：Cocos 帧采集实现，只供调试器执行，不能放入发布入口。

本技能正文和脚本统一在仓库 `.agents/skills/taptap-device-performance` 维护，根目录 `AGENTS.md` 提供发现入口。项目 `.claude/skills/taptap-device-performance`、旧路径 `tools/skills/taptap-device-performance`，以及本机 `~/.agents/skills/taptap-device-performance`、`~/.codex/skills/taptap-device-performance` 均链接到同一份内容。项目内链接使用相对路径；换电脑时如需个人级发现，再建立个人目录链接。

采用 [Agent Skills 格式](https://agentskills.io/specification)；目录兼容依据见 [OpenCode 技能发现](https://opencode.ai/docs/skills/)与 [Claude Code 技能目录](https://code.claude.com/docs/en/skills#choose-where-skills-load)。其他读取 `AGENTS.md` 的 agent 可沿项目入口读取，是否自动加载取决于各工具的技能发现机制。
