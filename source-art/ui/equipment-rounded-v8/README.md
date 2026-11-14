# 装备圆角框与神器四角纹饰 v8

2026-11-11，按用户的[标注截图](references/annotated-desktop.png)统一装备图标外框，并修正主手文字、项链空槽、列表分隔线和右侧属性区。

所有装备图标共用原生Cocos圆角边框与圆角裁切，包含装备列表、已穿戴槽、锻造列表、锻印奖励及旧外观面板。外框圆角半径为短边的12%；选中时使用连续金色描边，不再叠加旧切角品质框和选中角饰。神器在框内四角各增加一组金色卷叶花纹；普通至传奇均不加花纹，选中状态不改变这一品质规则。原有公共品质颜色保留。

主副手仍在人物脚下，图标与名称上下分离，58逻辑像素高的触控区容纳完整图案与标签，保持原来的横向位置和至少8像素间距。空槽的部位示意缩小并与名称分开。列表分隔线改为单条细线，右侧属性区按实际行数调整可视高度，长来源文字显式换行。

[三种品质与主副手放大图](review/frame-details.jpg) · [前后整屏对比](review/equipment-comparison.jpg) · [神器实际装备效果](review/equipment-runtime.jpg) · [锻造页效果](review/forge-runtime.jpg)。截图只裁黑边、缩放及排版，没有将图稿贴到运行图上。

本轮没有生成新图或新增依赖，花纹、边框与遮罩使用Cocos Creator 3.8.8现有Graphics和Mask绘制；图案继续复用已接入的装备插画。遮罩使用已安装引擎公开的`Mask.Type.GRAPHICS_STENCIL`与`subComp`接口，未依赖DOM或平台私有接口。统一组件见[EquipmentIconFrame.ts](../../../src/cocos/assets/scripts/features/equipment/runtime/EquipmentIconFrame.ts)。

TypeScript、Cocos构建、[1级检查](../../../src/cocos/test-results/equipment-rounded-v8/fresh-review.json)和[多视口装备检查](../../../src/cocos/test-results/equipment-rounded-v8/browser-review.json)分别记录。验证覆盖844×390、932×430、桌面和宽屏，核对圆角遮罩、神器四角数量、非神器无纹饰、旧边框移除、标签不压图、触控间隔、装备切换与存档重载。审阅神器通过现有Boss掉落及地面拾取接口取得，使用隔离存档。源码与构建镜像校验见[build-source-review.json](build-source-review.json)，截图来源与SHA256见[runtime-review.json](runtime-review.json)，排版程序见[prepare-review.py](prepare-review.py)。

[本地试玩](http://127.0.0.1:7469/?view=2d&player=3d&progression=natural&preview=equipment-v8-20261111)同步记录见[default-preview.json](../../../src/cocos/test-results/equipment-rounded-v8/default-preview.json)。用户存档保留。本轮仅更新本地Web预览，没有TapTap上传或发布；用户美术验收和真实AppID下的目标设备验收待进行。
