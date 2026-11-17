# 战士技能分化设计 v15

状态：设计预览，待用户美术验收；未接入正式游戏。

保留上一版确认的银白波前材质与较实的亮刃主体。纠正整套技能反复使用交叉剑气的问题，按每招用途分别组织动作、形状与触地反馈。

| 技能 | 本轮视觉设计 |
| --- | --- |
| 普攻三连 | 短刀光依次左右挥切、向下收刀，保持近身节奏 |
| 断空斩 | 两次定向剑气向前推出，突出切割与纵深 |
| 破军突袭 | 三条风痕沿实际突进路径延伸，抵达目标后爆出 120° 交叉剑气 |
| 铁誓壁垒 | 贴身菱盾轮廓与内肋，防御持续时保留盾形，真实受击后边缘短促加亮 |
| 裂地审判 | 使用现有重劈动作，指定落点出现下劈残影、地表裂缝、分叉与碎石起落 |
| 破晓裁决 | 横扫、上挑、120° 交叉终结，三段形态不同 |
| 战艺精通 | 真实技能命中后，持剑处闪出短促刃芒 |
| 铁誓不屈 | 真实盾击触发后，胸甲前出现短促银痕 |

裂地审判沿用当前指定落点、半径 2 米的实际命中区域。地裂是画面表现，不增加伤害、地形破坏、碰撞或额外判定。战士各招没有添加范围法阵。

## 观看

- `media/warrior-all-skills.mp4`：普攻、五个主动与两个被动的完整原速动画。
- `media/skill-contrast.gif`：四个用途不同的主动技能并排比较。
- `media/ground-cleave-detail.gif`：裂地审判半速局部。
- `media/all-skills-overview.jpg`：全套效果总览。
- `media/war_p1-focus.gif`、`media/war_p2-focus.gif`：被动触发局部。

## 来源与边界

角色、骨骼动画、场景与技能触发来自现有 Cocos 3D 构建及真实会话事件。录制器只在独立预览进程的模块响应中应用设计层，不写入 `src/cocos/assets/`。两张银白素材沿用 v14；`white.png` 是本地生成的纯白材质采样点，无新增生成式素材。

`review-checks.json` 对比上一版录制的战斗事件、目标、镜头与帧数，记录技能形态、交叉角度、地表贴合和原生骨骼。`provenance.json` 记录导出媒体与源文件哈希。媒体检查通过不等于用户美术验收，浏览器设计预览不替代 TapTap 真机表现验收。

## 复现

```powershell
node source-art/skills/warrior-distinct-kit-v15/capture.cjs --variant design
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/all-media.py video
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/all-media.py gifs
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/all-media.py stills
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/review-media.py
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/showcase-focus.py
F:/Models/ComfyUI_windows_portable/python_embeded/python.exe source-art/skills/warrior-distinct-kit-v15/all-media.py verify
```

导出使用环境中已有的 PyAV/Pillow，不安装依赖或启动本地生成模型。
