#!/usr/bin/env node
// Validate prepared launch cases only. Never calls a model or executes case inputs.
// Usage: node launch/validate-tasks.mjs [--self-test]
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const AUDIENCES = ['personal', 'creative', 'developer', 'business']
const PREFIX = { personal: 'PER', creative: 'CRE', developer: 'DEV', business: 'BUS' }
const SCENARIOS = ['simple', 'ambiguous', 'multistep', 'missing-tool', 'recovery', 'hebrew']
const HOST_FIELDS = ['task_id', 'candidate_version', 'candidate_commit', 'candidate_contract_hashes', 'host_name', 'host_version',
  'model_requested', 'model_resolved_or_unavailable', 'os', 'fresh_session_receipt', 'available_tool_inventory', 'input_hashes',
  'raw_prompt', 'raw_response', 'tool_trace', 'permission_trace', 'acceptance_outcomes', 'routing_observation_or_not_exposed']
const FIXTURE_FIELDS = ['task_id', 'fixture_id', 'validator_version', 'fixture_input_hashes', 'fixture_result', 'synthetic_label']
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b)
const strings = value => Array.isArray(value) && value.every(v => typeof v === 'string' && v.trim()) && new Set(value).size === value.length
const exact = (value, fields) => value !== null && typeof value === 'object' && !Array.isArray(value) && same(Object.keys(value).sort(), [...fields].sort())
const text = value => typeof value === 'string' && value.trim().length > 0
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value)
const assert = (condition, message) => { if (!condition) throw new Error(message) }
const skill = name => typeof name === 'string' && /^fabius(?:-[a-z]+)?$/.test(name) && existsSync(join(ROOT, 'skills', name, 'SKILL.md'))

export function validateSuite(suite) {
  assert(exact(suite, ['schema', 'title', 'status', 'protocol', 'audiences', 'scenarios', 'routing_policy', 'execution_policy', 'evidence_profiles', 'tasks']), 'unexpected suite fields')
  assert(suite.schema === 'fabius-launch-task-suite/v1' && suite.status === 'prepared-not-run', 'suite must be a prepared launch suite')
  assert(text(suite.title) && text(suite.protocol) && text(suite.routing_policy), 'missing suite description')
  assert(same(suite.audiences, AUDIENCES) && same(suite.scenarios, SCENARIOS), 'expected four audiences and six scenario types')
  const policy = suite.execution_policy
  assert(exact(policy, ['status', 'allowed_evidence_kinds', 'candidate_host', 'synthetic_fixture', 'comparison', 'safety', 'results']), 'unexpected execution policy fields')
  assert(policy.status === 'prepared-not-run' && policy.results === null, 'prepared policy cannot contain run results')
  assert(same(policy.allowed_evidence_kinds, ['candidate-host', 'synthetic-fixture']), 'candidate-host and synthetic-fixture evidence must remain separate')
  assert(['candidate_host', 'synthetic_fixture', 'comparison', 'safety'].every(k => text(policy[k])), 'missing execution boundaries')
  assert(exact(suite.evidence_profiles, ['candidate-host', 'synthetic-fixture']), 'exactly two evidence profiles required')
  for (const [kind, required] of [['candidate-host', HOST_FIELDS], ['synthetic-fixture', FIXTURE_FIELDS]]) {
    const profile = suite.evidence_profiles[kind]
    assert(exact(profile, ['kind', 'required', 'claim_scope', 'counts_as_host_execution', 'counts_as_independent_user_evidence']), `${kind}: unexpected profile fields`)
    assert(profile.kind === kind && same(profile.required, required) && text(profile.claim_scope), `${kind}: evidence requirements changed`)
    assert(profile.counts_as_host_execution === (kind === 'candidate-host') && profile.counts_as_independent_user_evidence === false, `${kind}: invalid claim scope`)
  }
  assert(Array.isArray(suite.tasks) && suite.tasks.length === 24, 'exactly 24 prepared tasks required')
  const ids = new Set(), pairs = new Set()
  for (const task of suite.tasks) {
    assert(exact(task, ['id', 'audience', 'scenario', 'language', 'status', 'prompt', 'input', 'routing_hypothesis', 'acceptance', 'required_evidence', 'result']), 'unexpected task fields')
    assert(AUDIENCES.includes(task.audience) && SCENARIOS.includes(task.scenario), `${task.id}: unknown audience/scenario`)
    const expectedId = `LAUNCH-${PREFIX[task.audience]}-${String(SCENARIOS.indexOf(task.scenario) + 1).padStart(2, '0')}`
    assert(task.id === expectedId && !ids.has(task.id), `${task.id}: invalid or duplicate stable ID`)
    ids.add(task.id); pairs.add(`${task.audience}/${task.scenario}`)
    assert(task.status === 'prepared-not-run' && task.result === null, `${task.id}: prepared task cannot contain a result`)
    assert(text(task.prompt) && !/fabius/i.test(task.prompt), `${task.id}: prompt must be natural language without explicit plugin invocation`)
    assert(['en', 'he'].includes(task.language), `${task.id}: unsupported language`)
    assert(task.scenario !== 'hebrew' || (task.language === 'he' && /[\u0590-\u05ff]/.test(task.prompt)), `${task.id}: Hebrew scenario requires a Hebrew prompt`)
    const input = task.input
    assert(exact(input, ['kind', 'materials', 'fixture_paths', 'tool_setup', 'authorization']), `${task.id}: input fields missing or unexpected`)
    assert(input.kind === 'synthetic-user-material' && Array.isArray(input.materials) && strings(input.fixture_paths), `${task.id}: invalid supplied materials`)
    for (const path of input.fixture_paths)
      assert(/^examples\/[a-z0-9.-]+$/.test(path) && existsSync(join(ROOT, path)), `${task.id}: missing or unsafe fixture path`)
    const tools = input.tool_setup
    assert(exact(tools, ['status', 'available', 'unavailable', 'scope']) && tools.status === 'required-for-run-not-observed' && text(tools.scope), `${task.id}: tool setup must remain unobserved`)
    assert(strings(tools.available) && strings(tools.unavailable) && !tools.available.some(v => tools.unavailable.includes(v)), `${task.id}: inconsistent tool inventory`)
    assert(task.scenario !== 'missing-tool' || tools.available.length === 0, `${task.id}: missing-tool scenario unexpectedly supplies tools`)
    const auth = input.authorization
    assert(exact(auth, ['allowed', 'prohibited']) && strings(auth.allowed) && auth.allowed.length > 0 && strings(auth.prohibited) && !auth.allowed.some(v => auth.prohibited.includes(v)), `${task.id}: invalid authorization`)
    assert(['send-external-message', 'write-project-memory', 'read-secrets', 'make-purchase', 'publish-or-deploy'].every(v => auth.prohibited.includes(v)), `${task.id}: missing external-action boundary`)
    const route = task.routing_hypothesis
    assert(exact(route, ['status', 'baseline', 'primary', 'supporting', 'reason', 'observation']), `${task.id}: invalid route fields`)
    assert(route.status === 'hypothesis-not-observed' && route.observation === null && same(route.baseline, ['fabius', 'fabius-parcus']), `${task.id}: routing must remain a hypothesis`)
    assert(skill(route.primary) && strings(route.supporting) && route.supporting.every(skill) && text(route.reason), `${task.id}: unknown route capability`)
    assert(Array.isArray(task.acceptance) && task.acceptance.length >= 3, `${task.id}: at least three acceptance expectations required`)
    task.acceptance.forEach((check, i) => {
      const fields = check.kind === 'deterministic' ? ['id', 'kind', 'expectation', 'expected'] : ['id', 'kind', 'expectation']
      assert(exact(check, fields) && check.id === `${task.id}-A${i + 1}` && text(check.expectation), `${task.id}: invalid acceptance fields/ID`)
      assert(['deterministic', 'human-review', 'trace-review'].includes(check.kind), `${check.id}: unknown oracle kind`)
      assert(check.kind !== 'deterministic' || (object(check.expected) && Object.keys(check.expected).length > 0), `${check.id}: deterministic check needs explicit expected values`)
    })
    assert(task.acceptance.some(check => check.kind === 'trace-review'), `${task.id}: permission/tool trace expectation required`)
    const evidence = task.required_evidence
    assert(exact(evidence, ['candidate_host_profile', 'synthetic_fixture_profile', 'candidate_host_additional', 'observations']), `${task.id}: invalid evidence fields`)
    assert(evidence.candidate_host_profile === 'candidate-host' && evidence.synthetic_fixture_profile === 'synthetic-fixture' && strings(evidence.candidate_host_additional) && evidence.observations === null, `${task.id}: evidence kinds must remain separate and unobserved`)
    if (tools.available.includes('python-shell'))
      assert(['stdout', 'stderr', 'exit_status'].every(field => evidence.candidate_host_additional.includes(field)), `${task.id}: execution expectations need stdout/stderr/exit status`)
  }
  assert(pairs.size === 24 && AUDIENCES.every(a => SCENARIOS.every(s => pairs.has(`${a}/${s}`))), 'every audience needs each of the six scenarios exactly once')
  return { prepared_tasks: suite.tasks.length, audiences: AUDIENCES.length, scenarios_per_audience: SCENARIOS.length, observed_task_runs: 0, observed_routing_results: 0 }
}

