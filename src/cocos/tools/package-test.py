"""Package a completed local Web build, without caches or source art."""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT = Path(__file__).resolve().parents[1]


def readme(version, platform, build_date, view='3d'):
    if view == '2d':
        return f'''剑与火 · 第一章 2D 可玩测试构建 v{version}
Cocos Creator 3.8.8 / {platform} / {build_date}

完整解压后，在解压目录运行：
python -m http.server 7459 --bind 127.0.0.1
浏览器打开 http://127.0.0.1:7459/ （默认2D）
需要 WebGL，请通过 HTTP 打开。手机横屏，在同一局域网将 bind 改为
0.0.0.0，并通过电脑局域网IPv4地址访问端口7459。

电脑：WASD移动、Shift慢走、J/左键攻击、空格闪避、L推击、R武器技、
F交互、B行囊、M地图、C技能；Q/E按住预瞄、松开施符。
弓按住蓄力、松开射出；右键/Esc取消预备。Esc暂停。
手机：左摇杆移动、右侧动作键；移动与动作支持双指同时操作。
拖至取消区松开可取消，不消耗箭或符咒。

当前试玩加载存档或新建旅程时补足经验至Lv40，保留装备、属性分配与剧情并正常保存。
普通主动、治疗、闪避与终极均无施放CD；终极暂时无需蓄能且不消耗蓄能，
没有45秒共享锁。施放前后摇、装备/被动触发、敌人招式与药剂间隔保留。
脱战后即可换装备，无需返回检查点；技能/属性配置仍在安全检查点进行。

保留原暖金任务栏、小地图、血条、技能栏、行囊、检定与存档规则。
32区地图使用2D绘制图块与纹理层；旅店为整图，其他区域复用建筑/道具家族。
10个人物身份依据前面批准的设计图，使用透明方向图和低帧姿态动画。
主角11类状态保留，七件真实武器各有四向站立、行走、八相位跑步与攻击表现。
人物按约38:62腰线比例及原场景标尺校准；服饰与冷灰旧木地分开配色。
行囊支持当前武器与四个真实方向；新增装备图谱展示35款五阶设计，后续设计款
明确标记并保持只读，库存、掉落、数值和存档仍按原规则计算。
防具与首饰提供分阶设计图谱，未制作逐槽纸娃娃身体换装。

开局在旅店与弥菈交谈。自动存档属于当前浏览器与地址；换端口或设备
会使用另一份存档。原玩法、分支、装备商店、检定与第一章结算保留。

真实发布版已通过合法核心命令整章通关、桌面/手机尺寸输入、双指动作、
预备取消及重载恢复检查。全32区加载审查与动作姿态夹具单独记录，
不把选区/摆姿态夹具当作合法通关。
此包是本地可玩的2D版本；低帧动作和场景家族复用仍有精修空间。
手机浏览器模拟不能代替实体手机性能验收；尚未进行TapTap真机验收或公开发布。
build-report.json 是完整Web包体积；含保留的3D对比资源，不是TapTap首包。
素材来源与许可证见 THIRD_PARTY_NOTICES.txt。
'''
    return f'''剑与火 · 第一章可玩测试构建 v{version}
Cocos Creator 3.8.8 / {platform} / {build_date}

推荐手机横屏游玩。将压缩包完整解压，在解压目录运行：
python -m http.server 7459 --bind 127.0.0.1
电脑浏览器打开 http://127.0.0.1:7459/
需要 WebGL。请通过 HTTP 服务打开，不要直接双击 index.html。

手机与电脑连接同一 Wi-Fi 时，可改用：
python -m http.server 7459 --bind 0.0.0.0
用电脑的局域网 IPv4 地址替换下面的示例地址，在手机浏览器访问：
http://192.168.1.100:7459/
电脑地址可在 ipconfig 的当前网络适配器中查看；手机保持横屏。

手机：左摇杆小幅推动慢走、推满奔跑；右侧按钮攻击、闪避、推击、武器技和交互。
弓按住攻击蓄力、松开射出；符咒按住预瞄、拖动瞄准、松开释放。
拖到“取消”区松开可取消预备，不消耗箭或符咒。地图/行囊/暂停位于右上。
支持一根移动手指与一根动作手指同时操作。

电脑：WASD 移动，Shift 慢走；J/鼠标左键攻击，F 交互，空格闪避，L 推击，
R 武器技，Q/E 松开施符，B 行囊，M 地图，C 技能与检定。
弓按住蓄力、松开射出；右键或 Esc 取消预备，Esc 暂停。
自动保存于当前浏览器和当前访问地址的本地存储；换设备或访问地址会使用另一份存档。

当前试玩加载存档或新建旅程时补足经验至Lv40，保留装备、属性分配与剧情并正常保存。
普通主动、治疗、闪避与终极均无施放CD；终极暂时无需蓄能且不消耗蓄能，
没有45秒共享锁。施放前后摇、装备/被动触发、敌人招式与药剂间隔保留。
脱战后即可换装备，无需返回检查点；技能/属性配置仍在安全检查点进行。

参考界面已接入：蜂蜜金主色、香槟高光、棕铜暗边与深棕黑内凹底，
金属包边和古典角饰、圆形小地图、人物头像状态与手机动作栏保持统一。
行囊包含真实3D人物预览、9装备槽、物品格/筛选/详情，脱战后即可换装；
人物/技能页可旋转预览并查看真实检定修正。地图含当前区域顶视地形、探索黑雾、
世界三层地图、缩放拖动、定位与自定义标记；人物地图说明避免提前揭露隐藏剧情。
场景配色区分自然绿植、灰石与暖土，人物使用暖白主光和中性填光，地下保留局部暖火。
加载页使用温润暖日光的原创河谷画面和真实加载阶段进度。横竖屏切换会暂停并提示横屏。
地图使用 FairyGUI；10 名人物复用 Quaternius 原生模型与模块化服装，保留65蒙皮骨骼、11个动作；
弓箭复用KayKit原动作、动态握点与原生Draw形变，贴图按手机尺寸共享。
六套配套 PBR 使用 512px 底色、OpenGL 法线及 AO/粗糙度/金属度通道图；
剑、命中、蓄弓、符咒和敌预警使用 Cocos 原生粒子与 Line。
人物身份、完整首章剧情、装备、存档与即时战斗保留。

开局与弥菈交谈，选择标有[洞悉/游说 DC]的选项，或调查旅店铜簧匣。
检定可直接点面板按钮；电脑 Enter/空格掷骰或确认，R 消耗1灵感重掷，G 切换协助。
掷骰前可取消；掷骰后需接受结果或消耗灵感。失败仍有其他剧情/探索路线。
旧 Cocos V1 进度兼容。独立 D20 展示夹具不作为真实操作、库存获取或完整通关证明。

这是本地 Web 测试构建。已检查浏览器发布版移动、触控、存档恢复与合法命令通关；
手机 UA/横屏模拟及动作录像不能代替真机性能验收。最终美术、完整多级 LOD、
TapTap 真机触控/前后台/持久化和目标设备帧率尚未验收；尚未公开发布。
包内 build-report.json 记录完整 Web 构建体积，不是 TapTap 首包大小。
TapTap 版本仍需真实小游戏 AppID。
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['web-mobile', 'web-desktop'], default='web-mobile',
                        help='Completed build to package (default: web-mobile).')
    parser.add_argument('--build-name', default='', help='Named build directory, e.g. concept-2d.')
    parser.add_argument('--view', choices=['3d', '2d'], default='3d', help='Presentation described by this package.')
    parser.add_argument('--revision', default='', help='Optional artifact revision, preserving earlier packages.')
    parser.add_argument('--report', default='test-results/build-size.json', help='Measured build report.')
    parser.add_argument('--date', default=date.today().isoformat(), help='Package date label (default: today).')
    parser.add_argument('--readme-file', default='', help='Optional current build instructions, replacing the historical default README.')
    args = parser.parse_args()
    build_name = args.build_name or args.platform
    if args.revision and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', args.revision):
        raise SystemExit('revision must contain only letters, digits, hyphens or underscores.')
    if Path(build_name).name != build_name or build_name in ('.', '..'):
        raise SystemExit('build-name must be one directory name.')
    root = PROJECT / 'build' / build_name
    if not (root / 'index.html').is_file():
        raise SystemExit('No completed HTML build at ' + str(root))
    report_file = PROJECT / args.report
    if not report_file.is_file():
        raise SystemExit('Measure the completed build first: python tools/report-build.py build/' + args.platform)
    build_report = json.loads(report_file.read_text(encoding='utf-8-sig'))
    if build_report.get('platform') != build_name:
        raise SystemExit('Measured report does not match ' + build_name + '. Rerun report-build.py.')
    files = sorted(file for file in root.rglob('*') if file.is_file())
    raw_bytes = sum(file.stat().st_size for file in files)
    if build_report.get('files') != len(files) or build_report.get('rawBytes') != raw_bytes:
        raise SystemExit('Build changed after measurement. Finish the build and rerun report-build.py.')
    version = json.loads((PROJECT / 'package.json').read_text(encoding='utf-8-sig'))['version']
    out = PROJECT / 'artifacts'
    out.mkdir(exist_ok=True)
    revision = '-' + args.revision if args.revision else ''
    target = out / f'first-chapter-playable-{build_name}{revision}-{args.date}.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        for file in files:
            archive.write(file, file.relative_to(root).as_posix())
        instructions = Path(args.readme_file).read_text(encoding='utf-8-sig') if args.readme_file else readme(version, args.platform, args.date, args.view)
        archive.writestr('README-TEST.txt', instructions)
        archive.writestr('build-report.json', json.dumps(build_report, ensure_ascii=False, indent=2))
    with ZipFile(target) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit('Archive CRC failed: ' + bad)
    report = {
        'file': str(target), 'version': version, 'platform': args.platform, 'view': args.view, 'revision': args.revision, 'date': args.date,
        'sourceBuild': str(root), 'buildFiles': len(files), 'buildBytes': raw_bytes,
        'bytes': target.stat().st_size,
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'crcVerified': True,
    }
    report_name = ('test-package-2d' if args.view == '2d' else 'test-package') + revision + '.json'
    (out / report_name).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
