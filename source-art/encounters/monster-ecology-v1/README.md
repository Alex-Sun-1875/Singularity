# 有机怪兽生产记录

2026-11-08。用户要求补上真正的怪兽、怪兽Boss和有反击机会的爽快战斗。本目录三套素材均用内置云端 OpenAI `image_gen` 生成；没有调用本地模型、下载依赖或替换已验收主角。

| 身份 | 原始图与最终提示词 | 运行资源 |
| --- | --- | --- |
| 荆背猎兽 | [raw.png](thorn-hound/raw.png)、[prompt.txt](thorn-hound/prompt.txt) | `flat2d/characters/thorn-hound` |
| 沼囊吐兽 | [raw.png](marsh-spitter/raw.png)、[prompt.txt](marsh-spitter/prompt.txt) | `flat2d/characters/marsh-spitter` |
| 裂岳獠王 | [raw.png](ridgebreaker/raw.png)、[prompt.txt](ridgebreaker/prompt.txt) | `flat2d/characters/ridgebreaker` |

每张1536×1024原始RGBA图是六列、四向。六姿态为待机、两张行走接触、蓄势、出招、收势；每个身份有24张实际绘制画面。四向之间没有镜像补画，蓄势/出招/收势由核心阶段驱动。两帧步态是稀疏动画，未声称三维骨骼、独立受击/尸体绘画或完整逐帧动画。

采用现有Pillow/NumPy与角色manifest流程。旧`enemy_atlas_runtime.py`只适配四列正方图，本次新增[六列适配器](../../../tools/design/prepare-monster-art.py)，不重写渲染器。所有RGB像素保持原始值、不逐帧缩放或平移；每个朝向固定同一个脚部支撑平面锚点，每个身份只使用一个比例。云端RGBA仍包含背景薄雾：猎兽清除alpha≤3、吐兽清除alpha≤24；獠王将原alpha210—244映射为0—255。按已有alpha处理，没有用白色RGB抠图，因此獠牙、爪甲与灰白岩甲保留。

`generation-and-review.json`逐身份保留原始/提示词/图集/manifest的SHA256、alpha参数、来源和检查状态。`processed/contact.jpg`是确定性切帧预览。图集单张RGBA展开约6MiB，按实际区域加载，单个新身份不会为每只实例复制纹理。

先检查猎兽小样，再生成吐兽和巨兽。生成成功、静态小样检查、实机验证分别记录；不把生成成功或静态图当作用户美术验收。三套已经接入真实场景与权威攻击、伤害、头顶血条；[运行记录](../../../docs/assets/monster-ecology-v1.md)列出实际玩法与边界。
