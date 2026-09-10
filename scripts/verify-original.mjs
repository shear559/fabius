#!/usr/bin/env node
// Package/coverage assertions, not a legal-originality or authorship detector.
import { existsSync, readFileSync, lstatSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const relativePath = value => typeof value === 'string' && value.length > 0 && !/[\\:\x00-\x1f]/.test(value) && value.split('/').every(p => p && p !== '.' && p !== '..');
const expected = ['agent-workflows', 'local-retrieval', 'design-and-scenes', 'engineering-evidence'];
export function verifyOriginal(base) {
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  const read = path => JSON.parse(readFileSync(join(base, path), 'utf8'));
  try {
    const map = read('credits/capabilities.json'), retired = read('credits/retired-upstream.json'), active = read('credits/upstream.json');
    check(map.schema === 'fabius-capabilities/v1', 'unknown capability schema');
    check(retired.schema === 'fabius-retired-sources/v1', 'unknown retired-source schema');
    check(/^[0-9a-f]{40}$/.test(retired.last_bundled_commit ?? ''), 'historical commit missing');
    check(Array.isArray(map.families) && map.families.length === expected.length && expected.every(id => map.families.some(f => f.id === id)), 'exact capability families required');
    check(Array.isArray(retired.entries) && retired.entries.length === 11, 'historical source inventory must contain eleven entries');
    check(Array.isArray(active.entries) && active.entries.every(e => e.consumed_as === 'informed-by'), 'current registry must not declare imported bundles');
    const covered = new Set();
    for (const family of map.families ?? []) {
      check(/^fabius-[a-z]+$/.test(family.owner ?? ''), 'invalid capability owner');
      check(typeof family.limits === 'string' && family.limits.length > 20, `${family.id}: limitations required`);
      check(Array.isArray(family.implements) && family.implements.length > 0, `${family.id}: behavior map required`);
      for (const field of ['code', 'tests']) check(Array.isArray(family[field]) && family[field].length > 0, `${family.id}: ${field} required`);
      for (const path of [...(family.code ?? []), ...(family.tests ?? []), family.entry]) {
        check(relativePath(path), `${family.id}: unsafe capability path`);
        if (!relativePath(path)) continue;
        const target = join(base, 'skills', family.owner, path);
        check(existsSync(target) && lstatSync(target).isFile() && !lstatSync(target).isSymbolicLink(), `${family.id}: missing or non-file ${path}`);
      }
      for (const id of family.retired_sources ?? []) {
        check(retired.entries.some(e => e.id === id && e.fabius_layer === family.owner), `${family.id}: unknown or mismatched retired source ${id}`);
        check(!covered.has(id), `duplicate replacement for ${id}`); covered.add(id);
      }
    }
    for (const entry of retired.entries ?? []) check(covered.has(entry.id), `retired source without replacement: ${entry.id}`);
    const oldPaths = [...(retired.entries ?? []).flatMap(e => e.fabius_paths ?? []), ...(retired.additional_retired_paths ?? [])];
    for (const path of oldPaths) {
      check(relativePath(path) && path.startsWith('skills/'), 'unsafe retired path');
      if (relativePath(path)) check(!existsSync(join(base, path)), `retired path returned: ${path}`);
    }
    check(Array.isArray(retired.additional_retired_paths) && retired.additional_retired_paths.length >= 5, 'additional imported content inventory missing');
  } catch (error) { errors.push(`invalid source inventory: ${error.message}`); }
  return errors;
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const errors = verifyOriginal(root);
  for (const error of errors) console.error(`FAIL ${error}`);
  console.log(`${errors.length ? 'FAIL' : 'PASS'} original capability package: ${errors.length} errors; not an originality proof`);
  process.exitCode = errors.length ? 1 : 0;
}
