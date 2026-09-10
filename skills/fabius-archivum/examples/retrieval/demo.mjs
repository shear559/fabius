import { mkdtempSync, copyFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import assert from 'node:assert/strict';
const root = mkdtempSync(join(tmpdir(), 'fabius-retrieval-demo-'));
try {
  const files = ['decisions.md', 'operations.txt'];
  for (const file of files) copyFileSync(fileURLToPath(new URL(file, import.meta.url)), join(root, file));
  const cli = fileURLToPath(new URL('../../scripts/retrieval.mjs', import.meta.url));
  const invoke = (verb, extra = []) => {
    const r = spawnSync(process.execPath, [cli, verb, '--root', root, '--index', 'index.json', '--files', ...files, ...extra], { encoding: 'utf8' });
    assert.equal(r.status, 0, r.stderr);
    return JSON.parse(r.stdout);
  };
  const built = invoke('index');
  assert.equal(invoke('check').status, 'fresh');
  const result = invoke('search', ['--query', 'release authority', '--limit', '1']);
  assert.equal(result.results[0].citation.path, 'decisions.md');
  assert.equal(result.results[0].citation.startLine, 1);
  console.log(JSON.stringify({ files: built.fileCount, chunks: built.chunkCount, fresh: true, result: result.results[0] }, null, 2));
} finally { rmSync(root, { recursive: true, force: true }); }
