# 装备提示：传奇与神器四角纹饰

2026-11-16。用户已确认此前的图文间距、名称位置与右侧基础属性，并要求传奇、神器的装备图周围补上花纹。

纹饰直接调用项目已有的 `UiChrome.cornerOrnaments`，沿用原有四角曲线、原始线宽与金属色。72×68 逻辑像素的透明装饰容器位于柔光之上、真实装备图之下，实际曲线内缩在通知边框内。名称与属性位置沿用已确认版本；普通至史诗不增加纹饰。没有生成新美术、添加新依赖或输入拦截。

日常 `concept-2d` test 游戏中的实际 Cocos 截图，使用独立浏览器上下文与 Lv40 隔离呈现夹具。Pillow 仅缩小完整截图或裁切提示局部，不替换装备与花纹。

- `preview-legendary.png`：传奇最后一班岗。
- `preview-artifact.png`：神器王庭的黄昏。
- `preview-ornaments.png`：两条实际通知的局部对照。

完整截图和测量在 `test-results/equipment-notice-ornaments/`，验证记录在 `src/cocos/release/equipment-notice-ornaments-validation.json`。呈现夹具不作为真实掉落来源或概率证据，TapTap 真机、安全区和性能待验收；新增花纹的用户最终美术确认单独记录。
