#!/usr/bin/env node
// Original Fabius retrieval: bounded, explicit files; no network or model dependency.
import { constants, openSync, closeSync, readSync, writeFileSync, fsyncSync, renameSync, unlinkSync, lstatSync, realpathSync, existsSync, fstatSync } from 'node:fs';
import { resolve, relative, basename, isAbsolute, sep } from 'node:path';
import { createHash, randomBytes } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const SCHEMA = 'fabius-retrieval/v1';
export const LIMITS = Object.freeze({ files: 256, fileBytes: 1048576, totalBytes: 16777216, indexBytes: 33554432, chunkChars: 1800, chunks: 20000, queryBytes: 4096, results: 50 });
const hash = (value) => createHash('sha256').update(value).digest('hex');
const order = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const tokens = (text) => text.normalize('NFKC').toLowerCase().match(/[\p{L}\p{M}\p{N}_]+/gu) || [];
const fail = (message) => { throw new Error(message); };
const SECRET_LEAF = /^(?:credentials?|secrets?|id_rsa|id_ed25519|id_ecdsa|id_dsa|terraform\.tfstate)(?:\.|$)|\.(?:pem|key|p12|pfx|keystore)$/i;

function relativeName(name, source) {
  if (typeof name !== 'string' || !name || name.length > 1024 || isAbsolute(name)
      || /[\\:\x00-\x1f\x7f]/.test(name) || name.split('/').some((p) => !p || p === '.' || p === '..')) fail('expected a safe relative file path');
  const parts = name.split('/');
  if (parts.some((p) => SECRET_LEAF.test(p) || (p.startsWith('.') && !(p === basename(name) && !source && p === '.fabius-index.json')))) fail('secret or hidden paths cannot be indexed');
  if (source ? !/\.(?:md|txt)$/i.test(name) : !/\.json$/i.test(name)) fail(source ? 'source files must be .md or .txt' : 'index file must end in .json');
  return name;
}

function context({ root, files, index } = {}) {
  if (typeof root !== 'string' || !isAbsolute(root)) fail('an explicit absolute root is required');
  const canonical = realpathSync(root);
  if (canonical.split(sep).some((p) => /^(?:\.ssh|\.aws|\.gnupg|\.kube|\.git|\.docker)$/i.test(p))) fail('secret root paths cannot be indexed');
  if (!lstatSync(canonical).isDirectory()) fail('root must be a directory');
  if (!Array.isArray(files) || !files.length || files.length > LIMITS.files) fail(`select 1-${LIMITS.files} source files explicitly`);
  const selected = files.map((f) => relativeName(f, true)).sort(order);
  if (new Set(selected).size !== selected.length) fail('duplicate source file');
  return { root: canonical, files: selected, index: relativeName(index, false) };
}

// Reject every symlink below the explicitly selected root, even an internal alias.
function checkedPath(ctx, name, { missingLeaf = false } = {}) {
  const parts = name.split('/');
  let current = ctx.root;
  for (let i = 0; i < parts.length; i++) {
    current = resolve(current, parts[i]);
    let st;
    try { st = lstatSync(current); } catch (error) {
      if (missingLeaf && i === parts.length - 1 && error.code === 'ENOENT') return current;
      fail(`selected path is unavailable: ${name}`);
    }
    if (st.isSymbolicLink()) fail(`symlinks are refused: ${name}`);
    if (i < parts.length - 1 && !st.isDirectory()) fail(`parent is not a directory: ${name}`);
    if (i === parts.length - 1 && !st.isFile()) fail(`selected path is not a regular file: ${name}`);
  }
  const rel = relative(ctx.root, realpathSync(current));
  if (rel.startsWith(`..${sep}`) || rel === '..' || isAbsolute(rel)) fail('path escaped selected root');
  return current;
}

function readBounded(ctx, name, limit) {
  const target = checkedPath(ctx, name);
  const fd = openSync(target, constants.O_RDONLY | (constants.O_NOFOLLOW || 0));
  try {
    const st = fstatSync(fd);
    if (!st.isFile() || st.size > limit) fail(`file exceeds ${limit} bytes: ${name}`);
    const bytes = Buffer.alloc(Math.min(st.size + 1, limit + 1));
    let count = 0, read;
    while (count < bytes.length && (read = readSync(fd, bytes, count, bytes.length - count, null))) count += read;
    if (count > st.size || fstatSync(fd).size !== st.size) fail(`file changed while reading: ${name}`);
    if (count !== st.size) fail(`file changed while reading: ${name}`);
    return bytes.subarray(0, count);
  } finally { closeSync(fd); }
}

