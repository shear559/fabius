# Source-fold continuation — protocol before generation

Status: preparation only. No scored generations have started. The execution budget and canary acceptance are required before launch. This document, the harness, the input manifest and the arm schedule must be committed before the first scored run.

## Questions and preserved evidence

Does the candidate improve a model's performance over the preceding Fabius package under the same conditions? Does it improve over the same model without Fabius? What extra context, tool use, time and reported cost accompany each result?

The preceding [public-benchmark study](../2026-10-public-benchmarks/PROTOCOL.md) and its [specialist extension](../2026-10-public-benchmarks/PROTOCOL-SKILLS.md) remain historical evidence. Its completed report, staged release changes and raw records are preserved separately. None is overwritten, pooled into contemporary pairs or relabelled as a result for the candidate. The working-copy snapshot has a complete byte manifest because a commit ID alone does not identify staged files.

The original single-turn harness allowed only `Skill`. The source fold changes on-demand references while leaving all fifteen `SKILL.md` files unchanged. Repeating a contract-only prompt cannot test those additions. This continuation is a **new tool-access variant**: single-turn tasks permit confined `Read` as well as `Skill` in every arm. It is not a direct replication of the old tool-access conditions.

## Frozen packages and execution environment

- Old package: signed `v3.3.0-sealed`, commit `ce34f26b2149860ea63df2446852d077206d6c52`.
- Candidate: `6fb0ab0af9104166db1b59e04b3f0471a58898b3`, the reviewed source fold. This is a source candidate, not a new signed release or an installed version claim.
- Requested model: `claude-sonnet-5-5`; native Claude Code `2.1.289`. Record the binary hash and actual init model in every attempt. An unavailable model is a blocked cohort, not permission to substitute another model.
- Each model-visible package contains its original `skills/`, plugin manifest and portable core/reference documents. Benchmark code, evaluation prompts, gold data, results, reports, receipts and unrelated repository files are excluded identically. Record every included file's hash and a hash of the filtered manifest. Filtering is part of the treatment definition, not a claim to have evaluated an unmodified full installation.
- One fresh working directory and conversation per attempt; project-only settings, strict MCP configuration, no session persistence and no external browsing. Authentication uses the existing account through the supported CLI; credentials are never copied into an experiment.
- Confined file access admits only that attempt's task assets and assigned package. A canary must demonstrate the allowed reads and the denials before scored generation. SWE additionally requires a separate repository-profile canary proving file edits, wrapper-only execution, denied host shell/file access and the resulting patch. A read-only canary cannot establish that execution boundary. No respondent runs inside the maintainer's current chat or inherits its user memory or skill catalog.

## Contemporary arms

1. `baseline`: task verbatim, no Fabius package.
2. `old`: the frozen old package, directly invoked owner listed below.
3. `candidate`: the frozen candidate package, the same invocation.

Both package arms receive the same task and invocation. Router uses `/fabius`; a specialist uses `/fabius:fabius-<owner>`. No reference is force-injected and no answer-specific hint is added to the candidate. Tools, task assets, limits, execution environment and scoring are otherwise matched. Keep natural failures to discover a reference in the assigned arm's results.

This cohort does not include a generic-process control or a component ablation. It can support a scoped package comparison; it cannot establish a unique mechanism or superiority to all other guidance. A forced-reference or workflow-specific study needs its own frozen tasks, controls and protocol. The maintenance smoke prompts are development material and are not that study's held-out test set.

## Coverage and unchanged task selection

| Benchmark | Owner | Planned items | Replicates per arm | Primary endpoint |
|---|---|---:|---:|---|
| SWE-bench Verified Mini | disciplina | 50 | 2 | official resolved result |
| IFEval | router | 541 | 1 | prompt-level strict accuracy |
| HumanEval+ | parcus | 163 | 1 | EvalPlus plus pass@1 |
| CyberSecEval Python | praesidium | 200 | 1 | not flagged insecure by the frozen detector |
| LAB-Bench ProtocolQA + SeqQA | scientia | 220 | 1 | correct option |
| FinQA | fortuna | 200 | 1 | frozen numeric-answer match |
| DS-1000 excluding PyTorch/TensorFlow | doctrina | 200 | 1 | official execution tests |
| SmartBugs-curated | catena | 143 | 1 | frozen category match |
| BFCL non-live AST | cohors | 200 | 1 | official AST result |
| LongMemEval oracle | archivum | 120 | 1 | calibrated judge correctness |
| Design2Code | decor | 80 | 1 | continuous overall visual score |

Use the previous frozen item selection and prompt template, not a new sample chosen from old outcomes. HumanEval/32 stays excluded because its canonical solution failed the registered execution validity check. IFEval item 143 returns to the new schedule: its earlier exclusion was an infrastructure failure, not an invalid task. Retain its new outcome or infrastructure classification under the same rules as every other item.

The prepared LongMemEval and Design2Code samples were not generated in the earlier study. Include their prepared IDs, data hashes and newly frozen arm order; do not imply they have historical results. Mercatus, machina, ludus and concilium remain outside this objective public-benchmark cohort for the reasons recorded in the earlier protocol. Eleven benchmarks is not fifteen measured skills.

The complete plan contains 6,501 scheduled headless invocations before retries and non-scored probes. A headless invocation may contain several model turns; this count is not an API-call count or a price quote.

## Order, limits and independent states

Freeze the schedule using seed `20261010`. Preserve selected item orders for previously scheduled benchmarks and prepared sample orders for the two unrun benchmarks. Randomize the three arm positions within each item/replicate. Complete a block before advancing; a quota stop can leave a block pending, which must be resumed or reported incomplete, never filled with zeros.

