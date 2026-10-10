# Fabius engineering workflows

Use the procedure whose output answers the current request. These are original Fabius procedures, maintained alongside the active engineering contract. They replace the old imported process directories. They are neither aliases for an external skill nor a reason to install another framework.

## Turn an ambiguous request into a buildable change

Read the call site, the current behavior and one representative consumer. Translate the request into a user-visible difference and an observation that would distinguish success from the current result. Preserve the project's terms; introduce a new term only when the existing vocabulary cannot name the distinction.

Keep a question pending only when its answer changes behavior, data ownership, a costly dependency or permission. Implement independent reversible work while waiting. When a question survives a targeted read of the repository, put it as the candidates that read produced, or as a short set of options that exclude one another, one marked as the default. If an optional question goes unanswered, the plan takes the default and lists it among its assumptions; a question on an authority boundary the existing authorization does not already cover — a WRITE or EXECUTE rung of the acting ladder ([`../../fabius/references/orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §9) not yet granted, an irreversible or outward-facing action — stays pending, and waiting never turns silence into authorization. For an architecture fork, compare the existing solution with the smallest viable replacement using the actual traffic, failure and maintenance constraints. Record what evidence could reverse the choice. Detailed architecture assessment lives in [architecture-decisions.md](architecture-decisions.md).

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

Declare the review's error bias before the first file is opened. A security pass and a low-effort pass are tuned for precision: few findings, each with a traced path, under praesidium's confidence gate ([`../../fabius-praesidium/references/ai-review.md`](../../fabius-praesidium/references/ai-review.md#the-confidence-gate--the-core-mechanism)). A high-stakes correctness review is tuned for recall, its depth set from the route's measured failure rate (M3) rather than from a label. Under recall, a finder forwards every candidate it can attach a failure scenario to, including the ones it doubts — a candidate the finder drops is one the verifier never sees.

The verifier grades as [architecture-decisions.md](architecture-decisions.md#challenge-every-material-conclusion) does — confirmed, narrowed, unresolved, discarded — and discards only on a counterexample, an existing control or test, or a recorded accepted trade-off it can quote (the bar of [process-playbook.md](process-playbook.md)). A state that is rare but reachable (an empty collection on first run, a locale that changes a sort order, a clock that steps backwards) stays PLAUSIBLE under R15; unlikely is not refuted. These grades apply to findings; the runtime state of a change takes the PASS / FAIL / BLOCKED / SKIP verdict in [codebase-and-proof.md](codebase-and-proof.md) §4.

One angle is mandatory in every correctness review: each guard the diff removes or rewrites — which invariant did it hold, and which new line holds it now? No such line is itself a finding. When the findings list must be truncated, a correctness defect keeps its place before any cleanup. cohors's *Adversarial verify* ([`../../fabius-cohors/SKILL.md`](../../fabius-cohors/SKILL.md)) remains the orchestration for an independent skeptic; a refuting vote counts toward the kill only when it carries a reason of the quotable kind above (the bar in [process-playbook.md](process-playbook.md)).

For parallel work, assign disjoint files and a shared interface, then delegate orchestration mechanics to Cohors. Review each result against its acceptance condition before integrating. Run the aggregate tests on the combined tree; several green isolated branches do not establish that their combination works.

## Preserve the quality bar while changing the code

Read the existing checks and accepted standards before proposing another gate. Keep each adopted constraint with its scope, measured baseline or chosen limit, direction of improvement, exact check and execution stage. A number without a check is an aspiration; a baseline without its workload and environment is not comparable. When no target was chosen, measure first and prevent regression rather than inventing a percentage. Existing deficits remain visible beside new regressions.

Place checks where their evidence becomes available: cheap local checks near the edit, related behavior checks at completion, environmental checks against the actual running surface. Reuse an existing coverage report or trace. A missing tool or unavailable environment is missing evidence, never a pass; do not install another checker merely because a template names one.

Review changes to the checks themselves: a lower threshold, new suppression, skipped or deleted test, removed assertion, unfinished stub or broader exception can manufacture green. Compare against the correct base and include staged, unstaged and relevant untracked work. A scan flags candidates; it cannot decide whether a replacement assertion preserves the invariant. For every justified weakening, name the old protection, the replacement or accepted exception, its owner and any expiry. Keep that decision reviewable under the existing authorization; a failing check is not permission to weaken it.

**Proof:** execute the adopted check on the changed behavior and, where practical, an input that violates its constraint. Keep the command, relevant output and exit status. A checker unable to obtain its comparison base must report failure or unavailable evidence distinctly from clean. A test renamed with equivalent coverage is different from one deleted to conceal the regression; inspect the actual assertion before accepting either verdict.

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

The report uses `schema: "fabius-evidence/v1"`, the `planSha256` returned by `plan`, `sources` with `{path, sha256}`, and check results with `{id, status, exitCode, observation, log: {path, sha256}}`. A skipped or blocked check instead carries `{id, status, reason}` with no execution evidence; `status` accepts the contract word or its past tense (`pass`/`passed`, `fail`/`failed`, `skip`/`skipped`, `blocked`) and is recorded normalized. Missing, stale or skipped evidence yields `incomplete`; any recorded failing or blocked check yields `failed` — what each verdict means is stated once, in [codebase-and-proof.md](codebase-and-proof.md) §4. A complete ledger means that its recorded checks and current bytes agree, not that arbitrary supplied evidence is trustworthy.

Generate hashes from the actual files after executing the checks. Keep logs inside the selected root, review them for sensitive content and retain their full output outside the model context when appropriate. The checker accepts up to 200 sources, checks and criteria, files up to 16 MiB, and JSON input up to 1 MiB. Hidden paths, secret-bearing filenames and symlinks are rejected. It is a local consistency check, not an OS sandbox.

Informed by **system_prompts_leaks** (asgeirtj, CC0-1.0 compilation; the collected vendor prompts remain their vendors' text) — studied for the explore-then-ask question shape, the assumed-default versus pending-authority split, the declared review bias, the forward-every-stateable-candidate rule, the removed-guard angle and the quotable-refutation bar (snapshot fetched 2026-09-13); and **Agent Skills** (addyosmani/agent-skills, MIT), read at revision 1be8e34187e34647bb83adc3a1323b26ae6f6abe (2026-10-10) — studied for measured quality constraints, checks placed by evidence and cost, and diff review for a lowered verification bar. Mechanisms re-expressed in fabius's own voice; no prompt text or checker code carried, nothing bundled. See credits/README.md.
