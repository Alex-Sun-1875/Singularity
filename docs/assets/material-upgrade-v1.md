# 人物与地表材质更新

> 当前版本（2026-11-05）已接入六套匹配颜色/法线/AO粗糙度的材质、手机镜头与更新人物动作，见 [PBR 运行时记录](pbr-runtime-v3.md) 和 [工程进度](../PROGRESS.md)。下文是 11 月 4 日第一轮接入记录，其中镜头数值、资源与表现不代表最新发布构建。

日期：2026-11-04。目标是将地图 UI 之外的真实 Cocos 游戏画面一并更新，延续 v5 人物身份、服装配色与 v3 地理。

## 已更新的画面

- 十名角色统一使用 Cocos 标准 PBR 材质，包括拉斐尔、弥菈、洛恩、夜祈、凯尔、伊芙琳、灰披队长，以及三类劫掠兵。
- 皮革、布料、金属使用各自的细节与粗糙度；肤色、头发、眼睛和黄铜沿用各自的 UV 贴图，修正导入材质再次乘上同色底色导致的发黑。
- 地面依据场景区分木地板、自然草地、林地土壤和岩面；聚落道路使用苔缝铺石，地下道路使用岩石材质。
- 木梁、家具、门窗框、石墙、岩石、屋顶、墙灰、帐篷和织物接入对应的可平铺表面与 OpenGL 法线贴图。
- 删除木地板上旧的重复接缝小方块；连续木板纹理由贴图表达。道路采用统一世界坐标 UV，避免逐段重置纹理。
- 复用 Three.js `BufferGeometry.computeTangents()` 补全程序生成地面、道路、球体和圆柱的切线数据，使法线贴图具有有效的切线空间；适配层只转换数组。原 FBX 角色和道具已经包含切线。选型与许可见[开源复用记录](open-source-reuse.md)。
- 镜头的正交半高从 8.5 米改为 5.2 米，角色在正常视野中更清楚；调整环境光，保持角色动作和碰撞几何。

本轮更新材质、纹理和呈现，不改变人物身份、任务、装备、存档格式及地理连接。角色仍使用当前可编辑 FBX/Blender 造型和骨骼动作，不能把材质更新等同于新的最终雕刻模型。

## 参考和素材来源

本地《博德之门 3》官方美术设定集 `DigitalDeluxe/BG3_Artbook_High_Res.pdf` 的 Emerald Grove（PDF 第 23 页）与地下场景（第 29 页）用于观察天然岩壁、木结构、织物和自然色彩。原游戏安装目录及地图 UI 资料见[本地参考记录](../maps/map-ui-bg3-reference.md)。

运行时新增贴图来自 [Poly Haven](https://polyhaven.com/)，资源许可为 [CC0](https://polyhaven.com/license)。素材获取工具使用其官方 API，署名：**Powered by Poly Haven**。本作运行时只加载已保存的本地素材，不连接素材 API。

| 本作用途 | Poly Haven 素材 |
| --- | --- |
| 木地板与木结构 | [Wood Floor Worn](https://polyhaven.com/a/wood_floor_worn) |
| 聚落铺石 | [Cobblestone Floor 04](https://polyhaven.com/a/cobblestone_floor_04) |
| 自然草地 | [Grass Ground](https://polyhaven.com/a/grass_ground) |
| 林地土壤 | [Forest Ground 04](https://polyhaven.com/a/forest_ground_04) |
| 岩面与地下 | [Rock Face](https://polyhaven.com/a/rock_face) |
| 墙灰 | [Plastered Wall](https://polyhaven.com/a/plastered_wall) |
| 皮革细节 | [Leather White](https://polyhaven.com/a/leather_white) |
| 布料织纹 | [Rough Linen](https://polyhaven.com/a/rough_linen) |
| 屋瓦 | [Grey Roof Tiles](https://polyhaven.com/a/grey_roof_tiles) |
| 金属表面细节 | [Metal Plate](https://polyhaven.com/a/metal_plate) |

原始 1K 图保存在 `source-art/materials/natural-v1/`，运行时使用 `src/cocos/assets/resources/surfaces/` 内的 512×512 导出图。`provenance.json` 记录来源 URL、原始 MD5、导出 SHA-256 与分辨率。织物去除原底色、角色染色和岩石色调统一由材质参数处理。

可用 `python tools/materials/fetch_surfaces.py` 重建素材导出。已有角色贴图及 FBX 文件保持原路径与 UUID，新增材质由场景管理释放，共享纹理复用。

## 验证范围

使用现有类型检查、本地 Web 构建、地形检查和真实 Cocos 浏览器画面验证，不新增测试代码或测试依赖。十名角色均保留十组动作，并确认所有角色渲染部件使用标准 PBR 材质。

`src/cocos/test-results/visual-upgrade-*.png` 是实际引擎画面。角色全员图和跨区域场景使用独立视觉检查场景，不能作为完整通关证据。Android 实机帧率、显存与最终角色雕刻质量仍须独立验收。
