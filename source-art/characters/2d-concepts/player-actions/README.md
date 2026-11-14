# 拉斐尔二维动作图：原始输出安装与元数据

## 2026-11-06 跑步 v3

当前 `run`、`run_bow`、`run_staff` 分别使用 `run-v3{,-b}.png`、`run-bow-v3{,-b}.png`、`run-staff-v3{,-b}.png`。每动作两张1536×1024原始PNG，每张4列×4方向行、每格384×256；A片为第0–3相位，B片为第4–7相位，合计每方向8帧。动作独立 `columns=4`、`frames=8`、`fps=14`，`frameImages`逐相位选择A/B，`frameIndices=[0,1,2,3,0,1,2,3]`。原 `run.png` 保留。

使用内置 `image_gen.imagegen`；未用Pillow绘制、缩放或改色，源与运行PNG保持生成器原字节。杖A片一次透明提取也由imagegen完成。完整提示、未采用草稿原因见 `run-v3-generation.json`；SHA、alpha包围框、逐帧身体/脚底测量见 `install-records.json` 和 `run-v3-verification.json`。

新版X锚测量腰胯区47–60%高度内的最长alpha支撑段中点中位数，消除生成图列间排版漂移；Y锚固定为每方向8帧脚底线中位数，不再随最低单脚逐帧跳动。`perFrameOrigins`采用方向到8个锚点的记录。A/B统一人物尺度；未把剑尖、杖头、箭筒顶部当成人物身高。

可执行 `python source-art/characters/2d-concepts/player-actions/install-run-v3.py` 重装本批。它只更新3个run动作及本批来源记录。旧 `install-player-actions.py` 仍重装旧动作集，若先运行旧脚本，应最后运行v3脚本。

本轮alpha检查确认96格前景都未碰格边，边线alpha最高3；单方向头顶Y变化1–6px，固定地面保留小幅自然起伏。逐帧意图记录不能替代实际播放审查，尤其A片第3列的侧向前摆、B第4列收腿离地与A/B相接，仍需在浏览器按实际速度复审。

原生Cocos实测证据位于 `src/cocos/test-results/run-v3-live-qa/`：实际点击启程后的物理d/a输入三武器均3.6m/s并触发对应run；12组合core-command夹具的0–7相位/A-B实际纹理均匹配，page errors为0。该轮视觉发现侧向A第3格大跨步后骤收，判自然循环未通过。当前三张A已由imagegen定向收为胯下低passing，旧源另存 `*-rejected-wide-step.png`，提示和选择证据在 `run-v3-a-corrections.json`。旧视频保留为缺陷证据；新A尚需统一构建后复审，不将旧视频写成新A通过。

第二轮原生复审另存 `run-v3-live-qa/after-fix/`，12段新视频与72张关键帧保留；剑/弓/杖基础腿序已在当前游戏尺度判可接受，A3骤收问题消除，B4到A1可读为收腿落脚。该轮发现W11杖B上段短于A的持物跳变，随后仅重画杖B道具并保留腿序，来源见 `run-v3-staff-prop-corrections.json`，旧短杖另存 `run-staff-v3-b-rejected-prop-short.png`。新B列排版收紧，采用动作 `frameRectsByImage` 的16个384×256窗口，图片未裁切改写。A/B材料细节仍有小差异，最终杖道具3/4/7/0相位待统一构建复核。

仅重装普通杖跑可执行 `python source-art/characters/2d-concepts/player-actions/install-run-v3.py --action=run_staff`。该模式只更新run_staff动作和两张staff来源记录，重读并保留最新manifest的其他动作。最新一次安装校验非staff动作全部等值、4张冻结剑/弓源SHA不变。

首版B因正/背面没有真正换支撑腿被视觉复审拒绝，另存三张 `*-b-rejected-same-leg.png`；历史安装信息见 `run-v3-rejected-install-records.json`。当前B是重新绘制的相反腿半周期：正面低靴在画面右侧、左脚后收，背面低靴在画面左侧、右脚鞋底抬起。剑、弓、杖均经全图目视确认；最低靴相对骨盆X的正负变化见测量记录。对应原始提示与选择原因在 `run-v3-b-corrections.json`，未使用图像后处理换腿。动作完整节拍与前倾角仍不以这些测量宣称通过。

