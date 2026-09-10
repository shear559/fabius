import test from 'node:test';
import assert from 'node:assert/strict';
import { executePlan, validatePlan } from './cohort.mjs';

const schema = { type: 'object', properties: { value: { type: 'integer' } }, required: ['value'], additionalProperties: false };
function plan(tasks = [{ id: 'a', agent: 'analyst', input: {}, dependsOn: [] }]) {
  return { schema: 'fabius-cohort/v1', agents: [{ id: 'analyst', description: 'Compute a checked result.', instructions: 'Return only supported facts.', tools: [], permissions: { read: 'deny', write: 'deny', execute: 'deny', network: 'deny' }, output: structuredClone(schema) }], tasks };
}
const task = (id, dependsOn = []) => ({ id, agent: 'analyst', input: {}, dependsOn });
const permit = () => true;
const good = async () => ({ value: 1 });

test('validates a DAG and returns deterministic dependency layers', () => {
  const checked = validatePlan(plan([task('join', ['left', 'right']), task('left'), task('right')]));
  assert.deepEqual(checked.order, ['left', 'right', 'join']);
  assert.deepEqual(checked.levels, [['left', 'right'], ['join']]);
});

for (const [name, mutate, message] of [
  ['cycle', p => { p.tasks = [task('a', ['b']), task('b', ['a'])]; }, /cycle/],
  ['missing dependency', p => { p.tasks[0].dependsOn = ['absent']; }, /unknown dependency/],
  ['duplicate task', p => { p.tasks.push(task('a')); }, /duplicate task/],
  ['duplicate dependency', p => { p.tasks.push(task('b', ['a', 'a'])); }, /duplicate/],
  ['unknown agent', p => { p.tasks[0].agent = 'missing'; }, /unknown agent/],
  ['too many tasks', p => { p.tasks = Array.from({ length: 65 }, (_, i) => task(`t${i}`)); }, /64/],
  ['missing permission', p => { delete p.agents[0].permissions.network; }, /network/],
  ['unknown plan key', p => { p.command = 'ignored command'; }, /unknown/],
  ['unsupported schema keyword', p => { p.agents[0].output.oneOf = []; }, /unknown/],
  ['invalid required field', p => { p.agents[0].output.required.push('missing'); }, /required/],
  ['non-JSON input', p => { p.tasks[0].input.bad = NaN; }, /finite/],
  ['accessor input', p => { Object.defineProperty(p.tasks[0].input, 'bad', { enumerable: true, get() { throw Error('must not execute getter'); } }); }, /data propert/],
]) {
  test(`rejects ${name} before authorization or execution`, async () => {
    const p = plan(); mutate(p); let calls = 0;
    await assert.rejects(executePlan(p, { authorize: () => { calls++; return true; }, runner: good }), message);
    assert.equal(calls, 0);
  });
}

test('requires caller-supplied runner and task authorization', async () => {
  await assert.rejects(executePlan(plan(), { runner: good }), /authorize/);
  await assert.rejects(executePlan(plan(), { authorize: permit }), /runner/);
  for (const concurrency of [0, 17, 1.5]) await assert.rejects(executePlan(plan(), { authorize: permit, runner: good, concurrency }), /concurrency/);
});

test('passes only completed direct dependency outputs', async () => {
  const result = await executePlan(plan([task('a'), task('b', ['a']), task('c', ['b'])]), {
    authorize: permit,
    runner: async ({ task, dependencies }) => {
      assert.deepEqual(Object.keys(dependencies), task.dependsOn);
      return { value: Object.values(dependencies).reduce((n, row) => n + row.value, 1) };
    },
  });
  assert.equal(result.status, 'succeeded');
  assert.deepEqual(result.tasks.c.output, { value: 3 });
});

test('never exceeds configured concurrency while using available slots', async () => {
  let active = 0, peak = 0, calls = 0;
  const result = await executePlan(plan(Array.from({ length: 7 }, (_, i) => task(`t${i}`))), {
    authorize: permit, concurrency: 2,
    runner: async () => { calls++; active++; peak = Math.max(peak, active); await new Promise(resolve => setTimeout(resolve, 5)); active--; return { value: 1 }; },
  });
  assert.equal(result.status, 'succeeded'); assert.equal(peak, 2); assert.equal(calls, 7); assert.equal(active, 0);
});

