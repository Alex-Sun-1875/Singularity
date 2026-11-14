"""Catalog six native image_gen evolution sheets and build a local contact sheet.

Generation and visual review are independent fields. Pillow only reads metadata
and makes deterministic thumbnails; it does not synthesize or edit artwork.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'source-art/skills/pure-skills-v1'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    data=json.loads((OUT/'skill-catalog.json').read_text(encoding='utf-8'))
    sources=json.loads((OUT/'generation-sources.json').read_text(encoding='utf-8'))
    lookup={s['id']:s for s in data['skills']}
    order={'WAR':0,'BOW':1,'FIR':2,'FRO':3,'THU':4,'ARC':5}
    sources.sort(key=lambda s:order[s['skill'].split('_')[0]])
    assert len(sources)==6
    reviews={
      'WAR_01':'五列双弧→交叉→三斩→半环→完整剑阵变化明确；第五级高光需实机降透明度，不是正式剑帧或碰撞。',
      'BOW_05':'星矢羽翼、三环、天弓结构逐级明确；高阶边缘偏紧，正式特效需独立画布，不能直接按等宽切片。',
      'FIR_02':'小陨星→火环→次爆→晶冠→凤凰爆核逐级明确；巅峰光翼有边缘裁切和跨列视觉，仅作整体方向。',
      'FRO_05':'冰环、六角阵、中央冰冠、浮空冰花、完整冰冠/冰轮层次明确；冰晶不代表物理障碍。',
      'THU_05':'三束落雷到多层雷冠/雷网的形态差别明确；装饰电弧不代表新增伤害次数或控制。',
      'ARC_05':'细束、螺旋、三环门、银轨、巨大星核门逐级明确；第五级边缘偏紧，尚非可直接使用的光束纹理。',
    }
    records=[]
    for source in sources:
        path=OUT/source['file']
        raw=Path(source['source'])
        assert path.is_file() and raw.is_file() and sha(path)==sha(raw)
        prompt=OUT/'prompts'/(path.stem+'.txt')
        assert prompt.is_file()
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            size=list(im.size)
        skill=lookup[source['skill']]
        records.append(dict(file=source['file'],skillId=skill['id'],skillName=skill['name'],size=size,sha256=sha(path),
                            generation=dict(status='succeeded',provider='OpenAI built-in image_gen',rawSource=str(raw),
                                            prompt=prompt.relative_to(OUT).as_posix(),promptSha256=sha(prompt),referenceImages=[],
                                            modelVersion='not returned by tool'),
                            visualReview=dict(status='concept-direction-reviewed',reviewer='Codex visual inspection',date='2026-11-08',
                                              notes=reviews[skill['id']],userAcceptance='not claimed',runtimeReady=False),
                            stages=[dict(rank=r['rank'],requiredCharacterLevel=r['requiredCharacterLevel'],direction='left to right') for r in skill['ranks']],
                            processing='native output copied byte-for-byte; no recolor, crop or resample'))
    (OUT/'provenance.json').write_text(json.dumps(dict(date='2026-11-08',sheetCount=6,localModelInvoked=False,entries=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # The montage is a preview only, not a source effect or runtime atlas.
    canvas=Image.new('RGB',(1440,1410),'#20242b')
    draw=ImageDraw.Draw(canvas)
    font_path=Path('C:/Windows/Fonts/msyh.ttc')
    font=ImageFont.truetype(str(font_path),22) if font_path.is_file() else ImageFont.load_default()
    for i,entry in enumerate(records):
        x=(i%2)*720
        y=(i//2)*470
        levels='/'.join(str(s['requiredCharacterLevel']) for s in entry['stages'])
        draw.text((x+12,y+8),entry['skillName']+' · 1→5级',font=font,fill='#ede4ce')
        draw.text((x+12,y+38),'角色等级 '+levels,font=font,fill='#b6c1ce')
        with Image.open(OUT/entry['file']) as im:
            thumb=ImageOps.contain(im.convert('RGB'),(704,392))
            canvas.paste(thumb,(x+(720-thumb.width)//2,y+72+(392-thumb.height)//2))
    canvas.save(OUT/'evolution-overview.jpg',quality=91)
    lines=['# 六流派技能五级效果图', '',
           '2026-11-08。六张原生OpenAI image_gen云端概念板，每板从左到右展示同一代表技能的1—5级形态。角色只作稳定比例的灰衣示意，不替换当前已验收主角身份。没有启动本地模型。', '',
           '**已完成生成和概念方向审阅。** 五级形态差异清楚；高阶部分构型接近画布边缘，正式独立技能纹理、透明通道、序列帧、命中时序、镜头内遮挡与手机性能尚未验收。不能把这些静态板切成五帧当动画。', '',
           '![六流派五级效果总览](evolution-overview.jpg)', '',
           '## 当前设计', '',
           '- [44技能、220级记录](../../../docs/design/combat-skills-v1.md)',
           '- [人物升级、四维属性与等级解锁](../../../docs/design/character-progression-v1.md)',
           '- [每个技能的五级特效与命中规则](../../../docs/design/skill-vfx-v1.md)',
           '- [97地点纯技能反制](../../../docs/design/world-combat-v3.md)',
           '- [74件装备技能联动](../../../docs/design/equipment-skills-v3.md)',
           '- [技能JSON](skill-catalog.json)、[当前世界战斗JSON](campaign-v7.json)、[静态核对](design-validation.json)',
           '- [逐图来源、提示词、SHA256与独立审图](provenance.json)', '',
           '## 代表技能', '',
           '| 图 | 技能 | 1—5级的角色门槛 | 视觉审阅 |', '|---|---|---|---|']
    for entry in records:
        levels='/'.join('Lv'+str(r['requiredCharacterLevel']) for r in entry['stages'])
        lines.append(f"| [{entry['file']}]({entry['file']}) | {entry['skillName']} | {levels} | {entry['visualReview']['notes']} |")
    lines+=['', '图中粒子、光刃、电弧和晶体数量是表现，不等于伤害段数；命中段数/范围/复制上限由技能目录决定。六张是每流派一个代表技的方向板，不声称已逐个生成44技能×5级的生产资产。其他技能的逐级形态、音效和判定均已写入设计稿。', '',
            '## 可复核的保存记录', '',
            '每张原图与工具输出逐字节SHA256一致，真实尺寸见provenance.json；不把提示词的期望尺寸冒充实际尺寸。六张均为全新文生图，无参考图输入，底层模型版本未由工具返回。没有关于上传缓存次数的假设。', '',
            '实际完整提示词在[prompts](prompts/)。本地Pillow仅生成总览缩略排版，不修改六张原图。原输出继续保留在Codex生成目录，项目使用副本已全部保存到本目录。', '',
            '运行 `python tools/design/build-skills-v1.py` 重建技能/人物/装备/世界设计JSON与五份文档；运行 `python tools/design/catalog-skill-art.py` 核对原图/提示词哈希并重建本索引与总览。两脚本不下载文件、不调用本地模型、不改运行数据或存档。', '']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    print('6 evolution sheets verified against native output; generation and concept review separate')

if __name__=='__main__': main()
