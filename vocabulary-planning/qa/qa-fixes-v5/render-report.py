from pathlib import Path
from xml.etree import ElementTree as ET
import json, re, sys, html, hashlib, argparse, tempfile
parser=argparse.ArgumentParser(description="Render the QA improvement verification report PDF")
parser.add_argument("--markdown-path", default=None, help="Optional directory containing the Markdown module")
args=parser.parse_args()
if args.markdown_path:sys.path.insert(0,args.markdown_path)
sys.path.insert(0,str(Path(__file__).parent/'tooling'))
import markdown, fitz
from fontTools.ttLib import TTCollection
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted

ROOT=Path(__file__).parent
OUT=ROOT
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[('개선-검증-보고서','개선-검증-보고서.pdf')]
source_cache={stem:(ROOT/f'{stem}.md').read_text() for stem,_ in SOURCES}
all_text=''.join(source_cache.values())+'• 기획 검토 자료 개선 검증 · 교육 승인 전 2026.10.04 페이지'
fontdir=Path(tempfile.mkdtemp(prefix='vocabulary-qa-pdf-fonts-',dir='/tmp'))
def korean_font(style):
    dest=fontdir/f'VocabularyKorean-{style}.ttf'
    collection=TTCollection(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{style}.ttc')
    source=next(f for f in collection.fonts if 'Noto Sans CJK KR' in str(f['name'].getDebugName(1)))
    options=subset.Options();options.layout_features=[]
    sub=subset.Subsetter(options=options);sub.populate(text=all_text);sub.subset(source)
    glyphset=source.getGlyphSet();order=source.getGlyphOrder();glyphs={}
    for g in order:
        pen=TTGlyphPen(glyphset)
        glyphset[g].draw(Cu2QuPen(pen,max_err=1.0,reverse_direction=True))
        glyphs[g]=pen.glyph()
    fb=FontBuilder(source['head'].unitsPerEm,isTTF=True)
    fb.setupGlyphOrder(order);fb.setupCharacterMap(source.getBestCmap());fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g:source['hmtx'][g] for g in order})
    hh=source['hhea'];fb.setupHorizontalHeader(ascent=hh.ascent,descent=hh.descent,lineGap=hh.lineGap)
    fb.setupNameTable({'familyName':'VocabularyKorean','styleName':style,'uniqueFontIdentifier':'VocabularyKorean-'+style,'fullName':'VocabularyKorean '+style,'psName':'VocabularyKorean-'+style,'version':'Version 1.0'})
    os=source['OS/2'];fb.setupOS2(sTypoAscender=os.sTypoAscender,sTypoDescender=os.sTypoDescender,sTypoLineGap=os.sTypoLineGap,usWinAscent=os.usWinAscent,usWinDescent=os.usWinDescent)
    fb.setupPost();fb.setupMaxp();fb.save(dest)
    name='Korean'+style;pdfmetrics.registerFont(TTFont(name,str(dest)));return name

regular=korean_font('Regular');bold=korean_font('Bold')
pdfmetrics.registerFontFamily('Korean',normal=regular,bold=bold,italic=regular,boldItalic=bold)
base=ParagraphStyle('body',fontName=regular,fontSize=9.5,leading=15.7,textColor=colors.HexColor('#233c4b'),wordWrap='CJK',splitLongWords=True,spaceAfter=8)
styles={tag:ParagraphStyle(tag,parent=base,fontName=bold,fontSize=size,leading=size*1.5,spaceBefore=before,spaceAfter=after,keepWithNext=True) for tag,size,before,after in [('h1',20,5,20),('h2',14.5,18,10),('h3',11.8,13,8),('h4',10,9,6)]}
small=ParagraphStyle('cell',parent=base,fontSize=8,leading=12.5,spaceAfter=0)
header=ParagraphStyle('headercell',parent=small,fontName=bold)
def inline(el):
    result=html.escape(el.text or '')
    for ch in el:
        body=inline(ch)
        if ch.tag in ['strong','b']: body=f'<b>{body}</b>'
        elif ch.tag in ['em','i']: body=f'<i>{body}</i>'
        elif ch.tag=='code': body=f'<font color="#406775">{body}</font>'
        elif ch.tag=='a': body=f'<font color="#0a7180">{body}</font>'
        elif ch.tag=='br': body='<br/>'
        result+=body+html.escape(ch.tail or '')
    return result

