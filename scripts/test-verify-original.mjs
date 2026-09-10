import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { verifyOriginal } from './verify-original.mjs';
const source = join(dirname(fileURLToPath(import.meta.url)), '..');
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'fabius-original-gate-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'credits'));
  const data = {};
  for (const name of ['capabilities', 'retired-upstream', 'upstream']) {
    data[name] = JSON.parse(readFileSync(join(source, `credits/${name}.json`), 'utf8'));
    writeFileSync(join(root, `credits/${name}.json`), JSON.stringify(data[name]));
  }
  for (const family of data.capabilities.families) for (const path of [...family.code, ...family.tests, family.entry]) {
    const target = join(root, 'skills', family.owner, path); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, 'original fixture');
  }
  return { root, data, save: name => writeFileSync(join(root, `credits/${name}.json`), JSON.stringify(data[name])) };
}
test('complete source map resolves without imported code', t => { assert.deepEqual(verifyOriginal(fixture(t).root), []); });
test('retired source returning is rejected', t => {
  const f = fixture(t); mkdirSync(join(f.root, f.data['retired-upstream'].entries[0].fabius_paths[0]), { recursive: true });
  assert.match(verifyOriginal(f.root).join(' '), /retired path returned/);
});
test('missing test file cannot claim replacement coverage', t => {
  const f = fixture(t), family = f.data.capabilities.families[0]; rmSync(join(f.root, 'skills', family.owner, family.tests[0]));
  assert.match(verifyOriginal(f.root).join(' '), /missing or non-file/);
});
test('unmapped sources cannot disappear from retirement', t => {
  const f = fixture(t); f.data.capabilities.families[0].retired_sources.pop(); f.save('capabilities');
  assert.match(verifyOriginal(f.root).join(' '), /without replacement/);
});
test('path escape and removal of explicit limitations fail', t => {
  const f = fixture(t); f.data.capabilities.families[0].code = ['../../bad']; delete f.data.capabilities.families[0].limits; f.save('capabilities');
  assert.match(verifyOriginal(f.root).join(' '), /unsafe capability path/); assert.match(verifyOriginal(f.root).join(' '), /limitations required/);
});
