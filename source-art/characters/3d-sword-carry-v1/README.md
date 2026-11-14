# 3D背剑位置对齐2D设计

后续[24件武器重建与对齐](../../weapons/3d-design-v1/README.md)已替换游戏中的武器外形和对应背鞘，并扩展所有弓、锤、杖；本页保留原2D测量依据与早期校准过程，当前模型和动图以新记录为准。

2026-11-09。用户指出收剑后没有背在背上，随后要求以现有2D设计稿校准背剑位置。当前更新已接入可选[3D主角入口](http://127.0.0.1:7469/?view=2d&player=3d)，默认2D入口保留。

## 设计依据与结果

以当前2D `explore_idle_W01/W02/L01`背向身体帧及独立的 `explore-{W01,W02,L01}-up-gear.png`为依据。独立装备图来源、SHA-256和主连通区域的轴线测量保存在 `design-reference.json`；[设计原图板](2d-reference.jpg)、[独立背负装备](2d-sheathed-swords.jpg)保留供核对。没有改动2D源图像。

按设计将剑柄靠近角色右肩颈侧，细皮革剑鞘斜向左胯，鞘尖至左胯下方。三件装备分别记录长度和角度；直剑与传奇剑沿用约22°的2D投影方向，誓剑约28.6°，考虑游戏相机俯视角后转换为模型空间方向。当前身形、衣装和剑柄装饰继续沿用已接入的3D近似模型，未冒称精确复制2D人物或雕花纹样。

- [2D与实际3D背负对照](runtime/design-comparison.jpg)：真实行囊RenderTexture，正交背视，等身高缩放，未重绘姿势。
- [三剑实机动图](runtime/sword-carry.gif)：连续转身、跑动、持剑挥击与回势、脱战后收回背部，142帧、7.1秒，以约2/3速度播放。
- [代表帧](runtime/review-contact.jpg)，以及八个代表方向的各剑原始截图在 `runtime/`。

## 复用与接入

使用项目已有Cocos Creator 3.8.8 `SkeletalAnimation.createSocket`、原生动画采样、`Node.setParent`、`primitives.cylinder`、现有皮革/金属PBR库，以及已安装Blender的 `bmesh.bisect_plane`。没有下载资源或安装依赖，也没有调用图像生成。

原生主角以前只有手持挂点，本轮新增 `spine_03`背部挂点。设计坐标以待机动画第0帧为基准，先采样两个不同帧，确保新建的烘焙动画挂点同步，再将位置与朝向转入挂点局部坐标。这样避免以导入静态姿态直接挂接造成躯干遮挡。参数保存在主角manifest的 `cocosBinding.swordBackCarry`，每件装备可独立校准。

持握时使用原完整武器预制体、原手掌挂点与原局部姿态；背负时切换为原剑柄网格与细皮革鞘，整组挂在同一个背部骨骼上。原生剑网格没有独立可隐藏刀刃，所以 `prepare-hilts.py`在**另存的静态附件**上用Blender原生平面切割移除鞘内刀刃，保留原剑柄、护手、UV与材质；来源及输出哈希在 `hilts/provenance.json`。未修改原手持武器FBX或身体FBX。

新增的三个附件安装在 `src/cocos/assets/resources/actors/props-native/stowed-*`；皮鞘沿用现有皮革与金属材质，不新增贴图。现有道具库没有适用剑鞘，因此只用引擎原生锥度柱体适配轮廓，并复用材质库。原角色与武器来源、CC0许可证见[原生资源记录](../../../docs/assets/native-library-runtime.md)。

探索/战斗收持判断从现有2D表现中提取为 `updateWeaponReadiness`供两种表现共用：转向本身不会拔剑；攻击、受击或附近可见威胁进入持握，威胁结束后延续原有2秒展示时间再背负；探索翻滚保持背负，战斗翻滚延续持握。暂停换装及时切换正确的背负装备。效果发射点始终读取原手掌位置，不跟随背剑挂点。

当前按原有表现时机切换挂点；本轮没有制作伸手拔剑、实际插入剑鞘的专用动作。持弓、法杖、原身体动作和已校准的箭轴不因背剑改动。

## 验证与范围

类型检查、Cocos web-mobile构建、相关差异格式检查通过。复用项目Playwright在隔离浏览器记录，没有读取或修改用户浏览器存档，也没有新增测试框架、测试依赖或玩法用例。

`inspect-runtime.cjs`以真实GameSession指令和原生动画采样记录24个八向静态视图及426个动态样本，逐帧检查仅一组剑附件可见、挂点局部坐标误差与手掌发射点误差小于1e-6；三剑背负→持握→背负均保持同一附件节点。另检查探索翻滚、暂停换装、13个蒙皮渲染器的实际行囊预览，页面运行错误为0。原始数据为 `runtime/report.json`。

`flat-regression.cjs`使用默认2D入口的真实状态变化检查待机背负、攻击持握、脱战背负和探索翻滚背负；结果见 `runtime/flat-regression.json`。`capture-comparison.cjs`导出实际行囊透明RenderTexture；`assemble-previews.py`仅裁切、缩放、加字幕、编码GIF，参数见 `runtime/previews.json`。这是本次背剑范围的运行及目视检查，不是所有装备、所有动作和全部场景的碰撞验收。

`prototype/`保留早期裸刃和猜测挂点，位置已被用户否决，不是当前验收结果；`depth-calibration/`与 `diagnostic.json`为定位静态骨骼/动画挂点与深度问题的制作中间记录。当前以manifest、最终构建、`runtime/`对照及动态记录为准。
