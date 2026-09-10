import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { contrast, validateTokens, validateStoryboard, tokensCSS, renderScene } from './design.mjs';
import { stateAt } from '../templates/timeline.mjs';

const tokens = {
  schema: 'fabius-design/v1',
  color: { canvas: '#f7f7f7', surface: '#ffffff', text: '#202020', muted: '#565656', border: '#707070', accent: '#394bcd', onAccent: '#ffffff', focus: '#394bcd' },
  focus: { widthPx: 2, offsetPx: 3 },
  motion: { durationMs: 240, distancePx: 16, reducedMotion: 'static', autoplay: false },
};
const board = { schema: 'fabius-storyboard/v1', title: 'Field notes', description: 'A supplied-copy storyboard.', lang: 'en', dir: 'ltr', tokens, scenes: [
  { id: 'observe', label: 'Observe', title: 'Start from evidence', body: 'Record what you can see.', durationSeconds: 4 },
  { id: 'decide', label: 'Decide', title: 'Choose one next step', body: 'Keep the decision small.', durationSeconds: 3 },
] };
const change = (fn, base = tokens) => { const value = structuredClone(base); fn(value); return value; };

test('contrast uses known black/white and identical-color reference values', () => {
  assert.equal(contrast('#000000', '#ffffff'), 21);
  assert.equal(contrast('#777777', '#777777'), 1);
  assert.ok(Math.abs(contrast('#767676', '#ffffff') - 4.542224959605253) < 1e-12);
  assert.throws(() => contrast('red', '#ffffff'), /six-digit/);
});
test('valid semantic tokens generate CSS and measured ratios', () => {
  const result = validateTokens(tokens);
  assert.equal(result.valid, true, JSON.stringify(result.issues));
  assert.equal(result.contrast.length, 9);
  assert.match(tokensCSS(tokens), /--color-accent: #394bcd;/);
});
test('rejects low text, control and focus contrast independently', () => {
  for (const role of ['text', 'muted', 'border', 'focus']) {
    const result = validateTokens(change(t => { t.color[role] = '#eeeeee'; }));
    assert.equal(result.valid, false, role);
    assert.ok(result.issues.some(i => i.path.startsWith(`color.${role}`)), role);
  }
  assert.equal(validateTokens(change(t => { t.color.onAccent = '#000000'; })).valid, false);
});
test('closed token schema rejects unsafe CSS, extra accents and invalid focus/motion', () => {
  for (const mutate of [
    t => { t.color.accent = 'red; } body { display:none'; },
    t => { t.color.accent = 12; },
    t => { t.color.extra = '#00ff00'; },
    t => { t.color.surface = '#fffafa'; },
    t => { t.focus.widthPx = 0; },
    t => { t.focus.offsetPx = -1; },
    t => { t.motion.durationMs = 600; },
    t => { t.motion.distancePx = Infinity; },
    t => { t.motion.reducedMotion = 'ignore'; },
    t => { t.motion.autoplay = true; },
    t => { t.unknown = true; },
  ]) assert.equal(validateTokens(change(mutate)).valid, false);
  assert.equal(validateTokens(null).valid, false);
  assert.throws(() => tokensCSS(change(t => { delete t.color.text; })), /Invalid design tokens/);
});
test('storyboard rejects duplicate IDs, invalid durations and unsupported fields', () => {
  assert.equal(validateStoryboard(board).valid, true);
  for (const mutate of [
    b => { b.scenes[1].id = b.scenes[0].id; },
    b => { b.scenes[0].durationSeconds = 0; },
    b => { b.scenes[0].durationSeconds = NaN; },
    b => { b.scenes[0].html = '<script>'; },
    b => { b.scenes = []; },
    b => { b.lang = 'en" onload="alert(1)'; },
    b => { b.dir = 'auto'; },
  ]) assert.equal(validateStoryboard(change(mutate, board)).valid, false);
});
test('seek is independent of history, clamps edges, selects exact scene boundaries', () => {
  const at = t => stateAt(board.scenes, t, tokens.motion);
  assert.equal(at(-1).time, 0);
  assert.equal(at(100).time, 7);
  assert.equal(at(3.999).index, 0);
  assert.equal(at(4).index, 1);
  assert.equal(at(7).index, 1);
  const middle = at(4.1);
  at(0); at(6);
  assert.deepEqual(at(4.1), middle);
  assert.ok(middle.offset > 0 && middle.offset < 16);
  assert.equal(stateAt(board.scenes, 4.1, tokens.motion, true).offset, 0);
  assert.equal(stateAt(board.scenes, 4, tokens.motion, true).opacity, 1);
  for (const time of [NaN, Infinity, '1']) assert.throws(() => at(time), /finite/);
});
test('generated content is escaped and scripts are external', async () => {
  const content = change(b => { b.title = '</title><script>alert(1)</script>'; b.scenes[0].body = '<img src=x onerror=alert(1)>'; }, board);
  const files = await renderScene(content);
  assert.match(files['index.html'], /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(files['index.html'], /<script>alert/);
  assert.match(files['index.html'], /<script type="module" src="\.\/scene.mjs"><\/script>/);
  assert.doesNotMatch(files['scene.mjs'], /<\/title>/);
  assert.equal(files['storyboard.json'], JSON.stringify(content, null, 2) + '\n');
  assert.deepEqual(await renderScene(content), files);
});
test('CLI fails before writing invalid scenes and never overwrites existing output', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'fabius-decor-test-'));
  const cli = new URL('./design.mjs', import.meta.url).pathname;
  const run = (...args) => spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' });
  try {
    const input = join(dir, 'board.json'), output = join(dir, 'site');
    await writeFile(input, JSON.stringify(board));
    assert.equal(run('scene', input, '--out', output).status, 0);
    await writeFile(join(output, 'owner.txt'), 'preserve');
    assert.equal(run('scene', input, '--out', output).status, 1);
    assert.equal(await readFile(join(output, 'owner.txt'), 'utf8'), 'preserve');
    assert.equal(run('scene', input, '--bogus', output).status, 1);
    await writeFile(input, JSON.stringify(change(b => { b.scenes = []; }, board)));
    assert.equal(run('scene', input, '--out', join(dir, 'invalid')).status, 1);
    await assert.rejects(readFile(join(dir, 'invalid', 'index.html')));
  } finally { await rm(dir, { recursive: true }); }
});