function decode(bytes, name) {
  if (bytes.includes(0)) fail(`binary content is refused: ${name}`);
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { fail(`source is not valid UTF-8: ${name}`); }
}

function chunksFor(text, path) {
  const chunks = [];
  let heading = '', start = 0, end = 0, rows = [], size = 0;
  const emit = () => {
    const body = rows.join('\n');
    if (body.trim()) {
      if (chunks.length >= LIMITS.chunks) fail(`selected source exceeds ${LIMITS.chunks} chunks`);
      chunks.push({ path, startLine: start, endLine: end, heading, text: body });
    }
    rows = []; size = 0;
  };
  text.split(/\r?\n/).forEach((line, index) => {
    const lineNumber = index + 1;
    const title = line.match(/^#{1,6}\s+(.+)$/u);
    if (title) {
      emit(); heading = title[1].slice(0, 240);
      // Keep the UTF-16 bound without leaving half of a surrogate pair.
      if (/[\uD800-\uDBFF]$/.test(heading)) heading = heading.slice(0, -1);
    }
    // Split oversized lines without splitting Unicode surrogate pairs. Citation
    // still points to the original line; text is an excerpt, not the whole line.
    const points = Array.from(line);
    const segments = [];
    let segment = '';
    for (const point of points) {
      if (segment.length + point.length > LIMITS.chunkChars) { segments.push(segment); segment = ''; }
      segment += point;
    }
    segments.push(segment);
    for (const part of segments) {
      if (rows.length && size + 1 + part.length > LIMITS.chunkChars) emit();
      if (!rows.length) start = lineNumber;
      rows.push(part); size += part.length + (rows.length > 1 ? 1 : 0); end = lineNumber;
      if (size >= LIMITS.chunkChars) emit();
    }
  });
  emit();
  return chunks;
}

function snapshot(ctx) {
  let total = 0;
  const files = [], chunks = [];
  for (const path of ctx.files) {
    const bytes = readBounded(ctx, path, LIMITS.fileBytes);
    total += bytes.length;
    if (total > LIMITS.totalBytes) fail(`selected sources exceed ${LIMITS.totalBytes} bytes`);
    files.push({ path, bytes: bytes.length, sha256: hash(bytes) });
    const parts = chunksFor(decode(bytes, path), path);
    for (const [ordinal, part] of parts.entries()) chunks.push({ id: hash(JSON.stringify({ ordinal, ...part })), ...part });
    if (chunks.length > LIMITS.chunks) fail(`selected sources exceed ${LIMITS.chunks} chunks`);
  }
  return { schema: SCHEMA, root: ctx.root, fingerprint: hash(JSON.stringify(files)), files, chunks };
}

function readIndex(ctx) {
  let saved;
  try { saved = JSON.parse(decode(readBounded(ctx, ctx.index, LIMITS.indexBytes), ctx.index)); }
  catch (error) { fail(`cannot read index: ${error.message}`); }
  if (saved?.schema !== SCHEMA) fail('unsupported index schema');
  if (saved.root !== ctx.root) fail('index belongs to another root');
  return saved;
}

function verified(ctx) {
  const saved = readIndex(ctx);
  if (!Array.isArray(saved.files) || JSON.stringify(saved.files.map((f) => f?.path)) !== JSON.stringify(ctx.files)) fail('index file selection differs; rebuild with the explicit selection');
  let fresh;
  try { fresh = snapshot(ctx); }
  catch (error) { fail(`stale or unavailable source: ${error.message}`); }
  if (saved.fingerprint !== fresh.fingerprint) fail('stale index: selected source bytes changed; rebuild before searching');
  // Rebuild from authorized source bytes, not stored text. A locally edited index
  // must not invent quotations/citations even if its editor recomputes a checksum.
  if (JSON.stringify(saved) !== JSON.stringify(fresh)) fail('index content does not match its sources; rebuild');
  return fresh;
}

function summary(ctx, data) {
  return { schema: SCHEMA, index: ctx.index, fingerprint: data.fingerprint, fileCount: data.files.length, chunkCount: data.chunks.length };
}

export function indexFiles(options) {
  const ctx = context(options), data = snapshot(ctx);
  const target = checkedPath(ctx, ctx.index, { missingLeaf: true });
  if (existsSync(target)) readIndex(ctx); // Do not overwrite an unrelated JSON file.
  const bytes = Buffer.from(JSON.stringify(data) + '\n');
  if (bytes.length > LIMITS.indexBytes) fail('serialized index exceeds byte limit');
  const tempName = `${ctx.index}.${randomBytes(12).toString('hex')}.tmp`;
  const temporary = checkedPath(ctx, tempName, { missingLeaf: true });
  let fd;
  try {
    fd = openSync(temporary, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | (constants.O_NOFOLLOW || 0), 0o600);
    writeFileSync(fd, bytes); fsyncSync(fd); closeSync(fd); fd = undefined;
    if (JSON.stringify(snapshot(ctx)) !== JSON.stringify(data)) fail('sources changed during index creation; retry');
    checkedPath(ctx, ctx.index, { missingLeaf: true });
    renameSync(temporary, target);
  } finally {
    if (fd !== undefined) closeSync(fd);
    if (existsSync(temporary)) unlinkSync(temporary);
  }
  return summary(ctx, data);
}

export function checkIndex(options) {
  const ctx = context(options);
  return { status: 'fresh', ...summary(ctx, verified(ctx)) };
}

export function searchIndex(options) {
  const { query, limit = 5 } = options || {};
  if (typeof query !== 'string' || !query.trim() || Buffer.byteLength(query) > LIMITS.queryBytes) fail(`query must contain 1-${LIMITS.queryBytes} UTF-8 bytes`);
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > LIMITS.results) fail(`limit must be 1-${LIMITS.results}`);
  const terms = [...new Set(tokens(query))];
  if (!terms.length) fail('query must contain a word or number');
  const ctx = context(options), data = verified(ctx);
  const docs = data.chunks.map((chunk) => {
    const words = tokens(`${chunk.path} ${chunk.heading} ${chunk.text}`);
    const counts = new Map();
    for (const word of words) counts.set(word, (counts.get(word) || 0) + 1);
    return { chunk, counts, length: words.length };
  });
  const n = docs.length, average = n ? docs.reduce((sum, doc) => sum + doc.length, 0) / n : 1;
  const df = new Map(terms.map((term) => [term, docs.filter((doc) => doc.counts.has(term)).length]));
  const results = docs.map(({ chunk, counts, length }) => {
    let score = 0;
    for (const term of terms) {
      const count = counts.get(term) || 0;
      const idf = Math.log(1 + (n - df.get(term) + 0.5) / (df.get(term) + 0.5));
      score += idf * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * length / average));
    }
    return { id: chunk.id, score, citation: { path: chunk.path, startLine: chunk.startLine, endLine: chunk.endLine, heading: chunk.heading }, text: chunk.text };
  }).filter((row) => row.score > 0).sort((a, b) => b.score - a.score || order(a.citation.path, b.citation.path) || a.citation.startLine - b.citation.startLine || order(a.id, b.id)).slice(0, limit);
  return { ...summary(ctx, data), results };
}

