"""Prepare a minimal Vercel Preview upload; never log in or deploy."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
result = subprocess.run([sys.executable, str(ROOT / 'prepare_demo_release.py')],
                        check=True, capture_output=True, text=True)
demo = json.loads(result.stdout)
source = Path(demo['output'])
output = ROOT / 'deploy/vercel-preview'
public = output / 'public'
output.mkdir(parents=True, exist_ok=True)
allowed_root = {'public', 'vercel.json', '.vercelignore', '.vercel'}
if any(path.name not in allowed_root for path in output.iterdir()):
    raise SystemExit('Unexpected files in Vercel upload folder.')
public.mkdir(exist_ok=True)
if any(path.name not in {'index.html', 'release-manifest.json'} for path in public.iterdir()):
    raise SystemExit('Unexpected files in Vercel public folder.')
(public / 'index.html').write_bytes((source / 'index.html').read_bytes())
manifest = json.loads((source / 'release-manifest.json').read_text())
manifest.update({'deployment_provider': 'Vercel', 'deployment_target': 'Preview',
                 'deferred_by_user': ['actual device QA', 'printing QA'],
                 'deployment_protection': 'Verify Vercel Authentication before sharing; not configured by this package.'})
(public / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
config = {
    '$schema': 'https://openapi.vercel.sh/vercel.json',
    'version': 2, 'framework': None, 'buildCommand': '', 'installCommand': '',
    'outputDirectory': 'public',
    'headers': [{'source': '/(.*)', 'headers': [
        {'key': 'X-Robots-Tag', 'value': 'noindex, nofollow, noarchive'},
        {'key': 'Cache-Control', 'value': 'no-store'},
    ]}],
}
(output / 'vercel.json').write_text(json.dumps(config, indent=2) + '\n')
(output / '.vercelignore').write_text('.git/\n.vercel/\n.env\n.env.*\nnode_modules/\n')
files = ['public/index.html', 'public/release-manifest.json', 'vercel.json', '.vercelignore']
archive = ROOT / 'deploy/교직원-테스트-배포-vercel-preview.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for name in files:
        package.write(output / name, name)
with zipfile.ZipFile(archive) as package:
    if set(package.namelist()) != set(files) or package.testzip():
        raise SystemExit('Vercel archive integrity check failed.')
    if hashlib.sha256(package.read('public/index.html')).hexdigest() != demo['html_sha256']:
        raise SystemExit('Vercel HTML differs from verified source.')
print(json.dumps({'output': str(output), 'archive': str(archive),
                  'source_commit': manifest['source_commit'],
                  'source_has_uncommitted_changes': manifest['source_has_uncommitted_changes'],
                  'html_sha256': demo['html_sha256'],
                  'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'externally_deployed': False, 'actual_device_print_qa': 'deferred by user'}, ensure_ascii=False))
