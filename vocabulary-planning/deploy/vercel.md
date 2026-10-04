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

GitHub Import나 서버 푸시를 먼저 완료할 필요는 없다. 이후 지속적인 자동 배포가 필요하면
GitHub 소스를 전달하고 Vercel Git 연동·빌드 설정을 별도로 마련한다. 현재 설정은 생성한
`vercel-preview` 폴더의 직접 업로드용이며 저장소 전체를 그대로 Import하는 설정은 아니다.

브라우저 기록은 주소·기기별로 분리된다. 한 차례 테스트를 같은 URL에서 진행하고 새 배포 URL에
이전 기록이 자동으로 옮겨진다고 안내하지 않는다. 가상 학생 기록만 사용한다.

## 현재 실행 상태

Vercel 직접 도구·CLI 인증·프로젝트 연결이 이 환경에는 없다. Vercel API와 문서 접속도
프록시 연결 실패로 막혔다. 여기서는 파일 생성·ZIP 무결성·HTML 일치까지 확인하며 실제
외부 배포와 접근 보호 적용은 미완료로 기록한다. 실제 기기·인쇄 검수는 보류 상태다.

공식 안내 링크: [CLI 배포](https://vercel.com/docs/cli/deploy),
[프로젝트 설정](https://vercel.com/docs/projects/project-configuration),
[Vercel Authentication](https://vercel.com/docs/deployment-protection/vercel-authentication).
이 환경에서 공식 문서의 최신 내용을 열어 대조하지는 못했다.
