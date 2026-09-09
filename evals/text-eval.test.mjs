import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { execFileSync, spawnSync } from 'node:child_process'
import { prepareRun, runPrepared, offlineFixture, replay, generationPrompt, validateVote, validateGrade, checkIds, DIMS, MODES, sha256 } from './text-eval-core.mjs'

const DIR = dirname(fileURLToPath(import.meta.url))
const TASK = JSON.parse(readFileSync(join(DIR, 'suite/tier1.smoke.jsonl'), 'utf8').split('\n')[0])
const clone = value => structuredClone(value)
const vote = n => Object.fromEntries(DIMS.map(d => [d, n]))
function workspace(t) {
  const repo = mkdtempSync(join(tmpdir(), 'fabius-text-eval-'))
  t.after(() => rmSync(repo, { recursive: true, force: true }))
  const put = (path, value) => { mkdirSync(dirname(join(repo, path)), { recursive: true }); writeFileSync(join(repo, path), value) }
  const stance = '\ufeffExact stance.\r\nUTF-8: café.\n'
  const routed = '# Exact routed contract\nUse the supplied task.\n'
  put('AGENTS.md', stance)
  put(`skills/${TASK.routed_skill}/SKILL.md`, routed)
  put('skills/fabius/references/failures.md', 'A separately hashed memory record with sufficient content for fallback.\n')
  put('provenance/seal-manifest.json', JSON.stringify({ spec: 'fabius-seal/v1', algorithm: 'sha256', files: {
    'AGENTS.md': sha256(stance), [`skills/${TASK.routed_skill}/SKILL.md`]: sha256(routed),
  } }))
  put('evals/suite/schema.json', readFileSync(join(DIR, 'suite/schema.json')))
  return { repo, put, plan: () => prepareRun({ repo, tasks: [TASK] }) }
}
function fakeCall({ generation = { answer: 'A text answer.' }, grading, judges = {} } = {}) {
  return async (_, options) => {
    if (options.phase === 'Generate') { if (generation instanceof Error) throw generation; return generation }
    if (options.phase === 'Grade') return grading ?? { checks: checkIds(TASK).map(check => ({ check, passed: true, evidence: 'Quoted evidence.' })) }
    const value = Object.hasOwn(judges, options.model) ? judges[options.model] : vote(3)
    if (value instanceof Error) throw value
    return value
  }
}

test('reads exact UTF-8 bytes including BOM/CRLF; hashes memory separately and isolates modes', t => {
  const w = workspace(t), plan = w.plan()
  assert.equal(plan.contracts[0].content, readFileSync(join(w.repo, 'AGENTS.md'), 'utf8'))
  assert.equal(plan.contracts[0].bytes, readFileSync(join(w.repo, 'AGENTS.md')).length)
  assert.equal(plan.memory.sealed, false)
  assert.equal(plan.max_calls, 12)
  assert(!generationPrompt(plan, TASK, 'BASE').includes('Exact stance'))
  assert(generationPrompt(plan, TASK, 'FAB').includes('Exact stance'))
  assert(!generationPrompt(plan, TASK, 'FAB').includes(plan.memory.content))
  assert(generationPrompt(plan, TASK, 'FAB_MEMORY').includes(plan.memory.content))
  const withMemory = { ...TASK, memory_snapshot: 'Task-specific memory record takes precedence over the lesson log.' }
  assert(generationPrompt(plan, withMemory, 'FAB_MEMORY').includes(withMemory.memory_snapshot))
  assert(!generationPrompt(plan, withMemory, 'FAB_MEMORY').includes(plan.memory.content))
})

for (const [label, mutate] of [
  ['missing stance', w => rmSync(join(w.repo, 'AGENTS.md'))],
  ['changed stance', w => w.put('AGENTS.md', 'Changed bytes')],
  ['changed routed contract', w => w.put(`skills/${TASK.routed_skill}/SKILL.md`, 'changed')],
  ['empty memory', w => w.put('skills/fabius/references/failures.md', '')],
  ['invalid UTF-8', w => w.put('AGENTS.md', Buffer.from([255]))],
  ['missing manifest entry', w => w.put('provenance/seal-manifest.json', JSON.stringify({ spec: 'fabius-seal/v1', algorithm: 'sha256', files: {} }))],
]) test(`fails before calls: ${label}`, async t => {
  const w = workspace(t); mutate(w)
  let calls = 0
  await assert.rejects(async () => runPrepared(w.plan(), async () => { calls++; return {} }))
  assert.equal(calls, 0)
})

