# 技能页全页细节对齐 v6

2026-11-10，按用户提供的[原稿](references/approved-skills.png)和[红框旧运行界面](references/annotated-runtime.png)调整五个流派共用的原生技能面板。

- 顶部改为连续流派栏，选中项单独发光；可用技能点使用原稿异形底板和独立大数字。
- 技能卡恢复原稿类型标签、选中光框和发光等级菱形，校准四主动、终极和双被动的横向位置；共享图标在面板内裁去旧边框后叠加细切角框，不修改HUD原图。
- 右侧恢复大图、战斗类型、等级与菱形层级，优先展示实际机制；断空斩段数读取当前等级的命中段数。角度比较拆为前值、原稿箭头和后值；其他升级效果与长说明保留原生滚动阅读。
- 加减、预览升级使用原稿小按钮；保持48逻辑像素触控范围和8像素间隔，按钮图案在触控区内适当偏移以贴近原稿。
- 底部恢复四个主动槽的独立编号饰框、组标题细线及竖向分隔；校准第二被动槽位置，空槽只留边框与主动槽编号。状态栏去掉重复点数，恢复较长的菱形装饰线。

[原稿／旧版／新档／16级运行对照](review/skills-comparison.jpg) · [八处细节放大对照](review/details-comparison.jpg) · [实际运行效果](review/skills-runtime.jpg) · [五流派运行图](review/all-families.jpg)。截图只裁黑边、缩放及排版，没有用原稿替换运行像素。原稿紧凑位图中顶部两层导航不足以容纳两排48像素触控区及8像素间隔，因此手机运行版仍保留必要纵向空间；全页对照如实展示位置差异，不宣称逐像素相同。

技能名字、解锁条件、段数、点数、升级费用与槽位配置均沿用现有规则。16级隔离审阅档通过现有经验与分配接口配置成原稿对应的3／2／3／2／1／3／2阶，实际剩余5点；1级档仍显示真实解锁与空槽，用户存档不改动。本轮没有改玩法或增加依赖。

本轮没有新生图。20项原稿细节通过Pillow裁切、清除旧文字区域和透明遮罩导出，来源矩形与SHA256见[runtime-assets.json](runtime-assets.json)，可通过[prepare-assets.py](prepare-assets.py)重建。随包字体已核对新增中文，无缺字。[构建镜像一致性](build-source-review.json)、[截图来源与校验](runtime-review.json)和[对照图生成程序](prepare-review.py)分别保留。

TypeScript检查、Cocos Creator 3.8.8构建及复用的浏览器验证记录见[16级检查](../../../src/cocos/test-results/skills-alignment-v6/browser-review.json)和[1级检查](../../../src/cocos/test-results/skills-alignment-v6/fresh-review.json)：覆盖844×390、932×430、桌面及与用户截图相同比例的宽屏；检查五个流派、字体、触控尺寸／间距，以及升级预览、应用、返还、主动槽交换与保存重载。[默认本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural)同步记录见[default-preview.json](../../../src/cocos/test-results/skills-alignment-v6/default-preview.json)。

实现与助手运行视觉复核完成，用户最终美术验收待进行。本轮仅更新本地Web预览，没有TapTap上传或发布；平台入口、安全区、触控、生命周期、存档、分包和真机性能仍需真实AppID与目标设备验收。