test('blocks descendants of failure but completes independent work', async () => {
  const calls = [];
  const result = await executePlan(plan([task('a'), task('b', ['a']), task('c', ['b']), task('independent')]), {
    authorize: permit, runner: async ({ task }) => { calls.push(task.id); if (task.id === 'a') throw Error('fixture failure'); return { value: 2 }; },
  });
  assert.equal(result.status, 'failed');
  assert.equal(result.tasks.a.status, 'failed'); assert.equal(result.tasks.a.error.stage, 'runner');
  assert.equal(result.tasks.b.status, 'blocked'); assert.equal(result.tasks.c.status, 'blocked');
  assert.equal(result.tasks.independent.status, 'succeeded'); assert.deepEqual(calls.sort(), ['a', 'independent']);
});

test('authorization is task-specific, deny prevents its runner and dependents', async () => {
  const authorized = [], ran = [];
  const result = await executePlan(plan([task('allow'), task('deny'), task('child', ['deny'])]), {
    authorize: ({ task }) => { authorized.push(task.id); return task.id === 'allow'; },
    runner: async ({ task }) => { ran.push(task.id); return { value: 1 }; },
  });
  assert.deepEqual(authorized, ['allow', 'deny']); assert.deepEqual(ran, ['allow']);
  assert.equal(result.tasks.deny.status, 'denied'); assert.equal(result.tasks.child.status, 'blocked');
});

test('authorization exceptions and non-boolean results fail closed', async () => {
  for (const authorize of [() => { throw Error('policy error'); }, () => Promise.resolve(true), () => 'yes']) {
    let ran = 0;
    const result = await executePlan(plan(), { authorize, runner: async () => { ran++; return { value: 1 }; } });
    assert.equal(ran, 0); assert.equal(result.status, 'failed');
    assert.equal(result.tasks.a.error.stage, 'authorize');
  }
});

for (const [name, output] of [['wrong type', { value: '1' }], ['extra field', { value: 1, surprise: true }], ['missing field', {}], ['nonfinite value', { value: Infinity }], ['undefined', undefined]]) {
  test(`rejects ${name} output before a dependent can consume it`, async () => {
    const calls = [];
    const result = await executePlan(plan([task('a'), task('b', ['a'])]), { authorize: permit, runner: async ({ task }) => { calls.push(task.id); return output; } });
    assert.deepEqual(calls, ['a']); assert.equal(result.tasks.a.status, 'failed'); assert.equal(result.tasks.a.error.stage, 'output'); assert.equal(result.tasks.b.status, 'blocked');
  });
}

test('validates bounded nested objects, arrays and enums', async () => {
  const p = plan();
  p.agents[0].output = { type: 'object', properties: { verdict: { type: 'string', enum: ['accept', 'reject'] }, evidence: { type: 'array', maxItems: 2, items: { type: 'object', properties: { location: { type: 'string', maxLength: 20 } }, required: ['location'], additionalProperties: false } } }, required: ['verdict', 'evidence'], additionalProperties: false };
  for (const [output, expected] of [[{ verdict: 'accept', evidence: [{ location: 'fixture:1' }] }, 'succeeded'], [{ verdict: 'maybe', evidence: [] }, 'failed'], [{ verdict: 'accept', evidence: [{ location: 'a' }, { location: 'b' }, { location: 'c' }] }, 'failed'], [{ verdict: 'accept', evidence: [{ location: 'x'.repeat(21) }] }, 'failed']]) {
    const result = await executePlan(p, { authorize: permit, runner: async () => output }); assert.equal(result.status, expected);
  }
});

test('snapshots and freezes plan and dependency objects at runner boundaries', async () => {
  const p = plan([task('a'), task('b', ['a']), task('c', ['a'])]);
  p.tasks[0].input = { nested: { value: 7 } };
  const shared = { value: 1 };
  const pending = executePlan(p, { authorize: permit, concurrency: 2, runner: async ({ task, agent, dependencies }) => {
    assert.throws(() => { agent.permissions.write = 'allow'; }, TypeError);
    if (task.id === 'a') { assert.equal(task.input.nested.value, 7); assert.throws(() => { task.input.nested.value = 8; }, TypeError); return shared; }
    assert.equal(dependencies.a.value, 1); assert.throws(() => { dependencies.a.value = 9; }, TypeError);
    shared.value = 99; return { value: dependencies.a.value };
  } });
  p.tasks[0].input.nested.value = 42;
  const result = await pending;
  assert.equal(result.status, 'succeeded'); assert.equal(result.tasks.c.output.value, 1); assert.equal(result.tasks.a.output.value, 1);
});

