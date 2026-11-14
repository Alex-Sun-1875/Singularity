# 旅店开场与石桥镇门面组合

本轮只调整 `S01-T1` 的开场家具、织物分区和灯具位置，`S01` 六栋已有建筑的门面与少量门旁功能组，以及 `S05` 林土地表上的低成本草地过渡。不代表全章场景美术完成。

## 实际接入

- 旅店入口的十二米整块地毯拆为短门垫和三块局部餐饮／会客织物，露出木地板。入口一桌、近侧一桌形成不对称前后景，保留中间出门通道与弥菈方向的通路。
- 开场与原旅店家具改用已安装的裸木圆桌，避免 `dining_table` 源模型自带亮黄色棋盘桌布。杯碗、书册、壶围绕餐饮、记账、备餐用途摆放。只移动既有两盏 180 lm 点光到实际桌面上方，没有增加实时灯数量。
- 石桥镇将灰泥面后退 0.6 米，在原建筑占地内加入石基、分段木柱、窗洞与深窗台。门上遮篷高于人物，门旁桶／工作墩与座凳形成小型功能组合。新实体采用保守旋转 AABB，同步进入 Navigation 和 Bullet；不改变建筑、任务、出口或地图坐标。
- Ground 材质与 UV 共同遵循 `SurfaceMaterials.ground(area)`，修复外景一概强制草地的覆盖逻辑。S05 使用原色林土底，路径边缘最多 54 块草色过渡，合并为一个共享材质的网格。每块 36 个三角形，上限 1,944 三角形；顶点透明度软化边缘，不增加碰撞或纹理。
- 原草地和林土的世界米制 UV、PBR 贴图、法线与粗糙度保留。草片高度逐点采样地形，低于道路，不改变原路线规划。
- 带纹理的原生箱体采用各面实际尺寸／材质米制 tile 缩放 UV，保留 Cocos 原始朝向、位置、切线和 Node 缩放。网格按尺寸及 tile 缓存，避免同尺寸物件反复生成。22×0.74×18 米石基的前后面重复 11×0.37 次、左右面 9×0.37 次、顶底面 11×9 次；独立地毯已有世界 UV，不再重复处理。

## 来源与所有权

继续复用 [Poly Haven CC0 资源记录](environment-fidelity-v2.md)及 [SHA-256 来源清单](environment-fidelity-v2-sources.json)，没有下载新模型、纹理或引入新依赖。BG3 本地参考只用于前中后景、功能组合与木石织物分区原则，不复用其图像、模型或纹理。场景只销毁自身的网格与材质，库中模型与贴图仍由 `EnvironmentAssets` 管理。

## 验证与画面证据

2026-11-05 已执行现有 `npm --prefix src/cocos run check` 与 `npm --prefix src/cocos test`：TypeScript 通过，95 项现有测试通过，未新增测试。

另以现有 Navigation 只读计算新增实体的完整包围盒：旅店出生点、5 个任务点和 3 个出口均不阻塞且可求路；石桥镇 4 个任务点、4 条 R1 道路和 6 个建筑门口均不阻塞且可求路。

第一轮 web-mobile 实际手机路线已走通旅店→石桥镇→劫车隘口→废磨坊村→白桦猎场，最终生命 120，场景无 failure、无 pageerror；另一次同构建的新旅程以真实触屏走到弥菈并打开对话。中间候选保留于 `scene-composition-route-review.json` 和 `scene-composition-after-phone-*.png`。该候选仍有结构 UV 拉伸及高不透明度的圆亮草斑，审图后已修 UV 和草片 alpha/边界，故这些之后图不是终稿。候选路线另记录 4 条敌方 bundle `index.js` 请求失败事件，运行人物、加载与后续路线正常，文件存在且 HTTP HEAD 200；最终构建还需记录具体 failure 文本，不能据此声称零网络失败。

之前的正常镜头已独立保留为：

- `src/cocos/test-results/scene-composition-before-phone-inn.png`
- `src/cocos/test-results/scene-composition-before-phone-town.png`
- `src/cocos/test-results/scene-composition-before-phone-S05.png`

以上之前画面来自此前实际发布版；不是本轮效果图。最终之后画面必须来自含 UV／低透明草片的新 web-mobile 发布构建，不能用临时夹具或状态跳转冒充真实游玩。

## 最终正常镜头复核

最终证据为 915×412、Android UA 的 Chrome 触屏仿真，使用真实摇杆与按钮、正常跟随相机；不是物理手机性能测试。汇总位于 `src/cocos/test-results/scene-composition-final-review.json`。

- `scene-composition-pre-frame-fix-town-review.json`：真实触屏从旅店走到弥菈、打开对话／拒约，再出门并走到 S04；0 pageerror、0 requestfailed、生命 120。实际 S01 石基 UV 符合 11／9 次重复；32 份 Navigation／Bullet 足迹逐项匹配，没有缺项。该报告所在构建随后只修正了 S01 两类门窗框的 Z 层次，不影响上述 UV、碰撞和 T1。
- `scene-composition-final-s05-review.json`：恢复上一条真实跨区旅程的存档后，在 S05 短程触屏步行；0 pageerror、0 requestfailed、生命 120。Ground 实际引用 earth、GrassCover 引用 grass，alpha 最高约 0.38；25 份 Navigation／Bullet 足迹匹配。该构建之后仅改 S01 门窗框位置，未改 S05。
- `scene-composition-final-town-review.json`：最后一次构建实际从旅店南门走到同一镇窗边及门边。门窗框实心箱体已移至墙内，窗玻璃／窗格和原木门正常露出；0 pageerror、0 requestfailed、生命 120。窗框 localZ=-8.64、窗面 localZ=-8.895，外侧窗面确实在框体之前。最后构建不再改源码。

最终图：`scene-composition-final-phone-inn.png`、`scene-composition-final-phone-town-window.png`、`scene-composition-final-phone-town-door.png`、`scene-composition-final-phone-S05-road.png`。坏窗框图另存 `scene-composition-pre-frame-fix-phone-town-window.png`，供核对遮挡修正。初始旅店之前图的视口尺寸不同，只用于定性组合比较，不是逐像素 A/B。

本轮最明确的改善是旅店中央空出木地板、裸木桌组与局部织物的前后景，以及镇门近景的真实米制石纹和可见门窗层次。S05 亮圆草斑已经收敛，但林土与道路共用 earth，路色差仍弱；森林群落密度、建筑主体轮廓和全章场景制作质量仍有后续空间。
