# Local Klein pilot inputs

## 本地部署与试跑结果（2026-11-07）

本地服务：http://127.0.0.1:8188 。运行 `F:\Models\Start-Klein.cmd` 可重新启动。
ComfyUI 的工作流列表中已有 `Raphael - Klein local trial.json`，也可加载本目录的 `workflow-ui.json`。

- `comparison-preview.jpg`：站姿参考、原跑姿、512×768 整图生成结果的对比。
- `results/running-head-reference`：416×624 首次试跑，端到端 20.07 秒。
- `results/running-head-reference-512`：512×768 缓存后试跑，端到端 5.05 秒。
- `results/head-local`：512×512 头部局部试跑，端到端 15.06 秒，以及本地遮罩合成实验。
- `visual-review.json`：来源校验、运行记录和画质问题。

模型运行成功，但美术结果尚未通过：整图试跑误把背剑移到腰侧；局部头部试跑改变了发型与面部朝向，当前窄遮罩合成还露出了原脸边缘。`running-head-local-composited.png` 是未通过的实验结果，不能用于正式素材。所有生产图与 manifest 均核实未改动。

实际运行：

```powershell
python F:\workspace\Singularity\source-art\characters\2d-concepts\local-klein-pilot-v1\run-local-pilot.py --name another-trial
```

只连接本机 API；默认 0.375MP、4 步、固定种子、CPU 文本编码。计时包含 API 轮询，不代表所有分辨率或提示词都同样快。

Only this directory is written. Preparation uses the already installed Python 3.14 / Pillow, with no network, dependency installation, image-viewing tool, upload or production asset change.

- `running-right-input.png`: current `standing-head-v2` W01 exploration run, right direction, phase 0, from `locomotion-alignment-v1/head-scale-v2/assets/W01-explore-run-a.png`.
- `standing-right-input.png`: approved current W01 exploration stand, right profile, from `locomotion-alignment-v1/assets/W01-explore-idle.png`; head shape and size authority.
- `standing-head-right-reference.png`: 384×384 magnified crop of that standing head and upper collar. Detail reference only; its displayed size is not the target head size.

The two 512×768 full-body inputs share a physical scale derived from the installed manifest's `worldUnitsPerPixel`, and the same support anchor. They are not independently stretched to fill the canvas. Original alpha is preserved during RGBA resizing and composited once onto RGB `(224,224,224)`; no alpha thresholding, matting, sharpening or costume editing is performed. Crop, scale, anchor, source/output SHA256 and original design ancestry are recorded in `inputs.json`.

Smallest useful experiment: run `run-right-head-alignment` once with image 1 = running input, image 2 = standing input, and `edit-prompt.txt`. Keep the runner's native 4-step distilled settings and a fixed seed. Add the close-up only if the two-image result lacks facial detail. Optional second case `standing-right-control` and its prompt are in `inputs.json`. These are the only two prepared cases.

Regenerate locally from the repository root:

```powershell
python source-art/characters/2d-concepts/local-klein-pilot-v1/prepare-inputs.py
```

The script checks the selected source hashes against the current installed manifest, validates that each canvas fits the whole crop, and writes only this directory. Preparation does not run a model or assert visual quality. Review locally whether pose, clothing and leg lengths remain stable, and whether the head follows standing size with a natural chin and restrained face width. Generated results are experimental and are not installed into the game.
