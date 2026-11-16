"""Extend the existing bundled serif from the installed OFL source, offline."""
from pathlib import Path
import hashlib
import json
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = Path('C:/Windows/Fonts/NotoSerifSC-VF.ttf')
TARGET = ROOT / 'src/cocos/assets/resources/ui/quiet-bronze/rpg-serif-v2.ttf'
existing = TTFont(TARGET)
characters = set(existing.getBestCmap())
license_text = next(n.toUnicode() for n in existing['name'].names if n.nameID == 13)
for script in (ROOT / 'src/cocos/assets/scripts').rglob('*.ts'):
    characters.update(ord(c) for c in script.read_text(encoding='utf-8') if c.isprintable())
characters.update(range(32, 127))
font = TTFont(SOURCE)
assert any('Open Font License' in n.toUnicode() for n in font['name'].names if n.nameID == 13)
available = set(font.getBestCmap())
options = subset.Options()
options.name_IDs = ['*']
options.name_languages = ['*']
options.recommended_glyphs = True
subsetter = subset.Subsetter(options=options)
subsetter.populate(unicodes=characters & available)
subsetter.subset(font)
font = instantiateVariableFont(font, {'wght': 500}, inplace=True)
names = {1: 'Sword Fire Serif SC', 2: 'Regular', 3: 'SwordFireSerifSC-Subset-20261115',
         4: 'Sword Fire Serif SC Regular', 6: 'SwordFireSerifSC-Regular',
         16: 'Sword Fire Serif SC', 17: 'Regular', 13: license_text}
for name in font['name'].names:
    if name.nameID in names:
        name.string = names[name.nameID].encode(name.getEncoding(), errors='replace')
font.recalcTimestamp = False
font.save(TARGET)
report = {'date': '2026-11-15', 'source': str(SOURCE),
          'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'license': 'SIL Open Font License 1.1', 'networkUsed': False,
          'method': 'Preserve existing codepoints, add project text, instantiate the same weight 500',
          'target': TARGET.relative_to(ROOT).as_posix(), 'bytes': TARGET.stat().st_size,
          'sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
          'requestedCodepoints': len(characters), 'unsupportedCodepoints': sorted(characters - available)}
(OUT / 'font-provenance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'bytes': report['bytes'], 'codepoints': len(characters & available),
                  'unsupportedSymbols': len(characters - available)}))
