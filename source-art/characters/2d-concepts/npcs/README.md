# 当前章节NPC：由已认可设计图派生的独立二维待机图

2026-11-06。使用内置 `image_gen.imagegen`，以已有设计图作为身份保留输入；没有调用3D模型、预渲染或CLI/API后备路径。PNG保持生成输出的原始字节，Pillow只读取alpha并计算元数据，不重画、裁切、改色或缩放图片。

| 稳定ID | 当前点位 | 身份参考与保留道具 |
| --- | --- | --- |
| lorn | `S01-T3:t3-lorn` | `explorers-v5-elegant.png`第二人；深短发与壮年脸型、靛灰甲、拼修木钢大盾 |
| nightqi | `S05:s05-nightqi` | `explorers-v5-recast.png`第三人；金色波浪高马尾与细辫、灰绿披风、长弓与箭袋 |
| kael | `U1-04:u104-kael` | `rivals-v5-balanced.png`第一人；青年成年脸、栗短发、赭黄短衣、地图筒与测距线 |
| evelyn | `U1-04:u104-dinner` | `rivals-v5-balanced.png`第二人；浅金半束波浪发、沉蓝卫甲、白布修补与炉灯 |

当前 `WorldData.ts`没有瑟维恩、艾莉丝或阿德里安的独立NPC点位，本轮按后续范围收敛指令暂不生成三者。`captain`是现有战斗敌人稳定ID，不在此处冒充阿德里安。未修改原人物ID、位置、任务、规则或商人库存。

四张运行图片分别位于 `src/cocos/assets/resources/flat2d/characters/{id}/atlas.png`。每图1254×1254、2列×2行、每格627×627，顺序为左上正面向下、右上向右、左下背面向上、右下向左。只有四方向各一帧待机，`actions.idle.directionFrameIndices=[0,1,2,3]`是绝对格索引；没有把重复站姿声明成行走或战斗动画。

各自 `manifest.json`包含原设计图与生成PNG的SHA-256、真实alpha包围框、逐方向脚底锚点、`worldUnitsPerPixel`、实际点位及限制。米制大小对齐当前二维主角的可见高度，并仅复用已有演员清单的身高标量比例；没有读取其模型或渲染画面。alpha包围框忽略数值不超过8的极低透明边缘残留；每格边缘最高alpha为1/255，原始抗锯齿字节保留。

完整提示、原始输出路径与输入角色选择见 `generation-prompts.json`。像素尺寸、透明检查、16格包围框、文件哈希与内存估算见 `alpha-and-source-review.json`。四张PNG共3,741,313字节；RGBA基础纹理合计25,160,256字节，约24MiB。`install-npcs.py`可由现成Python/Pillow重新读取同目录PNG并生成相同类型的清单，不安装新依赖。

已逐张查看生成结果：四位NPC有各自面孔、发型、衣装、体态和道具，四方向完整，无地板与不透明背景。侧背面属于基于原正面设计的生成派生，部分细小扣件和背带可能有差异。未构建、提交或宣称已通过引擎内视觉验收。
