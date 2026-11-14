# 第一章环境素材接入 v2

2026-11-04。范围是 Cocos Creator 3.8.8 的场景网格、室内陈设和环境细节。人物、HUD、战斗与镜头由各自模块负责。

## 实际变化

- 桌、椅、凳、书架、书、酒桶、木箱、宝箱、灯笼、陶壶、木碗、烛台、石火塘与木门改用 Poly Haven 发布的 CC0 模型。保留原 UV、漫反射和法线信息，按运行预算离线减面。
- 树木采用 `tree_small_02` 原作者 `.blend` 内的 LOD1，按树干、枝条、叶片分材质处理；叶片使用作者 GeometryNodes 的 2576 个枝叶簇位置，投影为 5152 个三角面的标准透明卡片，整树 8052 个三角面；岩石有六种源网格，蕨类四种、草丛四种。运行中共享网格与材质，旋转和缩放提供变化。
- 第三杯旅店当前两组裸木桌椅和桌灯位于 `(-2.8,-9.8)` 与 `(1.8,-2.8)`；2026-11-05 布局数据共增加 8 件有实体足迹的家具。新增家具的碰撞体与寻路阻挡一致，每次场景实例单独建立，不写入全局 WorldData。原任务、角色、出入口和已有障碍坐标保持。
- 旅店增加会客区织毯、灶间石面、门槛、窗扇、窗格、墙裙和壁灯；降低整屋木地板的纹理重复频率。靠镜头的围墙用低墙表现，保持人物可读性。
- 外景用真实草丛、蕨类、树桩与小岩石填充路肩；散布避开任务物、出口、水体、出生点和实际寻路通道。地理、河流、桥、主要建筑体量仍来自 v3 地图。

## 成熟资源、许可与来源

