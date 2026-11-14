# 第一章原生人物与动作库接入

本次按手机横屏使用场景替换人物资源，继续使用 Cocos Creator 3.8.8。
配色、背景层次与古铜界面沿用前次《博德之门3》研究后的原创方案；人物、服装、武器和动作直接复用作者可用的 CC0 资源。

## 实际复用

| 内容 | 来源与接入方式 |
| --- | --- |
| 10名角色 | Quaternius Universal Base Characters 的原头部、眼睛、眉毛、发型，与 Modular Character Outfits – Fantasy 的男女 Ranger/Peasant 模块组合；保留原蒙皮、UV和成人比例，按 v5 身高及身份配色适配，身体保留作者原生比例 |
| 站立、走路、跑步、剑击、施法、翻滚、受击、倒地、交互 | Quaternius UAL1/2 原生动作；保留65根蒙皮骨骼，以真实位移调节步频 |
| 弓箭 | KayKit Character Animations 原 Draw/Release，经已安装的 BVH Retargeter 4.4 和 Blender 官方约束适配；保留原作者动态握点 |
| 武器 | KayKit Adventurers 原剑、双手剑、杖、魔杖、弓、箭、匕首、圆盾；保留原 UV、原握持原点和弓的 Draw 形变 |
| 材质 | Cocos builtin-standard，接原作者底色、法线、ORM/粗糙度；避免旧人物材质适配器覆盖作者贴图 |

角色的 `manifest.json` 保存材质、默认可见衣装模块、动作节奏、骨架数量和来源哈希。
运行时通过 Cocos 的 `SkeletalAnimation.createSocket` 与 `MeshRenderer.setWeight` 使用原生附件和变形。
头罩随头部装备切换，弓按同一原片采样进度拉弦；Mira使用双匕首，盾兵使用原圆盾。
实际Cocos prefab的弓子节点带有Ry180，`cocosBinding`记录弓Euler(90,0,180)、箭Euler0及箭本地Y偏移+.355954468米；真实GPU形变满蓄后箭尾至弦点误差约.288毫米。
推击使用原Interact左手前伸的18–33帧，共.5秒原速窗，峰值在游戏.133秒，匹配.10–.16秒接触窗。

## 手机资源预算

主体图512×512；两位主角头部底色1024×1024；眼睛256×256。
全10角色56张去重共享图：PNG **15,401,066字节**，RGBA基础层 **63,438,848字节**，完整mipmap链 **84,585,056字节**。
这些是全部角色的资源预算，不代表每帧同时出现10人，也不代表真机显存实测。
旧人物贴图移出游戏资源目录保留备份，运行时材质引用共享图片。Cocos 3.8.8的FBX图名会重复，官方Image Remap按同名折叠，已撤回该优化；原导入材质的图片依赖目前仍可能重复打包，应以真实构建体积为准。

## 可复现入口

- `tools/model-pipeline/cocos_native_characters.py`：原生角色导出。
- `tools/model-pipeline/cocos_native_motions.py`：官方动作整理与成熟工具适配。
- `tools/model-pipeline/cocos_native_props.py`：官方武器与原生形变导出。
- `src/cocos/tools/install-native-actors.ps1`：保留原资产根UUID、备份旧资源、安装完整11动作。
- 官方下载归档、许可证与哈希：`source-art/characters/library-kits/`。
- 引擎验证使用实际 Web 构建，复用既有角色检查、浏览器触控与合法首章通关流程。

## 当前资源边界

免费包提供4套男女衣装，未购买付费全部衣装。Captain暂用大剑及 Ranger 护甲，尚非设定中的重板甲战锤；Kael/Evelyn暂空手，未把书卷/提灯伪装成剑。现成长发按身份染色，卷发、半束等细节仍是近似。

本地 Web 构建可玩性、浏览器手机触控模拟和真实设备性能是不同验收项。
未接入手机真机，不宣称已通过目标设备帧率、温升或 TapTap 发布验收。

## 本轮验证结果

2026-11-05：既有95项游戏规则检查、TypeScript检查、10份实际FBX roundtrip及既有3项资源检查通过。实际Web发布构建的完整首章路线经过11区域、击败4名敌人并取得结尾奖励，无运行错误；全部10个角色bundle已真实实例化，均含11动作和67层级关节。
桌面与915×412 Android UA触控模拟的实际输入、背包、存档重载通过，无pageerror或请求失败。动作录像另覆盖剑、弓、弓技、杖、符咒、翻滚、推击和跑步。
