# 手机任务追踪框与技能纹理兼容调整

2026-11-11。对应用户在 TapTap 手机截图中反馈的三行任务拥挤、继续操作栏过窄、技能图案与金边空白。

## 本次调整

- 任务框在原有状态框宽度基础上增加24个逻辑像素；手机框高72像素，三行中心间距20像素。地点、目标、路线字号分别10.5、12.5、10.5，使用既有字体和单层暗金边框。
- 导航列从36加宽至52个逻辑像素，操作文字12像素；48×48触控区位于列内，与任务详情触控区保留8像素间距。详情触控区覆盖全部三行，长任务以省略号收尾并可打开详情。
- `UiSkin.frame` 在小游戏环境保留已上传的纹理，不再为 UI 临时重新上传图片生成 mipmap；仅当纹理实际具有多个 mip 层级时启用 mipmap 过滤，单层纹理使用普通线性过滤。Web 预览继续保留原有可用的 mipmap 细节表现，无法生成多层时关闭 mipmap 过滤。

纹理处理复用 Cocos Creator 3.8.8 的 Texture2D 和既有资源分包加载，不新增依赖、素材或平台接口。依据：[Cocos 3.8 纹理说明](https://docs.cocos.com/creator/3.8/manual/zh/asset/texture.html)、[TapTap Cocos 适配说明](https://developer.taptap.cn/minigameapidoc/dev/engine/Cocos-Laya-Egret/)。

## 已完成的本地验证

- `npm run check`、`npm run build`、`npm run check:tap -- --mode test` 通过。
- 在日常 `concept-2d` 入口检查844×390、932×430、915×412和补充小屏667×375。三行没有重叠，导航触控区保持48×48及8像素间隔；另外检查1280×720桌面与模拟44像素侧边、21像素底边的硬件安全区。
- 实际触控点击继续后进入寻路，再点停止后停止；地点、目标、路线三行均可打开旅程详情。长任务保持选定字号并显示省略号。
- 四流派在满技能状态下，各自的普攻、闪避、四个主技能和终极共7个图标都有贴图；金边正常加载。该满技能状态仅用于本地画面验证，没有修改正式成长规则。
- 用当前 `UiSkin.ts` 的 `MINIGAME=true` 分支，结合实际 Cocos Web 渲染器模拟解码图片已回收：图标和金边均保留单层纹理，mipFilter为NONE，未重新上传图片。桌面WebGL2下将该纹理切回旧过滤方式也能显示，**没有复现TapTap截图中的空白，不能据此确认真机根因或宣称真机修复验收通过**。

截图与运行数据：[本地验收结果](../../test-results/hud-mobile-readability-v2/verification.json)、[完整画面](../../test-results/hud-mobile-readability-v2/iphone14.png)、[任务框局部](../../test-results/hud-mobile-readability-v2/quest-detail.png)。模拟安全区单独标记，不作为默认效果展示。

## TapTap 测试产物

游客测试包版本0.3.11，由现有打包脚本自动递增。官方转换完成；首次报告校验发现临时资源计划为preview模式，恢复test模式后重新运行现有报告器通过，没有放宽游客校验或修改打包校验代码。

- 包：`src/cocos/artifacts/taptap-guest-test/SwordAndFire_0.3.11_TapTap_guest-test_20261111T003512Z/SwordAndFire_0.3.11_TapTap_guest-test_20261111T003512Z.zip`。
- 完整上传ZIP：238,890,116字节（227.82 MiB）。
- 排除声明分包后的本地首包审计ZIP：1,266,335字节（1.21 MiB）；不是平台实测首包流量。
- 本轮未测可玩前资源总量、启动网络流量、内存及帧率。体积预算和控制台历史限制沿用现有报告，不能代替当前平台实测限制。
- ZIP SHA-256：`95bc4ad3614ea3c2226d53b8d9905803da7c53c4f194840aa119fb66f861eb26`。

没有上传或发布。本包沿用已授权的游客测试模式和本机存档；正式业务登录服务仍待部署。待在真实TapTap AppID下复测iOS/Android技能图案、金边、分包加载、导航继续与停止、长任务排版和实际安全区。
