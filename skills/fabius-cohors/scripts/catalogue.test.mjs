import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validatePlan } from './cohort.mjs';

const roles = JSON.parse(readFileSync(new URL('../examples/roles.json', import.meta.url)));
const fixture = new URL('../examples/sales-plan.json', import.meta.url);
test('every original catalogue role supplies a valid runnable definition contract', () => {
  assert.equal(roles.schema, 'fabius-cohort-catalog/v1'); assert.equal(roles.agents.length, 6);
  validatePlan({ schema: 'fabius-cohort/v1', agents: roles.agents, tasks: roles.agents.map(agent => ({ id: agent.id, agent: agent.id, input: {}, dependsOn: [] })) });
});
test('demo embeds the exact catalogue definitions it uses', () => {
  const plan = JSON.parse(readFileSync(fixture));
  for (const agent of plan.agents) assert.deepEqual(agent, roles.agents.find(role => role.id === agent.id));
});
test('CLI check and plan validate the real fixture without a runner', () => {
  const cli = fileURLToPath(new URL('./cohort.mjs', import.meta.url));
  const check = spawnSync(process.execPath, [cli, 'check', fileURLToPath(fixture)], { encoding: 'utf8' });
  assert.equal(check.status, 0, check.stderr); assert.deepEqual(JSON.parse(check.stdout), { ok: true, tasks: 5, agents: 2 });
  const plan = spawnSync(process.execPath, [cli, 'plan', fileURLToPath(fixture)], { encoding: 'utf8' });
  assert.equal(plan.status, 0, plan.stderr); assert.deepEqual(JSON.parse(plan.stdout).levels, [['coffee', 'tea', 'mug'], ['total'], ['review']]);
  const forbidden = spawnSync(process.execPath, [cli, 'execute', fileURLToPath(fixture)], { encoding: 'utf8' });
  assert.equal(forbidden.status, 1); assert.equal(JSON.parse(forbidden.stderr).ok, false);
});
test('deterministic adapter produces checked line totals and a successful review', () => {
  const run = spawnSync(process.execPath, [fileURLToPath(new URL('../examples/demo.mjs', import.meta.url))], { encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr);
  const result = JSON.parse(run.stdout);
  assert.equal(result.status, 'succeeded');
  assert.deepEqual(['coffee', 'tea', 'mug', 'total'].map(id => result.tasks[id].output.amount), [120, 90, 70, 280]);
  assert.equal(result.tasks.review.output.verdict, 'accept');
});
