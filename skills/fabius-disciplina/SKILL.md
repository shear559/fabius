---
name: fabius-disciplina
description: >
  Plan and review software architecture; build, debug, refactor, and verify non-trivial changes.
  Fabius's engineering process connects scope, evidence, alternatives, source/test impact, and
  observed results. Architecture analysis separates design direction from production proof;
  implementation follows the user's existing authorization. Use for system design, architecture
  assessment, technology choices, migrations, root-cause debugging, and completion checks.
  UI craft belongs to fabius-decor; agent engineering belongs to fabius-cohors.
when_to_use: >
  "where do we start", "write the tests first", "it keeps regressing", "why is it slow",
  "why does it still fail", "walk me through the fix before coding".
license: UNLICENSED
metadata:
  author: shear559
---
<!-- © 2026 shear559 · fabius · provenance fab1-6bbf82d118bce2cee9d7ac71f034fa26 · release evidence: PROVENANCE.md · github.com/shear559/fabius -->

# Fabius Disciplina — connect a change to its proof

Disciplina owns engineering work from understanding the current system through verifying the requested result. Architecture assessment, implementation and debugging use different entry points into the same evidence loop. A review request produces findings; an implementation request authorizes the necessary reversible edits.

## Establish the decision

Read the relevant code, callers, recent changes and accepted project decisions. Identify the current behavior, the requested difference and the smallest observation that distinguishes the two. Preserve working strengths and the project's vocabulary.

For a material architecture choice, compare viable alternatives, including retaining the current design. Support recommendations with inspected source or explicit requirements. Separate a promising design from evidence that it has run in production. Use [architecture-decisions.md](references/architecture-decisions.md) for the decision record and [transactional-updates.md](references/transactional-updates.md) for changes to running code or mutable state.

Ask only for information that changes the implementation or a real authority boundary. Existing authorization remains relevant. State small reversible assumptions and continue; do not require approval of a routine plan merely because the work has several steps.

## Build a plan that can fail

For multi-step work, connect each step to a verification observation: `step → verify`. Name inputs that depend on earlier results before scheduling later work. Batch independent reads and revise only the affected portion when evidence changes. Revisit remaining acceptance conditions during long runs so incidental subproblems do not replace the objective.

Choose an early vertical slice that reaches a useful output. Use [engineering-workflows.md](references/engineering-workflows.md) for ambiguity, prototyping, implementation, review, integration and handoff. Keep a prototype tied to one uncertainty; it does not acquire production guarantees by working once.

## Map source to observable behavior

Before changing non-trivial logic, map each affected source unit to a test or executable check that reaches its behavior. Read the assertion. A nearby test or a successful import is insufficient coverage.

Where the project provides a viable test seam, reproduce the intended failure before the patch. Confirm that it fails for the behavior being changed, not for missing setup. Implement the smallest coherent correction and run every covering check. Broaden validation where the dependency map, an observed failure or an uncovered concern warrants it.

If no useful assertion exists, create a small reproduction at the real boundary. Generated output and simple configuration can use a parser, compiler, render or direct read-back. Do not manufacture a unit test that merely restates the implementation.

## Diagnose before another edit

Reproduce the input and state, reduce the failing path, then choose a discriminating experiment among plausible causes. Read each tool result before using it as a premise for the next action (R5). Dependencies bind to observed outputs (R6).

When repeated attempts do not improve the verification result, reconsider ownership, lifetime, ordering and coupling. A retry should carry the previous failure signal and the changed hypothesis (M4). Roughly three unproductive cycles is a useful review point, not evidence that one more identical call will work. Escalate when the missing input or permission is external.

Branch candidate solutions only when a cheap evaluator can distinguish useful partial results and early mistakes are expensive (R7). Refine from an attributable test, compiler error or review finding (R8); unsupported self-criticism is not an oracle. The router's [routing-policy.md](../fabius/references/routing-policy.md) owns these policy identifiers.

Performance work needs a fixed workload, repeated measurements and one isolated variable per comparison. Report measurement conditions and uncertainty. Use [process-playbook.md](references/process-playbook.md) for worked diagnosis and oracle selection, and [testing-toolkit.md](references/testing-toolkit.md) when the current stack lacks a suitable instrument.

## Verify the combined result

Recheck the accepted scope against the diff and run the affected behaviors on the combined tree. Read back a written record, inspect the rendered DOM, verify a returned artifact or execute the relevant program. Successful transport or exit status alone does not prove the requested state.

For a UI, verify the actual environment and interaction, with console and network failures captured. Query semantic state and computed visibility; inspect screenshots for visual questions. Native app checks use [simulator-verify.md](references/simulator-verify.md). Larger codebase and browser proof workflows use [codebase-and-proof.md](references/codebase-and-proof.md).

Check the strength of the evidence as well as its color: where practical, an old-behavior or mutation control should break the relevant assertion. Investigate suspicious runner output before accepting its verdict. State missing or skipped checks explicitly.

For a large acceptance map, [evidence.mjs](scripts/evidence.mjs) checks plan coverage, recorded outcomes and current source/log hashes. It does not execute tests or authenticate a supplied report; its complete result is a consistency claim. The schema and CLI are in [engineering-workflows.md](references/engineering-workflows.md#optional-machine-readable-completion-ledger).

## Close the work at the correct boundary

Report what changed, what ran and what remains unverified. Distinguish source readiness, a pushed commit, deployment, installation and activation in a fresh session. Perform already-authorized finishing work; request a decision only at the remaining boundary that actually needs one.

Record durable outcomes through Archivum when writing is authorized. Give a handoff the precise remaining action and current evidence, so continuation can resume rather than reconstruct the task. Parcus keeps the implementation and explanation proportional; Cohors owns any delegated execution.
