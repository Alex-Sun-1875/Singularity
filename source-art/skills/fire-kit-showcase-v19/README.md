# 火系全部技能效果总览

本次任务：展示火系完整技能效果，供设计审阅。不修改正式技能、资源、数值、槽位或发布包。

## 当前展示内容

| 项目 | 展示内容 | 状态 |
| --- | --- | --- |
| FIR_01 赤焰枪 | v5 原生 3D 设计录制，火弹飞行、命中与残焰 | 候选，未记为用户已验收 |
| FIR_04 烈焰喷流 | v18 用户最新选定图片，五个法阵排列、火焰竖直上喷 | 用户选定的静态造型；动态待制作 |
| FIR_05 焚焰火域 | v7 合并火墙与火海的候选视觉，持续燃烧后消散 | 候选；合并后的完整规则和数值未实现 |
| FIR_03 焰心护盾 | 本轮从既有 Cocos Web 构建录制的原生护盾 | 现有预览实现，尚未另行改稿 |
| FIR_02 焚星坠落 | v7 扩大范围、v6 延长爆燃，保留双层纹样法阵 | 终极技能候选；未正式接入 |
| FIR_P1 余烬掌握 | 总览中列明燃烧延长被动 | 没有单独制造触发镜头 |
| FIR_P2 薪火余辉 | 总览中列明群攻直接击杀后的燃烧传播 | 没有单独制造触发镜头 |

`media/fire-skills-overview.jpg` 为全部五项和两个被动的总览。`media/fire-skills-preview.mp4` 为 27.1 秒汇总，依次为赤焰枪、喷流静态参考、合并火域、现有护盾、终极陨石。喷流章节明确标记为静态图，不能据此声称其动画已制作。

其余四项各有 `FIR_XX-motion.mp4` 可单独检查。录制保留原生角色动作与战斗时钟；与前版相同，仅陨石预告阶段在后期按原生相机投影合成已确认的纹样法阵。

## 来源与处理

- 喷流来源：`../fire-selected-reference-v18/user-selected-effect.jpg`，SHA256：`52b78fa21809693c830796ed479eb42acb545258f19286c0ff80f1d4acc20b36`。只为版面等比缩小，不重新生成、不改色、不改高度、不加工成伪动画。
- 赤焰枪：`src/.tmp/fire-spells-design-v5/final/design/FIR_01`。
- 火域、陨石：`src/.tmp/fire-kit-revision-v7/final/design/FIR_05`、`FIR_02`；后期法阵沿用 v7 `media.py`。
- 护盾：本轮 `capture-shield.cjs` 只读运行 `src/cocos/build/concept-2d-audio`，构建主文件完整哈希、原生骨骼、施放事件和逐帧护盾值记录于 `src/.tmp/fire-kit-showcase-v19/current/FIR_03/capture.json`。缓存构建的画面不代表后来源码修改已经构建或验收。
- 被动描述：现行 `PureSkills.ts` 的 FIR_P1 / FIR_P2；未另行声明数值设计。
- 沿用现有本地 Pillow / PyAV 进行排版和编码；本轮无需生成新图片，不调用本地或云端生成模型。

生成文件与参数检查见 `verification.json`；美术状态单独记录：喷流静态造型为用户选定，其余候选未据此自动通过美术验收。所有正式接入与真机验收仍未发生。

## 复现

```powershell
node source-art/skills/fire-kit-showcase-v19/capture-shield.cjs
& 'F:/Models/ComfyUI_windows_portable/python_embeded/python.exe' -X utf8 source-art/skills/fire-kit-showcase-v19/media.py
```
