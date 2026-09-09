#!/usr/bin/env node
// Focused R5/M4 regression examples, not a verifier for every whitepaper proof.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const proofs = JSON.parse(readFileSync(new URL('../paper/proofs.json', import.meta.url), 'utf8'));
const r5 = proofs.find(({ rule }) => rule === 'R5');
const m4 = proofs.find(({ rule }) => rule === 'M4');

// Bind the executable examples to the specific displayed predicates. This is
// deliberately a small source contract, not a general TeX theorem interpreter.
function checkR5Source(html) {
  for (const text of [
    String.raw`\arg\max_{\tau}J(\tau)=S`,
    String.raw`w\ge1`,
    'unfinished prefix',
    'completed run ending in Terminal',
    'next control step must be Replan or Terminal',
    'a <em>safety</em> property',
    'one of four qualitative blocks',
  ]) assert.ok(html.includes(text), `R5 missing source boundary: ${text}`);
  assert.doesNotMatch(html, /there exists no scalar objective|one qualitative rule among the eighteen|other seventeen/);
}

function checkM4Source(html) {
  for (const text of [
    String.raw`k^\star=\min\{k\ge1:g_k\le c_{\text{retry}}\}`,
    String.raw`1, & g_1\le c_{\text{retry}}`,
    String.raw`1+\left\lceil\dfrac{\log(g_1/c_{\text{retry}})}{\log(1/\rho)}\right\rceil`,
    String.raw`g_1\ge0`,
    String.raw`0<\rho<1`,
    String.raw`k^\star-1`,
    'myopic one-step lookahead',
    'conditional action policy and relevant problem state also stay fixed',
    'redundancy alone does not imply stopping',
  ]) assert.ok(html.includes(text), `M4 missing source boundary: ${text}`);
}

// Closed-form illustration; exact multiplication below is an independent
// oracle. Floating logarithms are not used to decide the oracle's crossing.
function rejectionFormula(gainCostRatio, rho) {
  assert.ok(Number.isFinite(gainCostRatio) && gainCostRatio >= 0);
  assert.ok(Number.isFinite(rho) && rho > 0 && rho < 1);
  return gainCostRatio <= 1
    ? 1
    : 1 + Math.ceil(Math.log(gainCostRatio) / Math.log(1 / rho));
}

function exactCrossing([numerator, denominator], [rhoNumerator, rhoDenominator], strict = false) {
  assert.ok(numerator >= 0n && denominator > 0n);
  assert.ok(rhoNumerator > 0n && rhoNumerator < rhoDenominator);
  for (let k = 1; k <= 1000; k++) {
    if (strict ? numerator < denominator : numerator <= denominator) return k;
    numerator *= rhoNumerator;
    denominator *= rhoDenominator;
  }
  throw new Error('Example exceeded the finite arithmetic scan budget');
}

// Small monitor for the stated response semantics. A terminal state repeats;
// an unfinished prefix at the deadline is pending until the next control step.
function responseState(events, window) {
  assert.ok(Number.isInteger(window) && window >= 1);
  let stalled = 0;
  let terminal = false;
  for (const event of events) {
    if (terminal && event !== 'terminal') return 'bad';
    if (stalled === window && !['replan', 'terminal'].includes(event)) return 'bad';
    if (event === 'terminal') {
      terminal = true;
      stalled = 0;
    } else if (event === 'replan' || event === 'progress') {
      stalled = 0;
    } else if (event === 'stall') {
      stalled++;
    } else {
      assert.equal(event, 'reason');
    }
  }
  return terminal ? 'complete' : stalled === window ? 'pending' : 'prefix';
}

test('source retains the focused predicates and 26-block classification', () => {
  assert.equal(proofs.length, 26);
  assert.equal(proofs.filter(({ class: kind }) => kind === 'real-math').length, 22);
  assert.equal(proofs.filter(({ class: kind }) => kind === 'qualitative').length, 4);
  assert.equal(r5.class, 'qualitative');
  checkR5Source(r5.html);
  checkM4Source(m4.html);
});

