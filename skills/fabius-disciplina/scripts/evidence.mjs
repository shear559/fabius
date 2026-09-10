#!/usr/bin/env node
// Original Fabius evidence ledger. Checks recorded coverage and byte freshness;
// it neither executes commands nor authenticates the origin of a test report.
import { realpathSync, lstatSync, openSync, closeSync, fstatSync, readSync, constants } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, resolve, relative } from 'node:path';
import { pathToFileURL } from 'node:url';
import { types } from 'node:util';

const requireValue = (ok, message) => { if (!ok) throw new Error(message); };
const JSON_LIMIT = 1024 * 1024;
// Validate descriptors before reading values, then work only on the copied JSON.
function jsonData(value) {
  let nodes = 0, bytes = 0;
  const charge = count => { bytes += count; requireValue(bytes <= JSON_LIMIT, 'JSON input exceeds 1 MiB'); };
  function copy(item, depth = 0) {
    requireValue(++nodes <= 100000 && depth <= 16, 'JSON input exceeds structural limits');
    if (item === null || typeof item === 'boolean' || typeof item === 'number') {
      requireValue(typeof item !== 'number' || Number.isFinite(item), 'JSON numbers must be finite');
      charge(JSON.stringify(item).length); return item;
    }
    if (typeof item === 'string') {
      requireValue(item.length <= JSON_LIMIT, 'JSON input exceeds 1 MiB');
      charge(Buffer.byteLength(JSON.stringify(item))); return item;
    }
    requireValue(item && typeof item === 'object' && !types.isProxy(item), 'input must contain plain JSON data');
    const isArray = Array.isArray(item), prototype = Object.getPrototypeOf(item);
    requireValue(isArray ? prototype === Array.prototype : prototype === Object.prototype || prototype === null, 'input must contain plain JSON data');
    const entries = Reflect.ownKeys(item).map(key => [key, Object.getOwnPropertyDescriptor(item, key)]);
    charge(2);
    if (isArray) {
      const length = Object.getOwnPropertyDescriptor(item, 'length').value;
      requireValue(length <= 200 && entries.length === length + 1, 'JSON requires dense arrays of at most 200 entries');
      const out = [];
      for (let i = 0; i < length; i++) {
        const entry = Object.getOwnPropertyDescriptor(item, String(i));
        requireValue(entry, 'JSON requires dense arrays');
        requireValue(entry.enumerable && Object.hasOwn(entry, 'value'), 'JSON requires enumerable data properties');
        if (i) charge(1);
        out.push(copy(entry.value, depth + 1));
      }
      return out;
    }
    const out = Object.create(null);
    for (let i = 0; i < entries.length; i++) {
      const [key, entry] = entries[i];
      requireValue(typeof key === 'string' && entry.enumerable && Object.hasOwn(entry, 'value'), 'JSON requires enumerable data properties');
      copy(key, depth + 1); charge(i ? 2 : 1);
      out[key] = copy(entry.value, depth + 1);
    }
    return out;
  }
  return copy(value);
}
const errorMessage = error => typeof error.code === 'string' && /^E[A-Z0-9_]+$/.test(error.code) ? error.code : error.message;
const text = (value, field) => requireValue(typeof value === 'string' && value.trim().length > 0 && value.length <= 8000, `${field} must be nonempty text (at most 8000 characters)`);
function object(value, keys, name) {
  requireValue(value && typeof value === 'object' && !Array.isArray(value), `${name} must be an object`);
  requireValue(Object.keys(value).every(k => keys.includes(k)), `${name} has unknown fields`);
}
function array(value, name, { empty = false } = {}) {
  requireValue(Array.isArray(value) && value.length <= 200 && (empty || value.length > 0), `${name} must be ${empty ? 'an' : 'a nonempty'} array of at most 200 entries`);
}
function unique(values, name) { requireValue(new Set(values).size === values.length, `${name} contains duplicate entries`); }
function id(value) { requireValue(typeof value === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(value), 'invalid id'); }
function safePath(path) {
  requireValue(typeof path === 'string' && path.length <= 1024 && !/[\\:\x00-\x1f\x7f]/.test(path)
    && path.split('/').every(part => part && !part.startsWith('.') && !/^(?:node_modules|credentials(?:\.json)?|id_rsa|id_ed25519)$/i.test(part))
    && !/\.(?:pem|key|p12|pfx)$/i.test(path), 'unsafe source or log path');
  return path;
}
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}
const planDigest = plan => sha(JSON.stringify(canonical(plan)));
export function hashPlan(plan) { return planDigest(validatePlan(plan)); }

