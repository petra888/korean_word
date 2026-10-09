"""Prepare a verified static demo folder; this does not upload or deploy it."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent
source = ROOT / 'prototype/pilot-flow.html'
source_bytes = source.read_bytes()
digest = hashlib.sha256(source_bytes).hexdigest()
validation_path = ROOT / 'qa/release-readiness/validation-summary.json'
if not validation_path.exists():
    raise SystemExit('Run release-readiness verification before preparing the demo release.')
validation = json.loads(validation_path.read_text())
if validation.get('status') != 'pass' or validation.get('html_sha256') != digest:
    raise SystemExit('Release verification does not match the current HTML. Verify this source first.')
asset_names = ['forest-entrance.webp', 'forest-reading.webp', 'forest-writing.webp', 'forest-teacher.webp', 'forest-world.webp', 'forest-world-mobile.webp']
asset_hashes = {name: hashlib.sha256((ROOT / 'prototype/assets' / name).read_bytes()).hexdigest() for name in asset_names}
if validation.get('asset_sha256') != asset_hashes:
    raise SystemExit('Release verification does not match the current illustrations.')
bank = json.loads((ROOT / 'curriculum/pilot-10.json').read_text())
embedded = re.search(r'<script type="application/json" id="curriculum-data">([\s\S]*?)</script>', source_bytes.decode())
if not embedded or json.loads(embedded[1]) != bank:
    raise SystemExit('Embedded curriculum differs from canonical content.')
if len(bank['words']) != 10 or len(bank['items']) != 160:
    raise SystemExit('Unexpected demo curriculum scope.')
try:
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT.parent, text=True, stderr=subprocess.DEVNULL).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT.parent, text=True, stderr=subprocess.DEVNULL).strip())
except (subprocess.CalledProcessError, FileNotFoundError):
    commit, dirty = None, None
output = ROOT / 'deploy/demo-site'
output.mkdir(parents=True, exist_ok=True)
release_files = ['index.html', 'release-manifest.json'] + ['assets/' + name for name in asset_names]
unexpected = [path.name for path in output.iterdir() if path.name not in {'index.html', 'release-manifest.json', 'assets'}]
if unexpected:
    raise SystemExit('Demo folder contains unexpected files; move them outside the deployment folder first.')
(output / 'index.html').write_bytes(source_bytes)
(output / 'assets').mkdir(exist_ok=True)
if any(path.name not in asset_names for path in (output / 'assets').iterdir()):
    raise SystemExit('Unexpected public illustrations.')
for name in asset_names:
    shutil.copyfile(ROOT / 'prototype/assets' / name, output / 'assets' / name)
manifest = {
    'release': validation['release'], 'mode': 'fictional staff review demo',
    'html_sha256': digest, 'asset_sha256': asset_hashes, 'source_commit': commit, 'source_has_uncommitted_changes': dirty,
    'word_count': 10, 'objective_items': 160, 'storage_schema': 2,
    'data_storage': 'browser localStorage; no cross-device or per-student server storage',
    'authentication': 'fixed client-side student/teacher test accounts; no server authentication or authorization',
    'hosting_access': 'configure staff-only access at the hosting provider before sharing',
    'real_student_pilot_ready': False, 'content_approval': bank['status'],
    'actual_browser_mobile_print': validation['actual_browser_mobile_print'],
    'verified_checks': validation['checks'],
}
(output / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
archive = ROOT / ('deploy/교직원-테스트-배포-' + validation['release'] + '.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    for filename in release_files:
        bundle.write(output / filename, filename)
with zipfile.ZipFile(archive) as bundle:
    if set(bundle.namelist()) != set(release_files) or bundle.testzip() is not None or hashlib.sha256(bundle.read('index.html')).hexdigest() != digest:
        raise SystemExit('Demo archive verification failed.')
    if any(hashlib.sha256(bundle.read('assets/' + name)).hexdigest() != digest for name, digest in asset_hashes.items()):
        raise SystemExit('Demo archive illustration verification failed.')
print(json.dumps({'output': str(output), 'archive': str(archive), 'html_sha256': digest,
                  'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'source_has_uncommitted_changes': dirty, 'deployed': False}, ensure_ascii=False))
