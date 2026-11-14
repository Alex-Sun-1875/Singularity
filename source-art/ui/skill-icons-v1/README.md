# 独立技能图标

为30个技能（含终极、闪避、治疗及被动）分别配置独立轮廓；HUD和技能页按同一技能ID映射加载。保持既有金属浮雕和圆框风格，空槽及未解锁槽位中央留空。设计约束见 `docs/design/ui-layout-guidelines.md`，运行映射见 `CombatSkillIcons.ts`。

复用已安装的 `@resvg/resvg-js` 与原有 `skill-relief-v18/emboss.py`，不新增依赖。原始SVG、上游固定提交、作者、CC-BY-3.0许可、SHA-256及导出记录均保存在 `sources.json`；运行资源保留 `combat-relief/CREDITS.txt`。导出为128×128透明PNG，30张共575,828字节，沿用现有资源加载与mipmap处理。

在仓库根目录执行 `node source-art/ui/skill-icons-v1/export.cjs` 可从已归档SVG重新导出，无需联网。`download.py` 仅用于补充源文件；其记录的WLAN绑定与实际直连地址须按当时环境重新核实，不得回退代理。临时树索引不是运行依赖。

生成结果与美术验收分开记录在 `sources.json`：`isolated-preview.jpg` 为最终图案总览，`pilot-preview.jpg` 为早期四图小样。浏览器复查覆盖844×390和932×430、四个流派的1级/40级共16种状态，含独立纹理、空槽、菜单入口、指定槽位换装、存档恢复、触控施放及快速切换。结果及实际游戏截图位于 `test-results/skill-icons-v1/`。`npm run check` 与Cocos Web构建通过；浏览器复查不代替TapTap真机验收。