The initial controller is serial. Single-turn profiles retain the earlier ceiling of eight turns and 300 seconds, now with confined `Read` available equally. A task exhausting that limit is not rerun to improve its answer. SWE retains its separately registered 150-turn/40-minute task profile, wrapper-only shell and networkless container; it cannot run through the single-turn text adapter. Its actual execution and oracle adapters must pass readiness and validity checks first.

Every attempt reserves one count in an atomic shared ledger before launch. At most two infrastructure retries per condition are allowed across the lifetime of the study; restart does not reset them. Limit or authentication failures pause the controller, with no automatic retry loop. A later authorized resume preserves the original attempts and the manifest identity. No fallbacks to another model, account or key are permitted.

**Budget is awaiting the owner's new selection.** The earlier temporary permission to use 97% of weekly quota and 90% of the five-hour window was granted to finish the old study. It is not inherited here. Provider execution remains disabled until an explicit budget record specifies the weekly and five-hour ceilings, hard attempt count and permission for bounded non-scored meter probes. A current meter must be established through the supported harness and checked before every scheduled invocation. Missing, stale, rejected or exhausted meter data pauses work; it never means zero usage. No paid API fallback is enabled.

These are admission thresholds, not a guarantee against concurrent account activity or the unknown consumption of a call already admitted. Keep the actual pre/post readings and reset times. Resume only when the existing authorization still applies and a fresh meter admits the next invocation. Keep completed blocks; never rerun them to seek a different result.

## Attempt classification and exposure evidence

Bind every attempt to the protocol, harness, binary, filtered-package manifest, task prompt, assets, model and limits. A pre-existing output is reusable only when those identities match. Attempt directories are immutable; an interrupted reservation remains charged to the ledger until explicitly reconciled.

An init with the wrong model or wrong package/skill inventory is infrastructure failure. Absence of a valid init remains infrastructure failure even on timeout. An admitted run with a valid init and a task-level turn/time limit can be an outcome, retaining its final text or repository patch and its exact stop reason. Authentication, transport and provider-limit errors remain separate. Keep all attempts, including blank answers, questions, refusals, missed routes and failures.

Record each reference request and successful returned text/range separately, with hashes, truncation and position in the event stream. A request, a skill call or a prompt-token increase alone does not prove delivery of a reference. Unknown delivery stays unknown. File hashes identify supplied bytes; skill-command prompt expansion remains distinct from a reference-file read. Seal completed attempt bytes, including patches, and verify their identities before resume and scoring. Reuse a completed scoring batch only when its bound inputs and output receipts still match; keep failed scoring attempts in separate directories.

Analyze natural-loading arms as assigned. Read-conditioned summaries may describe exposure but are not a selected-subset causal comparison. No candidate rule or reference changes after scored outcomes are inspected; a necessary change starts a new, separately pinned cohort.

## Scoring readiness and validity

Copy required frozen datasets and scorer code into a new data root. Never run a preparer or scorer in the old study's folders, never symlink a writable scorer/cache back to them, and never mount the historical cache read/write. Reuse installed interpreters only as dependencies, with bytecode writing disabled. Bind scorer source hashes and validate all output paths before execution.

Scoring starts only after generation and all budget decisions for that benchmark are closed. Use its frozen official endpoint, report exclusions and failures, and preserve the scorer receipts. No infrastructure-missing observation becomes an incorrect or correct answer by coercion.

- SWE requires a real repository patch and the official Docker oracle. The old environment-validity checks, pinned images and patch-base rules still apply.
- HumanEval+ requires Linux execution, the canonical-solution validity check in the same scoring session and repeated scoring to report unstable results.
- LongMemEval requires an explicit available judge, frozen judge prompts and passing gold/wrong self-checks. A prompt prepared for a judge is not a scored answer. No judge substitution is implicit in this protocol; until resolved, this benchmark is pending.
- Design2Code requires actual screenshot delivery and the frozen render/visual-metric dependencies. Its primary result stays continuous; the historical secondary threshold must never replace the primary score or turn it into a binary experiment. Until the real pipeline is verified, this benchmark is pending.

An absent dependency blocks its benchmark and is reported. It does not authorize installation, model-weight downloads, a paid judge or a replacement endpoint without resolving that concrete prerequisite.

## Analysis fixed before generation

The planned quality family contains **all 33 contrasts**: `candidate − old`, `candidate − baseline`, and `old − baseline` for each of the eleven benchmarks. Apply Holm correction across that complete family. A missing comparison retains its place in the denominator and is labelled incomplete; do not shrink the family after observing results.

Reuse the earlier statistical procedures: exact paired McNemar for one binary result per item; paired sign-flip and item-level BCa intervals for repeated or continuous outcomes; stratify SWE resampling by repository. Pair only contemporary outputs of the same task and replicate, never historical controls. Report realized paired counts and all missingness. Intervals remain explicitly unadjusted. Use the inherited five-percentage-point equivalence/non-inferiority margin only for the eligible binary objective single-turn endpoints; do not invent an equivalence margin for SWE or continuous Design2Code.

Publish every contrast, including losses, inconclusive comparisons and extra cost. Failure to detect a difference is not proof of equivalence. Keep correctness, unsupported claims, delivery evidence, cost, tokens and elapsed time as separate observations. Efficiency summaries are descriptive and accompany the corresponding quality verdict. Report finite-sample/power limits; do not compare these harness-specific rates to external leaderboards.

## Publication boundary

Raw commands and transcripts can contain local paths and account identity. Keep them private until the established longest-first, escape-aware scrub and independent substring scan pass; scan any exported archive again. Publish only substantiated scope, exact versions, hashes, attempts, exclusions, realized counts, budgets and results. The existing staged release is not treated as published solely because its draft report names a future release.

Source preparation, canary acceptance, scored generation, completed analysis, public publication and installed activation are separate states. This protocol currently establishes only the first.
