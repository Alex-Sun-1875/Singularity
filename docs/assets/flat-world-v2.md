# 首章2D世界层 v2

这份改动仅替换Cocos世界表现。现有HUD、任务、背包、技能、地图面板、规则、存档、地理、导航、碰撞、桥面与高度字段继续使用原工程。`WorldData`实际包含32个区域；旅店1区保留已验证的对齐整图，其余31区使用重复地表与手绘图块，不把一张1536底图放大到140米。

## 实现与接入

- `SceneBuilder`新增只读表现记录：`flatMapSurfaces`、`flatMapPatches`、`flatMapObjects`，记录原有渲染器、物件根节点和尺寸；不改变任何碰撞生成、路径、规则或地点数据。
- 在`SceneBuilder`之后、`Actors/Effects`之前创建`FlatWorldPresentation`。2D模式对所有区域调用`await build()`；旅店自动选择`flat2d/maps/inn`，其他区域委托`FlatWorldLayers`。
- 每帧在原`positionCamera`之后调用`flatWorld.update(camera)`。只有相机朝向改变时重算图块朝向，平移跟随不重建几何。
- 地面、道路、草地覆盖、地毯和住宅地面保留原网格、真实坡度与米制UV，使用原有授权albedo的原生`builtin-unlit`材质。没有normal/PBR照明；扫描贴图的细节不是纯色示意。
- 水面、门槛、桥面和地毯边缘由原尺寸/位置转换成原生XZ平面；桥的分段与断桥缺口保持。水面使用新绘制的重复纹理。
- 新生成PNG为非POT尺寸。图块使用CLAMP/no-mip；水面按4米原生plane实例拼贴，各块UV保持0..1，兼容Cocos WebGL1对非POT纹理强制CLAMP的行为，不依赖非POT重复采样，也未重采样源图。
- 其余原环境`MeshRenderer`停用。节点、BoxCollider、Ground MeshCollider和桥面碰撞保持启用，点击瞄准、Bullet胶囊与Navigation仍使用同一世界。
- 建筑、树岩、家具、墙、灯、货物、门、车、柱等使用新绘制的透明图块。使用原生quad、SpriteFrame UV、unlit alpha test、实例化和视锥剔除，不新增渲染引擎或依赖。长墙分段、大岩体按不超过约3米的图块铺放，保持手机近景像素密度。
- 销毁时恢复原渲染器材质、enabled和阴影状态，并释放本实例拥有的图块mesh、material、frame及纹理引用。原3D资源文件没有覆盖。

## 新美术及来源

`src/cocos/assets/resources/flat2d/world/`现有6张PNG、43个可裁切手绘图块：

| 文件 | 内容 | 实际尺寸 |
| --- | --- | --- |
| world-props-v1.png | 树、岩、建筑家族、墙、箱、桌、柜、牌、锻炉16格 | 1254×1254 |
| small-props-v1.png | 椅、凳、圆桌、长桌、桶、箱、书、灯、餐具、火堆、植被、门16格 | 1254×1254 |
| structures-v1.png | 柱、关卡门、遗物车、水车、碑、晶体、绳栏、残墙、桥9格 | 1254×1254 |
| house-v1.png | 近景高清木构房屋 | 1254×1254 |
| tower-v1.png | 近景高清石塔 | 1254×1254 |
| water-v1.png | 手绘重复水面 | 1254×1254 |

以上均通过内置ImageGen工具生成，保留原始alpha，没有用旧3D模型烘焙物件。完整提示、原始输出路径和透明要求保存在`world/sources.json`。文件SHA256、实际alpha裁切矩形、资源路径、31个原环境library键的家族映射及原尺寸保存在`world/manifest.json`。

`python tools/model-pipeline/cocos_flat_world_assets.py`仅检查现有PNG及alpha边界并生成元数据，不修改、重采样或重画任何像素。已有地表albedo沿用`surfaces/pbr-v3/provenance.json`及工程第三方声明；原生Cocos3.8.8能力和现有Pillow用于检查，无新安装依赖。

