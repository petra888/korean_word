import json,csv,collections,re,pathlib
R=pathlib.Path(__file__).resolve().parent
rows=json.loads((R/'vocabulary-raw.json').read_text())
normalization={'강단있는':'강단','나태한':'나태하다','무구한':'무구하다','방만한':'방만하다','생경한':'생경하다','어눌한':'어눌하다','희귀한':'희귀하다','지극한':'지극하다','고루한':'고루하다','현학적인':'현학적','왕성한':'왕성하다','침착한':'침착하다','혼잡한':'혼잡하다','병약한':'병약하다','소심한':'소심하다','비옥한':'비옥하다','산적한':'산적하다','자명한':'자명하다','완만한':'완만하다','고귀한':'고귀하다','비근한':'비근하다','희박한':'희박하다','궁극적인':'궁극적','순박한':'순박하다','선심쓰다':'선심 쓰다','영정사진':'영정 사진'}
native=set('까탈 깜냥 달포 말미 선잠 섣달 섬돌 어림 오금 갈무리 고명딸 너스레 넋두리 눈썰미 유유히 마파람 사재기 선머슴 어깃장 여의다 화수분 길라잡이 눈엣가시 비좁다 아름드리 가쁘다 미주알고주알 살포시 시나브로 엉겁결 게걸스럽다 겸연쩍다 굼뜨다 껄끄럽다 매몰차다 상큼하다 서슴없다 선선하다 섣부르다 생때같다 생뚱맞다 속절없다 수더분하다 골병들다 스산하다 애달프다 어쭙잖다 올곧다 옹골지다 구두쇠 궁상맞다 을씨년스럽다 터무니없다 투박하다 하릴없다 곰곰 여북 갸웃하다 조아리다 곱씹다 나부끼다 마무리 감돌다 내박치다 되뇌다 들쓰다 궁싯거리다 나부대다 니글거리다 벼르다 도지다 사무치다 뇌까리다 다잡다 마름하다 삭이다 시부렁거리다 얼버무리다 짐짓 무릇 얼추 노상 사뭇 자못 영특하다 알싸하다 옹고집 괄괄하다 얍삽하다 머쓱하다 솔깃하다 추레하다 어귀 든적스럽다 새삼스럽다'.split())
native.discard('유유히');native.discard('영특하다');native.discard('골병들다')
mixed=set('강단있는 기탄없이 현학적인 골병들다 선심쓰다'.split())
core=set('선잠 어림 집중 눈썰미 부족하다 치료하다 문안 비좁다 가쁘다 굼뜨다 신중하다 상큼하다 선선하다 발견하다 예상하다 작성하다 제조하다 구두쇠 오염 적립하다 정화 탈수 농도 수거 해저 방치 적중하다 급변하다 폐기하다 접수하다 고대하다 곰곰 교감 표면 수령하다 애용하다 모집 도입 몰입 순찰하다 침착한 혼잡한 반입하다 구술 연대 갸웃하다 소심한 인재 상승 포기 훼손하다 나부끼다 마무리 비교하다 조립하다 교체 주문하다 회상하다 되뇌다 비축 만류하다 결정하다 담소 등반 운행하다 유지하다 이동 작동하다 발생하다 변질되다 소지하다 첨부 수거하다 보육 수확하다 징수하다 살균 획득하다 중지하다 도피하다 얼추 폭염 발급하다 수료하다 제거하다 합격 향상되다 부착 선심쓰다 영특하다 암시 면역 근원 의지하다 결제 병행 백일장 차단하다 금지 밀봉 방어하다 억제하다 독특하다 머쓱하다 솔깃하다 관람 방지 정차하다 연세 언급하다 예민하다'.split())
literary=set('까탈 깜냥 달포 말미 섣달 섬돌 오금 갈무리 단장 도탄 고명딸 너스레 넋두리 도가니 유유히 생경한 어눌한 울화 마파람 선머슴 어깃장 여의다 지극한 화수분 길라잡이 눈엣가시 개가 고루한 침상 아름드리 미주알고주알 살포시 시나브로 도취 엉겁결 게걸스럽다 겸연쩍다 껄끄럽다 묘연 방불 서광 매몰차다 외람되다 서슴없다 섣부르다 생때같다 생뚱맞다 속절없다 수더분하다 백일몽 골병들다 스산하다 애달프다 어쭙잖다 올곧다 옹골지다 복마전 분수령 불야성 열변 기린아 궁상맞다 을씨년스럽다 투박하다 호남아 유복자 풍운아 하릴없다 불세출 공치사 주야 여북 시금석 진풍경 청백리 무진장 웅변 숙연하다 일장 기시감 조아리다 곱씹다 비운 감돌다 도래하다 내박치다 박차 봉착 섭렵 들쓰다 궁싯거리다 나부대다 니글거리다 암묵적 벼르다 도지다 사무치다 집념 감격 경종 뇌까리다 다잡다 마름하다 삭이다 냉소 시부렁거리다 얼버무리다 목도 선양 아류 엄습 고귀한 애통하다 짐짓 무릇 불한당 도화선 기승 노상 사뭇 자못 등용문 요지경 대단원 알싸하다 소인배 옹고집 일당백 화사하다 괄괄하다 애잔하다 얍삽하다 기별 순박한 자긍심 추레하다 극한 어귀 든적스럽다 새삼스럽다 일가견 좌우명 청사진 심미안'.split())
issues=[]
def issue(cid,kind,severity,problem,proposal,status='교정 후보·교사/사전 검수 필요'):
 row=next(r for r in rows if r['content_id']==cid)
 issues.append({'content_id':cid,'printed_number':row['printed_number'],'headword_original':row['headword_original'],'pdf_page':row['pdf_page'],'recall_page':row['recall_page'],'issue_type':kind,'severity':severity,'problem':problem,'proposal':proposal,'status':status})
