from pathlib import Path
import json, hashlib, re
import fitz
S=Path('/tmp/vocabulary-full-qa-0d75986-n5h3m0i4/vocabulary-planning')
O=Path('/workspace/korean_word/vocabulary-planning/qa/latest-commit-0d75986/mobile-print')
manifest=json.loads((S/'deliverables/report-charts-v4/render-validation.json').read_text())
mapping={'교사 평가 부모 자료 차트 개선안.pdf':'development-readiness','2주 학생 교사 수업 운영표.pdf':'two-week-operation','교재 첫 10개 단어 문항 작문.pdf':'10-word-curriculum','개발 상세 명세와 검수 기준.pdf':'development-spec'}
results=[]
for record in manifest['documents']:
 p=S/'deliverables/report-charts-v4'/record['file'];doc=fitz.open(p);text='\n'.join(page.get_text() for page in doc)
 font_results=[]
 for font in {font[0]:font for page in doc for font in page.get_fonts(full=True)}.values():
  xref=font[0];name=font[3];kind=font[2];_,ext,typ,content=doc.extract_font(xref)
  font_results.append({'xref':xref,'name':name,'type':kind,'extension':ext,'embedded_program_bytes':len(content),'embedded':len(content)>0})
 outside=[]
 for pn,page in enumerate(doc,1):
  for b in page.get_text('blocks'):
   r=fitz.Rect(b[:4])
   if not page.rect.contains(r): outside.append({'page':pn,'bounds':list(r),'text':b[4][:120]})
 source=S/'documents'/f"{mapping[record['file']]}.md";sha=hashlib.sha256(source.read_bytes()).hexdigest()
 results.append({'file':record['file'],'pages':len(doc),'pages_match_manifest':len(doc)==record['pages'],'source_sha256':sha,'source_hash_matches_manifest':sha==record['source_sha256'],'searchable_characters':len(text),'contains_korean':bool(re.search('[가-힣]',text)),'unicode_replacement_char_count':text.count('\ufffd'),'embedded_font_programs':font_results,'outside_page_text_blocks':outside})
 if record['file']=='교사 평가 부모 자료 차트 개선안.pdf':
  doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(O/'handoff-report-page1.png')
  O.joinpath('handoff-report-searchable-text.txt').write_text(text)
O.joinpath('delivery-pdf-validation.json').write_text(json.dumps({'method':'Direct inspection and rasterization of committed ReportLab PDFs using MuPDF; these are planning documents, not browser parent reports','actual_browser_print':'NOT RUN','results':results},ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