资源均来自 [Poly Haven 官方模型库](https://polyhaven.com/models)，许可是 [CC0 1.0](https://polyhaven.com/license)。2026-11-04 检索官方页面与公开 API，下载后验证官方 MD5，另记录 SHA-256。可用于商业游戏与改作；保留来源是项目的追溯措施。没有把 BG3、Larian 资源或本地参考图写入游戏素材。

| 用途 | 官方源模型 |
| --- | --- |
| 餐桌 | [Dining Table](https://polyhaven.com/a/dining_table) |
| 圆桌 | [Round Wooden Table 02](https://polyhaven.com/a/round_wooden_table_02) |
| 椅子 | [Wooden Chair 01](https://polyhaven.com/a/WoodenChair_01) |
| 凳子 | [Wooden Stool 01](https://polyhaven.com/a/wooden_stool_01) |
| 书架 | [Wooden Bookshelf Worn](https://polyhaven.com/a/wooden_bookshelf_worn) |
| 酒桶 | [Wine Barrel 01](https://polyhaven.com/a/wine_barrel_01) |
| 木箱 | [Wooden Crate 01](https://polyhaven.com/a/wooden_crate_01) |
| 宝箱 | [Treasure Chest](https://polyhaven.com/a/treasure_chest) |
| 灯笼 | [Wooden Lantern 01](https://polyhaven.com/a/wooden_lantern_01) |
| 陶壶 | [Jug 01](https://polyhaven.com/a/jug_01) |
| 木碗 | [Wooden Bowl 02](https://polyhaven.com/a/wooden_bowl_02) |
| 烛台 | [Wooden Candlestick](https://polyhaven.com/a/wooden_candlestick) |
| 书 | [Book Encyclopedia Set 01](https://polyhaven.com/a/book_encyclopedia_set_01) |
| 苔岩 | [Rock Moss Set 01](https://polyhaven.com/a/rock_moss_set_01) |
| 树 | [Tree Small 02](https://polyhaven.com/a/tree_small_02) |
| 蕨类 | [Fern 02](https://polyhaven.com/a/fern_02) |
| 火塘 | [Stone Fire Pit](https://polyhaven.com/a/stone_fire_pit) |
| 木门 | [Large Castle Door](https://polyhaven.com/a/large_castle_door) |
| 树桩 | [Tree Stump 01](https://polyhaven.com/a/tree_stump_01) |
| 草丛 | [Grass Medium 01](https://polyhaven.com/a/grass_medium_01) |

逐文件 URL、官方 MD5、SHA-256 与下载字节数见 [来源清单](environment-fidelity-v2-sources.json)，同一清单也保留在 `src/cocos/asset-pipeline/environment/sources.json`。派生文件的 SHA-256 位于 `assets/resources/environment/manifest.json`。

## 接入与预算

使用引擎已有的 `BufferAsset`、`MeshRenderer`、标准 PBR、法线贴图、Alpha Test 和 GPU instancing，无新增游戏依赖。法线所需切线复用现有 Three.js `withTangents` 适配器。自定义代码负责装配、单位换算、资源管理和地图尺寸适配；建筑外壳、桥梁和墙体仍由地图参数生成，因为它们需要精确对应既有地理与碰撞，而不是把一套现成村落套在地图上。

库包含 31 个模型变体、24 个共享材质。道具贴图为 512px，树和岩石的颜色为 1024px，所有法线为 512px。以 RGBA8 计算基础纹理约 60MiB，包含完整 mip 链约 80MiB；这是环境库的解压预算，不以 PNG 文件大小代替显存。整库约 25MB 磁盘数据，最终数值以资源清单为准。

植被源 glTF 的 JPG 漫反射不携带透明通道，即使材质标记为 MASK/BLEND。管线额外下载官方 Alpha PNG，将其合入 RGBA 颜色贴图，运行时使用 Alpha Test 与双面叶片，避免整块不透明叶片矩形。小草、蕨类、书与餐具不投动态阴影。旅店仅有两盏固定原生 PointLight，不为每件灯笼建立动态灯。

`await SceneBuilder.preload()` 必须在首次建场景前完成。每个场景的 `destroy()` 只销毁该场景的节点、程序网格和材料；环境库的共享网格、纹理与材质持续复用。离开整章时，先销毁所有 SceneBuilder 节点，再调用 `SceneBuilder.releaseAssets()`，统一释放共享库。切地图时不可释放库。

## 复现与检查

离线管线位于 `src/cocos/asset-pipeline/environment/`，使用本机现有 Python requests/Pillow 与 Blender 4.5 LTS。按 `download.py` → Blender 执行 `convert.py` → `pack.py` → `textures.py` → `metadata.py` 顺序生成。源文件缓存位于 `src/cocos/temp/environment-source`，不作为运行素材发布。`render-review.py` 使用转换后的同一网格和纹理制作离线检查图。

已运行 `npm run check --prefix src/cocos`，TypeScript 通过；50 个派生资源 SHA-256 核对一致。复用现有 Navigation 与 WorldData 的临时手动检查，加入 4 个新家具阻挡后，从旅店出生点仍能到达全部 5 个交互点与 3 个出口。没有新增测试代码或依赖。离线渲染检查了家具材质、模型比例、脚底对齐、植物透明与树木轮廓。下图是素材检查灯光下的资产陈列，不能代替 Cocos 实际游戏截图，也不能作为整章画面已经验收的证明。实际开场、树林与地下场景仍需在引擎中按最终镜头检查。

![转换后模型的离线检查图](environment-fidelity-v2-preview.png)

## 当前边界

这是可运行场景的素材与空间细节升级，未达到 BG3 的逐场景美术制作密度。建筑主体仍有参数化方体外壳；森林复用一类树形与多种地表植物，缺少专门制作的物种群落和树木 LOD 切换。整库在章节内常驻，尚未按区域拆分材质包。两盏 180 lm 桌灯随当前裸木桌重新定位，主路径可达性由场景导航和实际触屏路线共同验证。

## 2026-11-05 开场组合与地表修正

旅店将中央巨幅红褐地毯拆为短门垫及局部餐饮／会客织物，露出木地板；裸木圆桌替代近镜头的黄色棋盘桌布。两处桌组、靠边备餐架、书册和杯碗围绕实际通路组合。石桥镇六栋既有建筑增加凹入窗洞、木柱、石基和小门篷，门旁共 11 件实体使用同一份足迹进入 Navigation 和 Bullet。具体范围、来源、验证与图像阶段说明见 [开场组合记录](opening-scene-composition-v3.md)。

带纹理的原生箱体复用 Cocos `primitive.box`，保留原始几何、朝向和切线，只按各面实际尺寸／材质 tile 缩放 UV；网格按尺寸及 tile 缓存。22×0.74×18 米石基的源函数实际量测为：前后面 11×0.37 次、左右面 9×0.37 次、顶底面 11×9 次重复；同尺寸调用复用同一网格。扫描道具仍保留来源 UV，程序地毯已有独立世界 UV。

林地 Ground 与 UV 统一遵循 `SurfaceMaterials.ground(area)`，不再全部强制草地。S05 原色林土上使用最多 54 块低透明度不规则草色过渡，合并成一份 1,350 顶点／1,944 三角形网格，不增加纹理或碰撞。正式包实读顶点 alpha 为 0～0.379999995。林地土路与林土共用原色 earth，色差仍弱，当前主要由沿路植被与路标提示方向；这部分还需要后续场景构图和地表分区质量提升，不能称为森林氛围已经完成。

最终正常镜头已用 915×412 Android UA 浏览器的真实触屏输入复核旅店主路、弥菈交互、石桥镇窗门及恢复存档后的 S05 短路段。服务稳定后的各次复核均 0 pageerror／0 requestfailed。S01 实体石基读回 UV 与上文一致，32 份 Navigation／Bullet 足迹匹配；S05 为 25 份匹配。最后修复门窗框遮挡内层窗面／木门的问题，窗门最终图与分构建报告见 [组合复核记录](opening-scene-composition-v3.md)和 `src/cocos/test-results/scene-composition-final-review.json`。这不是物理手机帧率或所有 GPU 后端的验证。
