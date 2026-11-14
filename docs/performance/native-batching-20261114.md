# Cocos 原生合批复查（2026-11-14）

用户要求整体按 Cocos 原生方案继续优化，能合并的层合并，同时保留已确认的画面、交互、伤害／暴击／MISS 飘字和野外怪群提示。不改帧率、分辨率、怪物数、规则或现有素材清晰度。

## 已核对的原生方案

- [Sorting2D](https://docs.cocos.com/creator/3.8/manual/en/engine/rendering/sorting-2d.html)：不改触控节点层级，通过原生渲染顺序使相同纹理／材质相邻。
- [2D 合批条件](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-batch.html)：Sprite 与适当缓存的 Label 可以满足共享纹理等条件；Mask、Graphics 不能靠排序直接合成同一批。相同变换、材质和刷新条件的路径可直接画进同一个 Graphics，无需自定义 assembler。
- [3D MeshRenderer](https://docs.cocos.com/creator/3.8/manual/en/engine/renderable/model-component.html)、[BatchingUtility](https://docs.cocos.com/creator/3.8/api/en/class/BatchingUtility)：复用现有实例化、同材质网格合并；静态合并仍需检查剔除粒度和额外几何量。

本机安装的 Cocos 3.8.8 源码另确认：UIStaticBatch 已弃用，其 markAsDirty 不提供本轮需要的 Graphics 合并能力，未采用。没有引擎私有修改、全局渲染钩子、帧钟修改或跳过 GPU 上传。

## 本轮已接入的两项

**地图工具底图。** Hud.roundButton 可显式接收底图排序，仅地图工具使用。四个圆形工具底图统一为 -30；小地图金边与方位字为 -40，保持原来的覆盖顺序。技能栏沿用现有排序，其他按钮、补给弹窗、设置弹窗不套用这组底图参数。金边和方位字与工具底图存在实际重叠，不能只把底图提前而忽略原覆盖关系。按钮父节点、命中形状、图标与按下时的缩放目标均保持原样。

**小地图普通／任务标记。** 原 MinimapPins 与 TaskRadarFlags 同属 ChartCircle 坐标系、同材质、同刷新节奏，任务标记改为追加到已有 pins Graphics。普通标记→任务标记→独立首领皇冠→独立玩家箭头的覆盖顺序不变。任务为空时只停止追加任务路径，不隐藏普通标记。任务选择、坐标、离屏箭头、阻塞颜色、首领提示与 inspect 输出均不变；更新仍使用已有 200 ms 节奏。

没有新增纹理、图集、美术资源或依赖。新增排序声明由 MiniMap 的 MINIMAP_RENDER_ORDER 统一提供给 Hud。

## 实际构建与画面／交互验证

最终构建 `perf-desktop-native-layers-v2-20261114`，Creator 于22:37:04记录 Finished（build阶段1分29秒）；执行 legacy forward、ABI3 33561B导航WASM及branding后处理。原始第一版构建保留，未覆盖。当前57份变更源码与资源与独立编译快照逐字节一致，根版本仍0.3.40；记录在 `test-results/performance/native-layer-final-acceptance/source-verification.json`。本轮只修改 Hud.ts、MiniMap.ts 和本审计说明；工作树同期其他改动保留。

参考 MiniMap 直接加载上轮不可变构建 `perf-desktop-panel-atlas-20261114` 的真实编译模块，只在忽略目录的 QA 中使用。参考节点放回原构造顺序，比较同一冻结状态的原／新／恢复，世界相机仅在 QA 中关闭以隔离透明 UI。正式游戏未关闭世界相机。

| 队列 | normal 绘制（原／新／恢复） | 无任务标记 | 其他七种状态通常减少 |
| --- | --- | --- | --- |
| 默认Web，1608×768 DPR1 | 79／76／79 | 78／76／78 | 3次 |
| 启动即图片清理，1608×768 DPR1 | 85／81／85 | 84／81／84 | 4次 |
| 启动即图片清理，844×390请求DPR3 | 85／81／85 | 84／81／84 | 4次 |

三队列均包含 normal、no-task、boss-target、overlap、offscreen、blocked、supplies、settings、pressed 九种状态，共27组、81张截图。每组三角形数相同，按钮位置／尺寸／目标缩放／可用状态相同，MiniMap.inspect 逐字段相同；最大像素通道差均1/255，无像素差大于3。手机队列沿用引擎现有像素比限制，实际画布1688×780，未将请求DPR3误报为实际DPR3。已查看手机尺寸整体缩略图。

原始结果：

- `test-results/performance/native-layer-final-web-qa-v1/`
- `test-results/performance/native-layer-final-cleanup-qa-v1/`
- `test-results/performance/native-layer-final-phone-qa-v1/`

早先 `native-layer-compiled-cleanup-qa-v1` 和 `native-layer-priority-prototype-qa-v1` 的临时参考 MiniMap 插在 MapTools 后面，与真实原版构造顺序不符；UI夹具也曾保留新增的 boss 字段。两个目录另存 acceptance-review.json 标为不采纳，失败像素记录未改写。修正节点顺序和完整恢复夹具后，priority-prototype-qa-v2通过；上述最终三组使用实际编译优先级，未在运行时补生产排序。

完整 TypeScript 与本轮源文件空白检查通过。当前验证证明原生绘制批次减少和画面／交互等价；没有新的计时对照，不把3／4次提交直接换算为CPU或GPU百分比。

## 其他层的现状与继续检查项

最新只读 census 在 Director.EVENT_BEFORE_COMMIT 采集完整批次；Root 在 AFTER_DRAW 前已清理批次，早先采得空批次的目录不用于判定“没有绘制”。材质采用运行时对象身份区分，不用运行时 Material 可能为空的 UUID 推断相同材质。

`native-layer-final-census-v2` 的 H12 快照有155个活动 MeshRenderer／SkinnedMeshRenderer、81个2D批次。81块地表共享同一原生材质，当前相机视锥只覆盖其中4块；6块道路只覆盖1块。岩石等场景装饰使用共享材质，已启用原生 instancing。角色服装已有同材质的 Mesh.merge，其他部位含不同纹理、材质、骨骼及独立变换；战斗特效已有共享材质与有界原生池。

小地图地形、迷雾、普通／任务标记、皇冠、玩家箭头仍有不同的变换、覆盖关系或更新条件；不能单凭节点相邻便合为一个长期重绘层。独立更新、移动和透明淡出的怪物血条／名称／战斗飘字不做全局重排。

以下继续记录地形空间合批的实际评估，以及公共面板的进一步合并。整体 CPU/GPU 百分比不从提交次数外推；TapTap AppID、平台真机与手机功耗仍按既定范围待后续阶段验证，本轮未打包或上传。

## 地形空间合批：已评估，未接入

在最新不可变构建中，用公开 Mesh.merge 临时组合原有地块；位置／UV／材质／深度状态和连续 GroundCollision 碰撞网格均保持原状。比较2×1、1×2、2×2、3×3四种空间分组，每种七个相机平移位置。81块地表原有37,752三角形、655,152字节网格数据；分组后的全图三角形与数据量相同，活动渲染器分别45／45／25／9个。28组画面对照最大差1/255，没有源网格或碰撞变更。

主视角原有4块地形、2,048三角形。2×2组合仍有4个组与视锥相交，绘制提交没有减少，地形变成8,192三角形；3×3组合少2次提交，但地形变成9,216三角形。其余六个相机位置中，3×3少1–3次提交、额外增加6,560–15,680三角形。见 `terrain-native-merge-screen-v1/{report,pixel-comparison}.json`。

进一步对3×3做同页B-A-A-B四窗45秒连续移动战斗，每窗重新构建同一H12/Lv17/BOW夹具并持有两组资源，60秒实际战斗预热。使用公开网格 API，无分析器、GPU查询或截图；WDDM读取在CPU窗外，均有真实命中、技能、击杀、自然刷新和移动，0脚本／图形／并行构建错误。

| 窗口 | 合并 | CPU，100%=1核 | 主线程ms/帧 | 绘制p50 | 三角形p50 | GPU 3D忙碌度 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| B0 | 3×3 | 78.847% | 4.706 | 127 | 119082 | 14.893% |
| A1 | 原分块 | 85.610% | 5.186 | 131 | 111774 | 15.003% |
| A2 | 原分块 | 86.863% | 5.319 | 130 | 111748 | 12.261% |
| B3 | 3×3 | 85.295% | 5.125 | 128 | 122903 | 12.042% |

观察加权均值CPU低4.83%、主线程低6.42%、GPU忙碌度低1.21%，但合并版CPU首尾自身漂移约8.18%，GPU整个序列也有明显时段漂移；最终相邻对照差异明显小于首组。不能据此批准稳定净收益。实际帧率本队列约60FPS，与早先约56.8FPS不同；60FPS设置、分辨率和质量未改，未将不同实际节奏报告混算。原始记录 `terrain-native-merge-baab-v1/comparison.json.retained=false`，SceneBuilder.chunkedGround继续保持cells=16。原型只在忽略目录，未把更粗的剔除和额外几何写入游戏。

## 公共金框：阴影与底色在共享组件内合并

DoubleGoldFrame原有阴影与底色在同一坐标系、同一生命周期，底色紧随阴影绘制；现在把底色路径直接追加到阴影的原生 Graphics。删除独立GoldFrameBase节点。矩形、胶囊的原半径、描色、透明度、材质贴图、金边、徽饰和异步资源版本保护不变。

QuestTracker与AutomationHud先前各自调用batchHudFrameBase追加底色，再禁用原底色Graphics；现在在共享组件中完成，两个功能不再修改生成后的装饰几何，移除HudFrameGeometry.ts及其.meta。任务栏／挂机栏此前已有的合并结果保持，设置、背包、技能、技能说明等其他共用金框面板也能少一个Graphics提交。没有新增纹理、字体、遮罩或第三方依赖。

实际构建 `perf-desktop-native-frame-base-20261114`，Creator于22:56:21记录Finished（build阶段1分34秒），完成legacy forward、33561B ABI3 WASM与branding后处理。现有完整TypeScript与空白检查通过；62项变更／删除路径与独立编译快照一致，其中60项文件存在、2项旧辅助文件两侧均已移除，版本仍0.3.40。见 `native-frame-base-acceptance/source-verification.json`。

原／新／恢复参考采用修改前真实TypeScript的resize与HUD辅助函数体，用项目已安装的TypeScript编译，仅为忽略目录中的参考，不修改生产引擎。检查normal、supplies、settings、inventory、checks、automation、quest-expanded、description、map，以及带徽饰面板、胶囊、半透明填色／父透明度、尺寸变化四种公共组件状态。保留原金边前置关系，资源ready后再捕获。

默认Web、启动即图片清理策略、844×390手机横屏三组各13状态，共39组、117张截图，最大通道差均1/255，三角形数、按钮位置／尺寸／缩放／可用状态相同。设置、背包、技能、技能说明每组各少1次提交；正常HUD、补给、展开挂机／任务栏、地图维持既有提交数。四种独立公共组件状态也各少1次提交。手机实际画布仍1688×780。见 `native-frame-base-{cleanup,web,phone}-qa-v1` 和 `native-frame-base-acceptance/visual-acceptance.json`。

此项无需外围功能查找内部装饰节点后重画，公共组件自行保持正确顺序。没有降低帧率、删除攻击飘字或野外怪群提示。没有将未采纳的地形试验百分比归到当前版本。

## 最新版本连续战斗与下一项

复用farm.cjs的desktop／smoke／H12／显式Lv17／BOW／move，60秒实际战斗预热后重置夹具，完整测量60秒。移动201.43米、17击杀、10自然刷新，85普通命中与29技能命中，角色存活、正常手动输入、有限药水。FPS59.977、最低一秒58、P99 20.9ms、主线程4.912ms/帧、绘制p50为129。移动、战斗、渲染和采样覆盖检查完成，0脚本／图形／并行构建错误。

原始报告 `native-frame-base-moving-60s-v1/report.json` 仍为failed：既有1000MB进程族RSS硬预算失败，峰值1303.71MB，未更改预算或改写失败。`native-frame-base-acceptance/runtime-review.json`单独登记功能覆盖完成、完整内存预算未通过。这是当前约60FPS队列的绝对数据，不与早先约56.8FPS队列计算新收益百分比。

继续复查发现四张公共金框贴图还适合分成两对原生图集：矩形底纹／边框均512×512，胶囊底纹／边框均512×128。以2像素复制边缘、保留原九宫格参数和原双线性无mip采样打包，预估两张1032×516、1032×132纹理合计比原四张增加53,504字节（52.25KiB）。实际PNG体积、像素、合批和资源生命周期尚待验证，未接入生产图集。

上述是四张贴图的初步预算；实际配对图集的实现与验证见下节。地图／标记合批及公共Graphics合并均已保留，地形粗分组未保留。

## 公共金框贴图图集与预热统一

进一步核对后，准备界面的D.frame.asset还使用512×512的double-gold-frame-rpg-v4边框，且原预热层始终加载它。因此矩形图集纳入底纹、标准边框、RPG边框三张图，尺寸1548×516；胶囊图集纳入底纹、边框两张图，尺寸1032×132。两者保留全部原始RGBA像素和两像素复制边缘，无缩放／旋转／生成式编辑／mip。原图区和全部边缘逐像素等于原图及其clamp边缘扩展，九宫格参数、originalSize与节点缩放保持原样。

UiSkin沿用已存在的原生SpriteFrame区域路径，仅在dynamicAtlasManager.enabled=false时选择静态图集；默认Web策略继续读取原图。新增GoldFrameAtlas.ts由原有Pillow工具生成，纹理、来源、哈希与布局均有provenance。没有自定义材质、运行时拼图或渲染器私有访问。

首次图集构建发现PreparationResources直接加载原图，导致原图与图集重复常驻。现由UiSkin.texturePath统一解析绘制和纯纹理预热的路径，预热先去重再加载实际纹理，仍不租用可绘制SpriteFrame。新图集不引入额外永久框架租约；维持既有PreparationResources整场景预热生命周期。初始四图方案不是最终版本，相关报告另存acceptance-review，未覆盖原始数据。

最终构建 `perf-desktop-native-frame-atlas-v3-20261114`，Creator于23:27:52记录Finished（build阶段1分37秒）；完成legacy forward、33561B ABI3 WASM及branding。首次准备构建曾因输入目录未齐导致配置缺失退出，失败日志以attempt1-missing-config保留；补齐后重试。V1／V2中间构建保留，最终选择V3。

小游戏对应启动策略和844×390手机横屏各13种原／新／恢复对照，共26组、78张截图，通过原生原图参考。状态与上一节公共组件验证相同；三角形、按钮位置／尺寸／目标缩放／可用状态一致。常驻HUD、补给、任务展开、地图每组再少2次提交；设置、技能说明、展开挂机每组少3次；背包、技能页少2次。四种独立公共组件状态均少3次。桌面最大通道差1/255；手机设置页为3/255，其余不超过1/255，无像素差大于3。

| 最终图集对照（图片清理策略） | 原图／图集／恢复 draw |
| --- | --- |
| 常驻HUD | 81／79／81 |
| 设置 | 121／118／121 |
| 背包 | 217／215／217 |
| 技能 | 222／220／222 |
| 展开挂机 | 87／84／87 |
| 技能说明 | 89／86／89 |

原五张纹理GFX合计3,670,016字节，新两张3,739,968字节，净增69,952字节（68.3125KiB）。原图在图集队列的启动GFX均为0，预热纹理数量由93降至90；默认Web队列的两个新图集GFX均为0。两张PNG合计116,605字节，原图仍保留；这是新增PNG体积，不是TapTap首包或可玩前资源变化，未重新打TapTap包。GFX计数也不等于驱动实际物理显存分配。

正式资源探针在正常Director循环中创建／销毁临时标准、胶囊面板，四轮后FrameCache租约、条目和图集引用均回到基线；真实ChapterGame节点销毁后两张图集引用、GFX和预热纹理计数全部归零。默认Web也通过四轮和销毁测试，且未分配新图集。

首次资源探针未停止注入输入驱动，驱动在Cocos清空已销毁Component字段后继续读session，导致错误并中断帧事件；第二版快照又从已销毁Component读preparationResources。两个问题都在忽略目录的探针，未修改游戏以适配探针。最终使用独立观察引用，并先将测试输入置空再触发真实销毁。最终采纳 `gold-frame-atlas-final-resources-v3` 和 `gold-frame-atlas-final-web-resources-v2`，均0错误；此前失败报告与acceptance-review保留。

源文件与资源、删除的旧辅助模块及生成器共74项均与独立编译快照相同，完整TypeScript和本轮空白检查通过。证据集中在 `gold-frame-atlas-final-acceptance/{source-verification,visual-acceptance,atlas-budget}.json`。没有把这些提交减少换算为新的整体CPU／GPU百分比。

## 本轮收尾与验收边界

最新V3构建复用原有farm测量代码，仅在忽略的包装器中于引擎启动前设置图片清理策略；磁盘settings没有强制写入该开关。H12/Lv17/BOW、19怪4远程、正常移动输入、真实伤害、有限药水和自然刷新不变，60秒预热后完整测量60秒。实际59.979FPS、最低一秒58、P99 20.4ms、15击杀、11自然刷新、114次普通／技能命中，移动204.77米；角色存活，移动／战斗／采样检查完成，0脚本／图形／并行构建错误。

原报告 `native-frame-atlas-moving-cleanup-60s-v1` 保持failed，原因只有既有1000MB进程族RSS硬预算，峰值1285.73MB。未放宽预算，不称完整性能预算通过，也不把此图片清理队列与前一默认Web队列算成收益。副本说明位于 `gold-frame-atlas-final-acceptance/runtime-review.json`。

本轮已完成常驻HUD、小地图、公共面板、地形、装饰实例化、服装同材质合并及特效池的原生方案复查。保留地图工具排序、小地图普通／任务标记合并、公共面板阴影／底色合并，以及公共金框图集和统一预热；更粗地形组合没有足够稳定净收益，保持现有16格剔除。独立更新、不同变换、透明淡出、遮罩、材质或骨骼条件不兼容的层维持各自职责。没有引入自定义渲染器、改帧钟、删反馈或改画质来制造数字。

三项生产改动的分阶段原／新／恢复画面对照合计92组（27＋39＋26），源码和实际构建一致，资源驻留与销毁验证通过。逐项完成审计见 `gold-frame-atlas-final-acceptance/completion-audit.json`；原有RSS预算和真实TapTap／手机验证明确登记为尚未解决的外部验收项。当前范围的本地原生合批复查收尾，不声称手机高占用已解决，也没有新的整体CPU／GPU百分比。

本地预览：`http://127.0.0.1:7582/desktop-native-frame-atlas-v3/?view=2d&player=3d`。根版本仍0.3.40，未制作或上传TapTap包。
