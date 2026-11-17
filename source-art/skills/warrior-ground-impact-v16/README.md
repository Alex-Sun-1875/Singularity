# 裂地审判 · 重劈破地设计 v16

状态：用户已要求更换技能，本方案停止继续调整并保留历史记录。未接入游戏。

本轮只重做用户指出的“裂地斩”（当前技能名为裂地审判）。上一版黑色折线的地裂被替换为带凹陷、石质断层和碎石的裂隙贴图，并配合立体石片、飞石、贴地银白气浪和尘土。落点、半径 2 米的命中区域、伤害事件和现有重劈骨骼动作保持原录制规则。

动作设计：

1. 原有重劈动作蓄势，银白落刀残影压向落点。
2. 接触地面时短促闪击，贴地气浪前推，两侧石片掀起。
3. 裂隙沿斩击方向撕开，碎石沿弧线飞散，尘浪向两侧展开。
4. 尘土散开后露出凹陷与碎裂边缘，余势收束。

没有战士法阵。地裂、掀起的石片和深度均为预览画面效果，不包含地形破坏、碰撞或玩法改动。

## 观看

- [原速与局部慢放视频](media/ground-cleave.mp4)
- [局部慢放动图](media/ground-cleave-detail.gif)
- [上一版与重做同帧比较](media/ground-cleave-comparison.gif)
- [动作阶段图](media/ground-cleave-stages.jpg)

## 素材和生成记录

- [破碎石面贴图](rupture.png)：使用内置云端 OpenAI `image_gen`，以当前场景地表小样作为材质参考；完整[提示词](imagegen-prompt.txt)与[生成/处理记录](asset-provenance.json)已保存。
- [原始生成图](rupture-source.png)：保留模型原始输出。最终纹理仅清除透明边缘中异常高饱和红黄色溢色，并缩至 768×768，保留其余石色与透明通道。
- [地表小样](ground-reference.png)：从上一版同一场景的地表局部裁切，用于匹配石片颜色。
- `dust.png` 与 `flash.png`：复用项目已有 Kenney Particle Pack 1.1 CC0 的烟尘和光斑透明通道，白色 RGB 由材质着色。[项目内许可证](../../../src/cocos/assets/resources/vfx/kenney/LICENSE.txt)。
- 银白刀气沿用已确认的 v14/v15 材质与弯曲波前，没有新增配色方案。

生成完成、动画导出成功与用户美术验收分别记录。`provenance.json` 检查原生重劈动作、实际命中事件、地表采样、池容量、媒体解码、时长与输入文件哈希。临时预览通过不能替代 TapTap 真机表现验收。

## 复现

```powershell
node source-art/skills/warrior-ground-impact-v16/capture.cjs --variant design --shots WAR_04
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-ground-impact-v16/deliver.py video
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-ground-impact-v16/deliver.py gifs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-ground-impact-v16/deliver.py stills
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-ground-impact-v16/deliver.py verify
```

录制器在独立预览进程的模块响应中应用设计层，素材与脚本都位于本设计目录；不写入 `src/cocos/assets/`。
