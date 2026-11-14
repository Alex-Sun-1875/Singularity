# Seven Reference Screens Implementation Plan

**Goal:** 按用户提供的7张参考图实现实际游戏画面、背包、人物状态、技能与地图，手机横屏优先。

**Architecture:** 沿用Cocos Creator3.8.8及现有FairyGUI地图。界面采用烟黑底、暖金铜边框、象牙文字、青蓝选中态；背包/人物采用真实玩家模型的RenderTexture预览，地图连接实际WorldData与探索状态。所有数值和装备操作来自GameSession。

**Tech Stack:** Cocos Graphics/Sprite/Camera/RenderTexture/Mask/ScrollView，现有FairyGUI、原生角色与CC0图标。不新增UI框架、测试依赖，不将参考游戏截图打入资源。

## Reference acceptance

- [x] 图1：原创树木框景的河谷远景加载背景，暗渐隐、提示、真实资源阶段进度与动态指示。
- [x] 图2：暖火光与冷暗环境、角色选中底环、圆形地形小地图、人物头像状态与集中动作栏；保留即时战斗与手机双指操作。
- [x] 图3：全屏地图含地形、探索遮罩、图例、层级切换、地点详情、缩放平移/标记/定位；当前区域平面必须与实际建筑、障碍和入口一致。
- [x] 图4：人物真实3D全身预览可旋转，右侧可滚动状态/属性，顶部页签。
- [x] 图5：技能分组、真实修正值、可点击详情卡，手机不依赖悬停。
- [x] 图6：总览、真实生命/专注/装备护甲与检定资料；不虚构游戏尚无的等级、种族或力量数值。
- [x] 图7：左侧状态、中间人物和装备槽、右侧物品格，品质、数量、选中/已装备状态、筛选/物品详情/装备动作闭环。
- [x] 桌面1280×720与手机915×412/更窄横屏实际检查；主要触区至少44CSSpx，正文约14CSSpx以上，无遮挡、截断或滚动穿透。

## Ownership and implementation

1. Root：Hud/UiTheme/UiChrome/ChapterGame/Actors/Effects，接入加载、预览源、圆小地图，收紧HUD占屏与输入阻挡，角色脚环。
2. Character agent：CharacterPanel/CharacterPreview及Menus相关分支，原生RT人物、属性/技能/背包格/详情与装备。
3. Map agent：MapPanel/AtlasUi/LocalCartography/MiniMap，FairyGUI交互和真实区域地形展示。
4. World agent：SceneBuilder/EnvironmentPresentation/LoadingScreen，场景层次、暖光与原创加载图。

## Verification

复用TypeScript检查、现有核心检查与发布版触控/存档/完整首章通关脚本；不新建测试框架。为7个参考范围逐一保存实际运行截图：加载、普通游戏、地图、人物总览、技能详情、物品格/详情、换装。检查3D预览生命周期、缩放旋转/返回、地图拖动及遮罩、触控同时移动攻击，避免用静态图或空面板冒充实现。完整目标只有上述范围全部实装并有对应运行证据时才完成。

验收索引与当前资源边界：[reference-ui-v4.md](../../assets/reference-ui-v4.md)。
