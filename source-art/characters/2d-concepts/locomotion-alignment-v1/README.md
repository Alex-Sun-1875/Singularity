# 站立、慢走、跑步的一致性修正

最终按用户最新指示：**头型和头部体积以站姿为准，缩小移动中的大头**。身体比例、长腿及步幅延续此前认可的跑步身体。当前范围是W01长剑角色的探索/持剑站立、慢走和跑步；其他武器、闪避、HUD保持。

当前运行manifest SHA256：`4065d59acbccb8c85642cf31cab840a8fce3577a87806ce2c558096098b41df8`。

- `assets/`：独立站姿及其配套全身慢走的首阶段四张原生图；站立不再借用闪避第一列。
- `head-scale-v2/assets/`：最终六张跑步/慢走头部对齐图。最终站姿保留首阶段两张idle，不曾放大。
- 每个PNG相邻的`.prompt.txt`/`.provenance.json`记录实际使用的内置ImageGen提示、原始输出和SHA。默认raw保留；透明清理、持剑慢走头部纠正的前后记录保存在`head-scale-v2/attempts/`及provenance链。
- `calibration-proposal.json`、`held-calibration-proposal.json`：实际身体尺度、髋轴及支撑鞋锚点。头部编辑后保留UPP与每个runphase的地面/腾空关系。
- `head-scale-v2/install-report.json`：六图完整裁切/身体注册及有备份的安装事务。只写新`locomotion-v2`资源，旧PNG不覆盖；站姿/root/HUD及其余82个动作相对首阶段精确保留。对最初e1基线，本轮共修改9个动作记录（包含通用别名）。
- `head-scale-v2/served-build-audit.json`：当前69张动作图的源/运行资源/构建PNG/HTTP逐字节一致性、编译manifest与原稿HUD验证。
- `head-scale-v2/runtime-visual-review.json`：独立实机审查及实际覆盖范围；`visual-review-heads.json`为原图阶段审查，不等同实机通过。
- `final/`和`final-all/`：同相机1280×720、orthoHeight2.0的真实Cocos切换录像/截图及路由采样。合并覆盖四向、探索/持剑、慢走四帧与跑步八帧；持剑宽限期结束会正常转回探索跑，记录未掩盖这一点。
- `standing-walk-run.webm`：便于查看的实机右向短片，取完整录像9.30–13.00秒并只裁420×420观看区域；没有重绘人物。完整录像保存在`final-all/idle-walk-run.webm`。

全部角色栅格修改使用**内置ImageGen**；交付PNG与选定native raw逐字节一致。Python/Pillow/SciPy只测量，不重绘/抠图/重采样角色图。生成工具会重新编码和细微重绘，因此只依据实测轮廓/姿态说明保持身体比例，不声称身体RGBA逐像素相同。少量金绣/卷发高光和相位头部差异仍可能存在。

`idle-head-scale-v2.prompt.txt`是用户纠正方向前的未执行草稿，不属于最终提示词集。`before/`与`after/`是历史复现/首阶段结果，最终请看`final*`。

验证：TypeScript检查通过，复用的95项规则测试通过，最终Cocos3.8.8构建exit0，原有motion脚本通过；最终两轮切换采样无pageerror/贴图不匹配。没有新增测试框架、依赖、提交或发布。

桌面预览使用现有web-mobile构建模板的16:9 iframe，窄桌面侧栏也能运行，不保留浏览器临时viewport设置：
<http://127.0.0.1:7469/desktop-preview.048c2.html?view=2d&locomotion=standing-head-v2>
