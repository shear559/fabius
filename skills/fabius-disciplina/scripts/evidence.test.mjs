import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validatePlan, assessEvidence, hashPlan } from './evidence.mjs';

const hash = value => createHash('sha256').update(value).digest('hex');
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'fabius-evidence-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  writeFileSync(join(root, 'source.js'), 'export const answer = 42;\n');
  writeFileSync(join(root, 'test.log'), '1 test passed\n');
  const plan = { schema: 'fabius-plan/v1', goal: 'Return the specified answer',
    sources: ['source.js'], criteria: [{ id: 'answer', expectation: 'answer equals 42', checks: ['unit'] }],
    checks: [{ id: 'unit', command: 'node --test', covers: ['source.js'] }] };
  const report = { schema: 'fabius-evidence/v1', planSha256: hashPlan(plan),
    sources: [{ path: 'source.js', sha256: hash('export const answer = 42;\n') }],
    checks: [{ id: 'unit', status: 'passed', exitCode: 0, observation: 'The assertion returned 42.',
      log: { path: 'test.log', sha256: hash('1 test passed\n') } }] };
  return { root, plan, report };
}
test('fresh source and log hashes satisfy the recorded acceptance map', t => {
  const f = fixture(t);
  assert.equal(assessEvidence(f.plan, f.report, { root: f.root }).status, 'complete');
});
test('changed source invalidates previously passing evidence', t => {
  const f = fixture(t); writeFileSync(join(f.root, 'source.js'), 'export const answer = 41;\n');
  const result = assessEvidence(f.plan, f.report, { root: f.root });
  assert.equal(result.status, 'incomplete');
  assert.match(result.issues.join(' '), /source changed/);
});
test('altered logs cannot reuse a receipt hash', t => {
  const f = fixture(t); writeFileSync(join(f.root, 'test.log'), '1 test failed\n');
  assert.match(assessEvidence(f.plan, f.report, { root: f.root }).issues.join(' '), /log changed/);
});
test('skipped and absent checks leave criteria incomplete', t => {
  const f = fixture(t); f.report.checks[0] = { id: 'unit', status: 'skipped', reason: 'runner unavailable' };
  assert.equal(assessEvidence(f.plan, f.report, { root: f.root }).status, 'incomplete');
  f.report.checks = [];
  assert.match(assessEvidence(f.plan, f.report, { root: f.root }).issues.join(' '), /missing check/);
});
test('failed and inconsistent exit status cannot be called complete', t => {
  const f = fixture(t); f.report.checks[0].status = 'failed'; f.report.checks[0].exitCode = 1;
  assert.equal(assessEvidence(f.plan, f.report, { root: f.root }).status, 'failed');
  f.report.checks[0].status = 'passed';
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /passed.*exitCode/);
});
test('plan rejects unmapped source, nonexistent check, duplicate id and empty criterion', t => {
  const f = fixture(t);
  for (const mutate of [p => p.sources.push('uncovered.js'), p => p.criteria[0].checks.push('unknown'),
    p => p.checks.push(p.checks[0]), p => p.criteria[0].checks = []]) {
    const p = structuredClone(f.plan); mutate(p); assert.throws(() => validatePlan(p));
  }
});
test('extra checks cannot silently stand in for planned ones', t => {
  const f = fixture(t); f.report.checks[0].id = 'unplanned';
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /unplanned/);
});
test('hashes must be exact SHA256 and observations nonempty', t => {
  const f = fixture(t); f.report.sources[0].sha256 = 'abc';
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /sha256/);
  f.report.sources[0].sha256 = hash('export const answer = 42;\n');
  f.report.checks[0].observation = '';
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /observation/);
});
test('traversal, absolute, hidden and secret source paths are rejected', t => {
  const f = fixture(t);
  for (const path of ['../outside', '/etc/hosts', '.env', '.git/config', 'private.key', 'a\\b', 'a//b']) {
    const p = structuredClone(f.plan); p.sources = [path]; p.checks[0].covers = [path];
    assert.throws(() => validatePlan(p), /path/);
  }
});
test('symlinks cannot make a selected source read an unrelated file', t => {
  const f = fixture(t); rmSync(join(f.root, 'source.js'));
  symlinkSync(join(f.root, 'test.log'), join(f.root, 'source.js'));
  const result = assessEvidence(f.plan, f.report, { root: f.root });
  assert.equal(result.status, 'incomplete'); assert.match(result.issues.join(' '), /symlink/);
});
test('duplicate source or check evidence is rejected', t => {
  const f = fixture(t); f.report.sources.push(f.report.sources[0]);
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /duplicate/);
});
test('changed acceptance criteria invalidate an otherwise fresh report', t => {
  const f = fixture(t); f.plan.criteria[0].expectation = 'answer equals 43';
  assert.match(assessEvidence(f.plan, f.report, { root: f.root }).issues.join(' '), /plan changed/);
});
test('inherited plan and nested criterion fields cannot bypass plan binding', t => {
  const f = fixture(t);
  assert.throws(() => hashPlan(Object.create(f.plan)), /plain.*JSON/);
  f.plan.criteria[0] = Object.create(f.plan.criteria[0]);
  assert.throws(() => hashPlan(f.plan), /plain.*JSON/);
});
test('inherited report and nested log fields are rejected', t => {
  const f = fixture(t);
  assert.throws(() => assessEvidence(f.plan, Object.create(f.report), { root: f.root }), /plain.*JSON/);
  f.report.checks[0].log = Object.create(f.report.checks[0].log);
  assert.throws(() => assessEvidence(f.plan, f.report, { root: f.root }), /plain.*JSON/);
});
test('plan and report accessors are rejected without calling them', t => {
  const f = fixture(t); let calls = 0;
  for (const field of ['plan', 'report']) {
    const p = structuredClone(f.plan), r = structuredClone(f.report);
    const target = field === 'plan' ? p.criteria[0] : r.checks[0];
    const key = field === 'plan' ? 'expectation' : 'observation';
    const value = target[key];
    Object.defineProperty(target, key, { enumerable: true, get() { calls++; return value; } });
    assert.throws(() => assessEvidence(p, r, { root: f.root }), /data properties/);
  }
  assert.equal(calls, 0);
});
test('proxy inputs are rejected before inspecting their traps', t => {
  const f = fixture(t); let calls = 0;
  const wrapped = new Proxy(f.plan, { getPrototypeOf(target) { calls++; return Reflect.getPrototypeOf(target); }, ownKeys(target) { calls++; return Reflect.ownKeys(target); } });
  assert.throws(() => hashPlan(wrapped), /plain.*JSON/);
  assert.equal(calls, 0);
});
test('sparse arrays, accessor entries and custom array prototypes are rejected', t => {
  const f = fixture(t); let calls = 0;
  const sparse = structuredClone(f.plan); sparse.sources = new Array(1);
  assert.throws(() => hashPlan(sparse), /dense.*array/);
  const accessor = structuredClone(f.plan);
  Object.defineProperty(accessor.sources, '0', { enumerable: true, get() { calls++; return 'source.js'; } });
  assert.throws(() => hashPlan(accessor), /data properties/); assert.equal(calls, 0);
  const custom = structuredClone(f.plan); Object.setPrototypeOf(custom.sources, Object.create(Array.prototype));
  assert.throws(() => hashPlan(custom), /plain.*JSON/);
});
test('hidden, symbolic and non-JSON data are rejected instead of disappearing from hashes', t => {
  const f = fixture(t);
  for (const alter of [p => Object.defineProperty(p, 'goal', { enumerable: false, value: p.goal }),
    p => p[Symbol('hidden')] = true, p => p.goal = undefined, p => p.goal = NaN,
    p => p.goal = () => 'goal', p => p.goal = 1n]) {
    const p = structuredClone(f.plan); alter(p); assert.throws(() => hashPlan(p), /JSON|data properties/);
  }
});
test('validation returns an independent snapshot and preserves canonical JSON hash order', t => {
  const f = fixture(t), originalHash = hashPlan(f.plan);
  const reversed = Object.fromEntries(Object.entries(f.plan).reverse());
  assert.equal(hashPlan(reversed), originalHash);
  const checked = validatePlan(f.plan); f.plan.criteria[0].expectation = 'changed';
  assert.equal(hashPlan(checked), originalHash); assert.notEqual(hashPlan(f.plan), originalHash);
});
test('missing source errors contain relative paths and error codes only', t => {
  const f = fixture(t); rmSync(join(f.root, 'source.js'));
  const result = assessEvidence(f.plan, f.report, { root: f.root });
  assert.equal(result.status, 'incomplete');
  assert.deepEqual(result.issues, ['source unavailable: source.js (ENOENT)']);
  assert.equal(JSON.stringify(result).includes(f.root), false);
});
const cli = fileURLToPath(new URL('./evidence.mjs', import.meta.url));
function runCli(args) { return spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', timeout: 10000 }); }
test('CLI accepts valid plain JSON while rejecting symlink inputs, including oversized targets', t => {
  const f = fixture(t), path = join(f.root, 'plan.json'), link = join(f.root, 'linked.json');
  writeFileSync(path, JSON.stringify(f.plan));
  assert.equal(runCli(['plan', path]).status, 0);
  symlinkSync(path, link); const linked = runCli(['plan', link]);
  assert.equal(linked.status, 2); assert.match(linked.stderr, /symlink/);
  writeFileSync(path, JSON.stringify(f.plan) + ' '.repeat(1024 * 1024));
  assert.equal(runCli(['plan', path]).status, 2);
  assert.equal(runCli(['plan', link]).status, 2);
});
test('CLI bounds bytes actually read when file metadata understates input size', t => {
  const f = fixture(t), path = join(f.root, 'large.json');
  writeFileSync(path, JSON.stringify(f.plan) + ' '.repeat(1024 * 1024));
  const script = `import fs from 'node:fs'; import { syncBuiltinESMExports } from 'node:module'; import { pathToFileURL } from 'node:url';
    for (const name of ['lstatSync', 'fstatSync']) { const original = fs[name]; fs[name] = (...args) => { const stat = original(...args); Object.defineProperty(stat, 'size', { value: 0 }); return stat; }; }
    syncBuiltinESMExports(); const [modulePath, input] = process.argv.slice(1); process.argv = [process.execPath, modulePath, 'plan', input]; await import(pathToFileURL(modulePath).href);`;
  const result = spawnSync(process.execPath, ['--input-type=module', '-e', script, cli, path], { encoding: 'utf8', timeout: 10000 });
  assert.equal(result.status, 2); assert.match(result.stderr, /exceeds 1 MiB/);
});
test('CLI filesystem and JSON parse failures do not echo private paths or input fragments', t => {
  const f = fixture(t), missing = join(f.root, 'missing.json');
  const absent = runCli(['plan', missing]);
  assert.equal(absent.status, 2); assert.match(absent.stderr, /ENOENT/); assert.equal(absent.stderr.includes(f.root), false);
  const directory = runCli(['plan', f.root]);
  assert.equal(directory.status, 2); assert.match(directory.stderr, /regular file/); assert.equal(directory.stderr.includes(f.root), false);
  const invalid = join(f.root, 'invalid.json'), marker = 'synthetic-private-test-marker'; writeFileSync(invalid, marker);
  const malformed = runCli(['plan', invalid]);
  assert.equal(malformed.status, 2); assert.match(malformed.stderr, /valid JSON/); assert.equal(malformed.stderr.includes(marker), false);
});
