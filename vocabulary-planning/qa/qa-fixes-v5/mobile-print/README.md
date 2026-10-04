이 폴더는 `0d75986` QA에서 발견한 접근성·인쇄 문제를 수정한 작업 소스에 대한 회귀 검증을 보관합니다. 이전 커밋의 원본 QA 증거는 수정하지 않았습니다.

실행 순서는 다음과 같습니다. 저장된 JSON의 `sourceHtmlSha256`로 실제 검증 소스를 확인할 수 있습니다.

```bash
node vocabulary-planning/qa/qa-fixes-v5/mobile-print/markup-regression.js vocabulary-planning/prototype/pilot-flow.html
python vocabulary-planning/qa/qa-fixes-v5/mobile-print/contrast-regression.py vocabulary-planning/prototype/pilot-flow.html
python vocabulary-planning/qa/qa-fixes-v5/mobile-print/raster-charts.py
```

- `generated-markup-validation.json`: 현재 JavaScript의 Node VM 실행, 모의 DOM에서 생성한 접근성 속성과 인쇄 이벤트 검증 9개.
- `contrast-calculation.json`: 보조 글씨의 밝은 CSS 배경 18종과 출력 footer·SVG 작은 글씨·정답·오답 글씨의 대비 계산 22쌍.
- `chart-raster-validation.json`: SVG 생성물을 MuPDF로 실제 래스터화한 도넛 비율 검증 5개.
- `donut-*.svg/png`: 0개·100%·40/30/20/10%·99/1%·3등분 차트 산출물.
- `writing-fields.html`, `selected-question.html`, `parent-report-long-message.html`: 검증에 사용한 생성 마크업. 브라우저에서 렌더링하거나 인쇄한 결과물이 아닙니다.

모의 DOM 검증은 실제 브라우저 접근성 트리, 모바일 레이아웃, 키보드 포커스, 터치, 브라우저 인쇄를 검증하지 않습니다. SVG 래스터화는 색상과 면적 비율을 확인하며 HTML/CSS 레이아웃·인쇄 페이지 나눔을 확인하지 않습니다. 이전 QA에서 Chromium이 `setsockopt: Operation not permitted`와 SIGTRAP으로 종료되어, 같은 환경에서 브라우저 실행을 반복하지 않았습니다.