const args = process.argv.slice(2)
if (args.some(arg => arg !== '--self-test') || args.length > 1) throw new Error('usage: node launch/validate-tasks.mjs [--self-test]')
const suite = JSON.parse(readFileSync(join(ROOT, 'launch/task-suite.json'), 'utf8'))
try {
  const summary = validateSuite(suite)
  let rejectedMutations = 0
  if (args.includes('--self-test')) {
    for (const mutate of [s => s.tasks.pop(), s => { s.tasks[1] = s.tasks[0] }, s => { s.tasks[0].status = 'passed' },
      s => { s.tasks[0].result = { passed: true } }, s => { s.tasks[0].prompt = 'Use Fabius to do this.' },
      s => { s.tasks[5].language = 'en' }, s => { s.tasks[0].routing_hypothesis.observation = 'loaded' },
      s => { delete s.tasks[0].input }, s => { s.tasks[0].acceptance = [] },
      s => { s.tasks[0].required_evidence.candidate_host_profile = 'synthetic-fixture' },
      s => { s.evidence_profiles['synthetic-fixture'].counts_as_host_execution = true },
      s => { s.tasks[0].input.tool_setup.status = 'observed' },
      s => { s.tasks[0].input.fixture_paths = ['../LICENSE'] },
      s => { s.tasks[14].required_evidence.candidate_host_additional = [] }]) {
      const altered = structuredClone(suite); mutate(altered)
      let rejected = false
      try { validateSuite(altered) } catch { rejected = true }
      assert(rejected, 'validator accepted an invalid prepared-suite mutation')
      rejectedMutations++
    }
  }
  console.log(JSON.stringify({ status: 'prepared-suite-structure-valid', ...summary, rejected_invalid_mutations: rejectedMutations }))
  console.log('No task was run. No candidate-host, comparative or independent-user result is asserted.')
} catch (error) {
  console.error(`prepared-suite-validation-failed: ${error.message}`)
  process.exitCode = 1
}
