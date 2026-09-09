import { execFileSync } from 'node:child_process'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'

export const meta = {
  name: 'fabius-eval-v7-fbs',
  description: 'Versioned FBS text-only experiment: BASE / FAB / FAB_MEMORY, fixed model-graded checks and two blind rubric judges',
  phases: [
    { title: 'Load', detail: 'deterministic filesystem read and contract manifest hashes; fail before calls on mismatch' },
    { title: 'Generate', detail: 'fresh-context text answers; no tool execution' },
    { title: 'Grade', detail: 'exact task check IDs with boolean decisions and evidence' },
    { title: 'Judge', detail: 'two identified blind judges; exactly seven integers from 0 through 4' },
  ],
}

// Host Workflow adapter. This file intentionally retains its top-level return;
// use node evals/text-eval.mjs for ordinary Node preparation, fixtures and replay.
// args.tasks must contain parsed suite records, not just a tiers selector.
const REPO = process.env.FABIUS_REPO || execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim()
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const { prepareRun, runPrepared } = await import(pathToFileURL(join(REPO, 'evals/text-eval-core.mjs')).href)
phase('Load')
const plan = prepareRun({ repo: REPO, tasks: A.tasks, model: A.model, graderModel: A.graderModel, judges: A.judges, run: A.run })
log(`${plan.tasks.length} tasks × 3 modes; at most ${plan.max_calls} calls. Contract bytes verified; memory hashed separately. Text experiment only.`)
const result = await runPrepared(plan, (prompt, options) => agent(prompt, options), { phase })
log(`${result._meta.valid_cells}/${result._meta.expected_cells} complete cells; ${result._meta.status}`)
return result
