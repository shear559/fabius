#!/usr/bin/env node
// No keys, provider clients, network or model calls in this entry point.
import { readFileSync, writeFileSync, realpathSync } from 'node:fs'
import { basename, dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { prepareRun, offlineFixture, replay, sha256, RECEIPT_SCHEMA } from './text-eval-core.mjs'

const repo = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const [command, ...args] = process.argv.slice(2)
const options = {}
let inputBytes = null
let outputPath = null
const usage = 'node evals/text-eval.mjs prepare|fixture [--tiers 1,2,3] [--model ID] [--grader-model ID] [--judges ID,ID] --out FILE\nnode evals/text-eval.mjs replay --input RECEIPT.json --out FILE'
try {
  if (command === '--help' || !command) { console.log(usage); process.exit(0) }
  if (!['prepare', 'fixture', 'replay'].includes(command)) throw new Error(usage)
  for (let i = 0; i < args.length; i += 2) {
    if (!['--tiers', '--model', '--grader-model', '--judges', '--out', '--input'].includes(args[i]) || !args[i + 1] || args[i + 1].startsWith('--') || Object.hasOwn(options, args[i])) throw new Error(`invalid or duplicate option: ${args[i]}`)
    options[args[i]] = args[i + 1]
  }
  if (!options['--out']) throw new Error('--out is required; existing files are never overwritten')
  const requestedOutput = resolve(options['--out'])
  const output = join(realpathSync(dirname(requestedOutput)), basename(requestedOutput))
  if (/^evals\/results(?:\.|\/)/.test(relative(repo, output))) throw new Error('historical results paths are reserved')
  outputPath = output
  let result
  if (command === 'replay') {
    if (!options['--input']) throw new Error('--input is required for replay')
    inputBytes = readFileSync(options['--input'])
    const receipt = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(inputBytes))
    if (receipt._meta?.receipt_schema !== RECEIPT_SCHEMA || typeof receipt._meta.fixture !== 'boolean') throw new Error('unsupported receipt; historical files use verify-receipts.mjs')
    result = replay(receipt.plan, receipt.perTask.map(row => row.evidence).filter(cell => cell !== null), { fixture: receipt._meta.fixture })
    result.replayed_input = { sha256: sha256(inputBytes), bytes: inputBytes.length }
  } else {
    const tiers = (options['--tiers'] || '1').split(',').map(Number)
    if (tiers.some(t => ![1, 2, 3].includes(t)) || new Set(tiers).size !== tiers.length) throw new Error('--tiers must select unique values from 1,2,3')
    const files = tiers.map(t => ['evals/suite/tier1.smoke.jsonl', 'evals/suite/tier2.core.jsonl', 'evals/suite/tier3.stress.jsonl'][t - 1])
    const tasks = files.flatMap(file => readFileSync(join(repo, file), 'utf8').trim().split('\n').map((line, i) => {
      try { return JSON.parse(line) } catch { throw new Error(`invalid JSON: ${file}:${i + 1}`) }
    }))
    const plan = prepareRun({ repo, tasks, sourceFiles: files, model: options['--model'], graderModel: options['--grader-model'], judges: options['--judges']?.split(',') })
    result = command === 'prepare' ? plan : await offlineFixture(plan)
  }
  // Keep historical benchmark evidence immutable even when the caller chooses it.
  writeFileSync(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' })
  const status = result._meta?.status || 'prepared'
  console.log(`${status}: ${output}${result._meta?.fixture ? ' (synthetic infrastructure fixture; not benchmark evidence)' : ''}`)
  if (status === 'infrastructure-invalid') process.exitCode = 1
} catch (error) {
  // Preserve exact malformed input bytes for diagnosis; never turn parse failures into scores.
  if (inputBytes && outputPath) {
    try { writeFileSync(outputPath, JSON.stringify({ _meta: { receipt_schema: RECEIPT_SCHEMA, status: 'infrastructure-invalid' },
      error: error.message, byMode: null, deltas: null, raw_input: { encoding: 'base64', data: inputBytes.toString('base64'), sha256: sha256(inputBytes) } }, null, 2) + '\n', { flag: 'wx' }) } catch {}
  }
  console.error(`infrastructure-invalid: ${error.message}`)
  process.exitCode = 1
}
