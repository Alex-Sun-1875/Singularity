# 开源库与现成资源复用

更新日期：2026-11-05。当前运行工程为 Cocos Creator 3.8.8。开发规范见根目录及 `src/`、`src/cocos/` 下的 `AGENTS.md`：先查已有依赖和引擎能力，再检索成熟方案；优先接入，避免重写成熟算法、控件和素材。

## 本轮直接使用

| 需求 | 采用方案 | 接入状态与理由 |
| --- | --- | --- |
| 程序网格的法线贴图切线 | [Three.js BufferGeometry.computeTangents](https://threejs.org/docs/pages/BufferGeometry.html) | 固定 `three@0.187.0`，MIT；`MeshTangents.ts` 仅转换 Cocos 数组并调用现成算法，替换手写切线计算。已有 FBX 切线直接保留。 |
| 地面、建筑与场景表面 | [Poly Haven](https://polyhaven.com/license) | 已接入 CC0 场景底色、法线及配套 PBR 通道图，来源与校验值记录在 `surfaces/provenance.json` 和 `surfaces/pbr-v3/provenance.json`。当前原生人物使用角色库原作者贴图，运行时不请求素材网站。 |
| 当前人物网格、服装、头发与蒙皮 | [Quaternius Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html)、[Modular Character Outfits – Fantasy](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html) | 官方免费 Standard 包，CC0-1.0；10名生产角色复用原头部、发型及男女 Ranger/Peasant 模块，保留原 UV、65根蒙皮骨骼，按 v5 身高与身份配色适配。另有2根动画附件辅助骨，总层级67。来源、许可和哈希见 `source-art/characters/library-kits/` 及 [原生接入记录](native-library-runtime.md)。 |
| 当前走路、跑步、握剑与主要动作 | [Quaternius Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)、[UAL2](https://quaternius.com/packs/universalanimationlibrary2.html) | CC0-1.0；实际使用 `Walk_Loop`、`Jog_Fwd_Loop`、`Sword_Regular_A/A_Rec`、`Spell_Simple_*` 等原生动作，整理为11个游戏状态。握剑手指沿用作者闭握轨；步频按真实位移和原动作步幅适配。 |
| 当前弓箭动作与武器资源 | [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations)、[Adventurers](https://kaylousberg.itch.io/kaykit-adventurers) | Free 1.1 / Free 2.0，CC0-1.0；复用原 Draw/Release、动态附件握点，以及剑、大剑、杖、魔杖、弓、箭、匕首、圆盾网格。弓保留作者 Draw morph；23关节动作经成熟 BVH Retargeter 和 Blender 原生约束烘焙适配，游戏用 Cocos 原生 socket/morph，不自写 IK 求解器。魔杖资源已安装，当前装备目录使用杖。 |
| 历史人物基础网格与皮肤源文件 | [MakeHuman Community](https://www.makehumancommunity.org/) | 原 MakeHuman/53骨人物源文件与制作记录保留用于追溯、回退，不是当前 `native-kit-v1` 生产人物主路径。历史逐项来源见 `cocos-characters.md`。 |
| PBR 渲染、FBX、输入及 UI 基础组件 | [Cocos Creator](https://docs.cocos.com/creator/3.8/manual/en/) | 继续使用引擎标准材质、资源加载与 UI 组件；自定义代码负责项目数据、布局和适配。 |
| 地图 UI 组件与输入 | [FairyGUI Cocos Creator](https://github.com/fairygui/FairyGUI-cocoscreator/tree/ccc3.0) | 已接入官方 `fairygui-cc@1.2.2`，MIT；复用序列化 Button、Controller、裁剪、命中测试与拖动边界。详情见 [地图接入](fairygui-map-ui.md)。 |
| 地图边框与分隔纹样 | [Kenney Fantasy UI Borders](https://kenney.nl/assets/fantasy-ui-borders) | 已使用 CC0 1.0 素材的三张原图，九宫格适配和运行时着色，不手画替代纹样。 |
| 历史人物细化与头发拟合源文件管线 | [MPFB 2.0.18](https://github.com/makehumancommunity/mpfb2/releases/tag/v2.0.18) | 前阶段实际使用官方 TargetService/HumanService 制作 MakeHuman 人物与拟合记录；当前人物已切换 Quaternius 原生资源。MPFB 工具代码按 GPL，素材按各自 CC0/CC-BY 许可单独记录；游戏不打包工具代码。见 [历史人物升级](mpfb-character-upgrade.md)。 |

Three.js 通过 npm 公开入口导入，只调用 CPU 几何计算；不创建 Three.js 渲染器、场景或额外画布。Cocos 3.8.8 本地构建的解析器未能识别 Three.js `exports` 中的通配符子路径，所以使用公开包入口。使用方式遵循 [Cocos 外部代码支持](https://docs.cocos.com/creator/3.8/manual/en/scripting/external-scripts.html)，依赖版本由 lockfile 固定。Three.js MIT 许可随 Web 构建模板保留。

贴图完整清单、重建方式和画面验证见 [材质更新](material-upgrade-v1.md)。素材获取脚本只负责官方 API 下载、校验及缩图，不自行生成替代贴图。

## 接入范围与维护情况

| 方案 | 适用需求 | 当前决定 |
| --- | --- | --- |
| [FairyGUI Cocos Creator](https://github.com/fairygui/FairyGUI-cocoscreator/tree/ccc3.0) | 复杂游戏 UI、列表、滚动容器及编辑器制作 UI 包 | 官方 `ccc3.0` 分支支持 Creator 3.4 以上；固定 npm 1.2.2（2024-05），不假设仍频繁更新。项目内仅适配 Cocos 3.8 裁剪别名及有符号滚轮值，通过 postinstall 重现。地图使用库组件，其他 HUD/菜单仍为 Cocos UI。 |
| [MPFB2](https://github.com/makehumancommunity/mpfb2) | 历史 MakeHuman 人物源文件制作与回退 | 固定 2.0.18（2026-10-11），使用项目本地 Blender 4.5.15；GPL 工具代码与各项素材许可分开记录。当前生产角色不依赖 MPFB 实时生成，游戏不打包工具代码。 |
| BVH Retargeter 4.4.0 / Blender 原生约束 | KayKit 23关节弓动作至原生65蒙皮骨骼的离线适配 | 使用已归档的未修改 BVH Retargeter（GPL-2.0-or-later）与 Blender 自带 IK/Copy Rotation/姿势镜像，完成后烘焙为 FBX；工具代码不进入游戏。少量项目代码负责映射、握点坐标、片段时序和引擎绑定。 |

当前角色与动作库已接入，造型仍受免费资源范围限制：Captain暂用 Ranger 护甲与大剑，重板甲战锤、部分定制发型和提灯/书卷造型仍有缺口。后续优先寻找骨架、风格和许可兼容的现成资源，再做必要适配，不回到手写人物/动作或重造求解器。复杂 UI 新需求优先评估 FairyGUI 和引擎现有控件，避免再造通用控件框架。

验证优先复用现有类型检查、本地构建及实际引擎画面；本轮不增加测试代码或测试依赖。
