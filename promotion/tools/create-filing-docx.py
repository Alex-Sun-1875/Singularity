"""Editable DOCX for the TapTap ICP content-description attachment."""
from pathlib import Path
import ast,hashlib,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'promotion/qualification'
OUT.mkdir(parents=True,exist_ok=True)
DEST=OUT/'SwordAndFire-game-content-description.docx'
source=ast.parse((ROOT/'promotion/tools/create-filing.py').read_text(encoding='utf-8'))
sections=[(n.value.args[0].value,n.value.args[1].value) for n in source.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='section']
doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=Inches(.65)
sec.left_margin=sec.right_margin=Inches(.7)
sec.header_distance=sec.footer_distance=Inches(.28)
for name,size in [('Normal',11),('Title',22),('Heading 1',14),('Heading 2',12),('Caption',9)]:
    st=doc.styles[name];st.font.name='SimSun';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
    st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
    st.paragraph_format.space_after=Pt(7)
    st.paragraph_format.line_spacing=Pt(17 if name=='Normal' else size+5)
    if name.startswith('Heading'):st.paragraph_format.space_before=Pt(10)
doc.styles['Normal'].paragraph_format.widow_control=True
doc.core_properties.title='剑与火破晓之战游戏内容介绍说明'
doc.core_properties.author='Slash'

def body(text):
    p=doc.add_paragraph(text);p.paragraph_format.keep_together=True
    return p
def heading(title):
    # Use semantic headings without punctuation, preserving the product name in prose.
    title=title.split('、',1)[-1]
    return doc.add_paragraph(title,'Heading 1')
def picture(path,width,caption):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing=1.0
    p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(4)
    p.add_run().add_picture(str(path),width=Inches(width))
    cap=doc.add_paragraph(caption,'Caption');cap.paragraph_format.space_after=Pt(10)

footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('剑与火：破晓之战  |  0.3.60 release  |  ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
for run in footer.runs:run.font.size=Pt(8)

doc.add_paragraph('剑与火破晓之战游戏内容介绍说明','Title')
body('本说明用于 TapTap 小游戏 ICP 核准材料，介绍0.3.60正式构建的游戏内容、主要玩法与当前开放范围，并附实际运行画面。内容对应当前交付版本，不代替主体证照、权属文件或负责人身份核验。')
for title,text in sections[:5]:heading(title);body(text)

doc.add_page_break();heading('加载与四种战斗流派')
picture(ROOT/'promotion/screenshots/game-loading.jpg',6,'图1  实际 Cocos 加载界面，显示原生进度条与加载提示。')
picture(ROOT/'promotion/previews/four-classes.jpg',5.5,'图2  弓箭手、战士、雷电法师、火系法师的实际战斗截图。')
body('截图来源为当前 Cocos 生产资源的本地 HTML 预览，非 TapTap 手机实机录屏。四职业战斗均使用 H14 鹰背岩林；未合成命中、伤害或怪物画面。')

doc.add_page_break();heading('装备与内容制作说明')
picture(ROOT/'promotion/screenshots/BOW-artifact.jpg',6.6,'图3  实际装备页面中的神器、装备属性和角色信息。')
for title,text in sections[5:]:heading(title);body(text)
body('平台草稿、资质材料审核、版本提审和公开发布是不同状态。本文不宣称尚在审核中的资质已经通过，也不宣称当前游戏已经公开上线。')
for p in [doc.styles['Title']._element,*[p._p for p in doc.paragraphs if p.style.name=='Title']]:
    for border in p.findall('.//'+qn('w:pBdr')):border.getparent().remove(border)
doc.save(DEST)
check=Document(DEST)
assert len(check.inline_shapes)==3
assert all(x in '\n'.join(p.text for p in check.paragraphs) for x in ['0.3.60','1046344','主体证照','第一章'])
(OUT/'game-content-description-docx-provenance.json').write_text(json.dumps({'file':DEST.name,'bytes':DEST.stat().st_size,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'basedOn':'promotion/tools/create-filing.py','identityDetailsIncluded':False,'legalAttestation':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(DEST)
