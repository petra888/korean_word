import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(root, 'prototype/pilot-flow.html'));
const sha256 = createHash('sha256').update(source).digest('hex');
const validation = JSON.parse(readFileSync(join(root, 'qa/release-readiness/validation-summary.json'), 'utf8'));
assert.equal(validation.status, 'pass', 'The release must be verified before deployment.');
assert.equal(validation.html_sha256, sha256, 'HTML differs from the verified release.');
const bank = JSON.parse(readFileSync(join(root, 'curriculum/pilot-10.json'), 'utf8'));
const embedded = source.toString().match(/<script type="application\/json" id="curriculum-data">([\s\S]*?)<\/script>/);
assert.ok(embedded, 'Embedded curriculum is missing.');
assert.deepEqual(JSON.parse(embedded[1]), bank, 'Embedded curriculum differs from the source.');
assert.equal(bank.words.length, 10);
assert.equal(bank.items.length, 160);

let commit = null;
let dirty = null;
if (/^[a-f0-9]{40}$/.test(process.env.VERCEL_GIT_COMMIT_SHA ?? '')) {
  commit = process.env.VERCEL_GIT_COMMIT_SHA;
  dirty = false;
} else {
  try {
    const options = { cwd: join(root, '..'), encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] };
    commit = execFileSync('git', ['rev-parse', 'HEAD'], options).trim();
    dirty = Boolean(execFileSync('git', ['status', '--porcelain'], options).trim());
  } catch { /* Non-Git builds still retain the verified content hash. */ }
}
const output = join(root, 'deploy/demo-site');
mkdirSync(output, { recursive: true });
assert.ok(readdirSync(output).every(name => ['index.html', 'release-manifest.json'].includes(name)), 'Unexpected public files.');
writeFileSync(join(output, 'index.html'), source);
writeFileSync(join(output, 'release-manifest.json'), JSON.stringify({
  release: 'v5.1-demo', mode: 'fictional staff review demo',
  html_sha256: sha256, source_commit: commit, source_has_uncommitted_changes: dirty,
  word_count: bank.words.length, objective_items: bank.items.length, storage_schema: 2,
  data_storage: 'browser localStorage; no cross-device or per-student server storage',
  deployment_provider: 'Vercel', deployment_target: 'Preview',
  hosting_access: 'Vercel project deployment protection',
  real_student_pilot_ready: false, content_approval: bank.status,
  actual_browser_mobile_print: validation.actual_browser_mobile_print,
  deferred_by_user: ['actual device QA', 'printing QA'], verified_checks: validation.checks,
}, null, 2) + '\n');
console.log(JSON.stringify({ output, html_sha256: sha256, source_commit: commit, public_files: 2 }));
