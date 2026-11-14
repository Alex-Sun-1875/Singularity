# Qwen-Image-2.1-Turbo 本地角色评估

2026-11-07。已安装模型并完成两次真实本地推理，输出保留原始像素，未通过正式美术验收，不接入游戏资源。

## 实际运行与结果

使用 `F:\Models\Qwen-Image-2.1-Turbo` 中的 Turbo INT8 convrot、Qwen3-VL-8B INT8 convrot 与专用 RGBA VAE，复用离线 ComfyUI 0.44.0。三份权重合计17.28GB，直连下载，SHA256均匹配官方同仓库精确路径；没有安装额外依赖或调用云端生成。

| 小样 | 实际模型任务 | 端到端耗时 | 输出 |
| --- | --- | ---: | --- |
| 正跑衣裤色 | `3b81dd3d-7dec-42b4-bd18-492565954258` | 88.26秒 | `results/front-run/raw-model.png`，512×768 RGBA |
| 背剑加长 | `537d457d-47c8-4f01-95c9-2f061993be28` | 62.28秒 | `results/back-sword/raw-model.png`，512×768 RGBA |

两次均为8步固定sigma、Euler、CFG1、seed20261107、CPU编码器、CPU/default KV缓存、resolution=0。耗时包含首次/缓存加载、编码、采样、解码、保存与轮询，不是纯GPU采样时间。

`comparison-raw.jpg` 三列为原件／参考／模型原始输出。背剑没有单独参考，中列留空。仅为预览在棋盘背景上统一缩略，没有校色、对齐人物、替换手头或合成修复输出。`metrics.json` 的alpha包围框仅是几何代理；生成背景存在alpha约1/255的残留，不能仅凭PNG带Alpha就视为边缘已经清理。

初步观察：整体姿势与主要轮廓保持较稳定，背剑有加长；衣色明显变深，但裤色未精确匹配站姿，刺绣、手部和剑帽细节仍发生变化。当前结果只是模型评估，不能直接作为整套动画替换或宣称已经解决身份、颜色、手和武器的一致性问题。比例提示词已经准备，但本次没有运行第三个比例任务。

启动：`F:\Models\Start-Qwen21-Turbo.cmd`。在本地界面选择 **Raphael - Qwen 2.1 Turbo local trial**，或加载本目录 `workflow-ui.json`。命令行用便携Python执行 `run-local-trial.py --case front-run`／`--case back-sword`；同名已完成结果不会被静默覆盖。每组保存最终提示词、真实API工作流、提交ID、history与result。

权重和运行记录见 `F:\Models\deployment\qwen21-model-manifest.json`、`qwen21-install-verification.json`、`qwen21-direct-route-audit.json`；本次验收见 `verification.json`、`visual-review.json`。

本次按用户要求用于研究/效果评估。Qwen Research License约束模型用途；输出版权和商业目的运行模型的授权是不同问题，未把输出商用争议当成已经有官方明确答复。

`input-manifest.json` 为绑定依据：每张输入记录角色、绝对原路径、SHA256、尺寸、原图裁片坐标、统一仿射与脚部锚点。`original-input-preview.jpg` 是 896×378 本地原件缩略图，无候选图。

## 单帧顺序

默认使用 **RGBA原件** 测试模型原生透明编辑能力：ComfyUI `LoadImage` 后用 `JoinImageWithAlpha` 重新接入原alpha，检查其MASK是否需要反相，不只发送RGB的IMAGE张量。灰底RGB副本仅用于来源核验或后续兼容性对比。

1. **正跑衣色/裤色**：图1为 `originals-512x768/run-front-p0-rgba.png`，图2为 `originals-512x768/standing-front-p0-rgba.png`，使用 `front-run/prompt.txt`。
2. 上一步值得继续时，**另从原件试正跑腿长**：仍用相同两张原始输入，使用 `front-run/prompt-proportions.txt`，不将上一张生成结果串入。
3. **背剑**：图1为 `originals-512x768/standing-back-p0-rgba.png`，单图配 `back-sword/prompt.txt`。延长剑鞘中段，保留原柄、鞘帽、手和遮挡，原鞘帽平移约 `(-31,+65)`。
4. 备用背跑：图1 `run-back-p0-rgba.png`，图2 `standing-back-p0-rgba.png`，使用 `back-sword/prompt-run-back-optional.txt`。

## 原件与像素保留

- 站姿来自 `locomotion-alignment-v1/assets/W01-explore-idle.png`；正/背跑来自 `locomotion-alignment-v1/head-scale-v2/assets/W01-explore-run-a.png`，均与当前运行素材 SHA256 相同。
- `originals-native/` 是旧试验保留的原始 RGBA 裁片的逐字节复制，并已与原图相应裁片逐像素核对。
- 旧试验的 512×768 输入原本是 RGB 和独立 alpha，没有现成的该尺寸 RGBA 文件。这里从原始 RGBA 裁片按原来的动作统一尺度、仿射和 `(256,712)` 脚部锚点重建 `*-rgba.png`，不是把 RGB 灰底伪装成透明原件。alpha 与旧 alpha 逐像素相等，合成灰底后的 RGB 与旧未编辑输入逐像素相等。
- `*-model-rgb.png` 是旧未编辑 RGB 输入的逐字节复制，保留 `(228,228,228)` 灰底，避免只读 RGB 的模型加载器暴露透明黑色。512×768 RGBA 原件另外保留，供局部合成与透明边缘保护。
- 不使用 `guide`、`raw-model`、`candidate`、`constrained-candidate` 或 `candidate-v2` 的像素作为输入。上一轮 `guide` 曾横向整带缩放，造成手等细节问题，不能当原件。

## 验收与合成

提示词不能保证区域像素不变。生成输出只作为局部候选，在本地审查遮罩内合成；完成所有几何与校色后恢复原头、手腕手指、非目标剑细节、脚和透明边缘，并检查遮罩外变化。背剑须保留手在前的遮挡与指缝，不能用带灰底的整块矩形覆盖手。

先核对头型/银发/身份、跑姿前倾和相位、腿长比例、裤色、服装细节、手、剑帽、固定点、脚部锚点与边缘，再决定是否继续。脚部锚点是运行尺度参照，空中跑步脚底不要求落到同一水平线。未通过人工美术验收的输出不得覆盖正式素材和 manifest。

本地重建入口为 `prepare-inputs.py`，使用已有 Pillow，无网络、模型调用或新增依赖，只写本目录。
