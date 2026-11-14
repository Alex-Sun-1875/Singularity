# 现有七件武器场景图 v3

**旧候选，未通过人物验收。** 用户最新指出身体偏矮、上下身接近1:1和材质塑料感；当前停止继续派生/角色QA，等待成年7.5–8头身的新高质感母版评审。以下22张保留作来源与武器设计接入证据，不宣称人物比例、质感或整套动作已通过。

全部采用内置 `image_gen` 原生透明生成/编辑。PNG从工具输出按原字节复制，未用脚本绘图、拼图、换色、重采样或抠图。Pillow只读alpha以生成原生UV裁切metadata。

共有22张1536×1024 PNG，每张4方向×4格：

| 真实ID | stand/walk 与 attack stem | 高级run A/B stem |
|---|---|---|
| W01 | longsword-walk-v3 / longsword-attack-v3 | 复用动作负责人普通run，不在本子目录 |
| W02 | oath-walk-v3 / oath-attack-v3 | oath-run-v3 / oath-run-v3-b |
| L01 | storm-walk-v3 / storm-attack-v3 | storm-run-v3 / storm-run-v3-b |
| W07 | ashbow-walk-v3 / ashbow-attack-v3 | 复用动作负责人普通弓run |
| W08 | silverstag-walk-v3 / silverstag-attack-v3 | silverstag-run-v3 / silverstag-run-v3-b |
| L02 | astralbow-walk-v3 / astralbow-attack-v3 | astralbow-run-v3 / astralbow-run-v3-b |
| W11 | graystaff-walk-v3 / graystaff-attack-v3 | 复用动作负责人普通杖run |

`metadata.json`按stem索引，包含每图16个 `perFrameRects`（整图左上像素）、`perFrameOrigins`（相对各cropRect）、`alphaBounds`（相对cropRect）、`absoluteGroundPoints`（整图像素）、SHA及每动作UPP。Cocos动作manifest由root拥有，此目录不直接注册动作。

等宽384×256是原始格注册，横向长剑可能跨入相邻格之间的空白。必须读取 `perFrameRects` 获取完整原生源矩形，不可只按固定格裁断剑尖；矩形由每行真实透明间隙分开，不含相邻角色。不重画或裁存PNG。攻击为了完整长刃原生重排为约205–213像素主体高，已给每图UPP校准。

高级run只局部换现有武器，输入使用动作负责人2026-11-06明确冻结的新A（修侧向宽跨）/新B（修换腿），源路径和SHA写在每项 `frozenInputPNG/frozenInputSHA256`，没有使用 `*-rejected-*`。A为1–4相位，B为5–8；不做画布镜像。生成有少量水平布局漂移，需读新的脚支撑中心X。run A/B固定各方向源地面Y且共享源UPP，保存 `measuredSolePoints` 供审查，保留小幅垂直起伏，避免每帧把脚钉死。

`write-metadata.py`只补新SHA项，不覆盖已相同SHA的metadata；`annotate-run-metadata.py`验证冻结输入SHA并补run公共地面/比例字段。`generation-prompts*.json`保留提示，run文件另含最终工具输出文件名索引。`verification.json`记录只读资产验证；原生引擎的循环、握持与切换观感由root和动作负责人另验，不以静态资产检查声称通过。