test('rejects file symlinks outside the repo and unsafe routes', t => {
  const w = workspace(t)
  rmSync(join(w.repo, 'AGENTS.md')); symlinkSync(import.meta.filename, join(w.repo, 'AGENTS.md'))
  assert.throws(w.plan, /escapes repository/)
  assert.throws(() => prepareRun({ repo: w.repo, tasks: [{ ...TASK, routed_skill: '../../AGENTS.md' }] }), /routed_skill/)
})

test('rejects duplicate tasks, duplicate checks and invalid model configuration', t => {
  const w = workspace(t)
  assert.throws(() => prepareRun({ repo: w.repo, tasks: [TASK, TASK] }), /duplicate task/)
  assert.throws(() => prepareRun({ repo: w.repo, tasks: [{ ...TASK, automatic_checks: ['same', 'same', 'third'] }] }), /duplicate checks/)
  assert.throws(() => prepareRun({ repo: w.repo, tasks: [TASK], judges: ['opus', 'opus'] }), /distinct/)
  assert.throws(() => prepareRun({ repo: w.repo, tasks: [TASK], model: '' }), /model IDs/)
})

test('task input obeys full committed schema and tier/category/neutrality rules', t => {
  const w = workspace(t)
  for (const mutate of [task => { task.prompt = 'x' }, task => { task.category = 'does-not-exist' },
    task => { delete task.difficulty }, task => { delete task.human_review_notes }, task => { task.extra = 'unexpected' },
    task => { task.category = 'debugging' }, task => { task.tier = 3 }, task => { task.stress_kind = 'long_context' },
    task => { task.prompt += ' fabius' }]) {
    const task = clone(TASK); mutate(task)
    assert.throws(() => prepareRun({ repo: w.repo, tasks: [task] }))
  }
})

test('tampered prepared inputs fail before calls', async t => {
  const w = workspace(t)
  for (const mutate of [p => { p.tasks[0].prompt += 'tampered' }, p => { p.contracts[0].content += 'tampered' },
    p => { p.memory.content += 'tampered' }, p => { p.contracts.push(p.contracts[0]) },
    p => { p.contracts[0].content += 'tampered'; p.contracts[0].bytes = Buffer.byteLength(p.contracts[0].content); p.contracts[0].sha256 = sha256(p.contracts[0].content) }]) {
    const plan = w.plan(); mutate(plan)
    let calls = 0
    await assert.rejects(runPrepared(plan, async () => { calls++; return {} }))
    assert.equal(calls, 0)
  }
})

test('rubric rejects coercion, range errors, missing/extra keys; accepts both bounds', () => {
  for (const invalid of [null, {}, { ...vote(2), extra: 1 }, Object.fromEntries(DIMS.slice(1).map(d => [d, 2])),
    ...['4', true, null, NaN, Infinity, -1, 5, 1.5].map(n => ({ ...vote(2), quality: n }))]) {
    assert.throws(() => validateVote(invalid), /seven integers/)
  }
  assert.deepEqual(validateVote(vote(0)), vote(0))
  assert.deepEqual(validateVote(vote(4)), vote(4))
})

test('factual checks require the exact ID set, exact fields and primitive types', () => {
  const good = { checks: checkIds(TASK).map(check => ({ check, passed: false, evidence: '' })) }
  assert.equal(validateGrade({ checks: [...good.checks].reverse() }, TASK).length, TASK.automatic_checks.length)
  for (const mutate of [g => g.checks.pop(), g => g.checks.push(g.checks[0]), g => { g.checks[1].check = g.checks[0].check },
    g => { g.checks[0].check = 'unknown' }, g => { g.checks[0].passed = 'false' }, g => { g.checks[0].passed = 1 },
    g => { g.checks[0].evidence = null }, g => { delete g.checks[0].evidence }, g => { g.checks[0].extra = true },
    g => { g.extra = true }]) { const bad = clone(good); mutate(bad); assert.throws(() => validateGrade(bad, TASK)) }
})

test('surviving second judge keeps identity; failed first judge makes scores null', async t => {
  const out = await runPrepared(workspace(t).plan(), fakeCall({ judges: { opus: new Error('judge unavailable'), fable: vote(4) } }))
  assert.equal(out._meta.status, 'infrastructure-invalid')
  assert.equal(out._meta.logical_requests, 12)
  for (const row of out.perTask) {
    assert.deepEqual(row.byJudge, { fable: 28 })
    assert.equal(row.total, null)
    assert.equal(row.evidence.judges.opus.error.message, 'judge unavailable')
    assert.equal(row.evidence.judges.fable.raw, JSON.stringify(vote(4)))
  }
  assert.equal(out.byMode.BASE.total, null)
  assert.equal(out.byMode.BASE.n_invalid, 1)
  assert.equal(out.byMode.BASE.valid_checks, 0)
  assert.equal(out.byMode.BASE.expected_checks, TASK.automatic_checks.length)
  assert.equal(out.deltas.FAB_vs_BASE.total, null)
  assert.equal(out.judgeAgreement.mean_abs_total_diff, null)
})

