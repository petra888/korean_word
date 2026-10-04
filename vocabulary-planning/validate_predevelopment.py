from pathlib import Path
import json, collections, re

ROOT = Path(__file__).parent
OUT = ROOT / 'planning'
OUT.mkdir(exist_ok=True)
dataset = json.loads((ROOT / 'analysis/vocabulary.json').read_text())
source = {w['content_id']: w for w in dataset}
bank = json.loads((ROOT / 'curriculum/pilot-10.json').read_text())
expected = [w['content_id'] for w in sorted(dataset, key=lambda w:w['source_order'])[:10]]
words = bank['words']
items = bank['items']
errors = []
def check(ok, message):
    if not ok: errors.append(message)

check(bank.get('status') == 'teacher_review_required', 'Bank must remain teacher-review draft')
check(len(words) == 10 and [w['id'] for w in words] == expected, 'First 10 words must follow exact textbook order')
check(len(items) == 160, 'Expected 160 objective items')
check(len({i['id'] for i in items}) == len(items), 'Duplicate item IDs')
check(len({i['prompt'].strip() for i in items}) == len(items), 'Duplicate full prompt text')
by_word = {w['id']: w for w in words}
for w in words:
    s = source[w['id']]
    check(w['word'] == s['headword_original'], f"Headword altered: {w['id']}")
    for k in ['pdf_page','row_on_page','source_order','definition_original','example_original','issue_ids']:
        check(w['source'].get(k) == s[k], f"Source field altered {w['id']}:{k}")
    check(not s['issue_ids'] or w.get('approval_status') == 'draft', f"Flagged source falsely approved: {w['id']}")
    diagnostic=w.get('definition_diagnostic',{})
    check(diagnostic.get('definition_original') == s['definition_original'], f"Diagnostic source definition altered: {w['id']}")
    check(bool(diagnostic.get('definition_for_check')), f"Missing diagnostic definition: {w['id']}")
    check(diagnostic.get('approval_status') == 'draft' and diagnostic.get('dictionary_verified') is False, f"Diagnostic definition approval inaccurate: {w['id']}")
    check(w['meaning_id'] == w['id']+'-S1', f"Meaning ID mismatch: {w['id']}")
    check(w.get('approval_status') == 'draft', f"False approval: {w['id']}")
    for k in ['simple_definition','meaning_scope','usage_note','accepted_forms']:
        check(bool(w.get(k)), f"Missing word field {w['id']}:{k}")
    writing=w.get('writing',{})
    for k in ['prompt','sentence_frame','teacher_sample','judgment_labels','teacher_guidance','alternative']:
        check(bool(writing.get(k)), f"Missing writing field {w['id']}:{k}")
    check('criteria' not in writing, f"Removed writing score criteria still present: {w['id']}")
    check(writing.get('judgment_labels') == [{'id':'correct','label':'정답'},{'id':'incorrect','label':'오답'},{'id':'uncertain','label':'검토(애매)'}], f"Writing judgment labels mismatch: {w['id']}")
    check(writing.get('alternative',{}).get('prompt') != writing.get('prompt'), f"Duplicate writing prompt: {w['id']}")
    counts=collections.Counter(i['phase'] for i in items if i['word_id']==w['id'])
    check(counts == {'practice':9,'pretest':1,'posttest':1,'delayed':1,'weekly':2,'monthly':1,'quarterly':1}, f"Phase supply mismatch: {w['id']} {dict(counts)}")

for i in items:
    w=by_word.get(i['word_id'])
    check(w is not None, f"Unknown target: {i['id']}")
    if w: check(i['meaning_id']==w['meaning_id'], f"Meaning linkage mismatch: {i['id']}")
    options=i.get('options',[])
    check(len(options)==4 and {o['id'] for o in options}=={'a','b','c','d'}, f"Four option IDs invalid: {i['id']}")
    check(len({o['text'].strip() for o in options})==4, f"Duplicate options: {i['id']}")
    check(i.get('type')=='context_cloze', f"Non-cloze item: {i['id']}")
    check(i.get('prompt','').count('(____)')==1, f"Expected one sentence blank: {i['id']}")
    check(i.get('correct_option_id') in {o['id'] for o in options}, f"Missing correct answer: {i['id']}")
    if w:
        label=re.sub(r'\s+','',w.get('display_word',w['word']))
        correct=next((re.sub(r'\s+','',o['text']) for o in options if o['id']==i.get('correct_option_id')), '')
        for field in ['prompt','hint']:
            text=re.sub(r'\s+','',i.get(field,''))
            check(label not in text and (not correct or correct not in text), f"Answer exposed before submission: {i['id']}:{field}")
    for k in ['prompt','hint','explanation','context_cues']:
        check(bool(i.get(k)), f"Missing item field {i['id']}:{k}")
    check(i.get('review_status')=='draft', f"False item approval: {i['id']}")
    if i['phase']=='weekly': check(i.get('period_sequence') in [1,2], f"Weekly sequence absent: {i['id']}")

# A fixed fictional five/three/two-group allocation checks content supply, not a real student's choices.
groups={'unknown':expected[:5], 'uncertain':expected[5:8], 'known':expected[8:]}
needs={'unknown':36,'uncertain':18,'known':6}
supply={g:sum(i['phase']=='practice' and i['word_id'] in ids for i in items) for g,ids in groups.items()}
for g,n in needs.items(): check(supply[g]>=n, f"Fictional six-session objective supply insufficient: {g}")
check(sum(needs.values())==60, 'Six-session objective activity math mismatch')
distribution=collections.Counter(i['correct_option_id'] for i in items)
check(set(distribution)=={'a','b','c','d'} and max(distribution.values())-min(distribution.values())<=2, f"Answer position distribution unbalanced: {dict(distribution)}")

report={'status':'pass' if not errors else 'fail', 'word_count':len(words),'first_textbook_batch_order':[w['word'] for w in words],'flagged_source_rows_preserved':sum(bool(w['source']['issue_ids']) for w in words),'objective_item_count':len(items),'writing_prompt_count':sum(2 for w in words if w.get('writing',{}).get('alternative')),'phase_counts':dict(collections.Counter(i['phase'] for i in items)), 'answer_position_counts':dict(distribution),'fictional_practice_supply':supply,'fictional_practice_need':needs,'regular_submission_activities':70,'regular_objective':60,'all_word_drafts':10,'errors':errors,'limits':['Structural and source preservation checks only','Meanings, answer uniqueness and age suitability need Korean teacher approval','Does not prove real service access control, storage or learning efficacy']}
(OUT/'content-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(bool(errors))
