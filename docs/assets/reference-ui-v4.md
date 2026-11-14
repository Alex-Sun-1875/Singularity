# 参考界面落地与实际验收

后续配色/按钮质感已按用户反馈整体更新；本页保留功能验收范围，当前视觉见[BG3方向统一](bg3-visual-alignment-v5.md)。

2026-11-05。正式工程：Cocos Creator 3.8.8，`src/cocos/`；本轮以手机横屏为主，落实用户提供的7张《博德之门3》参考图中的配色、布局和信息层次。使用烟黑底、古铜细边、象牙文字、青蓝选中态和暖火光，保留本作即时战斗、v5身份和v3地理。参考截图未作为游戏素材打包。

## 7项对应实现

| 参考 | 实际实现 | 运行证据（均在 `src/cocos/test-results/`） |
| --- | --- | --- |
| 1 加载 | 原创树木框景河谷背景、暗渐隐、真实加载阶段进度、旋转指示、手机提示 | `final-loading-resize.json`；`final-loading-landscape.png`、`final-loading-portrait.png` |
| 2 游戏画面 | 暖光/冷暗环境、持续脚环、真实头像、圆形地形小地图、集中动作栏；手机双指移动攻击与预备取消 | `browser-touch.json`、`reference-world-v2-review.json`；`browser-playthrough-u1-dinner.png` |
| 3 地图 | 当前区域实际场景的顶视捕获、真实探索黑雾、图例/详情、世界三层、拖动缩放/标记/定位；未发现的地点与隐藏剧情不提前展示 | `reference-map-qa.json`（候选交互）、`reference-map-storage.json`、`reference-map-production-final-review.json`；`reference-map-production-mobile-local.png`、`reference-map-production-mobile-world.png` |
| 4 人物 | 当前玩家真实3D模型和装备的独立RenderTexture预览，可旋转；关闭时销毁预览相机/节点/临时材质 | `reference-character-interactions.json`、`reference-production-character-review.json` |
| 5 技能 | 游戏已有技能分类、真实修正、点击详情和检定记录；手机可滚动，不依赖悬停 | `reference-production-character-mobile-skills.png`、`reference-scroll-final.json` |
| 6 总览 | 实际生命、专注、护甲、武器、地点、目标和检定资料；资料来自GameSession | `reference-production-character-mobile-attributes.png`、`reference-summary-scroll-final.png` |
| 7 行囊 | 左侧状态、中间人物与9装备槽、右侧品质/数量/筛选/物品详情及装备操作；安全检查点规则与预览同步 | `reference-character-interactions.json`、`reference-production-character-mobile-inventory.png` |

桌面1280×720、Android UA横屏915×412及更窄横屏已检查。主要人物面板触区在915宽至少45.35 CSSpx、740宽至少44 CSSpx；地图另检查667宽布局。左栏与技能列表使用引擎ScrollView/ScrollBar，实际触屏滑动可看到末项资源和技能。竖屏提示旋转并暂停游戏，恢复横屏后继续；正式构建的CSS和GPU尺寸一致，未通过伪造进度或替换加载响应证明。

## 复用与必要适配

- 人物使用Quaternius Universal Base Characters、Modular Character Outfits免费Standard原件，动作使用UAL1/2；弓动作与武器使用KayKit。原件来源、许可及哈希保存在 `source-art/characters/library-kits/`。10名角色保留65蒙皮骨骼、67层级关节和11动作。握点、骨骼转换、步频和游戏命中窗是项目适配，完整说明见[原生库接入](native-library-runtime.md)。
- Cocos原生Camera、RenderTexture、Mask、Graphics、ScrollView、ScrollBar和标准PBR直接承担预览、布局与渲染。地图继续复用已有FairyGUI，不引入新UI框架或测试依赖。
- 加载图使用内置image_gen生成原创画面，完整提示和来源在 `source-art/ui/loading-reference-v1/`；人物头像与武器缩略图取自实际引擎模型。
- 修正人物PBR倍乘：以原glTF metallicFactor/roughnessFactor为准，粗糙度读取打包贴图G通道，避免皮肤错误金属化。导出脚本同步修正。
- 横竖屏使用[Cocos官方构建模板配置入口](https://docs.cocos.com/creator/3.8/manual/en/release-notes/build-template-settings-upgrade-guide-v3.6.html)设置screen.exactFitScreen，模板保留官方生命周期。来源记录在 `source-art/ui/loading-reference-v1/screen-sizing-provenance.json`。
- 地下晚饭场景保留实体桌碰撞；交谈采用真实头肩射线，战斗射线仍会被桌挡住。通关脚本走到桌边真实交互距离，不授予旗标或物品。

## 验证与交付边界

既有95项规则检查通过；TypeScript检查和正式web-mobile构建完成。发布版桌面/手机尺寸实际输入、存档重载、换装、预览旋转及关闭回收、地图交互、双指操作和横竖屏恢复均有运行记录。完整首章以合法游戏命令经过11区、击败4敌并取得结尾奖励，页面错误及失败请求为0，见 `browser-playthrough-release.json`。最后变更为滚动指示/末项可见性和窄栏公式换行，另以实际触屏滑动复查。

最终证据与生产源码哈希汇总在 `src/cocos/test-results/reference-ui-completion.json`。本机入口为 http://127.0.0.1:7458/ 。试玩包为 `src/cocos/artifacts/first-chapter-playable-web-mobile-2026-11-05.zip`，128,089,582字节，CRC已核对，SHA-256为 `6fb73111a92518e86cbeafb692665b36d0d69d941bdd83852a8e384c1bce0239`；这是完整Web构建，不是TapTap首包。

手机UA和尺寸模拟不能证明真机帧率、温升、内存或前后台稳定性。免费衣装尚不覆盖全部v5造型，重甲/部分发型与逐区域最终美术仍有差距；本轮完成7个参考范围的可操作实现，不代表达到BG3最终制作水准。未公开发布或上传。