export function validatePlan(plan) {
  plan = jsonData(plan);
  object(plan, ['schema', 'goal', 'sources', 'criteria', 'checks'], 'plan');
  requireValue(plan.schema === 'fabius-plan/v1', 'unsupported plan schema'); text(plan.goal, 'goal');
  array(plan.sources, 'sources'); plan.sources.forEach(safePath); unique(plan.sources, 'sources');
  array(plan.checks, 'checks'); array(plan.criteria, 'criteria');
  for (const check of plan.checks) {
    object(check, ['id', 'command', 'covers'], 'check'); id(check.id); text(check.command, 'command');
    array(check.covers, 'covers'); unique(check.covers, 'covers');
    requireValue(check.covers.every(p => plan.sources.includes(p)), 'check covers an unplanned source');
  }
  unique(plan.checks.map(c => c.id), 'checks');
  for (const source of plan.sources) requireValue(plan.checks.some(c => c.covers.includes(source)), `unmapped source: ${source}`);
  for (const criterion of plan.criteria) {
    object(criterion, ['id', 'expectation', 'checks'], 'criterion'); id(criterion.id); text(criterion.expectation, 'expectation');
    array(criterion.checks, 'criterion checks'); unique(criterion.checks, 'criterion checks');
    requireValue(criterion.checks.every(check => plan.checks.some(c => c.id === check)), 'criterion names an unknown check');
  }
  unique(plan.criteria.map(c => c.id), 'criteria');
  requireValue(plan.checks.every(c => plan.criteria.some(a => a.checks.includes(c.id))), 'check is not linked to a criterion');
  return plan;
}

function readBounded(path, limit, label) {
  const before = lstatSync(path);
  requireValue(!before.isSymbolicLink(), `${label} symlinks are not accepted`);
  requireValue(before.isFile(), `${label} must be a regular file`);
  requireValue(before.size <= limit, `${label} exceeds ${limit / JSON_LIMIT} MiB`);
  const fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const info = fstatSync(fd);
    requireValue(info.isFile() && info.dev === before.dev && info.ino === before.ino, `${label} file changed while opening`);
    requireValue(info.size <= limit, `${label} exceeds ${limit / JSON_LIMIT} MiB`);
    const bytes = Buffer.allocUnsafe(limit + 1); let size = 0;
    while (size <= limit) {
      const count = readSync(fd, bytes, size, bytes.length - size, null);
      if (!count) break;
      size += count;
    }
    requireValue(size <= limit, `${label} exceeds ${limit / JSON_LIMIT} MiB`);
    return bytes.subarray(0, size);
  } finally { closeSync(fd); }
}
function fileHash(root, path) {
  safePath(path);
  let current = root;
  for (const part of path.split('/')) {
    current = join(current, part);
    requireValue(!lstatSync(current).isSymbolicLink(), 'symlink evidence is not accepted');
  }
  requireValue(relative(root, realpathSync(current)) === path, 'evidence path escapes its selected root');
  return sha(readBounded(current, 16 * JSON_LIMIT, 'evidence'));
}
function digestRecord(value, name) {
  object(value, ['path', 'sha256'], name); safePath(value.path);
  requireValue(typeof value.sha256 === 'string' && /^[0-9a-f]{64}$/.test(value.sha256), `${name}.sha256 must be a full lowercase SHA256`);
}

