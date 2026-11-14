"""Record generation separately from concept review; make a local review index.

Pillow is already installed and is used only for deterministic local processing.
This script does not call a model, download files or register runtime resources.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'source-art/encounters/cloud-world-v2'
OLD_THREAD='01a1b6d6-7987-7941-b393-86e8b4a244d9'
NEW_THREAD='01a1b705-7a3e-7be2-9d34-e4c2f98feeb9'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    catalog=json.loads((ART/'campaign-design.json').read_text(encoding='utf-8'))
    sources=json.loads((ART/'generation-sources.json').read_text(encoding='utf-8'))
    # Compare exact RGB bytes, not a grayscale difference that could round tiny changes.
    with Image.open(ART/'drops-u2.png') as im:
        base=im.convert('RGB')
    with Image.open(ART/'drops-u2-edit-raw.png') as im:
        edit=im.convert('RGB')
    with Image.open(ART/'drops-u2-necklace-mask.png') as im:
        mask=im.copy()
    with Image.open(ART/'drops-u2-v2.png') as im:
        final=im.convert('RGB')
    assert base.size==edit.size==mask.size==final.size==(1536,1024)
    assert Image.composite(edit,base,mask).tobytes()==final.tobytes()
    for rect in [(0,0,1536,450),(750,450,1536,1024)]:
        assert base.crop(rect).tobytes()==final.crop(rect).tobytes()
    composite=dict(canvas=[1536,1024],editableRect=[0,450,750,1024],outsideRectPixelsIdentical=True,
                   verification='exact RGB bytes outside rectangle; full masked composite byte-for-byte reproduction',
                   base='drops-u2.png',generatedEdit='drops-u2-edit-raw.png',mask='drops-u2-necklace-mask.png',selected='drops-u2-v2.png')
    (ART/'necklace-composite-verification.json').write_text(json.dumps(composite,indent=2)+'\n',encoding='utf-8')
    matched={}
    for path in (Path.home()/'.codex/generated_images'/OLD_THREAD).glob('*.png'):
        matched[sha(path)]=str(path)
    new_sources={s['file']:s['source'] for s in sources['newImages']}
    selected=[]
    for region in catalog['regions']:
        selected.append((region['plate'],region['id']+' '+region['name'],'prior-concept'))
    selected.append(('elite-loot.png','八件精英固定奖','prior-concept'))
    for region in catalog['regions']:
        selected.append(('drops-u2-v2.png' if region['id']=='U2' else 'drops-'+region['id'].lower()+'.png',
                         region['id']+' 区域掉落四件','new-gear'))
    notes={
        'r1-stonebridge.png':'两首领、四普通敌、四装备的布局与成年轮廓可读；盾兵具体副武器仍须动画母版确认。',
        'r2-highlands.png':'桥卫/督猎与四足采掘机可区分，钢木链环各有材质；山路位移须玩法制作。',
        'r3-bellriver.png':'油壶头目、打捞者、钟卫及钩手轮廓可区分；油区与可破坏索桩是后续行为。',
        'r4-greyrock.png':'统帅/典狱长与盾、弩、镜、旗可区分；人物和武器未做正式碰撞/帧锚点验收。',
        'u1-oathcity.png':'冷白炉槽、三像同基座、六足虫、负重架可区分；不是灵魂/熔岩生物。',
        'u2-catacombs.png':'闸轮盾、三脚镜匣、实体镜眼和钟傀可区分；光路与闸门需要独立制作。',
        'elite-loot.png':'4×2八件奖，长剑/锤/轮盾/镜匣轮廓不同；边缘与透明切片未验。',
        'drops-r1.png':'护盔、护胸、双护手、绿晶指环四件完整，材料可区分。',
        'drops-r2.png':'双护胫、羊毛兜帽、短杖、风翼吊坠完整；护胫上边留白偏紧，正式图标需补安全边。',
        'drops-r3.png':'皮靴、双护腕、完整长弯刀、双色宝石戒四件完整；并非同图换色。',
        'drops-r4.png':'盔、胸甲、长窄直剑、双环蓝晶戒完整；剑尖靠近图角，正式切片需独立排版。',
        'drops-u1.png':'护额、围甲工装、带手指护手、封闭铜笼短杖完整，白光不吞材质。',
        'drops-u2-v2.png':'布靴、分片护腕、三镜扣短弓及完整闭合链吊坠可读；吊坠已定向修正，矩形外像素保持原图。',
    }
    entries=[]
    for filename,label,kind in selected:
        file=ART/filename
        revised=filename=='drops-u2-v2.png'
        stem='drops-u2' if revised else file.stem
        prompt=ART/'prompts'/('drops-u2-necklace-fix.txt' if revised else stem+'.txt')
        assert prompt.is_file(),prompt
        with Image.open(file) as im:
            im.verify()
        with Image.open(file) as im:
            size=list(im.size)
            mode=im.mode
        raw_file='drops-u2-edit-raw.png' if revised else filename
        source=(sources['revision']['source'] if revised else new_sources.get(filename)) if kind=='new-gear' else matched.get(sha(file))
        if source:
            assert Path(source).is_file()
            assert sha(Path(source))==sha(ART/raw_file), filename
        art_ids=[e['id'] for group in ['enemies','bosses','newEquipment'] for e in catalog[group] if e['art']['file']==filename]
        entries.append(dict(file=filename,label=label,sha256=sha(file),size=size,mode=mode,
                            generation=dict(status='succeeded',provider='OpenAI built-in image_gen',
                                            originatingThread=OLD_THREAD if kind=='prior-concept' else NEW_THREAD,
                                            rawSource=source,prompt=prompt.relative_to(ART).as_posix(),promptSha256=sha(prompt),
                                            referenceImages=['drops-u2.png'] if revised else ([] if kind=='new-gear' else 'see originating thread; not re-uploaded here')),
                            artReview=dict(status='concept-direction-reviewed',reviewer='Codex visual inspection',date='2026-11-08',
                                           notes=notes[filename],userAcceptance='not claimed',runtimeReady=False),
                            processing='local masked composite; see necklace-composite-verification.json' if revised else 'original generated bytes copied without resampling',
                            contentIds=art_ids))
    provenance=dict(date='2026-11-08',selectedConceptSheets=len(entries),generationTool='built-in image_gen',localModelInvoked=False,
                    licenses='Project-authored prompts and generated concepts; no third-party asset pack or exclusive copyright claim introduced.',
                    rawCandidates=[dict(file='drops-u2.png',status='superseded: clipped chain; keep source'),
                                   dict(file='drops-u2-edit-raw.png',status='generated edit; selected region composited onto original')],entries=entries)
    (ART/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Overview is not another model-generated artwork. It is a local thumbnail montage.
    width,height=1440,1200
    sheet=Image.new('RGB',(width,height),'#e7e1d7')
    draw=ImageDraw.Draw(sheet)
    font_path=Path('C:/Windows/Fonts/msyh.ttc')
    font=ImageFont.truetype(str(font_path),18) if font_path.is_file() else ImageFont.load_default()
    for index,entry in enumerate(entries):
        x=(index%4)*360
        y=(index//4)*300
        draw.text((x+12,y+8),entry['label'],font=font,fill='#312b25')
        with Image.open(ART/entry['file']) as im:
            preview=ImageOps.contain(im.convert('RGB'),(344,260))
            sheet.paste(preview,(x+(360-preview.width)//2,y+35+(260-preview.height)//2))
    sheet.save(ART/'concept-overview.jpg',quality=90)
    lines=['# 六区怪物、首领与掉落概念图', '',
           '2026-11-08。选用13张概念板：恢复原聊天的7张，加本轮6张区域掉落板；本轮另有1次吊坠链条的云端定向编辑。生成全部使用OpenAI内置image_gen，本轮没有启动Qwen/ComfyUI。', '',
           '**生成完成与美术审阅分开记录。** 本轮只通过概念方向审阅；正式动画、透明切图、碰撞、武器握点、脚部锚点及手机实机验收尚未完成，也未声称用户已验收。', '',
           '![十三张选用概念板总览](concept-overview.jpg)', '',
           '## 内容入口', '',
           '- [完整设计](../../../docs/design/encounters-and-loot-v2.md)',
           '- [主线与命名](../../../docs/design/campaign-v6.md)',
           '- [97处逐关表](../../../docs/design/world-levels-v2.md)',
           '- [奖励和装备属性](../../../docs/design/loot-catalog-v2.md)',
           '- [结构化设计数据](campaign-design.json)、[静态覆盖核对](design-validation.json)',
           '- [生成来源、SHA256与独立审图记录](provenance.json)', '',
           '## 逐板检查', '',
           '| 文件 | 画面内容 | 审阅记录 |', '|---|---|---|']
    for e in entries:
        lines.append(f"| [{e['file']}]({e['file']}) | {e['label']} | {e['artReview']['notes']} |")
    lines += ['', '区域板固定位置：上方左右是两首领，中排从左到右是该区四种普通敌，下排是四个既有装备/符的造型参考。精英奖板4×2，DE01—04在上排、DE05—08在下排。新增掉落板2×2，区域四件依次为左上、右上、左下、右下；具体键在JSON的art字段。', '',
              '原六区板下排映射：R1=W02/W08/A09/T03；R2=W03/A05/W09/J02；R3=W10/W12/J05/A03；R4=W06/J07/W14/T08；U1=W16/A12/W13/A16；U2=J04/A15/J06/T06。位置是概念定位，不能直接作为SpriteFrame精确切片。', '',
              '## 生成与处理记录', '',
              '完整实际提示词分别保存在[prompts](prompts/)；每板的提示词路径和哈希均在provenance.json。原图只复制原始字节，未调色或缩放。总览由本地Pillow确定性缩略排版。生成服务未返回可核验的底层模型版本，不猜测型号，也不声称引用只上传一次。', '',
              '沉钟区原drops-u2.png的吊坠链未闭合，未选作最终板。内置image_gen根据原板定向编辑，保存drops-u2-edit-raw.png；本地仅合成左下[0,450,750,1024]区域，其他三件保留原像素。最终为drops-u2-v2.png，遮罩与[矩形外像素核对](necklace-composite-verification.json)保留。修正后已检查闭合链与完整吊坠。', '',
              '旧提示词中的历史地区名与主线新名不同，不修改历史生成证据；图注与内容数据使用新名。当地装备可能是在另一地区制造/取得，概念板位置不自动改唯一来源。', '',
              '## 复现文档与清单', '',
              '运行 `python tools/design/build-encounters-v2.py` 重新导出内容JSON与三份设计表；运行 `python tools/design/catalog-encounter-art.py` 检查图像、原始来源与哈希并重建本清单/总览。两脚本不调用模型、不下载依赖、不改游戏运行数据。主线叙事campaign-v6.md为独立人工稿。', '',
              'runtime-content.json是中断前导出的首章32区/19项运行目录快照，只用于区分现状；campaign-design.json是未接入完整设计。历史本地模型试验位于相邻qwen-world-v1目录，按用户要求保留。', '']
    (ART/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'{len(entries)} selected plates verified; generation and concept review recorded separately')

if __name__=='__main__':
    main()
