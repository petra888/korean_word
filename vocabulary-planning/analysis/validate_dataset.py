import json,csv,collections,pathlib,re
R=pathlib.Path(__file__).parent
raw=json.loads((R/'vocabulary-raw.json').read_text());enriched=json.loads((R/'vocabulary.json').read_text());pages=json.loads((R/'extracted-raw-pages.json').read_text());v=json.loads((R/'validation.json').read_text());issues=json.loads((R/'correction-candidates.json').read_text())
assert len(raw)==len(enriched)==450
assert len(pages)==60
assert all(len(p['rows'])==15 for p in pages)
assert len({r['content_id']for r in raw})==450
assert all(r['recall_page']==r['pdf_page']+1 for r in raw)
assert all(r['source_order']==i+1 for i,r in enumerate(raw))
assert all(len([r for r in raw if r['pdf_page']==p])==15 for p in range(1,61,2))
assert all(r[k]==enriched[i][k]for i,r in enumerate(raw)for k in r),'Original fields were altered'
assert len({r['headword_original']for r in raw})==444
assert len({r['suggested_lemma']for r in enriched})==444
assert len({r['word_family_key']for r in enriched})==438
assert [r['recall_printed_number']for r in raw[135:150]]==list(range(136,151))
assert all(r['printed_number']is None for r in raw[135:150])
assert raw[224]['printed_number']==225 and raw[225]['printed_number']==266
assert v['numbers_absent_across_learning_and_recall']==list(range(226,266))
assert len(v['recall_without_blank'])==10
assert len(v['pair_semantic_mismatch_rows'])==13
assert len(issues)==71 and len({i['content_id']for i in issues})==67
for fn,rr in [('vocabulary-raw.csv',raw),('vocabulary.csv',enriched)]:
 with(R/fn).open(encoding='utf-8-sig',newline='')as f:data=list(csv.DictReader(f))
 assert len(data)==450
 for actual,expect in zip(data,rr):
  for k in ['content_id','headword_original','definition_original','example_original','recall_definition_original','recall_example_original']:
   assert actual[k]==expect[k],(fn,k,expect['content_id'])
print('PASS: 60 pages / 30 pairs / 450 rows; source preservation, CSV consistency, 444 unique headwords, 438 provisional families, numbering, 13 semantic conflicts, 10 exposed answers, 71 issues across 67 rows.')
