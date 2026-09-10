# Execute a bounded dependency plan

The original [cohort.mjs](../../scripts/cohort.mjs) module runs a finite directed acyclic graph through a caller-supplied function. It has no package dependencies and uses Node 22 or newer. Importing it performs no task, model call, shell command or network request.

From the repository root:

```sh
node skills/fabius-cohors/scripts/cohort.mjs check skills/fabius-cohors/examples/sales-plan.json
node skills/fabius-cohors/scripts/cohort.mjs plan skills/fabius-cohors/examples/sales-plan.json
node skills/fabius-cohors/examples/demo.mjs
node --test skills/fabius-cohors/scripts/*.test.mjs
```

`check` prints the validated agent/task counts. `plan` prints an immutable-plan representation, deterministic topological order and dependency layers. Neither CLI command executes a task. The demo executes only supplied arithmetic and a deterministic review; it is not a model benchmark.

## Plan format

A plan has exactly `schema: "fabius-cohort/v1"`, an `agents` array and a `tasks` array. Each agent contains:

- `id`, `description`, `instructions`;
- `tools`: unique adapter tool names;
- `permissions`: explicit `read`, `write`, `execute`, `network`, each `allow`, `ask` or `deny`;
- `output`: a supported closed object schema.

Each task contains `id`, `agent`, JSON-object `input`, and `dependsOn`, a unique array of task IDs. Agent/task IDs use lowercase letters, digits, `_` or `-`, start with a letter and have at most 64 characters. Unknown fields, missing references, duplicate IDs, duplicate edges and cycles fail before authorization or execution. Agent definitions do not inherit another agent's capabilities.

Limits: 1–32 agents, 1–64 tasks, 256 KiB plan JSON, JSON nesting depth 16 and 10,000 nodes per copied input/output value. Plans and runner-boundary values must be ordinary JSON data: no accessors, custom objects, functions, nonfinite numbers or sparse arrays. Returned output is capped at 64 KiB per task.

## Output schema subset

This is a small explicit subset, not a general JSON Schema engine. Unsupported keywords fail validation.

| Type | Supported fields beyond `type` |
|---|---|
| `object` | `properties` with at most 32 keys, `required`, mandatory `additionalProperties: false` |
| `array` | `items`, mandatory `maxItems` from 0 to 256 |
| `string` | Optional `maxLength` from 0 to 8192; default 8192; optional `enum` |
| `number`, `integer`, `boolean`, `null` | Optional `enum` |

Schemas nest at most eight levels. An enum contains 1–32 unique values of its declared scalar type. Every task's top-level output is an object. Validation occurs before an output can reach a dependent task.

## Execution interface

```js
import { executePlan, validatePlan } from './skills/fabius-cohors/scripts/cohort.mjs';

const checked = validatePlan(plan); // { plan, order, levels }; copied and deeply frozen
const receipt = await executePlan(checked.plan, {
  concurrency: 2,
  signal: abortController.signal,
  authorize: ({ task, agent }) => policyAllows(task, agent),
  runner: ({ task, agent, dependencies, signal }) => runWithHost({ task, agent, dependencies, signal }),
});
```

`policyAllows` and `runWithHost` belong to the integrating caller; no default implementation is supplied. Authorization must return a boolean synchronously. Async or malformed results fail closed, and policy exceptions are reported as authorization failures. The callback can use authority already granted by the user; this interface does not add a human checkpoint.

The runner receives the copied/frozen task and agent definitions, a frozen map of direct dependency outputs keyed by task ID, and an `AbortSignal`. It returns a JSON object or a promise for one. A failing runner or invalid output blocks descendants, while independent branches continue. Concurrency defaults to two and must be an integer from one through sixteen. Ready tasks fill free slots without waiting for an unrelated branch at the same depth.

The receipt has overall `status` and `tasks`, keyed by ID. Final task states are `succeeded` with `output`, `failed` with an error `stage` and `message`, `denied`, `blocked` with `blockedBy`, or `cancelled`. Overall status is `succeeded` only when every task succeeds; otherwise `failed`, or `cancelled` when the caller aborted. A denied task never reaches the runner.

Cancellation stops new launches, signals active runners and waits for them to settle. A runner that ignores the signal can delay completion indefinitely. Cancellation neither kills a process nor rolls back side effects; an interrupted external action may require reconciliation before retrying. Failed work is never automatically retried.

## Host boundary

The policy callback and runner execute as trusted JavaScript in the caller's process. Frozen data prevents accidental cross-task mutation; it does not sandbox a malicious function. The host supplies real tools, model access, per-tool approval, deadlines, filesystem isolation, network restrictions, delegation and persistence. Receipt content comes from those runners and can require redaction before sharing. The scheduler does not implement a provider SDK, dynamic swarm, durable job service or billing cap.