## 覆盖与明确限制

代码路径覆盖32区，31个现有环境模型键均有真实手绘家族；各区原有建筑、树岩、家具、地面、水、桥和交互坐标继续存在。`inspect()`提供`originalVolumeRenderersVisible`、`unmappedSourceKeys`、`retainedTexturedWalkSurfaces`和`paintedCutouts`，运行审查必须确认旧体积模型可见数为0、未映射键为空。

这不等于32区已经完成实际运行审查或完整首章通关。元数据状态保持`source-ready-runtime-review-required`，等待统一导入、构建及引擎审查。

当前美术是有材质细节的实际手绘图块与真实albedo地表，既非纯色占位，也非逐个地点独绘：木构房屋、工坊、仓库、水磨共享建筑家族；岩石和植被的原模型变体复用绘制家族；建筑尚未为每种世界朝向独立绘制背面。源图中的装饰门不替代原玩法入口，入口坐标及路牌保持。地表仍是原授权扫描albedo的unlit表现，未声称全部重新手绘。重复水面的接缝质量、遮挡、手机帧率与内存要以引擎/真机证据分别记录。

## 已复现的运行问题与修正

- **跨区纯灰地表**：隔离引擎夹具`U1-04 → S01-T3 → U1-04`复现，SurfaceMaterials静态库里的cobble对象变为`isValid=false/refCount=0/getGFXTexture=null`，而重新load同UUID得到另一个有效对象。原因是世界层错误释放共享albedo。现在只引用计数`flat2d/`自有图；surface库纹理只借用。`flat-world-texture-lifetime.json`及灰地面截图保留故障证据，后续构建必须连续换区复验。
- **道路覆盖人物**：真实S01/U1-02场景A/B证明透明道路按大网格中心排序会绘制在人物身体上。官方Cocos透明队列先比较`Model.priority`；现retained地图层设`-100`、演员保持`0`，原优先级在销毁时恢复。高建筑/树仍用原深度遮挡，不把演员强制画在高物件前。before/after图和`flat-world-priority-ab.json`保留。
- **过亮岩地**：地下岩地使用中性压亮、stone山口使用已有授权earth。统一构建实际S04图已由白灰岩地变为棕色土路；地下保留有真实纹理的中性灰岩面。
- **低物件的二次透视与比例**：将已有3/4源图直接铺XZ会使桌/车斜扁；仅恢复facing并填满footprint宽度，又会把桌放高到3.13m、车4.45m。实际页面两轮A/B已保存。当前桌/圆桌/车使用camera-facing卡片，严格保持裁切源图的`rectH/rectW`；统一缩放约束在原footprint投影宽与低物件高度包络内，底边锚定原物件base，避免沿camera.up减去footprint后把下半图埋入地面。原碰撞和业务坐标不缩改；卡片不声称逐像素填满碰撞footprint。`flat-world-aspect-fit-U1-04-after.png`与`flat-world-aspect-fit-S04-after.png`展示自然桌/车和完整轮足，表中实际尺寸分别为1.816×1.558m、3.107×2.783m。高物件深度遮挡仍保留，车后的角色可被车遮住；餐具仍沿原世界位置，并非与桌图逐像素贴合。

`flat-world-targeted-final.json`记录02:49统一构建的连续`S01-T3 → U1-04 → S01-T3 → U1-04`：共享cobble对象始终相同且GPU有效、7个重点场景原体积renderer可见为0、表面优先级-100/演员0、无页面错误。该构建的桌/车斜扁问题明确保留为失败证据，后续aspect修正由真实页面原生节点A/B验证、源代码TS检查通过，仍需统一构建复核；不把页面A/B冒充已构建产物。

这些是表现夹具与原生渲染A/B证据，不属于合法通关。合法首章流程由独立browser-playthrough记录。
