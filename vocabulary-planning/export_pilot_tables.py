from pathlib import Path
import csv,json
ROOT=Path(__file__).parent
bank=json.loads((ROOT/'curriculum/pilot-10.json').read_text())
words={w['id']:w for w in bank['words']}
with (ROOT/'curriculum/pilot-10-items.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(['문항ID','원문ID','의미ID','단어','용도','주간차수','유형','지문','보기a','보기b','보기c','보기d','정답ID','정답내용','힌트','해설','단서','검수상태'])
    for i in bank['items']:
        options={o['id']:o['text'] for o in i['options']}
        writer.writerow([i['id'],i['word_id'],i['meaning_id'],words[i['word_id']]['word'],i['phase'],i.get('period_sequence',''),i['type'],i['prompt'],options['a'],options['b'],options['c'],options['d'],i['correct_option_id'],options[i['correct_option_id']],i['hint'],i['explanation'],' / '.join(i['context_cues']),i['review_status']])
with (ROOT/'curriculum/pilot-10-words.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(['원문ID','의미ID','단어','PDF쪽','원문행','원문뜻','원문예문','진단뜻초안','진단뜻사전검증','원문교정이슈','새쉬운풀이초안','뜻범위','사용주의','활용예시','기본작문질문','기본문장틀','기본교사예시','대체작문질문','대체문장틀','대체교사예시','승인상태'])
    for w in bank['words']:
        s=w['source'];p=w['writing'];a=p['alternative']
        d=w.get('definition_diagnostic',{})
        writer.writerow([w['id'],w['meaning_id'],w['word'],s['pdf_page'],s['row_on_page'],s['definition_original'],s['example_original'],d.get('definition_for_check',''),d.get('dictionary_verified',False),';'.join(s['issue_ids']),w['simple_definition'],w['meaning_scope'],w['usage_note'],' / '.join(w['accepted_forms']),p['prompt'],p['sentence_frame'],p['teacher_sample'],a['prompt'],a['sentence_frame'],a['teacher_sample'],w['approval_status']])
with (ROOT/'curriculum/pilot-10-writing.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(['원문ID','의미ID','원문단어','학습표시','작문구분','질문','문장틀','교사용예시','작문판정JSON','교사관찰안내JSON','승인상태'])
    for w in bank['words']:
        writing=w['writing']
        for label,prompt in [('기본',writing),('대체',writing['alternative'])]:
            writer.writerow([w['id'],w['meaning_id'],w['word'],w.get('display_word',w['word']),label,prompt['prompt'],prompt['sentence_frame'],prompt['teacher_sample'],json.dumps(writing['judgment_labels'],ensure_ascii=False),json.dumps(writing['teacher_guidance'],ensure_ascii=False),w['approval_status']])
items=list(csv.DictReader((ROOT/'curriculum/pilot-10-items.csv').open(encoding='utf-8-sig')))
assert len(items)==len(bank['items'])==160
assert {i['문항ID']:i['지문'] for i in items}=={i['id']:i['prompt'] for i in bank['items']}
for i in items:assert i['정답내용']==i['보기'+i['정답ID']]
writings=list(csv.DictReader((ROOT/'curriculum/pilot-10-writing.csv').open(encoding='utf-8-sig')))
assert len(writings)==20
for row in writings:
    w=words[row['원문ID']]
    p=w['writing'] if row['작문구분']=='기본' else w['writing']['alternative']
    assert row['질문']==p['prompt']
    assert json.loads(row['작문판정JSON'])==w['writing']['judgment_labels']
print(json.dumps({'items_csv_rows':len(items),'words_csv_rows':len(bank['words']),'writing_csv_rows':len(writings),'encoding':'UTF-8 BOM','csv_json_consistent':True},ensure_ascii=False))