test('source oracle rejects the original impossibility, strict-crossing, and zero-branch regressions', () => {
  assert.throws(() => checkR5Source(`${r5.html} there exists no scalar objective`));
  assert.throws(() => checkM4Source(m4.html.replace(String.raw`g_k\le`, 'g_k<')));
  assert.throws(() => checkM4Source(m4.html.replace(String.raw`1, & g_1\le c_{\text{retry}}`, '')));
});

test('R5 indicator maximizers equal every nonempty feasible subset of a five-trace domain', () => {
  for (let mask = 1; mask < 32; mask++) {
    const feasible = Array.from({ length: 5 }, (_, i) => Boolean(mask & (1 << i)));
    const objective = feasible.map(Number);
    const maximum = Math.max(...objective);
    assert.deepEqual(objective.map(value => value === maximum), feasible);
  }
});

test('R5 a missed fixed deadline has an irreparable finite bad prefix', () => {
  const badPrefix = ['stall', 'stall', 'stall', 'reason'];
  const alphabet = ['stall', 'replan', 'progress'];
  let suffixes = [[]];
  for (let length = 0; length <= 4; length++) {
    for (const suffix of suffixes) assert.equal(responseState([...badPrefix, ...suffix], 3), 'bad');
    suffixes = suffixes.flatMap(suffix => alphabet.map(event => [...suffix, event]));
  }
});

test('R5 pending prefix, replan reset, progress reset, and terminal semantics are distinct', () => {
  assert.equal(responseState(['stall', 'stall', 'stall'], 3), 'pending');
  assert.equal(responseState(['stall', 'stall', 'stall', 'replan', 'stall'], 3), 'prefix');
  assert.equal(responseState(['stall', 'stall', 'progress', 'stall'], 3), 'prefix');
  assert.equal(responseState(['stall', 'stall', 'stall', 'terminal', 'terminal'], 3), 'complete');
  assert.equal(responseState(['terminal', 'reason'], 3), 'bad');
  assert.throws(() => responseState([], 0));
  assert.throws(() => responseState([], 2.5));
});

for (const [numerator, denominator, expected, executed] of [
  [4n, 1n, 3, 2],
  [1n, 1n, 1, 0],
  [1n, 4n, 1, 0],
  [0n, 1n, 1, 0],
  [3n, 1n, 3, 2],
]) {
  test(`M4 gain/cost=${numerator}/${denominator}, rho=1/2: reject at ${expected}, at most ${executed} retries`, () => {
    const exact = exactCrossing([numerator, denominator], [1n, 2n]);
    assert.equal(exact, expected);
    assert.equal(rejectionFormula(Number(numerator) / Number(denominator), 0.5), exact);
    assert.equal(exact - 1, executed);
  });
}

test('M4 strict crossing and the printed weak crossing differ exactly at ties', () => {
  assert.equal(exactCrossing([4n, 1n], [1n, 2n], true), 4);
  assert.equal(exactCrossing([4n, 1n], [1n, 2n]), 3);
  assert.equal(exactCrossing([3n, 1n], [1n, 2n], true), 3);
});

test('M4 closed form agrees with 65 exact dyadic examples; invalid domains are rejected', () => {
  for (let numerator = 0n; numerator <= 64n; numerator++) {
    assert.equal(rejectionFormula(Number(numerator) / 4, 0.5), exactCrossing([numerator, 4n], [1n, 2n]));
  }
  for (const [ratio, rho] of [[-1, 0.5], [1, 0], [1, 1], [1, -0.5], [Infinity, 0.5]]) {
    assert.throws(() => rejectionFormula(ratio, rho));
  }
});

test('M4 unchanged information requires a fixed policy for unchanged success, and unchanged success can still pay', () => {
  // Uniform cause posterior stays fixed after a constant reflection. The
  // conditional success vectors change when the action policy changes.
  const before = (0.5 + 0) / 2;
  const after = (1 + 0.5) / 2;
  assert.equal(before, 0.25);
  assert.equal(after, 0.75);
  assert.notEqual(before, after);
  // Exact fractions: 3/4 - 1/10 = 13/20 > 0.
  assert.equal(3n * 10n - 1n * 4n, 26n);
  assert.ok(26n > 0n);
});
