"""Embed the canonical bank and optionally retain one legacy bank for v2 migration."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--legacy-ref', help='Git revision whose item bank is retained for legacy v2 records')
args = parser.parse_args()
canonical = ROOT / 'curriculum/pilot-10.json'
bank = json.loads(canonical.read_text())
if args.legacy_ref:
    previous = json.loads(subprocess.check_output(
        ['git', 'show', f'{args.legacy_ref}:vocabulary-planning/curriculum/pilot-10.json'],
        cwd=ROOT.parent, text=True))
    bank['previous_version'] = previous['version']
    bank['previous_items'] = previous['items']
    canonical.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n')
target = ROOT / 'prototype/pilot-flow.html'
payload = json.dumps(bank, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
pattern = r'(<script type="application/json" id="curriculum-data">)[\s\S]*?(</script>)'
source, count = re.subn(pattern, lambda match: match[1] + payload + match[2], target.read_text())
if count != 1:
    raise ValueError('Expected exactly one embedded curriculum block')
target.write_text(source)
print(json.dumps({'objective_items': len(bank['items']),
                  'legacy_snapshot_items': len(bank.get('previous_items', [])),
                  'html_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}))
