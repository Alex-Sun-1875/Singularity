# 本地 Klein：剑长、衣色与正背跑比例试验

最新查看[第二版细节纠正](revision-v2/README.md)：恢复原剑鞘末端和完整手部，并以对应站姿统一裤料颜色。下述首轮记录与输出保留作问题追溯。

2026-11-07，按用户要求使用当前本地 FLUX.2 Klein 4B 蒸馏版进行四张代表帧小样。模型请求仅连接本机 ComfyUI，不调用云端生成，不下载模型或依赖。正式素材与运行 manifest 保持原校验值。

## 当前查看入口

- `comparison-constrained.jpg`：上排原图，下排加入本地像素保护及参考校色后的候选；从左到右为背剑、侧跑衣色、正跑比例、背跑比例。
- `comparison-initial.jpg`：首轮本地模型遮罩输出，保留剑鞘变粗、衣料/手臂细节漂移的原始问题，供比较。
- `results/<case>/raw-model.png`：真实本地模型生成结果。
- `results/<case>/candidate.png`：将模型结果按初始遮罩合成后的版本。
- `results/<case>/constrained-candidate.png`：当前查看的小样，使用原头部、原材质细节和其他像素约束。
- `verification.json`、`constraints-report.json`：来源 SHA、模型任务、颜色及像素保护验证。

## 先测量再制作

`geometry-inputs/`保留104帧四向度量及24张同身体世界尺度的输入：400px/世界单位，统一脚锚(256,712)，没有逐图拉满。`color-audit/`记录36帧胸腹与袖子颜色统计。

运行端各方向共用同一动作 UPP，没有正背面独立缩小，也没有站跑动作级染色或 gamma 差异。短矮观感与正背面源图收腿相位、腿/躯干比例有关；部分腾空相位的脚底也不同。跑步B的红衣比站姿亮约7.8–10.6 L*，袖子候选区域亮约9.2–16.3 L*，源图已存在差异。ROI存在阴影和材质混入不确定性，不能据此宣称全部帧已校色完成。

## 本地模型与约束的分工

1. **背剑小样**：使用Pillow仿射变换构造剑鞘轴向1.4倍的几何引导，接头(283,192)不变，剑鞘端点由(200,373)引导至(166.8,445.4)，完整剑长目标约增加30%。Klein负责遮罩内纹理和接缝候选；最终限制合成宽度、回配原剑鞘材质，并保留原握柄、上端挂点和头部。
2. **衣色小样**：以对应方向站姿为参考，Klein给出颜色候选。为保留原衣料纹理和缝线，把模型候选色向限制到站姿参考范围，再用Pillow ICC Lab转换映射回原衣料细节。金绣、皮肤与装备使用局部范围保护。Lab a/b在NumPy接口为有符号字节，已显式解码/回编码并检查往返误差，避免校色溢出偏蓝。
3. **正背跑比例小样**：保持原头部大小/位置和画布总高度，腰线引导420→388，躯干210px→178px，腿段292px→324px（约+11%）。Klein重绘遮罩内过渡与腿部细节，最终限制身体重绘范围，保留原手臂轮廓，并将y≥650的着地靴区域恢复为原像素。此约束不保证腾空腿的整只鞋或完整动画节奏不变。

采样采用官方原生节点：真实VAE latent + SetLatentNoiseMask，Flux2Scheduler/Euler/4步/CFG1/固定种子1707；文本编码在CPU，结果再以Pillow合成。工作流和提示词位于各`results`及`guides`目录，原生API图不依赖新增自定义节点。

## 复现

```powershell
python source-art/characters/2d-concepts/local-klein-consistency-v1/prepare-cases.py
python source-art/characters/2d-concepts/local-klein-consistency-v1/run-edits.py
python source-art/characters/2d-concepts/local-klein-consistency-v1/finalize-candidates.py
```

模型服务需已在`http://127.0.0.1:8188`运行。`run-edits.py --case sword-back`可仅运行指定小样。当前模板从`F:\Models\deployment-research`读取，本轮实际执行版本已逐项保存在`results/<case>/workflow-api.json`。

## 验收边界

这是四张代表帧效果试验，尚未批量修改所有方向、8个跑步相位、持剑动作或其他武器，也未接入游戏。原始模型输出存在剑鞘增粗、衣料与手臂漂移，不能直接作为全套素材替换。当前受约束小样用于判断方向；扩大到完整序列前仍需检查局部接缝、剑长跨动作一致性、全周期腿部动作、脚接触/腾空以及站跑颜色连续性。
