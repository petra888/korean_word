# 학원용 어휘 학습 프로그램

첨부 교재의 어휘로 만든 개발 전 기획·콘텐츠와 학생/교사 화면 시제품입니다. v9는 **디자인 1 · 상상 숲**과 **디자인 2 · 빛의 미래 도시**를 로그인 전후 상단 버튼에서 선택할 수 있습니다. 미래 도시는 청록·푸른 유리·은백색·주황 포인트, 각을 살린 버튼과 카드, 탐험·창작·교사 관제실 일러스트로 화면 전체를 구성합니다. 두 디자인 모두 모바일 배경과 움직임 조절을 제공합니다.

새 방문자의 기본값은 디자인 2이며 선택은 브라우저에 저장합니다. 디자인 전환은 입력 중인 로그인·답안·작문·교사 코멘트와 학습 기록을 유지합니다. [디자인 변경·실제 브라우저 검증](vocabulary-planning/qa/release-readiness/designs/README.md)에서 화면과 검증 범위를 확인할 수 있습니다. 2026년 10월 10일 사용자의 배포 요청에 따라 v9를 기존 `korean-word-demo` 프로젝트의 배포 대상으로 준비했습니다. 서비스 주소는 https://korean-word-demo.vercel.app/ 이며 최종 완료 여부는 Vercel의 커밋별 READY 상태와 주소 연결로 확인합니다.

## 시제품 열기

[vocabulary-planning/prototype/pilot-flow.html](vocabulary-planning/prototype/pilot-flow.html)을 브라우저에서 직접 엽니다. 학생 테스트 계정은 아이디·비밀번호 모두 `test1`, 교사는 모두 `test2`입니다. 로그인 유형을 먼저 선택하고 공백 없이 입력합니다. 학습 기록의 저장 형식은 v2이며 기존 답안·작문·판정을 보존합니다. 테스트 로그인은 화면 검토용이며 서버 인증·학원별 접근 권한은 구현 전입니다.

**배포는 사용자가 명시적으로 요청할 때만 진행합니다.** `main`에 푸시하면 Vercel 자동 배포가 실행되므로, 일반 수정 작업은 로컬에 보관하고 배포 요청 없이 `main`으로 푸시하지 않습니다.

저장 정책으로 직접 파일 열기가 제한되면 저장소 최상위 폴더에서 다음 명령을 실행합니다.

```bash
python3 -m http.server 8765 --directory vocabulary-planning/prototype
```

주소: http://localhost:8765/pilot-flow.html

## 주요 자료

- [PRD](vocabulary-planning/documents/PRD.md)와 [개발 상세 명세](vocabulary-planning/documents/development-spec.md)
- [교재 분석](vocabulary-planning/analysis/README.md), 원문 순서를 보존한 전체450학습행·45묶음
- [교재 첫10개 콘텐츠](vocabulary-planning/documents/10-word-curriculum.md): 빈칸4지선다160문항, 기본/대체 작문20질문
- [디자인 시안](vocabulary-planning/designs): 학생용 A/B/C/D와 교사·부모 자료 시안
- [참고 레퍼런스](vocabulary-planning/research/references.md)와 출처 근거
- [테스트 배포 준비](vocabulary-planning/documents/test-deployment.md)와 [교직원 데모 배포 폴더](vocabulary-planning/deploy/README.md)
- [v5 전달 자료](vocabulary-planning/deliverables/qa-fixes-v5/README.md): 추가 복구 수정 전 PDF 문서·ZIP
- [배포 전 추가 수정](vocabulary-planning/qa/release-readiness/choice-order-fix.md)와 [현재 검증 결과](vocabulary-planning/qa/release-readiness/validation-summary.json)
- [개선 검증 보고서](vocabulary-planning/qa/qa-fixes-v5/개선-검증-보고서.md)와 [수정 전 QA](vocabulary-planning/qa/latest-commit-0d75986/QA-보고서.md)
- [검수·작업 계획](vocabulary-planning/planning): 실서비스63검수 사례와28작업

교재 첫10개 순서는 까탈·깜냥·달포·말미·선잠·강단있는·격의·융통성·굴지·기탄없이입니다. 콘텐츠와 사전 뜻은 교육 담당자 최종 승인 전입니다.

## 검증

Python3.10+와 Node18+를 사용합니다. 다음 기본 검증에는 추가 Python/npm 패키지가 필요하지 않습니다.

```bash
cd vocabulary-planning
python3 validate_predevelopment.py
python3 analysis/validate_dataset.py
node qa/development-readiness/prototype-vm-check.js
```

현재 검증에는 기존 학습 회귀 검사와 테스트 로그인 검사가 포함됩니다. [실제 Chromium 결과](vocabulary-planning/qa/release-readiness/login/browser-results.json)는 로그인·계정 변경·객관 10문항·작문 10개·교사 검토 및 360/390/768/1280px 로그인 화면을 확인합니다. [로그인 경계 조건](vocabulary-planning/qa/release-readiness/login/vm-results.json)은 세션 손상·만료·저장 실패와 역할별 화면 진입을 검사합니다. 실제 기기와 실제 인쇄 검수는 사용자 요청으로 보류합니다. 서버 계정·권한·저장·기간별 집계를 제공하는 납품 서비스는 아직 구현하지 않았습니다.

## 데이터와 문서 재생성

기본 JSON/CSV 재생성:

```bash
python3 prepare_textbook_order.py
python3 export_pilot_tables.py
python3 sync_prototype_content.py
```

원본 PDF 재추출 또는 PDF 문서 재생성에는 추가 패키지가 필요합니다.

```bash
python3 -m pip install -r requirements.txt
python3 analysis/extract.py /path/to/도전수능1등급어휘1-수정본.pdf
python3 analysis/enrich.py
python3 render_predevelopment_reportlab.py
python3 package_predevelopment.py
```

위 명령은 `vocabulary-planning` 폴더에서 실행합니다. 교재 원본 PDF는 이 저장소에 포함하지 않았으므로 재추출 시 원본 파일을 지정합니다. PDF 문서 렌더러는 Linux의 `/usr/share/fonts/opentype/noto/NotoSansCJK-{Regular,Bold}.ttc` 한글 글꼴을 사용합니다. 렌더러가 생성하는 글꼴 캐시는 Git에서 제외합니다.

현재 소스의 배포 전 검증을 마친 뒤 `python3 prepare_demo_release.py`로 정적 데모를 준비합니다. 이 명령은 업로드·외부 배포를 하지 않습니다. 실제 학생 파일럿에 필요한 계정·권한·서버 저장·기간 집계는 테스트 배포 계획에 구분했습니다.
