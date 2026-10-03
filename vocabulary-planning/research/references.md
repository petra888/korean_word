# 어휘력 프로그램 참고자료 조사
검토일: 2026-10-03 (한국 시간 기준) · 대상: 한국어 어휘가 부족한 초등~중학생 · 용도: 학원 납품용 학생 학습/교사 운영 PRD와 디자인 시안

## 조사 범위와 확인 수준
실시간 웹 검색과 일반 웹페이지 열람 도구가 없어, 접근이 허용된 공개 GitHub의 공식 문서·공개 구현·논문을 직접 열람했다. Anki와 Khan Academy Perseus는 공식 저장소의 UI 이미지도 직접 확인했다. Scratch는 현재 공식 monorepo의 UI 구현과 색·스타일 정의를 확인했다. H5P Essay는 H5P 조직 저장소가 아닌 개발자 `otacke`의 공개 구현이라는 점을 구분했다.

아래 자료는 실제 확인한 기능·설계 방식의 참고 근거다. Duolingo·Quizlet·NoRedInk의 최신 상용 화면을 직접 확인한 것으로 서술하지 않는다. 외국어 학습 서비스, 성인용 도구, 행정 UI의 기능과 연구 결과를 한국어 초중등 어휘·작문 학습효과로 바로 일반화하지 않는다. 화면 디자인을 복제하지 않고 학습 흐름·정보 구조·조작 원칙을 재해석한다.

## 레퍼런스 한눈에 보기
| ID | 레퍼런스 | 직접 확인한 자료 | 프로그램에 적용할 요소 | 시안 연결 |
|---|---|---|---|---|
| R1 | Anki | 공식 학습·편집·복습 매뉴얼, 학습개요 UI 이미지 | 새 학습/복습 분리, 문장 빈칸, 정답 보기 전 회상, 복습 부담 표시 | A 어휘 탐험, B 읽기 라운지 |
| R2 | Khan Academy Perseus | 공식 README, 문항 샘플 이미지, 순차 힌트 구현 | 한 문항에 집중하는 화면, 선택지 분리, 단계별 힌트 | B 읽기 라운지, C 문맥 탐정 |
| R3 | H5P Fill in the Blanks | 공식 문항 스키마 | 문맥 빈칸, 허용 대안답, 텍스트 힌트, 재시도와 정답 설명 | B 읽기 라운지, C 문맥 탐정 |
| R4 | H5P Essay | 개발자 공개 README·문항 스키마 | 작문 초안, 단어 사용 확인, 피드백 후 수정, 여러 모범문장 | D 문장 스튜디오 |
| R5 | Moodle | 공식 과제·퀴즈 UI 문자열과 도움말 | 과제 배정, 제출/검토/반려/재제출, 시도 이력과 교사 일괄 처리 | D 문장 스튜디오, 교사 공통 |
| R6 | GOV.UK Design System | 공식 Textarea·Error message 안내 | 명확한 입력 라벨, 알맞은 입력 크기, 답안 보존, 구체적인 안내 | D 문장 스튜디오, 공통 접근성 |
| R7 | Duolingo Half-Life Regression | 공식 연구 저장소 README, 2016 ACL 논문 PDF | 복습 이력 기반 스케줄의 가능성, 적응형 정책의 검증 방법 | 모든 시안의 복습 기능 |
| R8 | IBM Carbon Design System | 공식 README·DataTable 안내 | 반/학생 필터, 상태별 정렬, 선택 행 일괄 과제 배정 | 교사 공통 |
| R9 | Scratch | 공식 새 저장소 README·튜토리얼 카드 UI·스타일·색 토큰 | 작은 단계, 이미지/짧은 제목, 진행 표시, 친근한 버튼 형태 | A 어휘 탐험 |

