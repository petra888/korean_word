# 교직원 테스트 배포 준비

2026년 10월 10일 사용자의 요청으로 v9의 디자인 1·2 선택, 미래 도시 UI와 일러스트를 기존 `korean-word-demo` 프로젝트에 배포합니다. 기존 배포는 v8.1 상상 숲 버전이며 새 배포의 완료는 커밋별 READY 상태와 기존 주소 연결로 확인합니다. **사용자가 새 배포를 요청할 때만 푸시·배포합니다.** [Vercel 안내](vercel.md)를 참고하세요.

배포 대상은 `demo-site`입니다. 현재 HTML과 일러스트 열한 장이 검증 요약의 해시와 일치해야 생성됩니다.

저장소 최상위에서 Git 연동용 정적 빌드를 로컬 확인할 수 있습니다.

```bash
node vocabulary-planning/build_vercel_preview.mjs
```

직접 업로드할 ZIP을 준비하려면 다음 명령을 사용합니다.

```bash
python3 vocabulary-planning/prepare_demo_release.py
python3 vocabulary-planning/prepare_vercel_demo.py
```

이 명령들은 로컬 파일만 만들며 업로드·배포하지 않습니다.

- `demo-site/index.html`: 테스트 화면
- `demo-site/assets/*.webp`: 검증된 네 가지 화면 일러스트와 두 가지 전체 배경
- `demo-site/release-manifest.json`: HTML·자산 해시, Git 기준, 검증 범위
- `교직원-테스트-배포-{release}.zip`: 위 열세 파일을 넣은 업로드용 ZIP
- `교직원-테스트-배포-vercel-preview.zip`: 설정과 public 폴더를 포함한 직접 Vercel 업로드용 ZIP

전체 교재·문서·QA 이력·테스트 스크린샷은 배포 폴더에 포함하지 않습니다. 생성 폴더와 ZIP은 Git에서 제외됩니다.

학생 계정은 `test1/test1`, 교사 계정은 `test2/test2`입니다. 고정된 프런트엔드 테스트 로그인으로, 서버 인증·권한·학원별 저장은 구현 전입니다. 실제 기기·실제 프린터 검수는 보류합니다.

브라우저 기록은 주소·기기·브라우저별로 분리됩니다. 파일로 만든 기록이 새 HTTPS 주소로 자동 이전되지 않습니다. 학부모용 자료는 교사의 확정 자료 출력 기능을 사용하며, 내부 메모도 포함하는 JSON 기록과 구분합니다.
