# Vercel 테스트 배포

Vercel Preview로 가상 학생·교사 데모를 검토한다. 사용자 요청에 따라 실제 기기·인쇄 검수는
이번 테스트 배포의 선행 조건에서 제외하고 보류한다. 실제 학생 서비스의 계정·권한·서버 저장과
교육 검수는 별도 개발 범위이며, 이번 배포로 완료되지 않는다.

## 배포 파일 준비

저장소 최상위에서 실행한다.

```sh
python3 vocabulary-planning/prepare_vercel_demo.py
```

검증된 HTML 해시와 원본 콘텐츠를 확인한 다음 별도 `deploy/vercel-preview`를 만든다.
원래 `demo-site`에는 Vercel 설정이나 로그인 파일을 추가하지 않는다.

```text
vercel-preview/
  vercel.json
  .vercelignore
  public/
    index.html
    release-manifest.json
```

업로드 ZIP은 `교직원-테스트-배포-vercel-preview.zip`이다. 전체 교재·문서·QA 이력은 포함하지 않는다.
Framework는 Other(`null`), Build/Install Command는 비움, Output Directory는 `public`이다.
별도 Python/Node 빌드를 Vercel 서버에서 실행하지 않는 사전 생성 정적 배포다.

## GitHub 없이 직접 배포

Vercel 접속과 Node/npm 사용이 가능한 컴퓨터에서 ZIP을 풀고 해당 폴더의 터미널을 연다.
계정 인증은 Vercel의 로그인 화면에서 진행하고 비밀번호나 토큰을 문서·대화에 붙이지 않는다.

```sh
npx vercel login
npx vercel link
```

Vercel에서 별도 테스트 프로젝트를 선택하거나 생성한다. Framework/빌드/출력 설정은 위와 같게 한다.
프로젝트 Settings → Deployment Protection에서 Preview에 Vercel Authentication을 적용하고
접근 범위를 확인한다. 정답·교사 참고 내용이 HTML에 포함되어 있으므로 허용한 본인·교직원만
접속하도록 한다. `noindex` 헤더는 검색 노출 제어이며 로그인 보호를 대신하지 않는다.
요금제별 보호·공유 기능은 해당 계정에서 확인한다.

설정 확인 후 같은 폴더에서 실행한다.

```sh
npx vercel
```

기본 Preview 배포를 사용한다. 이번 테스트에서 Production으로 올리는 `--prod`는 사용하지 않는다.
Ready 상태·생성 URL·보호 대상과 허용 사용자 접속을 확인한 뒤 공유한다. Preview 보호가
Production URL이나 다른 도메인에도 동일하게 적용된다고 가정하지 않는다.

직접 CLI 배포는 GitHub Import나 서버 푸시를 먼저 완료할 필요가 없다. 생성한 `vercel-preview`
폴더의 설정은 위의 직접 업로드용이다.

## GitHub 연동 배포

2026년 10월 5일 저장소 최상위에 Git 연동용 `vercel.json`과 Node 빌드 스크립트를 추가하고
GitHub `petra888/korean_word`의 `main`에 push했다. 저장소 전체를 Import할 때 Root Directory는
저장소 최상위, Framework는 Other, Build Command는 `node vocabulary-planning/build_vercel_preview.mjs`,
Output Directory는 `vocabulary-planning/deploy/demo-site`, Install Command는 비움이다.
`vercel.json`이 이 설정을 제공한다. 서버 빌드는 기존 검증 해시·원본 콘텐츠가 같을 때만
진행하며, 정적 출력은 index.html과 release-manifest.json 두 파일로 제한한다.

연결 도구로 `korean-word-demo`를 생성해 기본 Preview 배포를 요청했으나 `auhjins-projects`
팀 접근 권한403오류로 배포 전에 중단됐다. Vercel 계정을 해당 팀 접근 권한으로 다시
연결해야 한다. 프로젝트·배포 ID와 URL을 받기 전에는 배포 완료로 표시하지 않는다.

브라우저 기록은 주소·기기별로 분리된다. 한 차례 테스트를 같은 URL에서 진행하고 새 배포 URL에
이전 기록이 자동으로 옮겨진다고 안내하지 않는다. 가상 학생 기록만 사용한다.

## 현재 실행 상태

Vercel 플러그인과 배포 도구가 연결되어 프로젝트 조회는 성공했다. Vercel CLI62.2.0도
설치했다. 현재 실제 배포를 막는 오류는 위 Git 연동 요청의 팀 접근 권한403이다.
실제 외부 배포와 접근 보호 적용은 미완료로 기록한다. 실제 기기·인쇄 검수는 보류 상태다.

공식 안내 링크: [CLI 배포](https://vercel.com/docs/cli/deploy),
[프로젝트 설정](https://vercel.com/docs/projects/project-configuration),
[Vercel Authentication](https://vercel.com/docs/deployment-protection/vercel-authentication).
이 환경에서 공식 문서의 최신 내용을 열어 대조하지는 못했다.
