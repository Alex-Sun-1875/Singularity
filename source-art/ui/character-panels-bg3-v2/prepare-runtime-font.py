"""Subset an already installed OFL font; no network or dependency download."""
from pathlib import Path
import hashlib,json
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib.instancer import instantiateVariableFont

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
SOURCE=Path('C:/Windows/Fonts/NotoSerifSC-VF.ttf')
TARGET=PROJECT/'src/cocos/assets/resources/ui/quiet-bronze/rpg-serif-v2.ttf'
LICENSE='''© 2017-2023 Adobe (http://www.adobe.com/).
Noto Serif SC source font. Modified subset family: Sword Fire Serif SC.

SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007

PREAMBLE
The goals of the Open Font License (OFL) are to stimulate worldwide development of collaborative font projects, to support the font creation efforts of academic and linguistic communities, and to provide a free and open framework in which fonts may be shared and improved in partnership with others.

The OFL allows the licensed fonts to be used, studied, modified and redistributed freely as long as they are not sold by themselves. The fonts, including any derivative works, can be bundled, embedded, redistributed and/or sold with any software provided that any reserved names are not used by derivative works. The fonts and derivatives, however, cannot be released under any other type of license. The requirement for fonts to remain under this license does not apply to any document created using the fonts or their derivatives.

DEFINITIONS
"Font Software" refers to the set of files released by the Copyright Holder(s) under this license and clearly marked as such. This may include source files, build scripts and documentation.
"Reserved Font Name" refers to any names specified as such after the copyright statement(s).
"Original Version" refers to the collection of Font Software components as distributed by the Copyright Holder(s).
"Modified Version" refers to any derivative made by adding to, deleting, or substituting -- in part or in whole -- any of the components of the Original Version, by changing formats or by porting the Font Software to a new environment.
"Author" refers to any designer, engineer, programmer, technical writer or other person who contributed to the Font Software.

PERMISSION & CONDITIONS
Permission is hereby granted, free of charge, to any person obtaining a copy of the Font Software, to use, study, copy, merge, embed, modify, redistribute, and sell modified and unmodified copies of the Font Software, subject to the following conditions:
1) Neither the Font Software nor any of its individual components, in Original or Modified Versions, may be sold by itself.
2) Original or Modified Versions of the Font Software may be bundled, redistributed and/or sold with any software, provided that each copy contains the above copyright notice and this license. These can be included either as stand-alone text files, human-readable headers or in the appropriate machine-readable metadata fields within text or binary files as long as those fields can be easily viewed by the user.
3) No Modified Version of the Font Software may use the Reserved Font Name(s) unless explicit written permission is granted by the corresponding Copyright Holder. This restriction only applies to the primary font name as presented to the users.
4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font Software shall not be used to promote, endorse or advertise any Modified Version, except to acknowledge the contribution(s) of the Copyright Holder(s) and the Author(s) or with their explicit written permission.
5) The Font Software, modified or unmodified, in part or in whole, must be distributed entirely under this license, and must not be distributed under any other license. The requirement for fonts to remain under this license does not apply to any document created using the Font Software.

TERMINATION
This license becomes null and void if any of the above conditions are not met.

DISCLAIMER
THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, CONSEQUENTIAL DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM OTHER DEALINGS IN THE FONT SOFTWARE.
'''
font=TTFont(SOURCE)
assert any('Open Font License' in n.toUnicode() for n in font['name'].names if n.nameID==13)
text=''.join(p.read_text(encoding='utf8') for p in (PROJECT/'src/cocos/assets/scripts').rglob('*.ts'))
text+=''.join(chr(i) for i in range(32,127))+'＋−／～→①②③◆✦'
chars={ord(c) for c in text if c.isprintable()}
available=set(font.getBestCmap());missing=sorted(chars-available)
options=subset.Options();options.name_IDs=['*'];options.name_languages=['*'];options.recommended_glyphs=True
tool=subset.Subsetter(options=options);tool.populate(unicodes=chars);tool.subset(font)
font=instantiateVariableFont(font,{'wght':500},inplace=True)
for record in font['name'].names:
    value={1:'Sword Fire Serif SC',2:'Regular',3:'SwordFireSerifSC-Subset-20261110',4:'Sword Fire Serif SC Regular',6:'SwordFireSerifSC-Regular',16:'Sword Fire Serif SC',17:'Regular',13:LICENSE}.get(record.nameID)
    if value is not None:record.string=value.encode(record.getEncoding(),errors='replace')
font.recalcTimestamp=False
font.save(TARGET)
(TARGET.with_name('rpg-serif-v2-license.txt')).write_text(LICENSE,encoding='utf8')
(ROOT/'font-provenance.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_copyright':'© 2017-2023 Adobe (http://www.adobe.com/).','license':'SIL Open Font License 1.1','official_family_reference':'https://github.com/google/fonts/blob/main/ofl/notoserifsc/METADATA.pb','method':'Reuse installed font; FontTools subset to project source characters and instantiate weight 500; renamed modified family, retained copyright and embedded complete OFL in font metadata','file':TARGET.relative_to(PROJECT).as_posix(),'size':TARGET.stat().st_size,'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'requested_codepoints':len(chars),'missing_codepoints':missing},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Bundled serif subset:',TARGET.stat().st_size,'bytes;',len(chars),'requested codepoints;',len(missing),'missing symbols')
