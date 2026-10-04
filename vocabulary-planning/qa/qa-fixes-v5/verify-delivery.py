"""Verify exported document content and file identity, separately from browser printing."""
from pathlib import Path
import hashlib
import json
import fitz

QA = Path(__file__).resolve().parent
ROOT = QA.parents[1]
OUT = ROOT / 'deliverables/qa-fixes-v5'
bank = json.loads((ROOT / 'curriculum/pilot-10.json').read_text())
results = []
for path in sorted(OUT.glob('*.pdf')):
    document = fitz.open(path)
    text = ''.join(page.get_text() for page in document)
    overflow = []
    for number, page in enumerate(document, 1):
        for block in page.get_text('blocks'):
            if block[0] < -1 or block[1] < -1 or block[2] > page.rect.width + 1 or block[3] > page.rect.height + 1:
                overflow.append({'page': number, 'bbox': list(block[:4])})
    refs = {font[0] for page in document for font in page.get_fonts() if 'VocabularyKorean' in font[3]}
    row = {'file': path.name, 'pages': len(document), 'searchable_characters': len(text),
           'font_embedded': bool(refs) and all(document.extract_font(ref)[3] for ref in refs),
           'replacement_characters': text.count('\ufffd'), 'null_characters': text.count('\x00'),
           'out_of_page_text_blocks': overflow, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    if '단어 문항' in path.name:
        row['all_160_item_ids_present'] = all(item['id'] in text for item in bank['items'])
    assert row['font_embedded'] and not row['replacement_characters'] and not row['null_characters'] and not overflow and row.get('all_160_item_ids_present', True), row
    results.append(row)
sources = ['development-readiness', 'two-week-operation', '10-word-curriculum', 'development-spec']
render = json.loads((OUT / 'render-validation.json').read_text())
for stem, entry in zip(sources, render['documents']):
    assert hashlib.sha256((ROOT / 'documents' / (stem + '.md')).read_bytes()).hexdigest() == entry['source_sha256']
report_metadata = json.loads((QA / 'report-pdf-validation.json').read_text())
assert hashlib.sha256((QA / '개선-검증-보고서.md').read_bytes()).hexdigest() == report_metadata['documents'][0]['source_sha256']
result = {'status': 'pass', 'method': 'PyMuPDF document text/font/page-boundary inspection; not browser printing',
          'documents': results, 'all_exported_pages': sum(row['pages'] for row in results),
          'four_primary_document_pages': sum(entry['pages'] for entry in render['documents']),
          'source_hashes_match': True}
(QA / 'delivery-pdf-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'pass', 'pdfs': len(results), 'pages': result['all_exported_pages'], 'curriculum_ids': 160}))
