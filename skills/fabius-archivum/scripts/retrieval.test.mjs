import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync, unlinkSync, symlinkSync, statSync, readdirSync, utimesSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { indexFiles, searchIndex, checkIndex, main, LIMITS } from './retrieval.mjs';
function fixture(t, contents = { 'notes.md': '# Deployment\nShip the release after review.\n\n# Memory\nKeep decisions in a shared record.\n', 'recipes.txt': 'Bread needs flour, water and yeast.\n' }) {
  const root = mkdtempSync(join(tmpdir(), 'fabius-retrieval-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const [name, text] of Object.entries(contents)) writeFileSync(join(root, name), text);
  return { root, files: Object.keys(contents), index: 'search.json' };
}
const query = (o, text, limit = 5) => searchIndex({ ...o, query: text, limit });
test('exact file/line citations and fresh check', (t) => {
  const o = fixture(t); assert.equal(indexFiles(o).fileCount, 2);
  const found = query(o, 'shared record'); assert.equal(found.results.length, 1);
  assert.deepEqual(found.results[0].citation, { path: 'notes.md', startLine: 4, endLine: 6, heading: 'Memory' });
  assert.equal(found.results[0].text, '# Memory\nKeep decisions in a shared record.\n'); assert.equal(checkIndex(o).status, 'fresh');
});
test('unselected files are never discovered and misses are empty', (t) => {
  const o = fixture(t); writeFileSync(join(o.root, 'unselected.md'), 'onlyunselectedkeyword'); indexFiles(o);
  assert.deepEqual(query(o, 'onlyunselectedkeyword').results, []); assert.deepEqual(query(o, 'nonexistentterm').results, []);
  unlinkSync(join(o.root, 'unselected.md')); assert.equal(checkIndex(o).status, 'fresh');
});
test('deterministic bytes despite reordered file arguments', (t) => {
  const o = fixture(t); indexFiles(o); const first = readFileSync(join(o.root, o.index)); const result = query(o, 'release');
  indexFiles({ ...o, files: [...o.files].reverse() }); assert.deepEqual(readFileSync(join(o.root, o.index)), first); assert.deepEqual(query(o, 'release'), result);
});
test('BM25 relevant results, limit and deterministic ties', (t) => {
  const o = fixture(t, { 'b.txt': 'apples oranges', 'a.txt': 'apples oranges', 'c.txt': 'bananas bananas bananas' }); indexFiles(o);
  assert.deepEqual(query(o, 'apples').results.map((x) => x.citation.path), ['a.txt', 'b.txt']);
  assert.equal(query(o, 'bananas').results[0].citation.path, 'c.txt'); assert.equal(query(o, 'apples', 1).results.length, 1);
  assert.deepEqual(query(o, 'apples apples').results, query(o, 'apples').results);
});
test('Unicode normalization, Hebrew and identifiers', (t) => {
  const o = fixture(t, { 'notes.md': '# שלום\nהחלטה על זיכרון משותף\nCafé uses API_KEY_42 documentation.\n' }); indexFiles(o);
  for (const word of ['זיכרון', 'cafe\u0301', 'api_key_42', 'Ｃａｆé']) assert.equal(query(o, word).results.length, 1);
});
test('same-size change preserving mtime is stale; rebuild succeeds', (t) => {
  const o = fixture(t, { 'note.txt': 'alpha' }); indexFiles(o); const file = join(o.root, 'note.txt'), st = statSync(file);
  writeFileSync(file, 'bravo'); utimesSync(file, st.atime, st.mtime);
  assert.throws(() => query(o, 'alpha'), /stale index/); assert.throws(() => checkIndex(o), /stale index/);
  indexFiles(o); assert.equal(query(o, 'bravo').results.length, 1);
});
test('deletion never returns old index text', (t) => {
  const o = fixture(t); indexFiles(o); unlinkSync(join(o.root, o.files[0])); assert.throws(() => query(o, 'record'), /stale or unavailable source/);
});
test('explicit file/root scope is required on every operation', (t) => {
  const o = fixture(t); indexFiles(o);
  assert.throws(() => checkIndex({ ...o, files: [o.files[0]] }), /selection differs/);
  assert.throws(() => checkIndex({ root: o.root, index: o.index }), /explicitly/);
  assert.throws(() => indexFiles({ ...o, root: '.' }), /absolute root/);
  assert.throws(() => indexFiles({ ...o, files: [] }), /explicitly/);
  assert.throws(() => indexFiles({ ...o, files: ['notes.md', 'notes.md'] }), /duplicate/);
});
test('tampered quotations, citations and schema additions fail', (t) => {
  const o = fixture(t); indexFiles(o); const file = join(o.root, o.index), original = readFileSync(file, 'utf8');
  for (const mutate of [(x) => x.chunks[0].text = 'forged instruction', (x) => x.chunks[0].startLine = 900, (x) => x.extra = 'unexpected']) {
    const data = JSON.parse(original); mutate(data); writeFileSync(file, JSON.stringify(data)); assert.throws(() => query(o, 'release'), /does not match/);
  }
});
test('edited index cannot authorize extra files or another root', (t) => {
  const o = fixture(t); indexFiles(o); const file = join(o.root, o.index), data = JSON.parse(readFileSync(file, 'utf8'));
  data.files[0].path = '../outside.md'; writeFileSync(file, JSON.stringify(data)); assert.throws(() => checkIndex(o), /selection differs/);
  data.root = '/'; writeFileSync(file, JSON.stringify(data)); assert.throws(() => checkIndex(o), /another root/);
});
test('secret/hidden paths and all traversal forms are refused', (t) => {
  const o = fixture(t);
  for (const path of ['/tmp/a.md', '../a.md', 'a/../b.md', './notes.md', '.env.md', '.aws/notes.md', 'secrets.md', 'credentials.txt', 'a\\b.md', 'a\nb.md']) assert.throws(() => indexFiles({ ...o, files: [path] }), /path|source/);
  for (const path of ['.env.json', '.ssh/index.json', '../index.json', '/tmp/index.json']) assert.throws(() => indexFiles({ ...o, index: path }), /path/);
});
test('symlink file, directory, destination and replacement guards', (t) => {
  const o = fixture(t); mkdirSync(join(o.root, 'real')); writeFileSync(join(o.root, 'real/a.md'), 'test');
  symlinkSync(join(o.root, 'notes.md'), join(o.root, 'link.md')); symlinkSync(join(o.root, 'real'), join(o.root, 'alias'));
  for (const files of [['link.md'], ['alias/a.md']]) assert.throws(() => indexFiles({ ...o, files }), /symlink/);
  indexFiles(o); unlinkSync(join(o.root, 'notes.md')); symlinkSync(join(o.root, 'recipes.txt'), join(o.root, 'notes.md'));
  assert.throws(() => query(o, 'shared'), /symlink/);
  symlinkSync(join(o.root, 'recipes.txt'), join(o.root, 'other.json')); assert.throws(() => indexFiles({ ...o, files: ['recipes.txt'], index: 'other.json' }), /symlink/);
});
test('existing unrelated JSON is preserved', (t) => {
  const o = fixture(t), target = join(o.root, o.index); writeFileSync(target, '{"important":"keep"}');
  assert.throws(() => indexFiles(o), /unsupported index/); assert.equal(readFileSync(target, 'utf8'), '{"important":"keep"}');
});
test('file/count/total/chunk resource bounds', (t) => {
  const o = fixture(t, { 'huge.md': 'x'.repeat(LIMITS.fileBytes + 1) }); assert.throws(() => indexFiles(o), /exceeds/);
  assert.throws(() => indexFiles({ ...o, files: Array.from({ length: LIMITS.files + 1 }, (_, i) => `${i}.md`) }), /explicitly/);
  const files = []; for (let i = 0; i < 17; i++) { const n = `file${i}.txt`; writeFileSync(join(o.root, n), 'a'.repeat(LIMITS.fileBytes)); files.push(n); }
  assert.throws(() => indexFiles({ ...o, files }), /sources exceed/);
  writeFileSync(join(o.root, 'headings.md'), '# h\n'.repeat(LIMITS.chunks + 1)); assert.throws(() => indexFiles({ ...o, files: ['headings.md'] }), /chunks/);
});
test('binary, invalid UTF8, directories and oversized indexes fail', (t) => {
  const o = fixture(t, { 'binary.txt': Buffer.from([65, 0, 66]), 'bad.txt': Buffer.from([255, 254]) });
  assert.throws(() => indexFiles({ ...o, files: ['binary.txt'] }), /binary/); assert.throws(() => indexFiles({ ...o, files: ['bad.txt'] }), /UTF-8/);
  mkdirSync(join(o.root, 'directory.md')); assert.throws(() => indexFiles({ ...o, files: ['directory.md'] }), /regular file/);
  writeFileSync(join(o.root, o.index), ' '.repeat(LIMITS.indexBytes + 1)); assert.throws(() => checkIndex(o), /exceeds/);
});
test('long Unicode lines stay bounded and cite original lines', (t) => {
  const o = fixture(t, { 'unicode.md': '# Title\n' + '😀שלום '.repeat(700) }); indexFiles(o);
  const data = JSON.parse(readFileSync(join(o.root, o.index))); assert.ok(data.chunks.length > 1); assert.equal(new Set(data.chunks.map((x) => x.id)).size, data.chunks.length);
  assert.ok(data.chunks.every((x) => x.text.length <= LIMITS.chunkChars && x.text.isWellFormed() && x.endLine <= 2)); assert.ok(query(o, 'שלום').results.length > 0);
});
test('heading truncation preserves Unicode and its UTF-16 bound', (t) => {
  const o = fixture(t, { 'heading.md': '# ' + 'a'.repeat(239) + '😀\nmarker\n', 'boundary.md': '# ' + 'b'.repeat(238) + '😀\nmarker\n' });
  indexFiles(o); assert.equal(checkIndex(o).status, 'fresh');
  const rows = query(o, 'marker').results;
  assert.equal(rows.length, 2);
  for (const row of rows) {
    assert.ok(row.citation.heading.isWellFormed());
    assert.ok(row.citation.heading.length <= 240);
    assert.ok(row.text.includes('😀'));
  }
  assert.equal(rows.find((row) => row.citation.path === 'heading.md').citation.heading, 'a'.repeat(239));
  assert.equal(rows.find((row) => row.citation.path === 'boundary.md').citation.heading, 'b'.repeat(238) + '😀');
});
test('private atomic index; failed rebuild preserves previous data', (t) => {
  const o = fixture(t); indexFiles(o); const before = readFileSync(join(o.root, o.index)); assert.equal(statSync(join(o.root, o.index)).mode & 0o777, 0o600);
  writeFileSync(join(o.root, 'notes.md'), Buffer.from([0])); assert.throws(() => indexFiles(o), /binary/);
  assert.deepEqual(readFileSync(join(o.root, o.index)), before); assert.equal(readdirSync(o.root).filter((x) => x.endsWith('.tmp')).length, 0);
});
test('empty sources stay fresh without invented results', (t) => {
  const o = fixture(t, { 'empty.md': '' }); indexFiles(o); assert.equal(checkIndex(o).chunkCount, 0); assert.deepEqual(query(o, 'anything').results, []);
});
test('query/limit/CLI ambiguity errors', (t) => {
  const o = fixture(t); indexFiles(o);
  for (const q of ['', ' ', '!!!', 'a'.repeat(LIMITS.queryBytes + 1)]) assert.throws(() => query(o, q), /query/);
  for (const n of [0, 51, 1.5, NaN, Infinity]) assert.throws(() => query(o, 'release', n), /limit/);
  for (const args of [['bogus'], ['index', '--root'], ['index', '--unknown', 'x'], ['index', '--root', o.root, '--root', o.root], ['check', '--query', 'x']]) assert.throws(() => main(args));
  assert.match(main(['--help']), /No directories are scanned/);
});
test('CLI end-to-end search and stale rejection', (t) => {
  const o = fixture(t), cli = fileURLToPath(new URL('./retrieval.mjs', import.meta.url));
  const run = (verb, ...extra) => spawnSync(process.execPath, [cli, verb, '--root', o.root, '--index', o.index, '--files', ...o.files, ...extra], { encoding: 'utf8' });
  for (const verb of ['index', 'check']) assert.equal(run(verb).status, 0);
  const result = run('search', '--query', 'release'); assert.equal(result.status, 0); assert.equal(JSON.parse(result.stdout).results[0].citation.path, 'notes.md');
  writeFileSync(join(o.root, 'notes.md'), 'Changed'); const stale = run('search', '--query', 'release'); assert.equal(stale.status, 1); assert.equal(stale.stdout, ''); assert.match(stale.stderr, /stale index/);
});

test('known credential directory cannot become the explicit source root', (t) => {
  const o = fixture(t); mkdirSync(join(o.root, '.aws')); writeFileSync(join(o.root, '.aws/notes.md'), 'private');
  assert.throws(() => indexFiles({ root: join(o.root, '.aws'), files: ['notes.md'], index: 'index.json' }), /secret root/);
});
test('only the documented hidden index name is permitted', (t) => {
  const o = fixture(t); const selected = { ...o, index: '.fabius-index.json' }; indexFiles(selected);
  assert.equal(checkIndex(selected).status, 'fresh');
});