来源为 root 使用内置 `image_gen.imagegen` 从 `hero-v5-balanced.png`派生并指定的PNG。此目录保留原始生成字节；安装脚本仅复制文件与读取alpha，不用Pillow裁切、缩放、改色或绘制。

| 运行图集 | 动作与列顺序 | 时序 |
| --- | --- | --- |
| `walk-bow.png` | `idle_bow=[0]`、`walk_bow=[1,2,3,2]` | 已使用移除第2行第4列错误佩剑后的修订源 |
| `walk-staff.png` | `idle_staff=[0]`、`walk_staff=[1,2,3,2]` | 每帧实际持杖 |
| `attack-staff.png` | `attack_staff=[0,1,2,3]` | `phaseStarts=[0,.14,.28,.62]`；第3列接触/发射，贴近`.20/.70=.286` |
| `run.png` | `run=[0,1,2,3]` | 4帧循环；已用imagegen移除源图真正半透明灰雾 |
| `dodge.png` | `dodge=[0,1,2,3]` | `phaseStarts=[0,.12,.36,.65]`；imagegen收边后最小16px留白，深蹲首帧定标0.98m |
| `hit-death.png` | `hit=[0]`、`death=[1,2,3]` | 受击固定姿态；倒地最终为完全躺平姿态，尺寸取直立受击帧标尺 |
| `spell-interact.png` | `spell=[0,1]`、`interact=[2,3]` | 分别`phaseStarts=[0,.5]`与`[0,.18]` |
| `attack-bow.png` | `attack_bow=[0,1,2,3]` | 短弓ready/draw/full/release，`phaseStarts=[0,.2,.5,.75]` |

新增八张均为1536×1024、4列×4行、每格384×256。行依次为下、右、上、左。对应运行文件位于 `src/cocos/assets/resources/flat2d/characters/raphael/`。原有待机、行走和剑击清单保留；剑击只补充 `phaseStarts=[0,.15,.28,.6]`，对应`.44`秒动作中的`.12–.22`秒接触窗口。

每动作都有16格的 `alphaBounds`、`perFrameOrigins`及独立 `worldUnitsPerPixel`。身高标尺使用前向第0帧中央头发顶部至脚底，排除弓、杖侧面的最高点，再对齐当前主角待机的可见米制高度。`bodyScaleReference`保留具体取样区域、头顶像素、脚底像素与目标高度，方便复查。

脚锚X取可见高度下部30%支撑区（alpha>32）的左右外接边界中点，保留原脚底Y。旧算法只取最低5.5%的像素中位数，会在左右单脚之间跳动；修正后新增动作的单方向帧间锚X跨度最高0.232m，跑步左右方向从0.894/0.932m降为0.148/0.161m。原图字节、身高标尺和运行时代码未变。实测数据与浏览器同机位前后截图见 `src/cocos/test-results/flat2d-hero-visual-qa/origin-fix-report.json`。

图片存在alpha为0的透明背景；部分查看器仍会显示透明像素里保留的棕色RGB，实际渲染必须按PNG alpha混合。前景alpha最高254，格子边缘最高2–13，包围框以alpha大于32的前景为准，低透明抗锯齿尾不用于脚底或身高标尺。

`install-records.json`逐张记录原始生成路径、生成源/此处副本/运行PNG三份SHA-256、已认可人物设计来源SHA、完整alpha测量与文件预算。`install-player-actions.py`可读取这些指定源重新安装同一批资源，不安装依赖、不构建项目。

已裁切长弓顶部的旧 `exec-debed06b-b522-4ead-93c1-faf3827fc0bd.png`未安装，采用完整短弓替换。跑步灰雾提取和翻滚收边均由内置imagegen完成，各一次；原始输入、选用输出与完整提示见 `run-alpha-generation.json` 和 `dodge-reframe-generation.json`。所有选用PNG仍为生成输出原字节。

当前11个canonical动作均有对应图：`idle/walk/run/attack_sword/attack_bow/attack_staff/spell/dodge/hit/death/interact`；附加`idle_bow/walk_bow/idle_staff/walk_staff`。其中受击为单帧反应，施法与交互各两帧，其余按清单列数；不把这些简化帧数描述成完整逐帧长动画。尚未为每一档装备、或持弓/杖时的翻滚/倒地分别绘制独立变体。