# Exact source-pair errors; unrelated inserted material is not authorized new vocabulary.
for cid,problem,proposal in [
 ('W0008','학습은 융통성. 빈칸은 자신의 행복을 노래하고 누림/전성기 선수를 ( )하고 있다. 다른 단어의 뜻·예문.','융통성으로 두 페이지를 통일. 구가로 보이는 내용은 신규 단어로 자동 등록하지 않음.'),
 ('W0012','학습은 점령. 빈칸은 사람·기관에 일을 맡김/변호사에게 법적 문제 ( )했다.','점령으로 두 페이지를 통일. 의뢰로 보이는 빈칸은 별도 검수.'),
 ('W0013','학습은 방탕. 빈칸은 사물에 몸·마음을 기대 도움 받음/지팡이에 ( )했다.','방탕으로 두 페이지를 통일. 의지 내용 혼입 추정.'),
 ('W0015','전쟁에 참가함이라는 뜻에 미래를 위해 꾸준히 저축했다는 예문이 붙음. 빈칸도 없음.','참전 문맥의 예문·빈칸을 다시 작성.'),
 ('W0242','학습은 발굴. 빈칸은 재물를 몰래 훔치거나 독차지함/딸기를 따는 대로 ( ).','발굴의 유적·자료 발견 문맥으로 다시 작성.'),
 ('W0245','학습은 인재. 빈칸은 한 부분을 잘라 버림/말을 뚝 ( ).','인재의 뛰어난 재주·인력 문맥으로 통일.'),
 ('W0339','학습 성토는 잘못을 비판함. 빈칸은 사정을 생각해 헤아림/타당하다고 ( )되다. 학습 예문 마당에서 성토는 흙을 쌓는 다른 뜻을 암시.','성토(聲討)를 비판하는 문맥으로 고정. 원문은 의미 충돌 사례로 보존.'),
 ('W0364','학습은 조작. 빈칸은 눈에 띄게 시원스럽게/물건이 ( ) 마음에 들다.','조작의 사실 꾸밈 또는 기계 다룸 중 의미를 선정하여 통일.'),
 ('W0401','학습은 근원. 빈칸은 어떤 일·현상의 첫 단계/경기가 ( )됐다.','근원의 본바탕·발원지 문맥으로 재작성.'),
 ('W0402','학습 표제는 의지하다/기댐인데 학습 예문은 굳은 의지(뜻·결심). 빈칸은 근원의 뜻·강의 ( )을 찾아보자.','의지하다(依支)와 의지(意志)를 의미 ID로 분리; 사람에게 기대는 예문 작성.'),
 ('W0404','학습은 궁극적인. 빈칸은 일을 막아 못 하게 함/수면 부족은 건강을 ( )한다.','궁극적의 마지막 목표 문맥으로 통일.'),
 ('W0413','학습은 순박한. 빈칸은 상대 기권으로 싸우지 않고 올라감/행운의 ( )으로 결승 진출.','순박하다의 순진·소박 문맥으로 통일. 부전승 추정 내용 별도 검수.'),
 ('W0437','학습은 극한(몹시 심한 추위). 빈칸은 부드럽고 상냥/ ( ) 말씨를 쓰다.','극한의 한자·의미를 확정한 뒤 추위 문맥으로 통일.')]:issue(cid,'학습/빈칸 의미 불일치','출제 차단',problem,proposal,'원문 불일치 확인·수정안은 미확정')
