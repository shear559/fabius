# Fabius engineering workflows

Use the procedure whose output answers the current request. These are original Fabius procedures, maintained alongside the active engineering contract. They replace the old imported process directories. They are neither aliases for an external skill nor a reason to install another framework.

## Turn an ambiguous request into a buildable change

Read the call site, the current behavior and one representative consumer. Translate the request into a user-visible difference and an observation that would distinguish success from the current result. Preserve the project's terms; introduce a new term only when the existing vocabulary cannot name the distinction.

Keep a question pending only when its answer changes behavior, data ownership, a costly dependency or permission. Implement independent reversible work while waiting. For an architecture fork, compare the existing solution with the smallest viable replacement using the actual traffic, failure and maintenance constraints. Record what evidence could reverse the choice. Detailed architecture assessment lives in [architecture-decisions.md](architecture-decisions.md).

## Prototype one uncertainty

A prototype ends with a decision, not with an accidental production service. Name the uncertainty, choose a representative input and set the observation that will settle it. Put throwaway files in a clearly separate scratch location. For a UI uncertainty, render the actual interaction at mobile width; for a data or algorithm uncertainty, execute representative and adversarial inputs. Record the result and remove the scratch files you created after extracting the useful finding.

Promoting a prototype requires explicit production requirements: persistent state, failure handling, tests, permissions and operational ownership. A successful demonstration does not establish those properties.

## Implement a vertical slice

Map each changed behavior to the code that implements it and the test that would detect its absence. Start with one input through the real boundary to an observable output. A changed response shape, for example, needs its consumer assertion as well as a unit test for the mapper. An import succeeding is not a test of behavior.

Run the failing behavior check before the change where a viable seam exists. Setup errors are not behavioral failures. Make the change, rerun the covering tests, then broaden only along the dependency map. Do not accumulate separate testing and implementation passes that cannot be connected to a specific regression.

## Diagnose a defect

Capture the exact input, actual state and expected state. Reduce the failing path without removing the condition that triggers it. Choose among competing causes with one discriminating experiment at a time. Record the observation before deciding the next action.

When several attempts repeat the same failure, pause edits and revisit the model of the system: shared state, lifetime, ownership, ordering or a missing boundary. A new retry should name new evidence or a different mechanism. Escalate when the missing information or authority can only come from outside the task.

For latency, hold the workload and environment fixed, measure repeated runs, isolate one variable and compare distributions. State cache state, sample count and network conditions. Do not report an optimization from a faster single run or from reduced file size alone.

## Review and integrate a change

Separate behavior defects, maintainability costs and stylistic preferences. A blocking finding needs a concrete input or execution path, an observed or demonstrable consequence, and a correction. Recheck the most severe findings against contrary evidence before presenting them. Respect explicitly accepted trade-offs.

For parallel work, assign disjoint files and a shared interface, then delegate orchestration mechanics to Cohors. Review each result against its acceptance condition before integrating. Run the aggregate tests on the combined tree; several green isolated branches do not establish that their combination works.

## Finish and hand off

Compare the final diff with the accepted scope. Record what changed, what was executed, where its evidence lives and what remains unverified. Distinguish a local commit, remote push, deployed build, successful installation and a newly active session. Each is a separate observation.

A handoff carries the current objective, decisions, modified files, precise remaining steps, failing command if any, and the reason work stopped. Keep unavailable evidence unavailable; never write a suggested result as an observed result. Durable project records belong in the workspace's authorized store, under Archivum's contract.

## Optional machine-readable completion ledger

For a change with many acceptance checks, [`../scripts/evidence.mjs`](../scripts/evidence.mjs) checks that the supplied plan and evidence agree and that selected source files and logs still match their SHA256 digests. It does not execute a command, judge whether a test is adequate, or authenticate who produced a report.

```sh
node skills/fabius-disciplina/scripts/evidence.mjs plan plan.json
node skills/fabius-disciplina/scripts/evidence.mjs check plan.json report.json --root /absolute/workspace
```

The plan uses `schema: "fabius-plan/v1"`, a `goal`, a nonempty `sources` array of relative file paths, `checks` with `{id, command, covers}`, and `criteria` with `{id, expectation, checks}`. Every source must have coverage and every check must serve a criterion. Commands are labels; the checker never runs them.

The report uses `schema: "fabius-evidence/v1"`, the `planSha256` returned by `plan`, `sources` with `{path, sha256}`, and check results with `{id, status, exitCode, observation, log: {path, sha256}}`. A skipped check instead carries `{id, status: "skipped", reason}`. Missing, stale or skipped evidence yields `incomplete`; any recorded failing check yields `failed`. A complete ledger means that its recorded checks and current bytes agree, not that arbitrary supplied evidence is trustworthy.

Generate hashes from the actual files after executing the checks. Keep logs inside the selected root, review them for sensitive content and retain their full output outside the model context when appropriate. The checker accepts up to 200 sources, checks and criteria, files up to 16 MiB, and JSON input up to 1 MiB. Hidden paths, secret-bearing filenames and symlinks are rejected. It is a local consistency check, not an OS sandbox.
