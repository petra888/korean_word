# 학원용 어휘 학습 프로그램

첨부 교재의 어휘로 만든 개발 전 기획·콘텐츠와 학생/교사 화면 시제품입니다. 현재 v5.1은 교사의 작문 3버튼 판정·자동 분류·수동 조정, 오답 표시·확정 도넛을 유지하며, QA의 저장·입력·접근성·인쇄 개선과 배포 전 보기 순서 복구 보완을 포함합니다.

## 시제품 열기

[vocabulary-planning/prototype/pilot-flow.html](vocabulary-planning/prototype/pilot-flow.html)을 브라우저에서 직접 엽니다. 브라우저 저장 형식은 v2이며 기존 답안·작문·판정 기록을 보존합니다. 학생·교사 전환은 모의 화면입니다.

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

기존 Node VM·모의 DOM27검수와 별도 SVG 이미지 비율 검증이 있습니다. v5의 추가 회귀 검사·실제 수행 결과·남은 미검증 항목은 개선 검증 보고서에 기록합니다. 실제 브라우저·마우스·모바일·인쇄 검증은 실행 환경 제한으로 미실행입니다. 실제 계정·서버 권한·저장·기간별 집계를 제공하는 납품 서비스는 아직 구현하지 않았습니다.

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