export function assessEvidence(plan, report, { root } = {}) {
  plan = validatePlan(plan); report = jsonData(report);
  requireValue(typeof root === 'string' && root.length > 0, 'an explicit evidence root is required');
  let base;
  try { base = realpathSync(root); }
  catch (error) { throw new Error(`evidence root unavailable (${errorMessage(error)})`); }
  requireValue(lstatSync(base).isDirectory(), 'evidence root must be a directory');
  object(report, ['schema', 'planSha256', 'sources', 'checks'], 'report');
  requireValue(report.schema === 'fabius-evidence/v1', 'unsupported evidence schema');
  requireValue(typeof report.planSha256 === 'string' && /^[0-9a-f]{64}$/.test(report.planSha256), 'report.planSha256 must be a full lowercase SHA256');
  array(report.sources, 'recorded sources', { empty: true }); array(report.checks, 'recorded checks', { empty: true });
  report.sources.forEach(r => digestRecord(r, 'source'));
  unique(report.sources.map(r => r.path), 'recorded sources'); unique(report.checks.map(r => r?.id), 'recorded checks');
  requireValue(report.sources.every(r => plan.sources.includes(r.path)), 'unplanned source evidence');
  const issues = [];
  if (report.planSha256 !== planDigest(plan)) issues.push('plan changed since evidence was recorded');
  const matchFile = (record, kind) => {
    try { if (fileHash(base, record.path) !== record.sha256) issues.push(`${kind} changed: ${record.path}`); }
    catch (error) { issues.push(`${kind} unavailable: ${record.path} (${errorMessage(error)})`); }
  };
  for (const path of plan.sources) {
    const record = report.sources.find(r => r.path === path);
    if (!record) issues.push(`missing source evidence: ${path}`); else matchFile(record, 'source');
  }
  for (const result of report.checks) {
    object(result, ['id', 'status', 'exitCode', 'observation', 'log', 'reason'], 'check result'); id(result.id);
    requireValue(plan.checks.some(c => c.id === result.id), `unplanned check: ${result.id}`);
    requireValue(['passed', 'failed', 'skipped'].includes(result.status), 'unknown check status');
    if (result.status === 'skipped') {
      text(result.reason, 'skip reason');
      requireValue(result.exitCode === undefined && result.log === undefined && result.observation === undefined, 'skipped check cannot carry execution evidence');
    } else {
      requireValue(Number.isInteger(result.exitCode) && result.exitCode >= 0 && result.exitCode <= 255, 'exitCode must be an integer from 0 to 255');
      requireValue(result.status !== 'passed' || result.exitCode === 0, 'passed check must have exitCode zero');
      requireValue(result.reason === undefined, 'executed check cannot carry a skip reason');
      text(result.observation, 'observation'); digestRecord(result.log, 'log'); matchFile(result.log, 'log');
    }
  }
  for (const check of plan.checks) if (!report.checks.some(c => c.id === check.id)) issues.push(`missing check: ${check.id}`);
  const criteria = plan.criteria.map(criterion => {
    const states = criterion.checks.map(id => report.checks.find(c => c.id === id)?.status ?? 'missing');
    const status = states.includes('failed') ? 'failed' : states.every(s => s === 'passed') && issues.length === 0 ? 'complete' : 'incomplete';
    return { id: criterion.id, status };
  });
  return { status: criteria.some(c => c.status === 'failed') ? 'failed' : criteria.every(c => c.status === 'complete') ? 'complete' : 'incomplete',
    criteria, issues, boundary: 'Checks recorded coverage and current file hashes; does not prove tests ran, test quality, authorization, or authenticity of supplied reports.' };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const [command, planFile, reportFile, flag, root] = process.argv.slice(2);
    requireValue((command === 'plan' && planFile && !reportFile) || (command === 'check' && planFile && reportFile && flag === '--root' && root && process.argv.length === 7),
      'usage: evidence.mjs plan PLAN.json | check PLAN.json REPORT.json --root DIRECTORY');
    const readJson = path => {
      const bytes = readBounded(path, JSON_LIMIT, 'JSON input');
      try { return JSON.parse(bytes.toString('utf8')); }
      catch { throw new Error('JSON input must contain valid JSON'); }
    };
    const plan = readJson(planFile);
    const result = command === 'plan' ? { planSha256: hashPlan(plan) } : assessEvidence(plan, readJson(reportFile), { root });
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status && result.status !== 'complete' ? 1 : 0;
  } catch (error) { console.error(errorMessage(error)); process.exitCode = 2; }
}
