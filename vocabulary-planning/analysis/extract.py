import fitz,json,csv,re,collections,pathlib,argparse
ROOT=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Extract source-ordered vocabulary from the supplied textbook PDF.')
parser.add_argument('pdf',type=pathlib.Path,help='Path to the original textbook PDF')
args=parser.parse_args()
pdf=fitz.open(args.pdf)
raw_pages=[]
rows=[]
for idx,p in enumerate(pdf):
 spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans'] if 205<s['bbox'][1]<730 and s['bbox'][0]<525]
 headwords=[s for s in spans if 435<s['bbox'][0]<499]
 if idx%2==0:
  assert len(headwords)==15,(idx+1,len(headwords),headwords)
  anchors=[(s['bbox'][1]+s['bbox'][3])/2 for s in headwords]
 else:
  numbers=[s for s in spans if 499<s['bbox'][0]<525 and re.fullmatch(r'\d+',s['text'].strip())]
  anchors=[(s['bbox'][1]+s['bbox'][3])/2 for s in sorted(numbers,key=lambda s:s['bbox'][1])]
  if len(anchors)!=15:
   anchors=raw_pages[-1]['anchors']
  assert len(anchors)==15,(idx+1,anchors)
 page_rows=[dict(pdf_page=idx+1,row_on_page=j+1,definition_original='',example_original='',headword_original='',printed_number=None,source_span_bboxes=[]) for j in range(15)]
 pieces=[collections.defaultdict(list) for _ in range(15)]
 for s in spans:
  center=(s['bbox'][1]+s['bbox'][3])/2
  j=min(range(15),key=lambda i:abs(anchors[i]-center))
  x=s['bbox'][0]
  if x<243.8:col='definition_original'
  elif x<435:col='example_original'
  elif x<499:col='headword_original'
  else:col='printed_number'
  pieces[j][col].append(s)
  page_rows[j]['source_span_bboxes'].append({'text':s['text'],'bbox':[round(v,2) for v in s['bbox']],'column':col})
 for j,row in enumerate(page_rows):
  for col,ss in pieces[j].items():
   ss.sort(key=lambda s:(s['bbox'][1]+s['bbox'][3])/2)
   lines=[]
   for span in ss:
    sy=(span['bbox'][1]+span['bbox'][3])/2
    if not lines or abs(sy-lines[-1][0])>4:
     lines.append([sy,[span]])
    else:lines[-1][1].append(span)
   text=' '.join(''.join(s['text'] for s in sorted(line[1],key=lambda s:s['bbox'][0])) for line in lines).strip()
   if col=='printed_number':row[col]=int(text) if text.isdigit() else None
   else:row[col]=text
  if idx%2==0:
   row['content_id']=f'W{len(rows)+1:04d}'
   row['source_order']=len(rows)+1
   rows.append(row)
  else:
   original=rows[-15+j]
   original['recall_page']=idx+1
   original['recall_definition_original']=row['definition_original']
   original['recall_example_original']=row['example_original']
   original['recall_printed_number']=row['printed_number']
   original['recall_source_span_bboxes']=row['source_span_bboxes']
 raw_pages.append({'pdf_page':idx+1,'anchors':anchors,'rows':page_rows})
(ROOT/'extracted-raw-pages.json').write_text(json.dumps(raw_pages,ensure_ascii=False,indent=2))
(ROOT/'vocabulary-raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
cols=[k for k in rows[0] if 'bbox' not in k]
with (ROOT/'vocabulary-raw.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({k:r[k] for k in cols}for r in rows)
print('ROWS',len(rows))
for idx in range(0,60,2):
 rr=rows[idx//2*15:idx//2*15+15]
 print(idx+1,'words',len(rr),'nums',rr[0]['printed_number'],rr[-1]['printed_number'])
print('duplicates',[(w,n) for w,n in collections.Counter(r['headword_original'] for r in rows).items() if n>1])
norm=lambda s:re.sub(r'[\s,.。]+','',s)
print('DEFINITION DIFFS')
for r in rows:
 if norm(r['definition_original'])!=norm(r['recall_definition_original']):
  print(r['content_id'],r['printed_number'],r['pdf_page'],r['headword_original'],r['definition_original'],'<>',r['recall_definition_original'])
print('HEADWORDS')
for i in range(0,len(rows),15):
 print(rows[i]['pdf_page'],', '.join(f"{r['printed_number']}:{r['headword_original']}" for r in rows[i:i+15]))