# Source spelling errors and other meaningful corrections; originals remain intact.
for cid,problem,proposal in [
 ('W0026','4쪽 빈칸 예문 모구에게','모두에게로 교정'),
 ('W0055','8쪽 예) 예) 중복','예) 하나 삭제'),
 ('W0075','9–10쪽 빠져드렀다','빠져들었다로 교정'),
 ('W0088','12쪽 예) 예) 중복','예) 하나 삭제'),
 ('W0119','15–16쪽 단체나 조직을 새로 만듬','만듦으로 교정'),
 ('W0150','19–20쪽 궁상맞은 얼굴 좀 하자마라','하지 마라로 교정; 초등용 긍정적 생활 예문을 별도로 새로 작성'),
 ('W0157','21쪽 어머니 배 속에 았을 때','있을 때로 교정'),
 ('W0163','21–22쪽 폑수 정화 시설','폐수 정화 시설로 교정'),
 ('W0193','25–26쪽 병애 걸렸다','병에 걸렸다로 교정'),
 ('W0222','29–30쪽 용합되어','융합되어로 표기 교정하되 과학 문맥은 별도 교정'),
 ('W0239','31쪽 기시감이들었다/것같이','기시감이 들었다/것 같이 등의 띄어쓰기 검수'),
 ('W0282','37–38쪽 자기 것으로 만듬','만듦으로 교정'),
 ('W0388','51–52쪽 꾸준한 연습해','꾸준히 연습해 또는 꾸준한 연습으로'),
 ('W0392','53–54쪽 시물이 자라기','식물이 자라기로 교정'),
 ('W0400','53–54쪽 높혀준다','높여 준다로 교정'),
 ('W0411','55–56쪽 기별부터 해하','기별부터 해라로 교정'),
 ('W0430','57–58쪽 물의 본질을','사물의 본질을로 교정 후보'),
 ('W0438','59–60쪽 접아들었다','접어들었다로 교정')]:issue(cid,'표기·띄어쓰기','검수 후 교정',problem,proposal,'원문 표기 확인·교정 후보')
