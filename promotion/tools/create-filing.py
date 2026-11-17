"""Create a factual game introduction attachment; no identity or legal attestations."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit, ImageReader
from pypdf import PdfReader
import hashlib, json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'promotion/qualification'
OUT.mkdir(parents=True,exist_ok=True)
FILE=OUT/'SwordAndFire-game-content-description.pdf'
pdfmetrics.registerFont(TTFont('STSong-Light','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
c=canvas.Canvas(str(FILE),pagesize=(595.28,841.89))
c.setTitle('剑与火：破晓之战 - 游戏内容介绍说明')
c.setAuthor('Slash')
W,H=595.28,841.89
INK=HexColor('#222b30'); MUTED=HexColor('#637078'); GOLD=HexColor('#8e6a26')

def base(page,heading):
    c.setFillColor(INK);c.setFont('STSong-Light',22);c.drawString(44,H-65,heading)
    c.setStrokeColor(GOLD);c.setLineWidth(1);c.line(44,H-80,W-44,H-80)
    c.setFont('STSong-Light',9);c.setFillColor(MUTED)
    c.drawString(44,27,'剑与火：破晓之战 | 0.3.60 release | 2026-11-18')
    c.drawRightString(W-44,27,f'{page} / 3')

def text(s,y,size=11,leading=19,color=INK):
    c.setFont('STSong-Light',size);c.setFillColor(color)
    lines=[];line=''
    for ch in s:
        if line and pdfmetrics.stringWidth(line+ch,'STSong-Light',size)>W-88:
            lines.append(line);line=ch
        else:line+=ch
    if line:lines.append(line)
    for line in lines:
        c.drawString(44,y,line);y-=leading
    return y-9

def section(title,body,y):
    y=text(title,y,13,21,GOLD)
    return text(body,y)

def picture(path,y,caption,width=W-88):
    im=ImageReader(str(path));iw,ih=im.getSize();height=width*ih/iw
    c.drawImage(im,(W-width)/2,y-height,width,height)
    return text(caption,y-height-18,9,15,MUTED)-12

base(1,'游戏内容介绍说明')
y=H-110
y=section('一、产品基本信息','游戏名称：剑与火：破晓之战。版本：0.3.60 release。运行形式：TapTap 小游戏，手机横屏。类型：西方奇幻题材动作角色扮演与探索冒险。TapTap 游戏 ID：1046344。',y)
y=section('二、主要内容与当前开放范围','玩家从石桥镇展开旅途，探索城镇、荒野、矿道与地下遗迹，通过任务、调查、对话及战斗推进冒险。当前版本开放第一章“兽潮之夜”和第二章“群山战火”；后续章节仍在制作中，不列为当前已开放内容。',y)
y=section('三、核心玩法','战斗包含近战剑术、弓术、火焰和雷电四种流派。玩家组合主动技能与终极技，使用移动、侧移、闪避、瞄准和职业资源应对敌人。任务与野外狩猎均可提供成长机会；探索中的支线、线索和地图记录帮助玩家整理目标。',y)
y=section('四、成长和装备','正式构建的新旅程从1级开始，采用正常经验、技能冷却与成长限制。角色通过战斗和任务成长，选择属性与技能配置。装备系统包含不同品质、传奇与神器、强化、宝石镶嵌和重复装备分解。展示素材中的20级角色与满阶技能为独立展示配置，不代表正常开局、自然20级技能点预算或装备获取速度。',y)
y=section('五、账号与存档','当前交付包保留 TapTap 平台登录流程，关闭开发加速工具和游客绕过。旅程采用本地持久化；包体上传和本地预览通过不等于平台与目标手机验收已经完成。',y)
c.showPage()
base(2,'加载与四种战斗流派')
y=picture(ROOT/'promotion/screenshots/game-loading.jpg',H-108,'图1：实际 Cocos 加载界面，显示原生进度条与加载提示。',420)
y=picture(ROOT/'promotion/previews/four-classes.jpg',y,'图2：按弓箭手、战士、雷电法师、火系法师排列的实际战斗截图。',420)
text('截图来源：当前 Cocos 生产资源的本地 HTML 预览，非 TapTap 手机实机录屏。四职业战斗展示使用 H14 鹰背岩林；未合成命中、伤害或怪物画面。',y,10,17,MUTED)
c.showPage()
base(3,'装备与内容制作说明')
y=picture(ROOT/'promotion/screenshots/BOW-artifact.jpg',H-108,'图3：实际装备页面中的神器、装备属性和角色信息。')
y=section('六、内容制作方式','项目的部分美术、图标、宣传插画、贴图等资产使用生成式 AI 制作或辅助编辑，再经开发者选择、调整并接入游戏。云端图像生成工具及历史本地工作流的来源记录随项目素材留档。宣传封面为插画，游戏截图与录屏来自实际运行画面。',y)
y=section('七、交付与申报边界','本说明对应已经生成并上传的 0.3.60 release 包体。包体 ID：501182；ZIP SHA-256：8bf2f8c8e5d78cfb5ee7bdbab133cace36cb7834fe217ed1ae84d43644173c9f。此文件仅说明产品功能与内容，不代替主体证照、软件权属文件、授权书、备案核准结果或负责人电子化身份核验。',y)
text('平台草稿、资质材料审核、版本提审和公开发布是不同状态。本文不宣称尚在审核中的资质已经通过，也不宣称当前游戏已经公开上线。',y,10,17,MUTED)
c.save()
r=PdfReader(FILE)
assert len(r.pages)==3
assert all(p.extract_text().strip() for p in r.pages)
(OUT/'game-content-description-provenance.json').write_text(json.dumps({'file':FILE.name,'version':'0.3.60','date':'2026-11-18','pages':3,'sha256':hashlib.sha256(FILE.read_bytes()).hexdigest(),'identityDetailsIncluded':False,'legalAttestation':False,'sources':['src/out/0.3.60/upload-settings.json','promotion/records/taptap-upload-progress.json','promotion/records/game-loading.json','promotion/records/archer-volley.json','promotion/README.md']},ensure_ascii=False,indent=2),encoding='utf-8')
print(FILE)
