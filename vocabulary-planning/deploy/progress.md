# 테스트 배포 진행 기록

2026년 10월 4일. 목적은 가상 학생 기록을 이용한 본인·교직원 검토다.

## 2026년 10월 5일 Vercel 연결 후 실행

- Vercel 연결 도구로 프로젝트 조회가 성공했다. 기존 `korean-learning-website`는 별도 Next.js 서비스이므로 변경하지 않았다.
- 저장소 최상위 `vercel.json`과 `build_vercel_preview.mjs`를 추가했다. Vercel에서 검증된 HTML과 릴리스 정보 두 파일만 정적 출력하도록 구성했다. Python 빌드나 추가 npm 설치는 필요 없다.
- Node 빌드를 실제 실행해 기존 검증 HTML SHA와 첫10개·160문항 원본 일치를 확인했다.
- `8b6f9a63004304ba07006f48ad98b5a8fad67231`을 GitHub `petra888/korean_word`의 `main`에 실제 push했고, 원격 ref의 같은 SHA를 확인했다. 아래의 미푸시 기록은 이전 시점의 내역이다.
- 별도 `korean-word-demo` 프로젝트를 GitHub 소스에 연결해 Preview 배포하려고 요청했다. Vercel은 저장소 연결 조회 단계에서 `auhjins-projects` 팀 접근 권한이 없다는403오류를 반환했다. 프로젝트 생성·배포는 완료되지 않았고 생성된 배포 ID·URL은 없다.
- 오류 원문: `Not authorized: Trying to access resource under scope "auhjins-projects". You must re-authenticate to this scope or use a token with access to this scope.`
- 재개 조건은 Vercel 플러그인 연결에서 `auhjins-projects` 팀 접근 권한을 허용하는 것이다. 허용 후 같은 저장소·프로젝트 이름으로 다시 요청하고 READY 상태·배포 URL·접근 보호를 확인한다. 기존 별도 서비스나 보호 설정을 임의 변경하지 않는다.
- 실제 기기·인쇄 검수는 사용자 결정에 따라 보류한다.

## Vercel로 테스트 호스팅 변경

사용자 요청에 따라 Vercel Preview를 테스트 배포 경로로 준비한다. 실제 기기·인쇄 검수는
이번 배포의 선행 조건에서 제외하고 보류하며 통과로 표시하지 않는다. [Vercel 안내](vercel.md)의
직접 CLI 배포는 GitHub 푸시 없이 진행할 수 있다. 검증된 HTML을 그대로 별도 폴더·ZIP에
담고, 전체 저장소·교재 문서는 정적 출력에서 제외한다.

이 환경에는 Vercel 인증·프로젝트 연결·직접 도구가 없고, Vercel API·문서 접속은 프록시
연결 실패로 막혔다. 따라서 아래의 미배포 상태는 유지한다. Vercel Authentication 적용과
생성 URL·Ready 상태는 실제 배포 가능한 환경에서 확인해야 한다.

## 기존 진행 내역

| 항목 | 실제 상태 | 근거·후속 작업 |
| --- | --- | --- |
| QA 개선 소스 확정 | 완료 | `b1b6c136a6219490acb68fdfa624bdc1a6a6cd00` 커밋. HTML SHA `85226d2f83dc08803de48bdebe401c67602296507ee21cbfab91dfb6761976d7` |
| 커밋 후 데모 재생성 | 완료 | index·manifest·ZIP 재생성, 변경 없는 소스 표시 확인 |
| GitHub 원격 확인 | 완료 | petra888/korean_word는 브랜치0개, 기존 커밋 조회는 empty repository409 |
| 일반 Git 연결 | 실패 | proxy:8080에 연결하지 못해 ls-remote 실패. 네트워크 정책을 우회하지 않음 |
| GitHub 초기 파일 등록 | 자동 승인 거절 | “MCP tool call requires approval, but approval policy is never”. 원격 변경 없음 |
| HTTPS 테스트 사이트 | 미배포 | Sites 계정은 확인했으나 필수 소스 push를 완료할 수 없어 어휘 사이트 등록·게시 안 함 |
| 교직원 접근 제한 | 미설정 | 허용 명단 미확정. 공개/전체 구성원 접근으로 임의 확대하지 않음 |
| 실제 기기·인쇄 | 미검증 | 실제 브라우저 실행 제한. 최종 코드·콘텐츠 검증과 구분 |
| 실제 학생 파일럿 | 시작 전 | 로그인·학원/학생 권한·서버 저장·기간 집계·교육 검수 필요 |

## 다른 실행 환경에서 이어가기

clean한 소스에서 `python3 vocabulary-planning/prepare_source_transfer.py`를 실행한다.
`deploy/transfer/테스트-배포-인계.zip`은 정확한 소스 이력 번들, 같은 HTML의 교직원 데모 ZIP,
해시·커밋 기록, GitHub 전달 및 비공개 배포 안내를 포함한다. 생성 자료는 Git 추적에서 제외한다.
번들을 임시 폴더에 복원해 기준 커밋과 HTML 해시가 같은지 확인한다. 정상 push 후에만
원격 전달을 완료로 바꾸고, 배포 성공 상태와 URL·접근 범위를 확인한 뒤 배포를 완료로 기록한다.

인계 ZIP은 코드·교재 분석·교사용 초안과 QA 이력을 포함하는 개발용 자료다.
학부모 전달이나 공개 웹 폴더에 사용하지 않는다. 학부모 자료는 교사 화면의 확정 출력물을 사용한다.
