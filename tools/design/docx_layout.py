from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

FONT = 'Noto Sans CJK SC'

def xml(parent, tag, **attrs):
    e = OxmlElement(tag)
    for k,v in attrs.items(): e.set(qn(k), str(v))
    parent.append(e)
    return e

def font(obj, size=None, bold=None, color='000000'):
    obj.font.name = FONT
    obj.font.color.rgb = RGBColor.from_string(color)
    if size: obj.font.size = Pt(size)
    if bold is not None: obj.font.bold = bold
    rpr = obj._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = xml(rpr, 'w:rFonts')
    for key in ('ascii','hAnsi','eastAsia','cs'): rf.set(qn('w:'+key), FONT)
    for key in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):
        rf.attrib.pop(qn('w:'+key), None)
    lang = rpr.find(qn('w:lang'))
    if lang is None: lang = xml(rpr,'w:lang')
    lang.set(qn('w:val'),'zh-CN'); lang.set(qn('w:eastAsia'),'zh-CN')

def build_document():
    doc=Document()
    s=doc.sections[0]
    s.page_width=Inches(8.5); s.page_height=Inches(11)
    s.top_margin=Inches(.65); s.bottom_margin=Inches(.65)
    s.left_margin=Inches(.7); s.right_margin=Inches(.7)
    s.header_distance=Inches(.25); s.footer_distance=Inches(.3)
    for name,size,bold,before,after in [('Normal',11,False,0,4),('Title',24,True,0,12),('Subtitle',11,False,0,8),('Heading 1',19,True,0,10),('Heading 2',12.5,True,8,4),('Heading 3',11,True,6,3)]:
        st=doc.styles[name]; font(st,size,bold)
        st.paragraph_format.space_before=Pt(before); st.paragraph_format.space_after=Pt(after)
        st.paragraph_format.line_spacing=Pt(30 if name=='Title' else 24 if name=='Heading 1' else 17 if name=='Heading 2' else 15)
        st.paragraph_format.widow_control=True
        st.paragraph_format.keep_with_next=name in ['Title','Subtitle','Heading 1','Heading 2','Heading 3']
        ppr=st._element.find(qn('w:pPr'))
        if ppr is not None:
            for b in list(ppr.findall(qn('w:pBdr'))): ppr.remove(b)
    # Quiet page numbers aid use of the ten-page production handbook.
    fp=s.footer.paragraphs[0]
    fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=fp.add_run(); font(r,9,color='666666')
    xml(r._r,'w:fldChar',**{'w:fldCharType':'begin'})
    xml(r._r,'w:instrText').text=' PAGE '
    xml(r._r,'w:fldChar',**{'w:fldCharType':'end'})
    doc.core_properties.author=''
    doc.core_properties.last_modified_by=''
    doc.core_properties.subject=''
    doc.core_properties.comments=''
    return doc

def clean_heading(s):
    return re.sub(r'[^\w\s\u3400-\u9fff]', ' ',str(s)).strip()

def heading(doc,text,level=2,new_page=False):
    p=doc.add_paragraph(clean_heading(text),'Title' if level==0 else 'Heading '+str(level))
    if new_page: p.paragraph_format.page_break_before=True
    return p

def para(doc,text='',bold_lead=None,small=False,after=None):
    p=doc.add_paragraph()
    if bold_lead:
        r=p.add_run(bold_lead); font(r,11,True)
    r=p.add_run(str(text)); font(r,10 if small else 11)
    if after is not None: p.paragraph_format.space_after=Pt(after)
    return p

def bullet(doc,text):
    p=para(doc,'• '+text)
    p.paragraph_format.left_indent=Inches(.12)
    p.paragraph_format.first_line_indent=Inches(-.12)
    p.paragraph_format.space_after=Pt(3)
    return p

def table(doc,headers,rows,widths,center=()):
    t=doc.add_table(rows=1,cols=len(headers))
    t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for i,w in enumerate(widths):
        t.columns[i].width=Inches(w)
    pr=t._tbl.tblPr
    b=xml(pr,'w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        xml(b,'w:'+edge,**{'w:val':'single','w:sz':'4','w:color':'D9D9D9'})
    mar=xml(pr,'w:tblCellMar')
    for edge,val in [('top',75),('left',95),('bottom',75),('right',95)]:
        xml(mar,'w:'+edge,**{'w:w':val,'w:type':'dxa'})
    for ri,rowvals in enumerate([headers]+rows):
        cells=t.rows[0].cells if ri==0 else t.add_row().cells
        trpr=t.rows[ri]._tr.get_or_add_trPr()
        xml(trpr,'w:cantSplit')
        if ri==0: xml(trpr,'w:tblHeader')
        for i,txt in enumerate(rowvals):
            c=cells[i]; c.width=Inches(widths[i]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=c._tc.get_or_add_tcPr()
            if ri==0: xml(cp,'w:shd',**{'w:fill':'EAE7E2','w:val':'clear'})
            p=c.paragraphs[0]
            p.paragraph_format.space_after=Pt(0); p.paragraph_format.space_before=Pt(0)
            p.paragraph_format.line_spacing=Pt(14)
            p.paragraph_format.keep_with_next=ri==0
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER if i in center else WD_ALIGN_PARAGRAPH.LEFT
            r=p.add_run(str(txt)); font(r,11,ri==0)
    gap=doc.add_paragraph()
    gap.paragraph_format.space_after=Pt(1); gap.paragraph_format.space_before=Pt(0)
    gap.paragraph_format.line_spacing=Pt(3)
    font(gap.add_run(''),2)
    return t