for cid,problem,proposal in [
 ('W0006','표제는 강단있는, 뜻·빈칸·예문 핵심은 강단.','표제 강단, 확장 표현 강단 있다를 분리.'),
 ('W0010','표제 기탄없이, 빈칸 ( )없이의 정답은 기탄.','기탄과 기탄없이의 관계·답안 단위를 명시.'),
 ('W0004','말미를 다른 일로 얻게 되는 여유라고 풀어 의미가 모호함.','다른 일을 위해 잠시 쉬거나 얻는 겨를 등의 쉬운 풀이 후보; 사전 대조.'),
 ('W0081','관철 뜻은 사물을 꿰뚫어 봄, 예문 내 주장이 관철되다는 뜻을 이루어 냄.','한자와 의미 ID를 구분하고 관철(貫徹)의 목표 달성 의미를 학습.'),
 ('W0095','껄끄럽다 뜻은 물리적 거침, 예문은 상대와의 불편한 관계.','물리적·심리적 의미를 나눠 제시.'),
 ('W0108','상동은 의미·분야를 가르지 않고 서로 같음만 제시.','생물학의 상동 관계인지 같은 내용이라는 뜻인지 의미 ID 선정.'),
 ('W0160','섭취를 좋은 양분을 몸속에 빨아들임으로 한정; 예문은 영양 섭취가 안 좋다.','음식·영양분을 몸에 받아들이는 일과 흡수의 차이를 검수.'),
 ('W0161','달은 거의 진공 상태이라는 예문은 장소 범위를 넓게 단정.','달에는 대기가 거의 없다 등 과학 검수된 상황으로 수정.'),
 ('W0174','불모지를 내버려 두어 거친 땅으로 설명해 황무지와 구별이 약함.','생물이 자라기 어렵거나 성과가 없는 분야라는 의미와 황무지 차이를 검수.'),
 ('W0178','표제 폐기하다이지만 예문 건축 폐기물이 심각하다는 동사 사용이 없음.','낡은 자재를 폐기했다 등 동사 활용 예문으로 수정.'),
 ('W0182','고대하다의 뜻 기다리던 바로 그때가 학습 예문 내가 고대하던 소식과 맞지 않음.','몹시 기다리다로 교정 후보; 고대의 다른 뜻과 분리.'),
 ('W0192','치명적 뜻 죽을 지경에 이름, 예문은 선수의 실수로 비유적 손해.','생명 위험/매우 큰 손해 두 의미를 구분.'),
 ('W0202','혼돈의 뜻은 천지 미분화, 예문은 정치적 혼란.','우주 발생 이전 상태와 질서 없는 혼란을 의미 ID로 분리; 혼동과 비교.'),
 ('W0207','공탁 뜻 은행에 맡김, 예문 은행에 공탁한 돈은 예탁과 혼동 가능.','법령에 따른 공탁 기관에 맡김이라는 법률 의미를 사전 검수.'),
 ('W0208','담합하다의 서로 의논해서 합의함은 부당한 거래·경쟁 제한 문맥을 드러내지 못함.','일반적 합의와 부당한 담합의 문맥을 구별.'),
 ('W0222','산소와 수소가 융합되어 물이 된다는 예문은 화학 결합과 핵융합·일반 융합을 혼동시킴.','음악과 미술을 융합한 공연처럼 안전한 일반 의미 예문 작성.'),
 ('W0233','경위 뜻 사리 시비 분간, 예문 사건의 경위는 일의 진행 사정.','경위(經緯)의 과정·사정 의미로 통일하거나 동음이의어 분리.'),
 ('W0276','박차를 말을 채찍질하듯으로 설명하여 본뜻의 말에 쓰는 발뒤꿈치 도구와 다름.','본뜻은 정확히 짧게, 박차를 가하다의 비유적 쓰임 중심.'),
 ('W0284','체포의 범죄 혐의자를 구속은 법적 절차상 구속과 체포를 동일시할 우려.','체포·구속 구별을 사전·법률 문맥에서 교사 검수.'),
 ('W0299','작동하다 예문 엔지니어가 기계를 작동했다는 타동·사동 사용 검수 필요.','기계가 작동했다/기계를 작동시켰다로 역할을 분명히 함.'),
 ('W0384','대단원 예문 대단원의 막을 내리다는 대단원의 막/막을 내리다 관용표현 검수 필요.','공연이 감동적인 대단원에 이르렀다 등의 문맥.'),
 ('W0391','선심쓰다 표제와 명사 선심 뜻이 불일치.','선심/선심 쓰다를 표제·관용표현으로 분리하고 띄어쓰기 검수.'),
 ('W0398','일당백을 매우 용감함만으로 풀어 한 사람이 백 사람을 당함이라는 핵심이 약함.','용감함뿐 아니라 많은 사람의 몫을 해냄을 풀어쓰기.'),
 ('W0422','독특하다 뜻 특별하게 다름. 훨씬 뛰어남은 독특함을 우수함과 동일시.','보통 것과 구별되는 특별한 특징이 있음으로 교정 후보.'),
 ('W0428','관람 표제인데 뜻은 구경하는 사람, 예문은 관람자.','관람의 행동 뜻과 관람자의 사람 뜻을 분리.'),
 ('W0429','호사가의 일을 벌이기를 좋아하는 사람과 입에 오르내리다 예문이 문맥상 맞지 않음.','남의 일에 관심이 많아 이야기하기 좋아하는 사람이라는 문맥 검수.'),
 ('W0437','극한 표제는 추위 의미인데 극한의 추위라는 예문은 극한(極限)과 혼동 가능.','극한(極寒)과 극한(極限)을 의미 ID로 분리.')]:issue(cid,'뜻·예문·표제 정합성','출제 전 교사 검수',problem,proposal)
for cid in ['W0274','W0286','W0289','W0439']:
 issue(cid,'표제어 사전 대조','검토',f"드문 표현 {next(r for r in rows if r['content_id']==cid)['headword_original']}의 표준 표제·방언·문학 사용 여부 확인 필요.",'기계적으로 다른 단어로 고치지 말고 국립국어원 사전과 교재 의도를 대조.')
for cid in ['W0193','W0256','W0257','W0258','W0265','W0292','W0367','W0422','W0448']:
 issue(cid,'빈칸 누락','출제 차단','복습 페이지의 예문에 괄호 빈칸이 없고 목표어가 그대로 노출됨.','뜻과 예문을 보존한 후 목표어 또는 활용 부분에 빈칸을 만듦.','원문 누락 확인·수정안은 미확정')
