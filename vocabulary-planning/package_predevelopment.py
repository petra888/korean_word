from pathlib import Path
import hashlib
import json
import zipfile
import csv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'deliverables/report-charts-v4'
files = []
for folder, suffixes in [
    ('documents', {'.md'}), ('curriculum', {'.json', '.csv'}),
    ('planning', {'.json', '.csv'}), ('prototype', {'.html', '.md'}),
    ('qa/development-readiness', {'.js'}),
]:
    files.extend(p for p in (ROOT / folder).iterdir() if p.suffix in suffixes)
files.extend([
    ROOT / 'analysis/vocabulary.json', ROOT / 'analysis/README.md',
    ROOT / 'analysis/report.md', ROOT / 'research/references.md',
    ROOT / 'research/evidence.json', ROOT / 'validate_predevelopment.py',
    ROOT / 'export_pilot_tables.py', ROOT / 'prepare_textbook_order.py',
])
files.extend(OUT.glob('*.pdf'))
files.extend([OUT / 'render-validation.json', OUT / 'README.md'])
files = sorted(set(files))
entries = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
manifest = {
    'created_date_kst': '2026-10-04',
    'scope': 'Predevelopment planning, draft content and a fictional interactive prototype',
    'content': {'words': 10, 'objective_items': 150, 'writing_prompts': 20,
                'approval_status': 'teacher_review_required'},
    'textbook_order': {'rows': 450, 'batches_of_10': 45},
    'qa_cases': len(list(csv.DictReader((ROOT/'planning/acceptance-matrix.csv').open(encoding='utf-8-sig')))),
    'development_tasks': len(list(csv.DictReader((ROOT/'planning/work-breakdown.csv').open(encoding='utf-8-sig')))),
    'report_charts': {'type': 'inline SVG donut', 'understanding_basis': 'latest confirmed teacher classification; pending otherwise', 'writing_basis': 'latest confirmed three-button judgment', 'unique_meaning_ids': True, 'comparison': 'previous confirmed report snapshot only'},
    'actual_service_qa': 'not executed',
    'actual_browser_validation': 'not executed: browser startup blocked',
    'files': entries,
}
manifest_path = OUT / 'package-manifest.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
archive = OUT / '교사 평가 부모 자료 차트 개선 자료 v4.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for p in files + [manifest_path]:
        z.write(p, p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in entries:
        assert hashlib.sha256(z.read(entry['path'])).hexdigest() == entry['sha256']
result = {'archive': archive.name, 'members': len(files) + 1,
          'bytes': archive.stat().st_size, 'integrity': 'pass',
          'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
(OUT / 'package-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False))