test('missing/invalid judge and check evidence never becomes a zero or an accepted partial score', async t => {
  const plan = workspace(t).plan()
  for (const config of [{ judges: { opus: null } }, { judges: { fable: null } }, { judges: { opus: null, fable: null } },
    { judges: { opus: 'malformed JSON {' } }, { judges: { opus: { quality: 99 } } },
    { grading: { checks: [] } }, { grading: { checks: [{ check: 'unknown', passed: 'yes' }] } }]) {
    const out = await runPrepared(plan, fakeCall(config))
    assert.equal(out.perTask[0].status, 'infrastructure-invalid')
    assert.equal(out.perTask[0].checks_passed, null)
    assert.equal(out.perTask[0].quality, null)
  }
})

test('generation infrastructure failures skip downstream calls and preserve raw text/errors', async t => {
  const plan = workspace(t).plan()
  for (const generation of ['  malformed {', null, { content: 'wrong schema' }, new Error('provider timeout')]) {
    const out = await runPrepared(plan, fakeCall({ generation }))
    assert.equal(out._meta.logical_requests, 3)
    assert(out.perTask.every(r => r.answer === null && r.status === 'infrastructure-invalid'))
    if (typeof generation === 'string') assert.equal(out.perTask[0].evidence.generation.raw, generation)
  }
})

test('valid poor/empty model answers remain measured failures, distinct from infrastructure failures', async t => {
  const plan = workspace(t).plan()
  const out = await runPrepared(plan, fakeCall({ generation: { answer: '' },
    grading: { checks: checkIds(TASK).map(check => ({ check, passed: false, evidence: 'Absent.' })) }, judges: { opus: vote(0), fable: vote(0) } }))
  assert.equal(out._meta.status, 'valid')
  assert.equal(out.byMode.BASE.total, 0)
  assert.equal(out.byMode.BASE.check_rate, 0)
  assert.equal(out.byMode.BASE.chars, 0)
  assert.equal(out.deltas.FAB_vs_BASE.output_cut_pct, null)
})

test('offline receipt replay recomputes scores, rejects duplicate/foreign cells and handles missing cells', async t => {
  const out = await offlineFixture(workspace(t).plan()), plan = out.plan
  assert.equal(out._meta.fixture, true)
  const cells = out.perTask.map(r => r.evidence)
  assert.deepEqual(replay(plan, cells, { fixture: true }).byMode, out.byMode)
  assert.throws(() => replay(plan, [...cells, cells[0]]), /duplicate/)
  assert.throws(() => replay(plan, [{ ...cells[0], id: 'FAB-999' }]), /unexpected/)
  assert.throws(() => replay(plan, [{ ...cells[0], executed_code: true }]), /cell evidence fields/)
  const missing = replay(plan, cells.slice(1))
  assert.equal(missing._meta.expected_cells, 3)
  assert.equal(missing._meta.received_cells, 2)
  assert.equal(missing.byMode.BASE.n_invalid, 1)
  assert.equal(missing.byMode.BASE.total, null)
  assert.equal(missing.byMode.FAB.n_valid, 1)
  const tampered = clone(cells); tampered[0].judges.opus.raw = '{}'
  assert.equal(replay(plan, tampered).perTask[0].status, 'infrastructure-invalid')
  const missingRequest = clone(cells); delete missingRequest[0].generation.request
  assert.equal(replay(plan, missingRequest).perTask[0].status, 'infrastructure-invalid')
  const changedPrompt = clone(cells); changedPrompt[0].generation.request.prompt_sha256 = sha256('another prompt')
  assert.equal(replay(plan, changedPrompt).perTask[0].status, 'infrastructure-invalid')
  assert.equal(replay(plan, [])._meta.valid_cells, 0)
})

test('fixture provenance cannot be removed by changing the replay flag or plan kind alone', async t => {
  const out = await offlineFixture(workspace(t).plan())
  const cells = out.perTask.map(r => r.evidence)
  assert.throws(() => replay(out.plan, cells, { fixture: false }), /fixture label/)
  const alteredPlan = { ...out.plan, execution_kind: 'model' }
  assert.equal(replay(alteredPlan, cells)._meta.status, 'infrastructure-invalid')
})

