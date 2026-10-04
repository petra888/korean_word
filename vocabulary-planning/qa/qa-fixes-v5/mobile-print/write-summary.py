from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).resolve().parent
source=O.parents[2]/'prototype/pilot-flow.html';digest=hashlib.sha256(source.read_bytes()).hexdigest()
markup=json.loads((O/'generated-markup-validation.json').read_text());contrast=json.loads((O/'contrast-calculation.json').read_text());raster=json.loads((O/'chart-raster-validation.json').read_text())
assert markup['sourceHtmlSha256']==digest,'markup metadata does not match current source'
assert contrast['sourceHtmlSha256']==digest,'contrast metadata does not match current source'
assert markup['failed']==0 and contrast['failed']==0
assert all(r['status']=='PASS' for r in raster['results'])
checked=[{'id':'MP-001','kind':'verified implementation issue','change':'객관식 4보기 aria-pressed 상태를 상호 배타적으로 제공','verification':'생성 마크업: 선택1개 true, 나머지3개 false; 선택 전4개 false; 재시도 후 제출선택 유지 및 최초오답 보존','result':'PASS (Node VM)'},{'id':'MP-002','kind':'verified implementation issue','change':'작문 초고와 수정 입력란에 고유 id 및 단어별 제목·안내 연결','verification':'초고10개 및 수정10개 모두 단어별 accessible name; 초고참조 id 실제존재','result':'PASS (generated markup)'},{'id':'MP-003','kind':'print structural risk, browser behavior previously unverified','change':'beforeprint 및 앱 출력 버튼이 현재 부모 자료를 매번 새로 생성','verification':'최초 대상생성·이전내용갱신·초안/내부메모 제외; 확정문구escape 및 장문10836자보존','result':'PASS (Node VM callback; browser print NOT RUN)'},{'id':'MP-004','kind':'verified implementation issue','change':'보조 글씨·footer·SVG 작은 글씨 #4b6474로 대비 개선','verification':'밝은 CSS배경18종 및 기타4쌍 대비22쌍 모두4.5:1이상','result':'PASS (color calculation)'}]
limitations=['320/375/768px 및 데스크톱의 실제 브라우저 레이아웃·가로 넘침','모바일 터치·마우스 드래그·실제 Tab/Enter 포커스·스크린리더','Chrome/Safari의 실제 Ctrl+P 및 앱 출력, PDF 페이지 나눔·장문 잘림','실제 브라우저의 색상 합성·안티앨리어싱·disabled opacity','SVG 한국어 글꼴 렌더 품질 및 실제 HTML/CSS 인쇄 배치']
summary={'reviewed_base_commit':'0d7598638dac12c59e2cf7d0151b43a73f51c42a','verified_working_source':str(source),'sourceHtmlSha256':digest,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':checked,'counts':{'markup_vm':{'passed':markup['passed'],'failed':markup['failed']},'contrast_pairs':{'passed':contrast['passed'],'failed':contrast['failed']},'svg_raster':{'passed':len(raster['results']),'failed':0}},'minimum_contrast':min(x['ratio'] for x in contrast['results']),'svg_max_error_percentage_points':100*max(x['max_absolute_error'] for x in raster['results']),'additional_changes_reviewed':'430px 이하 부모 미리보기 패딩 축소 및 도넛1열; 장문 종합평가/부모메시지의 페이지 분할 허용 CSS. 실제 모바일·인쇄 효과는 미검증.','unverified':limitations,'browser_block':'Previous baseline QA Chromium launch terminated with setsockopt: Operation not permitted and SIGTRAP; unchanged launch was not retried.','baseline_browser_evidence':'../../latest-commit-0d75986/mobile-print/browser-launch.json'}
O.joinpath('mobile-print-fix-report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
rows='\n'.join(f"| {r['id']} | {r['change']} | {r['verification']} |" for r in checked)
text=f'''접근성·모바일·인쇄 수정 검증

기준 커밋 `0d75986`의 QA 문제를 수정한 작업 소스를 검증했습니다. 검증 HTML SHA256: `{digest}`.

| 항목 | 반영한 개선 | 실제 검증 |
|---|---|---|
{rows}

Node VM 마크업·인쇄 이벤트9개, 대비 계산22쌍, MuPDF 도넛 SVG 래스터5개 모두 통과했습니다. 밝은 배경 전체 중 보조 글씨 최소 대비는 {summary['minimum_contrast']:.2f}:1이고, 도넛 색상 면적 비율 최대오차는 {summary['svg_max_error_percentage_points']:.4f}%p입니다. 이는 실제 모바일 화면 또는 브라우저 출력의 통과 판정이 아닙니다.

430px 이하 부모 미리보기 패딩을 줄이고 도넛을1열로 배치하는 CSS, 장문 종합평가·부모 메시지의 페이지 분할을 허용하는 CSS를 검토했습니다. 좁은 화면 배치와 실제 출력 페이지 나눔의 결과는 미검증입니다.

Chromium 실행이 이전 QA에서 `setsockopt: Operation not permitted`와 SIGTRAP으로 차단되어 같은 실행을 반복하지 않았습니다. 실제320/375/768px·데스크톱 화면, 터치/드래그, 키보드 포커스/스크린리더, Chrome/Safari 인쇄와 PDF 잘림은 미검증으로 남깁니다. MuPDF 결과는 SVG 색상과 면적 검증이며 HTML/CSS 인쇄 레이아웃을 검증하지 않습니다.

재현 가능한 스크립트와 JSON·SVG·PNG 증거는 같은 폴더에 있습니다. 검증 범위와 실행 순서는 README.md를 참고하세요.
'''
O.joinpath('mobile-print-fix-report.md').write_text(text)
print(json.dumps(summary['counts'],ensure_ascii=False))
