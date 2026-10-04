"""Package an exact committed release for a machine with Git/network access."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()


if git('status', '--porcelain'):
    raise SystemExit('Commit all source changes before preparing a transfer.')
branch = git('branch', '--show-current')
if not branch:
    raise SystemExit('A named source branch is required for an independently clonable bundle.')
commit = git('rev-parse', 'HEAD')
tree = git('rev-parse', 'HEAD^{tree}')
demo_result = subprocess.run(
    [sys.executable, str(ROOT / 'prepare_demo_release.py')], cwd=REPO,
    check=True, capture_output=True, text=True,
)
demo = json.loads(demo_result.stdout)
if demo['source_has_uncommitted_changes']:
    raise SystemExit('Demo metadata must identify a clean committed source.')
output = ROOT / 'deploy/transfer'
output.mkdir(parents=True, exist_ok=True)
bundle = output / 'source-history.bundle'
subprocess.run(['git', 'bundle', 'create', str(bundle), f'refs/heads/{branch}'], cwd=REPO, check=True)
subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=REPO, check=True, capture_output=True)
heads = subprocess.check_output(['git', 'bundle', 'list-heads', str(bundle)], cwd=REPO, text=True).strip()
if heads != f'{commit} refs/heads/{branch}':
    raise SystemExit('Bundle branch does not match the committed source.')
manifest = {
    'source_commit': commit, 'source_tree': tree, 'source_branch': branch,
    'html_sha256': demo['html_sha256'],
    'bundle_sha256': hashlib.sha256(bundle.read_bytes()).hexdigest(),
    'demo_archive_sha256': demo['archive_sha256'],
    'github_uploaded': False, 'externally_deployed': False,
    'actual_browser_mobile_print': 'NOT RUN',
}
(output / 'transfer-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
instructions = f'''# 테스트 배포 인계 자료

외부 배포 완료본이 아니다. 소스 기준 커밋: `{commit}`.
검증된 HTML SHA-256: `{demo['html_sha256']}`.
실제 학생 계정·서버 저장은 아직 없으며 가상 교직원 검토에만 사용한다.

## GitHub 전달

GitHub 인증과 일반 네트워크가 동작하는 컴퓨터에서 ZIP을 풀고 실행한다.
현재 GitHub 저장소는 비어 있는 것으로 확인했으나, 실행 전에 변경 여부를 다시 확인한다.

```sh
git clone -b {branch} source-history.bundle vocabulary-release
cd vocabulary-release
git remote set-url origin https://github.com/petra888/korean_word.git
git ls-remote origin
git push -u origin {branch}:main
git ls-remote origin refs/heads/main
```

마지막 조회의 SHA가 위 기준 커밋과 같아야 전달 완료다. 원격에 새로운 이력이 있거나
일반 push가 거절되면 강제 push하지 말고 기존 이력과 통합한다.
번들은 최초 기획 커밋부터 배포 준비까지의 이력을 포함한다.

## 교직원 데모 배포

동봉한 `staff-demo.zip`의 index.html과 release-manifest.json만 정적 웹 폴더에 올린다.
HTTPS와 본인/허용 교직원 접근 제한을 먼저 설정한 후 공유한다.
전체 소스 저장소나 source-history.bundle은 웹 폴더에 올리지 않는다.
Sites를 사용한다면 Sites의 소스 저장소에 동일 배포 소스를 먼저 push하고,
그 저장소의 실제 커밋으로 버전을 저장·비공개 배포한다. GitHub 커밋을 대신 쓰지 않는다.

배포 성공 상태·접근 범위·URL을 확인하고 기록한다.
실제 기기·인쇄 검수는 소스의 vocabulary-planning/documents/test-deployment.md를 따른다.
기록은 주소·기기별로 분리되므로 새 주소에서는 가상 기록으로 다시 시작한다.
'''
(output / 'README.md').write_text(instructions)
archive = output / '테스트-배포-인계.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for name in ['source-history.bundle', 'transfer-manifest.json', 'README.md']:
        package.write(output / name, name)
    package.write(Path(demo['archive']), 'staff-demo.zip')
with zipfile.ZipFile(archive) as package:
    if set(package.namelist()) != {'source-history.bundle', 'transfer-manifest.json', 'README.md', 'staff-demo.zip'} or package.testzip():
        raise SystemExit('Transfer archive validation failed.')
if git('rev-parse', 'HEAD') != commit or git('status', '--porcelain'):
    raise SystemExit('Source changed during transfer preparation; prepare again.')
print(json.dumps({'archive': str(archive), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  **manifest}, ensure_ascii=False))