test('unsupported provider, usage, timing and envelope metadata invalidate evidence', async t => {
  const out = await offlineFixture(workspace(t).plan())
  for (const mutate of [e => { e.elapsed_ms = -1 }, e => { e.elapsed_ms = 1.5 }, e => { e.raw_kind = 'provider-wire-bytes' },
    e => { e.resolved_model = 'invented-proven-provider-version' }, e => { e.usage = { input_tokens: 999 } },
    e => { e.extra = 'unverified' }, e => { e.error = { message: 'no name' } }]) {
    const cells = clone(out.perTask.map(r => r.evidence)); mutate(cells[0].generation)
    const replayed = replay(out.plan, cells)
    assert.equal(replayed.perTask[0].status, 'infrastructure-invalid')
    assert.equal(replayed.byMode.BASE.total, null)
  }
})

test('legacy Workflow adapter executes with its top-level return and shared validation', async t => {
  const w = workspace(t)
  w.put('evals/text-eval-core.mjs', readFileSync(join(DIR, 'text-eval-core.mjs')))
  const source = readFileSync(join(DIR, 'harness.v7.workflow.js'), 'utf8').replace(/^import .*\n/gm, '').replace('export const meta =', 'const meta =')
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  const execute = new AsyncFunction('execFileSync', 'join', 'pathToFileURL', 'args', 'phase', 'log', 'agent', source)
  const previous = process.env.FABIUS_REPO
  process.env.FABIUS_REPO = w.repo
  try {
    const out = await execute(execFileSync, join, pathToFileURL, { tasks: [TASK], model: 'fixture-model' }, () => {}, () => {}, fakeCall())
    assert.equal(out._meta.model, 'fixture-model')
    assert.equal(out._meta.valid_cells, 3)
    let calls = 0; w.put('AGENTS.md', 'tampered')
    await assert.rejects(execute(execFileSync, join, pathToFileURL, { tasks: [TASK] }, () => {}, () => {}, async () => { calls++ }), /seal hash/)
    assert.equal(calls, 0)
  } finally { if (previous === undefined) delete process.env.FABIUS_REPO; else process.env.FABIUS_REPO = previous }
})

test('Node CLI prepares, generates synthetic fixtures and replays; errors retain original bytes', async t => {
  const w = workspace(t)
  for (const file of ['text-eval-core.mjs', 'text-eval.mjs']) w.put(`evals/${file}`, readFileSync(join(DIR, file)))
  w.put('evals/suite/tier1.smoke.jsonl', JSON.stringify(TASK) + '\n')
  const invoke = args => spawnSync(process.execPath, [join(w.repo, 'evals/text-eval.mjs'), ...args], { encoding: 'utf8' })
  for (const command of ['prepare', 'fixture']) {
    const result = invoke([command, '--out', join(w.repo, `${command}.json`)])
    assert.equal(result.status, 0, result.stderr)
  }
  const fixture = JSON.parse(readFileSync(join(w.repo, 'fixture.json'), 'utf8'))
  fixture.byMode.BASE.total = 999 // Replay ignores supplied summary scores.
  w.put('edited.json', JSON.stringify(fixture))
  assert.equal(invoke(['replay', '--input', join(w.repo, 'edited.json'), '--out', join(w.repo, 'replayed.json')]).status, 0)
  assert.equal(JSON.parse(readFileSync(join(w.repo, 'replayed.json'), 'utf8')).byMode.BASE.total, 0)
  assert.equal(invoke(['fixture', '--out', join(w.repo, 'fixture.json')]).status, 1)
  w.put('broken.json', '{ broken input\n')
  assert.equal(invoke(['replay', '--input', join(w.repo, 'broken.json'), '--out', join(w.repo, 'error.json')]).status, 1)
  const error = JSON.parse(readFileSync(join(w.repo, 'error.json'), 'utf8'))
  assert.equal(error._meta.status, 'infrastructure-invalid')
  assert.equal(Buffer.from(error.raw_input.data, 'base64').toString(), '{ broken input\n')
  assert.equal(error.byMode, null)
  assert.equal(invoke(['replay', '--input', join(w.repo, 'broken.json'), '--out', join(w.repo, 'evals/results.new.json')]).status, 1)
  assert.throws(() => readFileSync(join(w.repo, 'evals/results.new.json')), /ENOENT/)
})
