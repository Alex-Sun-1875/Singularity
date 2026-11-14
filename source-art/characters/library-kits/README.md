# 现成人物与动作库

2026-11-05。用户再次明确人物、握剑与走路优先直接复用现成库。本目录保存此次官方免费 Standard 包的来源与 SHA-256；原始压缩包、解压原件在 `src/.tools/quaternius-ready-kits/`，原生产人物备份保留，原生版本接入说明见 `docs/assets/native-library-runtime.md`。

| 官方库 | 本次取得的实际内容 | 许可 |
| --- | --- | --- |
| [Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html) | Superhero 男女原身体/头部、原发型/眉/眼；不是付费版全部体型 | CC0-1.0 |
| [Modular Character Outfits – Fantasy](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html) | Male/Female Ranger、Male/Female Peasant，各有整套与模块化导出；不是全部12套 | CC0-1.0 |
| [Universal Animation Library 2](https://quaternius.com/packs/universalanimationlibrary2.html) | 原生65骨原地/RootMotion GLB、FBX及动作；与项目已有UAL1配套 | CC0-1.0 |

全部从作者 Itch 免费下载入口取得，未购买 Source 版。原 ZIP CRC 已检查，精确文件大小、哈希、上传 ID 与许可文件路径见 [sources.json](sources.json)。以实际归档内容为准，不将官方新付费 Source 的更新记录视为已下载版本。

## 前期兼容性实证（历史候选）

前期候选位于 `src/.tmp/native-kit-review/`；随后原生生产适配位于 `src/.tmp/native-production/`，通过安装脚本接入正式人物资源。直接组合作者衣装、对应原头与原发型，按作者说明移除被衣物覆盖的身体；保留原骨架、权重、UV和原生动作，没有再转成旧53骨或自写重定向求解器。

- 男 Ranger完整本体32,879三角，女Peasant完整本体22,120三角，均为65骨；现有剑另476三角。
- UAL1/2骨架与bind完全一致；衣装与对应Base头颈bind一致。其余体型rest与Mannequin有差异，不能把原始glTF绝对TRS直接覆盖人体节点。
- 已离线播放/渲染原生Idle、Walk、Jog及Sword动作；候选原材质、发型和颜色尚不等同v5设定。
- `Sword_Regular_A`原长约.433秒，但完整段主斩晚于现有命中窗；候选为原速A帧4–13接A_Rec前.14秒，保留.44秒游戏时序。具体接触与淡入仍需Cocos实测。
- 原衣装贴图4096²、头发/头部2048²，必须通过现有导出流程处理手机预算；不是直接原尺寸打入游戏。
- 这次免费UAL1/2不含专用弓/杖战斗动作；已补取下述官方KayKit资源，尚未宣称11状态全部已在Cocos替换。

精确原件、骨架契约、动作时序、图像与预算在 `src/.tmp/native-kit-review/evaluation-summary.json`，可编辑候选为 `native65-candidates.blend`。首批人物已在真实Cocos构建验收；旧人物和此前可玩构建保留，完整替换以生产接入报告为准。

## 已补齐的现成弓、施法与武器原件

- [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations) Free1.1，官方CC0，ZIP14,858,957字节、SHA-256 `65882f31f905ad2e953819648a59287cdeab8f623908d5ef701971d3758be20f`。真实 `Rig_Medium_CombatRanged.glb` 包含 `Ranged_Bow_Aiming_Idle/Draw/Idle/Release` 与 `Ranged_Magic_Raise/Shoot/Spellcasting` 等动作。
- [KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers) Free2.0，官方CC0，ZIP13,024,345字节、SHA-256 `abe48f4763fba0896bab486ee9e6d08ca6b5b3884b9601f235c8847ae94dc479`。原生 `sword_1handed` 300三角、`staff` 440、`wand` 150、`arrow_bow` 52、`bow` 412、`bow_withString` 684；后者自带原作者 `Draw` morph，可接引擎原生形变，不必重造拉弦几何。

原件及逐文件实拆位于 `src/.tools/research-animation-kaykit/`，官方获取清单副本在本目录。KayKit的23关节与Quaternius原生65骨不同，需要用成熟工具一次重定向，不能盲复制节点TRS或原hand slot坐标。动画首帧已有动作，独立T-Pose另存，不能照旧UAL校准帧逻辑删掉首帧。本段记录原件获取及结构核验；后续生产接入与实际手部接触记录见原生接入说明。

进一步实际检查确认：已有UAL1原生65骨中含 `Spell_Simple_Enter/Exit/Idle_Loop/Shoot`，先直接作为施法/持杖候选；不是专用双手杖战斗。只有弓优先采用KayKit动作转换。KayKit的hand slot在Bow_Draw中还有约90度作者动画，不能只转身体、再用固定rest握点；需通过成熟工具把作者附件动作保留/烘焙到目标附件资源，Cocos使用原生动画和Morph能力。详细证据为 `src/.tools/research-animation-official/` 与 `src/.tools/research-animation-kaykit/socket-animation-inspection.json`。