export function main(args = process.argv.slice(2)) {
  const [command, ...rest] = args;
  if (command === '--help' || command === 'help') {
    return 'Usage: retrieval.mjs index|check|search --root ABSOLUTE_DIR --index FILE.json --files FILE.md [FILE.txt ...] [--query TEXT] [--limit 5]\nAll files are relative to the explicit root. Search/check require the same file selection. No directories are scanned.';
  }
  if (!['index', 'search', 'check'].includes(command)) fail('expected index, search, or check; use --help');
  const options = {}, seen = new Set();
  for (let i = 0; i < rest.length; i++) {
    const flag = rest[i];
    if (!['--root', '--index', '--files', '--query', '--limit'].includes(flag) || seen.has(flag)) fail(`unknown or duplicate option: ${flag}`);
    seen.add(flag);
    if (flag === '--files') {
      options.files = [];
      while (i + 1 < rest.length && !rest[i + 1].startsWith('--')) options.files.push(rest[++i]);
    } else {
      const value = rest[++i];
      if (value === undefined || value.startsWith('--')) fail(`missing value for ${flag}`);
      options[flag.slice(2)] = flag === '--limit' ? Number(value) : value;
    }
  }
  if (command !== 'search' && (seen.has('--query') || seen.has('--limit'))) fail('query/limit apply only to search');
  return ({ index: indexFiles, check: checkIndex, search: searchIndex })[command](options);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { const result = main(); process.stdout.write(typeof result === 'string' ? result + '\n' : JSON.stringify(result, null, 2) + '\n'); }
  catch (error) { process.stderr.write(`retrieval: ${error.message}\n`); process.exitCode = 1; }
}
