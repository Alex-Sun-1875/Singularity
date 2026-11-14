# 人物外观 v5

2026-11-07资源清理说明：`appearance-v5/retired-runtime/`与`hero-v4/retired-runtime-v4/`中的PNG/meta重复副本已移入回收站，两份`archive-index.json`及目录外SHA-256相同的全部PNG原件保留。少量明确标记失败/淘汰的图亦已回收，提示词、来源JSON与选用版本保留；下文阶段验收为历史记录。具体范围与恢复位置见[资源清单](../../tools/resource-cleanup-2026-11-07.json)。

用户于2026-11-06指定男主发型、脸部和服装参考《博德之门3》阿斯代伦，女性参考影心，同时脸部更饱满、轮廓和阴影更柔和。

男主发型按随后用户的新要求改为《巫师3》杰洛特式银白中长后梳半束发；酒红高领短衣、深蓝袖与金色植物绣纹、炭灰裤和棕靴延用前一轮服装方向，移除旧青绿肩披。用户指出侧脸太尖后，进一步填平颧骨下方与面颊到下颌的凹陷，圆钝下巴，柔化鼻侧阴影。身体延用腰线上下约38.2:61.8的母版目标与约1.556m图面站立标尺，重绘不以整图纵向拉伸实现。

弥菈、夜祈、伊芙琳采用深色刘海与编辫、柔和饱满的脸部，分别保留酒红佣兵衣装和双匕首、灰绿游侠披风和弓箭袋、沉蓝守卫衣装和白布修补及灯笼。保留三人的成年年龄感、身份与差异。官方参考只存在source-art参考目录，不作为游戏运行图片。

继续使用项目现有Cocos3.8.8的Texture2D、SpriteFrame、quad和unlit透明材质，无新引擎、动画库或运行依赖。男主35张动作图与独立HUD头像、三位女性3张动作图统一新外观；行囊取当前武器的方向图，HUD使用独立清晰头部裁切。现有装备外形、动作时序与数值规则不因换衣改变。

所有位图由内置image_gen编辑，原始字节复制至source-art与运行目录；无外部API/CLI生成、像素重绘脚本或Pillow修图。Pillow仅只读测量alpha、独立组件、裁切与支撑脚锚点。提示词、输入/输出SHA与工具原路径保存在`source-art/characters/2d-concepts/appearance-v5/`。

最新母版：`male-direction-soft-geralt-v3.png`、`female-direction-soft-v2.png`。旧卷发母版与首轮动作源保留为历史，不作为最新验收。运行装配与原始manifest备份：`install-runtime.py`、`runtime-install.json`、`manifest-before-appearance-v5.json`；各`*-soft-v3/owned-actions.json`记录逐格测量。版本化PNG保留旧图，未覆盖历史源设计。

2026-11-06 14:43:44统一构建已通过。男主60动作键全部选择35张hero-v6图片，HUD与三位女性也选择最新版本。39张运行PNG与生成原图、source-art、构建native PNG逐字节相同，完整索引见`source-art/characters/2d-concepts/appearance-v5/generation-index.json`；106个未选旧运行文件安全归档在`retired-runtime/`并校验SHA，未删除源图。

本轮复用现有95项规则检查与类型检查，均通过。发布构建的桌面/手机横屏实际移动、攻击、行囊与存档重载无错误；剑/弓/杖/施法/闪避动作检查通过。三族真实键盘跑动及独立12方向2160个循环样本覆盖八相位，原生纹理匹配全部正确。弥菈、夜祈、伊芙琳在S01-T1/S05/U1-04的12个原生四向视图正确，无运行错误或失败请求。弥菈柔化鞋底边缘超出不透明支撑锚点1–2个源像素（最多0.0116m），另两人该偏差为0，画面未见悬浮。这些选区/摆姿夹具用于外观验收，不计为本轮完整首章通关。

汇总与截图见`src/cocos/test-results/appearance-v5/checks.json`及同目录。远景脸部仍受游戏画面像素数量限制，HUD及近景用于检查五官细节。

## 2026-11-06后续：三融合面容 face-v3

按用户最后的修正，男主面部改为阿斯代伦眉眼、盖尔饱满面颊与杰洛特沉稳下脸气质的原创融合；正面嘴型及下巴重做，继续保留已认可的侧脸方向、银白中长半束发、酒红/深蓝/金绣衣装。当前正面/近正面母版为`source-art/characters/2d-concepts/face-blend-v1/face-front-v3.png`，侧脸约束为同目录`face-study-v1.png`最右面板；没有把尚未回复的可选审美反馈记录为额外认可。

完整68张动作PNG和独立HUD头像已接入。冻结的88动作（60战斗/短动作、28探索）及各自UPP、FPS、阶段、方向和帧顺序全部保留；`FlatActors.ts`与背负版字节一致。新图实际有整体平移时仅转移原绝对支撑锚点，跑步保留原各阶段的地面关系；旧图本来连通的受击姿态及少量低alpha边缘按既有语义分帧，全部alpha≥16像素完整且唯一覆盖，没有通过裁主体、提高透明阈值或缩小人物消除问题。

所有位图继续使用内置image_gen，未通过脚本修图或重存。逐图请求、输入与原始输出路径/SHA、失败尝试、透明修正版及配准记录在`source-art/characters/2d-concepts/face-blend-v1/`；`generation-jobs-v3.json`为提示集，`runtime-install-record.json`为完整装配记录。安装复用现有Pillow/NumPy/SciPy只读测量和Cocos原生渲染，没有新增依赖；先暂存并校验PNG，再原子替换并具备失败回滚，未知manifest修改会拒绝覆盖。68张旧运行输入及原母版保留。

最终同一构建已复核：69张PNG的raw/source/runtime/按meta UUID定位的compiled文件逐字节一致，源manifest、构建JsonAsset及实际加载manifest深相等。95项既有规则、类型检查、88动作的1,364个原生姿态样本、28项携行行为与476个携行绑定、桌面/915×412手机横屏输入及存档重载、双指/取消检查全部通过；合法命令经过11区、4次击杀及首章结算，HP120→106，未授予资源或任务旗标，页面与网络错误均为0。进阶装备姿态夹具与合法获取/通关证据分开记录。

当前交付为[face-v3试玩包](../../src/cocos/artifacts/first-chapter-playable-concept-2d-face-v3-2026-11-06.zip)，CRC/SHA见`src/cocos/artifacts/test-package-2d-face-v3.json`；[最终验收](../../src/cocos/test-results/face-blend-v3/final-audit.json)与[运行行囊截图](../../src/cocos/test-results/face-blend-v3/final/release/test-results/flat2d-release-desktop-inventory.png)可直接核对。仍是既有低帧方向图流程；没有新增拔剑/入鞘过渡帧、逐槽防具纸娃娃或实体手机/TapTap性能验收。完整Web包保留3D对照与历史资源，不等同TapTap首包。
