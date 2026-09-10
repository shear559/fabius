// Deterministic worked adapter: no model, network, shell or output-file writes.
import { readFileSync } from 'node:fs';
import { executePlan } from '../scripts/cohort.mjs';

const plan = JSON.parse(readFileSync(new URL('./sales-plan.json', import.meta.url)));
const result = await executePlan(plan, {
  concurrency: 2,
  authorize: ({ task, agent }) => ['coffee', 'tea', 'mug', 'total', 'review'].includes(task.id)
    && ['write', 'execute', 'network'].every(cap => agent.permissions[cap] === 'deny')
    && agent.tools.every(tool => tool === 'read_file'),
  runner: async ({ task, dependencies }) => {
    if (task.agent === 'reviewer') {
      const actual = dependencies.total.amount;
      return { verdict: actual === task.input.expectedTotal ? 'accept' : 'revise', findings: actual === task.input.expectedTotal ? [] : [{ severity: 'P1', location: 'total.amount', problem: `Expected ${task.input.expectedTotal}, received ${actual}.`, fix: 'Check the input quantities and arithmetic.' }], limitations: ['Synthetic arithmetic demo; no model was called.'] };
    }
    if (task.id === 'total') {
      const amounts = Object.values(dependencies).map(row => row.amount);
      return { amount: amounts.reduce((a, b) => a + b, 0), evidence: [amounts.join(' + ')] };
    }
    return { amount: task.input.quantity * task.input.unitPrice, evidence: [`${task.input.quantity} * ${task.input.unitPrice}`] };
  },
});
console.log(JSON.stringify(result, null, 2));
if (result.status !== 'succeeded' || result.tasks.review.output.verdict !== 'accept') process.exitCode = 1;
