# 工坊方图完整显示 v2

修复 v1 实际手机图片中，非剑方图上缘被房间裁切、下缘进入石台的边界问题。保持既有房间、文字、皮肤和触控范围：

- 非剑方图可用边长为 `min(136, 房间高度 - 石台高度 - 16)`，受限时上下各留 8 个设计单位，并使用自身高度定位。
- 桌面可容纳 136 方图时，保留原大小和原中心；剑的展示不改。
- 名称/品质列保留已验证的 12 设计单位横向间隔。

父代理执行标准 test 构建与独立冻结；`snapshot.json` 保存本轮 main/copy manifest。实际 Cocos QA 仅检查最终方图边界，没有重复冷加载、三个页签或 VFX。原预热源码未变，相关证据继续引用 `forge-cold-load-fix-v1/verification.json`；v1 已注明后续发现，不擦除历史记录。

`native-qa/report.json` 中两项均通过：

- 桌面 1280×636：方图仍为 136 设计单位；[最终图](native-qa/desktop-complete-square.png)。
- iPhone 14 横屏 844×390 / DPR 3：方图 90.7069 设计单位，顶部与石台各留 8.0000 设计单位，名称/品质各留 10.8923 逻辑像素；[最终图](native-qa/iphone14-complete-square.png)。

用真实 test 初始旅程和真实拥有的 W11 展示，等级保持 1，库存/穿戴未改，正常游戏运行，页面与控制台错误均为零。尺寸来自节点自身 contentSize/anchor 变换，避免把含后代的包围盒误当裁切边界。浏览器、服务均已退出。

本轮生产仅补 `ForgeWorkshop.ts` 的非剑高度/中心。所有源码保持 LF；`PreparationResources.ts` 与 v1 相同。用户美术确认、TapTap 真机和硬件安全区仍分别验收。
