#!/usr/bin/env node
// Exercise the real structural entry point on isolated, mutated contract copies.
// Reference directories are read-only links; tests never edit the source checkout.
import { mkdtempSync, mkdirSync, copyFileSync, readFileSync, writeFileSync, readdirSync, symlinkSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const fixture = mkdtempSync(join(tmpdir(), 'fabius-structural-'));
const file = 'skills/fabius-disciplina/SKILL.md';
const original = readFileSync(join(root, file), 'utf8');
const removeKey = (s, key) => s.replace(new RegExp(`^${key}:[^\\n]*\\n(?:[ \\t]+[^\\n]*\\n)*`, 'm'), '');
const cases = [
  ['missing trigger', s => removeKey(s, 'when_to_use'), /FAIL\s+frontmatter: keys canonical/],
  ['missing license', s => removeKey(s, 'license'), /FAIL\s+frontmatter: license matches/],
  ['missing metadata', s => removeKey(s, 'metadata'), /FAIL\s+frontmatter: metadata carries/],
  ['duplicate name', s => s.replace('name: fabius-disciplina', 'name: fabius-disciplina\nname: fabius-disciplina'), /FAIL\s+frontmatter: keys canonical/],
  ['empty trigger', s => s.replace(/when_to_use: >\n(?:  [^\n]*\n)+/, 'when_to_use: ""\n'), /FAIL\s+frontmatter: keys canonical/],
  ['empty author', s => s.replace('author: shear559', 'author: ""'), /FAIL\s+frontmatter: metadata carries/],
  ['duplicate author', s => s.replace('author: shear559', 'author: shear559\n  author: shear559'), /FAIL\s+frontmatter: metadata carries/],
  ['null author', s => s.replace('author: shear559', 'author: null'), /FAIL\s+frontmatter: metadata carries/],
  ['commented null author', s => s.replace('author: shear559', 'author: null # restore author'), /FAIL\s+frontmatter: metadata carries/],
  ['commented empty author', s => s.replace('author: shear559', 'author: "" # restore author'), /FAIL\s+frontmatter: metadata carries/],
  ['collection trigger', s => s.replace(/when_to_use: >\n(?:  [^\n]*\n)+/, 'when_to_use: []\n'), /FAIL\s+frontmatter: keys canonical/],
  ['comment-only trigger', s => s.replace(/when_to_use: >\n(?:  [^\n]*\n)+/, 'when_to_use: # add triggers\n'), /FAIL\s+frontmatter: keys canonical/],
  ['unknown key', s => s.replace('license: UNLICENSED', 'model: unavailable\nlicense: UNLICENSED'), /FAIL\s+frontmatter: keys canonical/],
  ['license mismatch', s => s.replace('license: UNLICENSED', 'license: MIT'), /FAIL\s+frontmatter: license matches/],
  ['description exceeds byte budget', s => s.replace(/description: >\n(?:  [^\n]*\n)+/, `description: >\n  ${'界'.repeat(350)}\n`), /FAIL\s+frontmatter: every flattened description/],
];

const run = () => {
  const r = spawnSync(process.execPath, [join(root, 'evals/structural.mjs')], {
    env: { ...process.env, FABIUS_VERIFY_ROOT: fixture }, encoding: 'utf8', timeout: 20000,
  });
  assert.equal(r.error, undefined, r.error?.message);
  assert.ok(r.status !== null, 'structural process must finish');
  return { status: r.status, text: `${r.stdout}\n${r.stderr}` };
};

try {
  for (const dir of ['skills', '.claude-plugin', 'provenance']) mkdirSync(join(fixture, dir));
  for (const name of readdirSync(join(root, 'skills'))) {
    mkdirSync(join(fixture, 'skills', name));
    copyFileSync(join(root, 'skills', name, 'SKILL.md'), join(fixture, 'skills', name, 'SKILL.md'));
    symlinkSync(join(root, 'skills', name, 'references'), join(fixture, 'skills', name, 'references'));
  }
  for (const f of ['README.md', 'AGENTS.md', 'ARCHITECTURE.md', 'CORPUS.md',
    '.claude-plugin/plugin.json', '.claude-plugin/plugin-index.json', '.claude-plugin/marketplace.json', 'provenance/seal-manifest.json']) {
    copyFileSync(join(root, f), join(fixture, f));
  }
  // Source may be under development before resealing. Frontmatter must still be valid.
  const baseline = run();
  assert.ok(!/FAIL\s+frontmatter:/.test(baseline.text), baseline.text);
  console.log('PASS valid source frontmatter');
  let failed = 0;
  for (const [name, mutate, failure] of cases) {
    const changed = mutate(original);
    assert.notEqual(changed, original, `${name}: mutation must apply`);
    writeFileSync(join(fixture, file), changed);
    const result = run();
    const pass = result.status !== 0 && failure.test(result.text);
    console.log(`${pass ? 'PASS' : 'FAIL'} ${name}: rejected by its intended frontmatter check`);
    if (!pass) failed++;
    writeFileSync(join(fixture, file), original);
  }
  console.log(`${cases.length + 1 - failed}/${cases.length + 1} structural controls passed`);
  process.exitCode = failed ? 1 : 0;
} finally {
  rmSync(fixture, { recursive: true, force: true });
}