test('pre-aborted plan starts no authorization or runner', async () => {
  const controller = new AbortController(); controller.abort(); let calls = 0;
  const result = await executePlan(plan([task('a'), task('b', ['a'])]), { signal: controller.signal, authorize: () => { calls++; return true; }, runner: good });
  assert.equal(calls, 0); assert.equal(result.status, 'cancelled'); assert.ok(Object.values(result.tasks).every(row => row.status === 'cancelled'));
});

test('cancellation aborts active work, waits for settlement and prevents new launches', async () => {
  const controller = new AbortController(); let settled = false; const calls = [];
  let started; const firstStarted = new Promise(resolve => { started = resolve; });
  const pending = executePlan(plan([task('a'), task('b'), task('c', ['a'])]), {
    signal: controller.signal, concurrency: 1, authorize: permit,
    runner: async ({ task, signal }) => { calls.push(task.id); started(); await new Promise(resolve => signal.addEventListener('abort', resolve, { once: true })); settled = true; return { value: 1 }; },
  });
  await firstStarted; controller.abort();
  const result = await pending;
  assert.ok(settled); assert.deepEqual(calls, ['a']); assert.equal(result.status, 'cancelled'); assert.ok(Object.values(result.tasks).every(row => row.status === 'cancelled'));
});

test('cancellation inside authorization does not start a runner', async () => {
  const controller = new AbortController(); let calls = 0;
  const result = await executePlan(plan(), { signal: controller.signal, authorize: () => { controller.abort(); return true; }, runner: async () => { calls++; return { value: 1 }; } });
  assert.equal(calls, 0); assert.equal(result.tasks.a.status, 'cancelled');
});

for (const throws of [false, true]) {
  test(`runner signal shadowing cannot defeat cancellation when it ${throws ? 'throws' : 'returns'}`, async () => {
    const controller = new AbortController(), authorized = [], calls = [];
    const result = await executePlan(plan([task('a'), task('b'), task('c', ['a'])]), {
      signal: controller.signal, concurrency: 1,
      authorize: ({ task }) => { authorized.push(task.id); return true; },
      runner: async ({ task, signal }) => {
        calls.push(task.id);
        Object.defineProperty(signal, 'aborted', { value: false, configurable: true });
        controller.abort();
        if (throws) throw Error('runner settled after cancellation');
        return { value: 1 };
      },
    });
    assert.deepEqual(calls, ['a']); assert.deepEqual(authorized, ['a']);
    assert.equal(result.status, 'cancelled');
    assert.ok(Object.values(result.tasks).every(row => row.status === 'cancelled'));
  });
}

test('multiple individually valid outputs can merge without a hidden aggregate node limit', async () => {
  const p = plan([task('a'), task('b'), task('merge', ['a', 'b'])]);
  p.agents[0].output = { type: 'object', properties: { rows: { type: 'array', maxItems: 256, items: { type: 'array', maxItems: 32, items: { type: 'integer' } } } }, required: ['rows'], additionalProperties: false };
  const result = await executePlan(p, { authorize: permit, runner: async ({ task, dependencies }) => {
    if (task.id === 'merge') { assert.equal(dependencies.a.rows.length + dependencies.b.rows.length, 512); return { rows: [] }; }
    return { rows: Array.from({ length: 256 }, () => Array(32).fill(1)) };
  } });
  assert.equal(result.status, 'succeeded');
});

test('rejects oversized output while leaving an independent branch usable', async () => {
  const p = plan([task('oversized'), task('independent')]);
  p.agents[0].output = { type: 'object', properties: { rows: { type: 'array', maxItems: 256, items: { type: 'string' } } }, required: ['rows'], additionalProperties: false };
  const result = await executePlan(p, { authorize: permit, runner: async ({ task }) => ({ rows: task.id === 'oversized' ? Array(9).fill('x'.repeat(8192)) : [] }) });
  assert.equal(result.tasks.oversized.status, 'failed'); assert.equal(result.tasks.oversized.error.stage, 'output');
  assert.match(result.tasks.oversized.error.message, /byte limit/); assert.equal(result.tasks.independent.status, 'succeeded');
});
