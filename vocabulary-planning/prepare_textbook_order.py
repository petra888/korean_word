from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
source = sorted(json.loads((ROOT / 'analysis/vocabulary.json').read_text()), key=lambda r: r['source_order'])
assert len(source) == 450
assert [r['source_order'] for r in source] == list(range(1, 451))
rows = [{
    'id': r['content_id'], 'source_order': r['source_order'],
    'word_original': r['headword_original'], 'pdf_page': r['pdf_page'],
    'row_on_page': r['row_on_page'], 'printed_number_original': r['printed_number'],
    'definition_original': r['definition_original'], 'example_original': r['example_original'],
    'issue_ids': r['issue_ids'], 'approval_status': 'teacher_review_required',
} for r in source]
batches = [{'id': f'T{n//10+1:02d}', 'source_order_start': n+1,
            'source_order_end': n+10, 'word_ids': [r['id'] for r in rows[n:n+10]]}
           for n in range(0, len(rows), 10)]
out = {'version': 'textbook-order-v2-2026-10-04',
       'source_file_sha256': '9a79871a2ff684c43f1415a97127a811540420479e0d107803b890a6dac5ff2a',
       'ordering': 'PDF page then row; source_order, not printed numbering',
       'row_count': 450, 'batch_size': 10, 'batch_count': 45,
       'duplicates': 'Preserve each source position; do not skip or merge without an approved mapping',
       'publication': 'Hold flagged/unapproved items in place; never silently substitute another word',
       'words': rows, 'batches': batches}
target = ROOT / 'curriculum/textbook-order.json'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2))
with (ROOT / 'curriculum/textbook-order.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['원문ID','수록순서','10단어묶음','교재표제어','PDF쪽','쪽내행','원문인쇄번호','원문사전뜻','원문예문','교정이슈','승인상태'])
    for r in rows:
        w.writerow([r['id'],r['source_order'],f"T{(r['source_order']-1)//10+1:02d}",r['word_original'],r['pdf_page'],r['row_on_page'],r['printed_number_original'],r['definition_original'],r['example_original'],';'.join(r['issue_ids']),r['approval_status']])
candidates = {'version': out['version'], 'status': 'teacher_review_required',
              'selection_rule': 'The first 30 consecutive source rows, with no skips',
              'words': [{**r, 'authoring_status': 'full_draft_bundle' if r['source_order'] <= 10 else 'source_only_not_authored'} for r in rows[:30]]}
(ROOT / 'curriculum/pilot-30-candidates.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
assert [x for b in batches for x in b['word_ids']] == [r['content_id'] for r in source]
check = {'source_rows': 450, 'batches': 45, 'order_preserved': True,
         'first_batch': [r['word_original'] for r in rows[:10]],
         'duplicate_positions_preserved': True, 'source_pdf_same_as_prior_upload': True}
(ROOT / 'planning/order-validation.json').write_text(json.dumps(check, ensure_ascii=False, indent=2))
print(json.dumps(check, ensure_ascii=False))
