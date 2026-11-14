"""Verify cloud concept provenance and arrange the current four-family preview."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'source-art/skills/pure-skills-v2'
CURRENT = [
    ('WAR_01', 'combat-war-impact-v1.png', '破军战技 · 首版飞刃强化', 'combat-war.png'),
    ('BOW_02', 'combat-bow-impact-v1.png', '逐风弓术 · 首击分裂强化', 'combat-bow.png'),
    ('FIR_02', 'combat-fir-impact-v1.png', '烈焰秘术 · 体积爆燃强化', 'combat-fir-redesign-v4.png'),
    ('THU_02', 'combat-thu-impact-v1.png', '雷霆秘术 · 横向电弧强化', 'combat-thu.png'),
]
SOURCE_FILES = ['generation-sources.json', 'awakened-generation-sources.json',
                'redesign-generation-sources.json', 'latest-generation-sources.json',
                'round-generation-sources.json', 'four-impact-generation-sources.json']
HISTORICAL_REVIEWS = ['independent-art-review.json', 'independent-art-review-straight-arrow-red-core-v1.json',
                      'independent-art-review-round-orb-v5.json', 'independent-art-review-five-styles-v6.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    sources = [entry for name in SOURCE_FILES for entry in json.loads((OUT / name).read_text(encoding='utf-8'))]
    assert len({s['file'] for s in sources}) == len(sources)
    selected = {file: skill for skill, file, _, _ in CURRENT}
    bases = {base for _, _, _, base in CURRENT}
    entries = []
    for source in sources:
        path, raw = OUT / source['file'], Path(source['source'])
        prompt = OUT / 'prompts' / (path.stem + '.txt')
        assert path.is_file() and raw.is_file() and sha(path) == sha(raw)
        assert prompt.is_file()
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            size = list(im.size)
        refs = source.get('reference', [])
        if isinstance(refs, str):
            refs = [refs]
        reference_records = []
        for ref in refs:
            ref_path = OUT / ref
            assert ref_path.is_file()
            reference_records.append(dict(file=ref, sha256=sha(ref_path), role='see exact saved prompt'))
        current = path.name in selected
        status = ('strengthened-concept-candidate' if current else 'retained-base-reference' if path.name in bases
                  else 'superseded-or-inactive-exploration')
        entries.append(dict(file=path.name, skillId=selected.get(path.name, source['skillId']), size=size,
                            sha256=sha(path), currentConceptCandidate=current,
                            generation=dict(status='succeeded', provider='OpenAI built-in image_gen',
                                            modelVersion='not returned by tool', rawSource=str(raw),
                                            prompt=prompt.relative_to(OUT).as_posix(), promptSha256=sha(prompt),
                                            referenceImages=reference_records),
                            visualReview=dict(status=status, userAcceptance='not claimed for strengthened outputs',
                                              independentReview='independent-art-review-current.json' if current else None,
                                              runtimeReady=False),
                            processing='native output copied byte-for-byte; preview montage only is resized'))
    write('provenance.json', dict(date='2026-11-08', generatedImageCount=len(entries), currentCandidateCount=len(CURRENT),
                                  localModelInvoked=False, uploadCacheBehavior='not assumed', entries=entries,
                                  historicalReview=HISTORICAL_REVIEWS,
                                  userFeedbackReferences=[dict(file='references/' + name, sha256=sha(OUT / 'references' / name),
                                                               uploadedToGenerator=False)
                                                          for name in ['user-first-arrow-selection.png', 'user-round-orb-feedback.png']],
                                  productionAcceptance=False))
    lookup = {entry['file']: entry for entry in entries}
    write('current-selection.json', dict(date='2026-11-08', status='strengthened-concept-candidates-not-runtime-assets',
                                        inactivePlayableStyles=dict(FRO='removed', ARC='temporarily-withdrawn'),
                                        latestConstraints=[
                                            'WAR/BOW retain first selected silhouettes; THU retains the selected horizontal bounded graph',
                                            'strengthen four families through contact, material depth and short directional trails',
                                            'BOW_02 splits only after first impact; children follow frozen bounded paths without recursive splitting',
                                            'no active ARC or FRO class, unlock, reward or equipment linkage'],
                                        entries=[dict(skillId=skill, file=file, sha256=lookup[file]['sha256'],
                                                      baseReference=base, baseSha256=lookup[base]['sha256'],
                                                      userAcceptance='not claimed for this strengthened variant')
                                                 for skill, file, _, base in CURRENT]))
    canvas = Image.new('RGB', (1440, 1100), '#20242b')
    draw = ImageDraw.Draw(canvas)
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    font = ImageFont.truetype(str(font_path), 23) if font_path.is_file() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 19) if font_path.is_file() else ImageFont.load_default()
    for index, (_, file, title, _) in enumerate(CURRENT):
        x, y = (index % 2) * 720, (index // 2) * 520
        draw.text((x + 12, y + 9), title, font=font, fill='#ede4ce')
        with Image.open(OUT / file) as im:
            thumb = ImageOps.contain(im.convert('RGB'), (704, 470))
            canvas.paste(thumb, (x + (720 - thumb.width) // 2, y + 44 + (470 - thumb.height) // 2))
    draw.text((16, 1055), '当前四系 · 30技能 / 150阶     奥术暂撤，冰系退出     升级属性与门槛保留     静态概念，尚未接入游戏', font=small, fill='#b9c4d0')
    canvas.save(OUT / 'current-overview.jpg', quality=92)
    ImageOps.grayscale(canvas).save(OUT / 'current-silhouettes.jpg', quality=91)
    notes = {
        'WAR_01': '沿首版单层细长月牙与狭长走廊，强化锋缘、定向金属斩裂和接触火星；没有改成多层巨刃。',
        'BOW_02': '沿首版主箭首击后分出细淡子箭，强化首击与五处分支的物理穿刺；不加光羽绸带或递归分裂。',
        'FIR_02': '强化红橙体积翻卷、紧凑白金火核和敌人接触处的短促爆燃；脚部与安全区仍需动态验收。',
        'THU_02': '沿此前认可的横向分叉图，强化冷白电芯、细紫层次和接点雷裂；人数与半径不随光效暗增。',
    }
    lines = ['# 四系技能强化概念稿', '',
             '2026-11-08。奥术秘法暂时撤下，冰系继续退出；当前只保留战技、弓术、火焰、雷霆四系与通用技能，共30技/150阶。人物1—40级、属性成长与保留技能门槛沿用原表。', '',
             '四张新强化候选沿用原版造型与交战距离，把提升放在材质深度、方向短尾、真实接触爆发及消散节奏。150阶表现方案同步加强，伤害、目标上限与几何不因装饰增加。新稿尚待用户审阅，没有接入游戏或完成动画/碰撞/手机性能验收。', '',
             '![四系强化总览](current-overview.jpg)', '',
             '| 强化候选 | 方向 | 基础参考 |', '|---|---|---|']
    for skill, file, title, base in CURRENT:
        lines.append(f'| [{title}]({file}) | {notes[skill]} | [{base}]({base}) |')
    lines += ['', '## 当前规则', '',
              '- [30技能与150阶](../../../docs/design/combat-skills-v2.md)、[人物属性和等级门槛](../../../docs/design/character-progression-v1.md)',
              '- [分裂箭与限额电弧](../../../docs/design/skill-spatial-v2.md)、[四系五级表现](../../../docs/design/skill-vfx-v2.md)',
              '- [差异化简报](../../../docs/design/skill-differentiation-brief-v2.md)、[参考与原创转化](../../../docs/design/skill-reference-bg3-v2.md)',
              '- [74装备适配](../../../docs/design/equipment-skills-v4.md)、[97地点与12首领](../../../docs/design/world-combat-v4.md)',
              '- [远程接入要求](../../../docs/design/ranged-combat-integration-v2.md)',
              '- [技能JSON](skill-catalog.json)、[世界JSON](campaign-v8.json)、[设计核对](design-validation.json)、[交付核对](delivery-validation.json)', '',
              '## 来源与审阅', '',
              '全部使用内置云端OpenAI image_gen，没有启动本地模型。完整提示词与逐图参考、真实尺寸、SHA256见[provenance.json](provenance.json)和[prompts](prompts/)。原生输出逐字节复制，Pillow仅排版缩略图与灰度对照；不假定上传缓存行为，底层模型版本未由工具返回。', '',
              '[当前选图](current-selection.json)与[独立审阅](independent-art-review-current.json)分别记录。生成成功、方向审阅、用户接受与运行生产通过相互独立。图中人物只是尺度示意，概念图不能证明实际米制、动作先后、弹体数量或命中。', '',
              '奥术与冰系旧稿、失败探索及原版基础素材全部保留；它们不属于当前可选职业，也不自动成为后续必须补完的工作。历史[五系审阅](independent-art-review-five-styles-v6.json)及[v1基础稿](../pure-skills-v1/README.md)保留原记录，不代表本轮强化验收。', '',
              '复核命令：`python tools/design/build-skills-v2.py`、`python tools/design/catalog-skill-art-v2.py`。前者导出当前设计，后者核对来源与排版；不改运行代码、存档或下载依赖。', '']
    (OUT / 'README.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(entries)} native outputs verified; {len(CURRENT)} current strengthened concept candidates; no runtime assets emitted')


if __name__ == '__main__':
    main()