issue_ids=collections.defaultdict(list)
for n,i in enumerate(issues,1):i['issue_id']=f'I{n:03d}';issue_ids[i['content_id']].append(i['issue_id'])
answers=[]
for r in rows:
 w=r['headword_original'];lemma=normalization.get(w,w)
 family=lemma[:-2] if lemma.endswith(('하다','되다')) else lemma
 r['suggested_lemma']=lemma
 r['lemma_status']='제안·국립국어원 표제/품사 검수 필요' if w in normalization else '원문 형태 유지·사전 전수검증 전'
 r['word_family_key']=family
 r['inferred_source_number']=r['printed_number'] if r['printed_number'] is not None else r['recall_printed_number']
 r['number_inference_note']='19쪽 학습번호 없음; 20쪽 짝페이지 원문번호 136–150을 연결'  if r['printed_number'] is None else ''
 r['origin_tag_provisional']='고유어 중심' if w in native else '혼합·표현' if w in mixed else '한자어 중심(잠정)'
 r['usage_tag_provisional']='생활·학습 기초' if w in core else '문학·묘사·관용' if w in literary else '추상·사회·전문'
 r['difficulty_band_proposal']='A: 생활 맥락으로 시작' if w in core else 'B: 묘사·관용으로 확장' if w in literary else 'C: 추상·전문 의미 확장'
 r['tag_status']='편집 초안; 학년 규준이 아님. 진단과 교사 검수로 조정'
 r['issue_ids']=issue_ids[r['content_id']]
 r['release_status']='검수대기' if r['issue_ids'] else '사전·교사 검수 전'
 norm=lambda s:re.sub(r'[\s,\.。!\?]','',s).replace('예)','')
 original=norm(r['example_original']);recall=norm(r['recall_example_original'])
 pattern=re.sub(r'\\\(\\\)',r'(.+?)',re.escape(recall))
 m=re.fullmatch(pattern,original)
 r['recall_answer_inferred']=m.group(1) if m and m.lastindex else None
 r['answer_inference_note']='학습/빈칸 문장 대조에서 추정. 원문 정답표가 아님.' if r['recall_answer_inferred'] else '원문 정답표 없음; 불일치 또는 빈칸누락·문장변경으로 교사 지정 필요'
# Row order and raw text are unchanged. Enrichment is always marked proposed.
(R/'vocabulary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
cols=[k for k in rows[0] if 'bbox' not in k]
with (R/'vocabulary.csv').open('w',encoding='utf-8-sig',newline='') as f:
 ww=csv.DictWriter(f,fieldnames=cols);ww.writeheader()
 for r in rows:ww.writerow({k:';'.join(r[k])if isinstance(r[k],list)else r[k]for k in cols})
(R/'correction-candidates.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2))
with(R/'correction-candidates.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.DictWriter(f,fieldnames=issues[0].keys());w.writeheader();w.writerows(issues)
counts=lambda key:dict(collections.Counter(r[key]for r in rows))
unique=collections.Counter(r['headword_original']for r in rows)
normalized=collections.Counter(r['suggested_lemma']for r in rows)
family=collections.Counter(r['word_family_key']for r in rows)
numbered=[r for r in rows if r['printed_number'] is not None]
validation={'pdf_pages':60,'page_pairs':30,'learning_rows':len(rows),'rows_per_learning_page':dict(collections.Counter(r['pdf_page']for r in rows)),'unique_original_headwords':len(unique),'duplicate_original_headwords':{k:[{'content_id':r['content_id'],'printed_number':r['printed_number'],'pdf_page':r['pdf_page']}for r in rows if r['headword_original']==k]for k,v in unique.items()if v>1},'unique_suggested_lemmas':len(normalized),'unique_word_families':len(family),'rows_with_printed_number':len(numbered),'missing_number_rows':[r['content_id']for r in rows if r['printed_number']is None],'numbers_absent_across_learning_and_recall':sorted(set(range(1,491))-{v for r in rows for v in [r['printed_number'],r['recall_printed_number']] if v is not None}),'numbers_absent_on_learning_pages':sorted(set(range(1,491))-{r['printed_number']for r in numbered}),'printed_numbers_strictly_increasing':all(a['printed_number']<b['printed_number']for a,b in zip(numbered,numbered[1:])),'paired_number_mismatches':[r['content_id']for r in rows if r['printed_number']!=r['recall_printed_number']],'all_learning_rows_nonempty':all(r['headword_original']and r['definition_original']and r['example_original']for r in rows),'all_recall_rows_nonempty':all(r['recall_definition_original']and r['recall_example_original']for r in rows),'recall_without_blank':[r['content_id']for r in rows if not re.search(r'\(\s*\)',r['recall_example_original'])],'pair_semantic_mismatch_rows':[i['content_id']for i in issues if i['issue_type']=='학습/빈칸 의미 불일치'],'correction_issue_count':len(issues),'rows_with_correction_candidate':sum(bool(r['issue_ids'])for r in rows),'provisional_origin_counts':counts('origin_tag_provisional'),'provisional_usage_counts':counts('usage_tag_provisional'),'provisional_difficulty_counts':counts('difficulty_band_proposal')}
(R/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2))
print(json.dumps(validation,ensure_ascii=False,indent=2))
