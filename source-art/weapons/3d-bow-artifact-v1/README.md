# 拉弓时异常三角面片修复

用户截图为弓前方出现棕色大三角面。已在相同旅店、位置、朝向及拉弓阶段复现：[原图局部](reference-crop.png)、[实际复现与修复对比](runtime/bow-artifact-before-after.jpg)。

直接原因是构建缓存 `temp/asset-db/.../build1.0.1/release.json` 保存了另一版本的弓网格结构，实际打包的 `library/*.bin` 则是当前数据。以 W07 为例，旧结构最后一段 morph 数据结束于 755112 字节，当前原生网格只有 655272 字节；其他子网格的顶点布局也不同。于是 Cocos 16352 / Invalid typed array length 报错，部分表面被错误拉伸为用户看到的三角面。单看箭矢是否发射或节点是否 active，无法发现这种引擎日志错误。

本次检查了 17 份形变网格缓存，将七把弓共 14 份错配缓存移入 `temp/morph-cache-backup-...` 备份，让原生 Cocos 构建重新生成；没有删除角色/武器源素材，也没有手工调整网格偏移去遮掩错误。[缓存修复与备份记录](cache-repair.json)。

[构建前检查工具](../../../src/cocos/tools/refresh-morph-build-cache.py) 已接入 [Build-Local.ps1](../../../src/cocos/Build-Local.ps1)：比较形变网格结构、哈希、原生数据长度；遇到过期构建缓存会备份并刷新，若 library 本身已经不一致则停止构建。复用 Cocos 缓存重建及项目已有 Python 标准库，无新依赖、图片生成或资源下载。

通过现有类型检查、web-mobile 构建和实际引擎检查：RTX 3080 / D3D11 中相同拉弓/松弦/恢复过程 18 个画面，七把弓八向搭箭、飞行朝向和收回；剑/双手剑/法杖挂载回归。还检查了 30 段实际加载的形变数据范围，全部落在对应原生缓冲内，控制台引擎错误和页面错误均为零。[相同场景检查](runtime/after/report.json)、[七把弓及形变数据范围](runtime/all-bows-review.json)。此前软件渲染/硬件渲染固定姿势检查是独立的旧正确构建，见 runtime/before、runtime/hardware、runtime/inventory；真正的异常来自 runtime/current 对应的当前发布包。

角色 GLB、四款发型、全部动作与七把弓 FBX 保持原样，见 [资源保护记录](preservation.json)。本轮将完整当前 assets 同步到现有 C 盘构建镜像后构建，以保留同期的其他游戏修改，见 [暂存记录](stage-record.json)。

[接入记录](install-record.json)、[本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&revision=bow-artifact-v1)。
