# 旋风斩 · 裂地技能的替代方案 v17

状态：单招概念动画，待用户评审；未接入游戏，也未注册新技能或修改原技能数据。

用户决定停止调整裂地斩，本方案将第四个主动技能提议替换为旋风斩。视觉流程是短蓄力、连续两圈回旋、收尾向前甩斩、收刀复位。两道银白月牙在腰侧不同高度扫过，带弯曲的波前厚度、尖端与柔和尾流；主刃保持较实的银白质感。

## 观看

- [原速与局部慢放视频](media/whirlwind-skill.mp4)
- [原速动图](media/whirlwind-skill.gif)
- [局部慢放动图](media/whirlwind-detail.gif)
- [动作阶段图](media/whirlwind-stages.jpg)

## 动画来源与设计边界

- 场景、角色、骨骼、装备与横斩动作来自现有 Cocos 3D 素材，使用 `attack_sword_2` 的源姿势，并在独立预览中编排转身与动作采样。
- 月牙为原生弯曲网格，有不透明亮刃、径向厚度、弯起的波身和逐渐消散的尾流。本轮没有新增生图。
- 三个周围目标的受击动作和短促亮痕是概念动画中的接触示意，不是已经实现的伤害、范围、连击或硬直。录制不会施放占位技能，真实会话中不产生攻击或伤害事件。
- 地裂、地面破坏和法阵均不参与本方案。v16 留作已停止的历史方案。
- 正式旋转动作、攻击判定、技能数值及 TapTap 真机表现都不属于本次概念交付。

`provenance.json` 记录使用的原生动作、设计转身角度、视觉接触、绘制容量、完整媒体解码、时长和输入哈希。动画导出成功与用户美术验收分别记录。

## 复现

```powershell
node source-art/skills/warrior-whirlwind-v17/capture.cjs --variant design
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-whirlwind-v17/deliver.py video
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-whirlwind-v17/deliver.py gifs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-whirlwind-v17/deliver.py stills
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-whirlwind-v17/deliver.py verify
```

设计模块只在独立录制进程的 HTTP 响应中替换；没有写入正式游戏的 `src/cocos/assets/`。
