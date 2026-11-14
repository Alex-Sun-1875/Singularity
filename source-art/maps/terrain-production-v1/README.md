# 手绘地图材质与环境变化接入

2026-11-08。按照[已采用的地图画风](../../../docs/maps/map-art-style-v1.md)，将静态方向板转化为可重复使用的地面与环境切片。运行资源在[terrain-v1](../../../src/cocos/assets/resources/flat2d/terrain-v1/)，区域选择由[MapArt.ts](../../../src/cocos/assets/scripts/features/world/data/MapArt.ts)定义。

## 生成素材

九种地面分别为旧石板flagstone、林土forest、城镇铺石cobble、灰褐土earth、草甸meadow、湿泥wet-earth、自然岩地bedrock、老木地板wood和水面water。每种通过一次独立云端OpenAI image_gen调用生成；请求1024×1024，实际均为1254×1254，以实际尺寸保存到raw目录。

透明环境变化图集包含六种岩体、两种草、两种蕨与两种芦苇。首版两丛芦苇越过单元格，记录为淘汰；针对性云端编辑后的terrain-props-v2.png通过主体隔离初审，保持1254×1254 RGBA。新图集与旧建筑、家具切片共同使用。

沉船岸另有独立生成的低矮破旧河船：原图1536×1024 RGBA，按真实alpha包围框裁切并等比例缩至1024×358。船体位于B14实际港水的阻挡范围内，与木栈道错开；生成提示词、原图来源和透明通道检查见[沉船生成记录](generated-shipwreck.json)及[处理记录](processed-shipwreck.json)。

- [完整地面提示词](prompts.json)
- [五张首批原图来源](generated-primary.json)
- [四张后续原图与美术初审](generated-secondary.json)
- [透明图集提示词 原图与裁切记录](generated-props.json)

只使用必要的已采用方向板作为风格参考，没有启动本地模型、调用CLI生图或下载依赖。云端生成与本地像素处理分别记录。

## 本地处理与资源规格

[准备脚本](../../../tools/model-pipeline/prepare_map_terrain.py)复用项目已有Cocos图像导入格式和Pillow。原始生成文件保留，运行地面缩为512×512 RGB，并仅在外缘6像素内混合对边，使首尾行列相等。对边像素相等只证明颜色连续，图案是否自然仍需平铺与正常镜头审阅。

九张地面使用Repeat、线性过滤、线性mip与4倍各向异性。两张透明图集保留原尺寸，使用Clamp与无mip，按裁切UV及alpha-test显示。所有meta使用项目既有UUID5命名方案，目录meta由Cocos导入。

旧树木图集仅在橡树、白桦、松树三个裁切区内对绿色叶片做0.65去饱和与少量灰橄榄适配；透明通道、树干及其他切片像素保留。旧图集文件未改，运行manifest指向新的world-props-muted.png。

- [九张地面处理与边缘数值](processed-textures.json)
- [新切片与透明通道处理记录](processed-props.json)
- [树木选择性调色及像素保护记录](processed-trees.json)
- [九种运行材质预览](terrain-materials-preview.jpg)
- [原图缩小与边缘修复后的平铺对照](terrain-tiling-review.jpg)
- [树木调色对照](tree-foliage-review.jpg)

## 运行表现

FlatWorldLayers按区域选择地面与道路，按原米制UV换算材质尺度。遗迹使用旧石板，山口使用自然岩地，林地有落叶土，湿地有湿泥；地下居所使用人工铺石，区别于天然洞厅。石墙以原朝向的低剖切实体呈现，岩石、草蕨与芦苇保留源图比例，低碎石仅用于无碰撞装饰。

低矮装饰改为沿树岩脚、墙边、岸边成组，留出主路与人物活动区。次级小径连接已有道路，出口主路保留；用于既有通行和布景的原导航路径及查询顺序保持。铁匠铺补炉边和维修工位石垫，仓院与拘留所移除通用青色大地毯。

地脚阴影、湿岸过渡与可见灯源的柔和暖光合并到一层静态地面绘制；已有灯具与火焰节点继续保留；2D人物仍使用现有unlit材质，地面暖光属于环境表现。Terrain的地面、坡道、水、桥、入口与任务坐标继续作为实际通行依据。旅店保留已验收的整图表现。

## 验收记录

当前运行定义已扩展到97区，九类画风均有材质选择。原32区的地形数值与采样保持一致；新增65区由独立CampaignTerrain配置广坡、水体、桥栈及干沟，覆盖与连通结论见[地形记录](campaign-terrain-review.json)。全97区1203个目标及320个回落点通过通行检查；18402次桥面采样误差为0。这些数据验证源地形和导航，不代替GPU画面与实际胶囊移动检查。

生成成功、素材处理、美术初审和运行验收分列。最终map-art-release3包完成97区正常生产渲染与严格资源释放检查、76组桌面/手机尺寸视点、9条桥坡胶囊行走，以及桌面键盘/触屏移动、攻击、行囊与存档恢复；错误与失败请求均为0。选区截图用于画面复核，手机检查为浏览器触屏模拟，不作为合法通关或实体手机性能证据。

- [最终运行验收与证据索引](runtime-review.json)
- [九类地形游戏内画面总览](runtime-style-review.jpg)与[原截图索引](runtime-style-review-sources.json)
- [八处干地形复核](runtime-dry-landforms-review.jpg)与[原截图索引](runtime-dry-landforms-review.sources.json)
- [最终包构建与一致性校验](map-art-release3-build.json)

峡谷覆盖层直接复用实际Ground网格，连续接到桥下，由桥面深度遮挡，已消除独立重采样的浅色条带与桥沿三角缺口。大面积地表仍可见平铺节奏，建筑与家具复用兼容切片；本轮完成统一材质和环境表现的第一轮整理，后续可按地点继续丰富构图和独有地标。

用户参考继续作为风格依据，不改变其授权范围。新生成素材按AI制作结果登记，既有建筑与家具沿用原来源记录；不将生成图登记为CC0下载材质。
