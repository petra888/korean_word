# 어휘 학습 QA 개선 자료 v5

2026년 10월 4일. 커밋 `0d75986`의 전체 QA에서 확인한 문제를 수정한 작업 자료입니다. 브라우저 저장 형식은 v2로 유지합니다.

## 사용 방법

압축을 풀고 `prototype/pilot-flow.html`을 브라우저에서 엽니다. 학생 화면에서 진단·혼합 객관·10단어 작문·기간별 복습을 진행하고, 교사 모의 화면에서 작문 판정과 부모 자료를 확인합니다. 콘텐츠는 교재 첫10개의 원문 순서를 유지하며 객관형160문항·작문질문20개입니다.

저장 기록이 손상되면 복구 가능한 기록을 유지하고 손상 원본 내보내기를 제공합니다. 저장 실패 안내를 확인하고 필요한 기록을 내려받아 보관합니다. 기존 기록은 저장 형식 v2에서 이어 사용합니다.

## 이번 개선

- 초기 진단 분포에 따른 문제 공급 부족을 해소하도록 단어별 연습 문항을9개씩 준비합니다. 이후 미사용 문항이 소진되면 공급 부족을 명시합니다.
- 오래된 호스트 상태의 덮어쓰기, 손상된 저장 기록, 로컬·호스트 저장 결과 표시를 보완합니다.
- 재시도 중 선택과 버전별 교사 평가 초안을 보존합니다. 과거 풀이에는 당시 문제·보기를 유지합니다.
- 선택 상태·작문 입력란의 접근성, 보조 글씨 대비, 인쇄 직전 최신 부모 자료 생성과 저장 데이터의 속성 escaping을 보완합니다.
- 격의·굴지 문맥과 일부 평가·복습의 보기·힌트·해설을 정비합니다.

## 검증 범위

세부 결과는 `qa/qa-fixes-v5/개선-검증-보고서.md`와 같은 이름의 PDF에 있습니다. Node VM·모의 DOM/저장소, 정적 마크업·색 대비, SVG 이미지화, 콘텐츠·CSV·HTML 일치 및 전달 문서 PDF 검증을 실제 브라우저 검증과 구분합니다.

실제 브라우저·터치·모바일 배치·스크린리더·부모 자료의 브라우저 인쇄는 이 실행 환경에서 미검증입니다. 실제 계정·서버 권한·저장·달력별 집계는 후속 실서비스 개발 범위이며 검수63사례는 미실행입니다. 콘텐츠는 사전 대조 및 교육 담당자 최종 승인 전이고 실학생 학습효과를 검증하지 않았습니다.

## 재검증

프로젝트 최상위 폴더에서 실행합니다.

```bash
python validate_predevelopment.py
python export_pilot_tables.py
node qa/development-readiness/prototype-vm-check.js
node qa/qa-fixes-v5/independent/regression.js
node qa/qa-fixes-v5/mobile-print/markup-regression.js
python qa/qa-fixes-v5/mobile-print/contrast-regression.py
python qa/qa-fixes-v5/mobile-print/raster-charts.py
python qa/qa-fixes-v5/content/audit-content.py .
```

파일별 SHA256은 `deliverables/qa-fixes-v5/package-manifest.json`에 있으며 ZIP 내 각 파일과 대조합니다. 이전 v4 자료와 `qa/latest-commit-0d75986` 보고서는 수정 전 근거로 보존합니다.