W=A4[0]-88
def blocks(node):
    out=[]
    for el in node:
        tag=el.tag
        if tag in styles: out.append(Paragraph(inline(el),styles[tag]))
        elif tag=='p': out.append(Paragraph(inline(el),base))
        elif tag in ['ul','ol']:
            for n,li in enumerate(el,1):
                prefix=f'{n}. ' if tag=='ol' else '• '
                out.append(Paragraph(prefix+inline(li),base))
        elif tag=='table':
            rows=el.findall('.//tr');data=[]
            for row in rows:
                data.append([Paragraph(inline(c),header if c.tag=='th' else small) for c in row])
            if not data:continue
            columns=len(data[0]);weights=[]
            for c in range(columns):
                lens=sorted(len(''.join(rows[r][c].itertext())) for r in range(len(rows)) if c<len(rows[r]))
                typical=lens[min(len(lens)-1,int(len(lens)*.7))] if lens else 12
                weights.append(max(12,min(85,typical))**.7)
            widths=[W*w/sum(weights) for w in weights]
            table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1,splitInRow=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf3f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d5e3e8')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            out.extend([table,Spacer(1,10)])
        elif tag=='pre':
            for line in ''.join(el.itertext()).splitlines():
                out.append(Paragraph(html.escape(line) or ' ',small))
            out.append(Spacer(1,8))
        elif tag=='blockquote': out.extend(blocks(el))
        elif tag=='hr':out.append(Spacer(1,8))
        else: out.extend(blocks(el))
    return out

def footer(canvas,doc):
    canvas.saveState();canvas.setFont(regular,7);canvas.setFillColor(colors.HexColor('#66818e'))
    canvas.drawString(44,24,'2026.10.04 · 0d75986 이후 수정 검증 · 실제 브라우저 인쇄 미검증')
    canvas.drawRightString(A4[0]-44,24,str(doc.page));canvas.restoreState()

report=[]
for stem,name in SOURCES:
    source=source_cache[stem]
    tree=ET.fromstring('<root>'+markdown.markdown(source,extensions=['tables','fenced_code'])+'</root>')
    doc=SimpleDocTemplate(str(OUT/name),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=42,bottomMargin=43,title=source.splitlines()[0].lstrip('# '),author='기획 검토 자료')
    story=[Paragraph('QA 개선 검증 · 2026.10.04 · 수정 작업본',small),Spacer(1,12)]+blocks(tree)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    pdf=fitz.open(OUT/name)
    text=''.join(p.get_text() for p in pdf)
    pdf[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(OUT/f'{stem}-preview.png'))
    korean_fonts={f[0] for p in pdf for f in p.get_fonts() if 'VocabularyKorean' in f[3]}
    report.append({'file':name,'pages':len(pdf),'searchable_characters':len(text),'font_embedded':bool(korean_fonts) and all(len(pdf.extract_font(ref)[3])>0 for ref in korean_fonts),'source_sha256':hashlib.sha256(source.encode()).hexdigest()})
    if stem=='two-week-operation':
        ix=next((i for i,p in enumerate(pdf) if '학생과 교사의 2주 시간표' in p.get_text()),1)
        pdf[ix].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(OUT/'operation-table-preview.png'))

(OUT/'report-pdf-validation.json').write_text(json.dumps({'renderer':'ReportLab with embedded Korean subset font','documents':report,'browser_print':'NOT RUN: this PDF is a QA document export, not a parent report browser print'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