## R1. Anki — 회상과 복습량을 관리하는 간결한 학습 시작
직접 열람:
- [공식 학습 매뉴얼](https://github.com/ankitects/anki-manual/blob/main/src/studying.md)
- [공식 편집·Cloze 안내](https://github.com/ankitects/anki-manual/blob/main/src/editing.md)
- [공식 복습 옵션·FSRS 안내](https://github.com/ankitects/anki-manual/blob/main/src/deck-options.md)
- [직접 확인한 학습개요 이미지](https://github.com/ankitects/anki-manual/blob/main/src/media/study_overview.png)

관찰: 학습 시작 화면은 New/Learning/To Review 수량과 Study Now 버튼으로 구성된다. 카드 앞면을 먼저 보고 답을 생각한 뒤 정답을 공개한다. Cloze는 문장 속 단어를 가리고 힌트를 붙일 수 있다. 공식 FSRS 안내는 높은 목표 기억률이 더 잦은 복습과 학습량 증가를 수반한다고 설명한다.

적용: 학생 홈에 ‘오늘 새로 배울 단어’와 ‘다시 써 볼 단어’를 구분하고, 10~15분 세션 안에 끝낼 수 있는 분량을 제시한다. 복습은 뜻 카드만 반복하지 않고 다른 문맥·관계 비교·짧은 작문으로 다시 출제한다. 정답 여부와 힌트 사용 여부를 저장한다.

적용 경계: Anki의 자기평가 버튼은 초등학생이 정확히 사용한다는 보장이 없다. 학습 프로그램은 실제 답안과 교사 피드백을 함께 사용한다. 특정 FSRS 설정값이나 ‘90%’를 이 제품의 검증된 최적값으로 채택하지 않는다.

## R2. Khan Academy Perseus — 문항 집중과 점진적 도움
직접 열람:
- [공식 README](https://github.com/Khan/perseus/blob/main/README.md)
- [공식 문항 샘플 이미지](https://github.com/Khan/perseus/blob/main/sample.png)
- [힌트 순차공개 UI 구현](https://github.com/Khan/perseus/blob/main/packages/perseus/src/hints-renderer.tsx)

관찰: 공식 샘플은 문항 제목, 문제, 선택지, 도움말을 분리한다. 힌트 UI는 보이는 힌트 수를 관리하고 새 힌트가 나타나면 해당 콘텐츠로 포커스를 옮긴다. README는 문항 표현·상호작용·평가를 담당하는 exercise system임을 명시한다.

적용: ‘문장에서 단어 찾기’ 화면은 한 번에 하나의 학습 목표만 요구한다. ‘문맥의 단서 보기 → 쉬운 말로 뜻 보기 → 첫 글자/선택지 보기’처럼 도움을 단계화한다. 도움을 사용한 성공과 독립적으로 푼 성공을 진도에서 구분한다.

적용 경계: 수학 문항의 자동 채점 방식이 한국어 문장의 의미 적절성까지 평가해 주는 것은 아니다. 질문 UI 원칙만 참고한다.

## R3. H5P Fill in the Blanks — 문맥 유추와 답안 변형
직접 열람:
- [공식 README](https://github.com/h5p/h5p-blanks/blob/master/README.md)
- [공식 문항 스키마](https://github.com/h5p/h5p-blanks/blob/master/semantics.json)

관찰: 빈칸의 대안 정답, 텍스트 힌트, 점수 구간별 피드백, 재시도, 정답 공개, 보조기술용 안내 문구를 정의할 수 있다.

적용: 단어를 감춘 새로운 문장을 제시하고 학생이 단서를 찾은 뒤 답한다. 한국어의 조사·활용형·띄어쓰기 변형을 문항별 허용 답안으로 관리한다. 정답 공개 후에는 ‘이 단어가 어울리는 이유’와 ‘다른 선택지가 어울리지 않는 이유’를 제공한다.

적용 경계: 허용 답안을 넓히는 문자열 규칙만으로 모든 한국어 변형을 처리하지 않는다. 문항 제작자가 예문과 의미별 정답을 검토하며, 연습 모드의 재시도와 진단 모드의 독립 수행을 분리한다.

## R4. H5P Essay — 작문을 수정 가능한 과정으로 다루기
직접 열람:
- [개발자 공개 README](https://github.com/otacke/h5p-essay/blob/master/README.md)
- [작문 문항 스키마](https://github.com/otacke/h5p-essay/blob/master/semantics.json)

관찰: 공개 README는 교사가 정의한 키워드를 찾아 즉시 피드백하는 구현이라고 명시한다. 초안 저장, 최소/최대 길이, 키워드와 변형, 포함/누락 피드백을 제공한다. 스키마는 ‘예시 답안이 유일한 답이 아니다’라는 설명을 포함한다. README는 실험적 구현임을 밝히며 자동 에세이 채점의 교육적 한계를 언급한다.

적용: ‘상황 고르기 → 목표 단어를 사용해 한 문장 쓰기 → 사용 확인 → 교사 피드백 → 다시 쓰기’로 구성한다. 단어가 들어갔다는 사실과 단어의 뜻을 바르게 사용했다는 판정을 분리한다. 모범문장은 비교용이며 학생의 다른 유효한 문장을 인정한다.

적용 경계: 키워드 포함만으로 의미·문맥·문법을 통과시킬 수 없다. MVP에서는 단어 포함/빈 답안 같은 명확한 조건만 자동 확인하고, 의미 적절성은 교사가 루브릭으로 확정한다. AI를 추가하더라도 조언은 교사 검토 대상이며 최종 성적 근거로 단독 사용하지 않는다.

## R5. Moodle — 학원 운영을 학습 흐름에 연결하기
직접 열람:
- [공식 과제 UI 문구·도움말](https://github.com/moodle/moodle/blob/main/public/mod/assign/lang/en/assign.php)
- [공식 퀴즈 UI 문구·도움말](https://github.com/moodle/moodle/blob/main/public/mod/quiz/lang/en/quiz.php)

관찰: 과제는 시도별 성적·피드백 이력을 보존하고 교사·학생이 이를 볼 수 있도록 설명한다. 초안으로 되돌리기, 채점 상태 일괄 변경, 재시도 허용 정책 등의 UI 문구가 있다. 퀴즈 도움말에는 즉시 피드백과 반복 응답, 시도 수, 자동 저장이 정의되어 있다.

적용: 교사 화면에 ‘미시작·학습중·제출됨·검토대기·수정요청·완료’를 일관되게 표시한다. 학생별 작문 초안/제출본/수정본을 남기고, 교사는 필요한 학생부터 검토한다. 반 단위 배정, 개별 보충, 과제 마감, 출석과 별개의 학습 진도를 관리한다.

적용 경계: 학원 어휘학습에는 범용 LMS의 모든 메뉴가 필요하지 않다. MVP 교사 업무는 반 만들기·과제 배정·검토·진도 확인의 네 가지 중심으로 줄인다. 연습의 오답 횟수를 일률적으로 감점하지 않는다.

## R6. GOV.UK Design System — 읽기와 입력의 부담 줄이기
직접 열람:
- [Textarea 안내](https://github.com/alphagov/govuk-design-system/blob/main/src/components/textarea/index.md)
- [Error message 안내](https://github.com/alphagov/govuk-design-system/blob/main/src/components/error-message/index.md)

관찰: 라벨은 입력칸 위에 표시하고 placeholder만으로 라벨을 대체하지 않도록 한다. 입력칸 높이는 예상 응답량에 맞춘다. 오류 표시 시 기존 값을 지우지 않으며 무엇을 어떻게 고칠지 구체적으로 안내한다. 스크린리더용 오류 접두어도 제공한다.

적용: ‘단어를 사용해 한 문장을 써 보세요’처럼 짧고 분명한 요구를 상단에 둔다. 작문은 2~4줄 입력 영역부터 시작하고 초안을 자동 보존한다. ‘틀렸어요’ 대신 ‘아직 문장을 쓰지 않았어요. 목표 단어를 넣어 한 문장을 써 보세요’처럼 다음 행동을 알려 준다. 색상 외 아이콘·텍스트로 정답·검토대기 상태를 표시한다.

적용 경계: 행정 사이트의 밀도와 색을 그대로 사용하지 않는다. 어린 학습자를 위한 단계적 지시와 한국어 가독성은 학생 사용성 검토가 필요하다.

## R7. Duolingo HLR — 복습 정책은 측정하여 고도화하기
직접 열람:
- [Duolingo 공식 연구 저장소](https://github.com/duolingo/halflife-regression/blob/master/README.md)
- [공식 저장소의 2016 ACL 논문 PDF](https://github.com/duolingo/halflife-regression/blob/master/settles.acl16.pdf)
- 논문: Burr Settles & Brendan Meeder, *A Trainable Spaced Repetition Model for Language Learning* (2016), DOI `10.18653/v1/P16-1174`.

관찰: 저장소는 단어별 마지막 노출부터의 시간, 누적 정답/노출, 세션 정답/노출을 사용하는 기억 반감기 모델을 공개한다. 논문은 Duolingo 외국어 학습 데이터를 이용해 회상률 예측 오차를 평가하고 실제 서비스의 다음날 활동 여부를 측정한다. 모델별 단어 특성이 과적합과 학생 경험 문제를 만들 수 있었다고 논의한다.

적용: MVP는 교사가 설명 가능한 규칙 기반 복습부터 시작한다. 정답·힌트·응답 유형·마지막 시도 시점으로 다음 복습을 정하고, 지연 평가 데이터가 쌓인 뒤 고급 모델과 비교한다. 정답 맞힌 횟수와 새 문맥에서 쓸 수 있는 능력은 별도로 측정한다.

적용 경계: 논문의 ‘12%’는 다음날 서비스 재방문/활동 지표의 변화이며, 어휘 기억력이나 작문 능력이 12% 늘었다는 뜻이 아니다. 회상률 예측 오차 감소도 학습효과 자체와 다르다. 이 연구는 한국어 초중등 모국어 어휘·작문 평가를 검증하지 않았다. 제품의 효과는 새 예문과 지연 작문을 포함한 파일럿으로 확인한다.

## R8. IBM Carbon — 반과 학생 상태를 빠르게 검토하기
직접 열람:
- [공식 디자인시스템 README](https://github.com/carbon-design-system/carbon/blob/main/README.md)
- [공식 DataTable 안내](https://github.com/carbon-design-system/carbon/blob/main/packages/react/src/components/DataTable/DataTable.mdx)

관찰: 행/열 기반 데이터 테이블에 정렬, 필터링, 행 선택, 확장, 일괄 작업을 단계적으로 추가하는 구조를 설명한다.

적용: 교사 화면은 ‘반 → 검토대기 → 학생 → 답안’ 순서로 좁힌다. 학생 목록에 단순 평균 점수뿐 아니라 ‘문맥유추 도움 필요’, ‘작문 검토대기’, ‘복습 누락’을 표시한다. 선택한 학생에게 보충 과제를 일괄 배정한다. 상세 내용은 학생을 선택한 뒤 제공한다.

적용 경계: 학생 화면에 교사 대시보드의 높은 정보 밀도를 가져오지 않는다. 교사 목록의 점수는 객관식·작문·지연 평가를 구분하여 해석할 수 있어야 한다.

## R9. Scratch — 친근한 단계형 안내
직접 열람:
- [현재 공식 monorepo README](https://github.com/scratchfoundation/scratch-editor/blob/develop/README.md)
- [튜토리얼 카드 UI](https://github.com/scratchfoundation/scratch-editor/blob/develop/packages/scratch-gui/src/components/cards/cards.jsx)
- [카드 스타일](https://github.com/scratchfoundation/scratch-editor/blob/develop/packages/scratch-gui/src/components/cards/card.css)
- [색 토큰](https://github.com/scratchfoundation/scratch-editor/blob/develop/packages/scratch-gui/src/css/colors.css)

관찰: 튜토리얼 카드에는 이미지 또는 영상, 단계 제목, 이전/다음 버튼, 현재 단계 점 표시가 있다. 스타일 정의에는 둥근 모서리와 큰 둥근 조작 버튼이 있다. 색 토큰은 흰색·연청색 기반과 초록·주황 등 활동 강조 색을 구분한다. 구 `scratch-gui` README의 이전 안내를 확인한 뒤 새 `scratch-editor` 저장소를 조사했다.

적용: A 탐험 시안에서 한 장면에 한 학습 단계, 쉬운 제목, ‘3/5 단계’ 진행 표시, 친근한 조작 버튼을 사용한다. 캐릭터 보상은 학습을 마친 뒤 제공하고 문항 텍스트를 읽는 동안 화면을 계속 움직이지 않는다.

적용 경계: Scratch 캐릭터·블록 화면·색상값을 복제하지 않는다. 직접 확인한 것은 공식 UI 구현과 토큰이며 최신 운영 사이트 화면을 열람한 것은 아니다.

## 네 가지 디자인 방향과 출처 연결
| 방향 | 학습 화면의 중심 | 직접 참고한 원칙 | 사용자 검토에서 확인할 점 |
|---|---|---|---|
| A 어휘 탐험 | 오늘의 작은 미션, 친근한 카드와 진행 | R1 세션 개요·복습, R9 작은 단계와 친근한 조작 | 초등학생이 지시를 읽고 도움 없이 다음 단계로 진행하는가 |
| B 읽기 라운지 | 오늘의 계획, 문장 읽기, 역량별 진행 | R1 세션/복습 개요, R2 문항 집중, R3 문맥 빈칸 | 중학생이 유아감 없이 학습 계획과 자신의 약한 역량을 이해하는가 |
| C 문맥 탐정 | 문장 속 단서를 발견하는 문제 공간 | R2 순차 힌트, R3 문맥 빈칸과 대안 답안 | 장식보다 문맥 단서에 집중하는가, 힌트 사용이 이해로 이어지는가 |
| D 문장 스튜디오 | 작문 초고, 피드백 수정, 문장 포트폴리오 | R4 초안·단어확인·예시, R6 폼, R5 교사 검토흐름 | 첫 문장 시작의 부담과 피드백 후 의미가 바르게 수정되는가 |

교사 공통 화면은 R5 Moodle의 과제 상태와 R8 Carbon의 필터·일괄 작업을 참고한다.

네 시안은 같은 내용·같은 학습 단계로 비교한다. 색만 바꾸는 네 벌의 테마가 아니라 정보의 배치, 동기 부여 방식, 읽기/작문 강조점이 다르다. 최종 선택은 선호도와 함께 과제 이해, 독립 수행, 작문 시작, 교사 업무시간을 확인한다.

## PRD에 반영할 공통 결정
1. 학습 목표는 ‘뜻을 알아봄’에서 끝나지 않고 ‘새 문장의 문맥에서 고름 → 자신의 문장에 사용함 → 피드백을 보고 수정함’으로 확장한다.
2. 단어 단위의 ‘알고 있음’ 체크만 두지 않고 인식·문맥·표현·지연 회상을 나누어 기록한다.
3. 학년은 화면과 과제 길이를 정하는 보조 정보이며 실제 수준은 짧은 진단과 교사 판단으로 결정한다.
4. 선택형/빈칸형의 확정 정답과 작문의 열린 답안을 별도 평가한다. 작문 루브릭은 의미 적절성·문맥 연결·문장 완결성 중심으로 교사가 확정한다.
5. 입력 자동 저장, 힌트 접근, 색 외 상태 표시, 키보드 조작을 공통 요구사항으로 둔다.
6. 복습은 교재 예문 그대로의 재인보다 새 예문·상황을 포함한다. 파일럿에서 즉시 정답률과 7~14일 뒤의 새 문맥/작문 수행을 별도 측정한다. 기간은 검증 설계 제안이며 효과를 보증하는 값이 아니다.

## 증거 파일
`evidence.json`은 실제 열람 URL, 자료 종류, 관찰을 뒷받침한 짧은 원문, 적용 범위와 검증 한계를 기록한다. `source-images/`의 두 이미지는 원본 레퍼런스 확인용이며 디자인 시안 자체는 아니다. `duolingo-hlr-2016.pdf`와 추출 텍스트는 공식 공개 논문 사본이다.
