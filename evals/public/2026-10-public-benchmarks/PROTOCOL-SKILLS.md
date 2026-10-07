# Fabius on public benchmarks — Part B: every skill on a benchmark of its own domain

**Version 1.0 · 2026-10-07 · fixed before the first Part B run.** Part A (`PROTOCOL.md`) measured the router: `/fabius` put the router contract in context in 803 of 803 runs, but a specialist was loaded in 1 run of 803, so Part A measured the router's rules, not the specialists'. The owner asked for every skill to be tested. Part B invokes each skill directly and measures it on an established public benchmark of that skill's domain. Everything not stated here is as in `PROTOCOL.md` v1.4 (harness, clean context, file-access denies, classifier, retries, item-ordered seeded scheduling, path audit, receipts).

## Arms

- `baseline` — the task verbatim, no plugin.
- `fabius-<skill>` — plugin loaded and the task prefixed with that skill's own slash command, `/fabius:fabius-<skill> `. A non-scored canary (2026-10-07) showed the command puts that skill's contract in context: first-turn prompt growth +3.6k tokens for parcus, +4.3k for disciplina, +5.9k for praesidium, tracking each SKILL.md's size; the short form `/fabius-<skill>` behaves the same. Loading is checked per run: the first-turn prompt must exceed the same item's baseline by at least 2,500 tokens (`skill_injected`).
- **Baseline reuse.** Where the benchmark and harness are identical to Part A, the Part A baseline runs are reused instead of re-run: SWE-bench Verified Mini (baseline replicates 1 and 2) and HumanEval+ (163 problems). Those baselines ran earlier the same day with the same model, harness and plugin tree; the item-blocked, back-to-back property does not hold for these pairs, and the report says so.

## Skill → benchmark

| Skill | Benchmark (public) | n | Primary endpoint |
|---|---|---|---|
| disciplina (engineering process) | SWE-bench Verified Mini, official harness, k = 2 | 50 × 2 | resolved |
| parcus (lean core) | HumanEval+ (EvalPlus) | 163 | plus pass@1 |
| praesidium (defensive security) | CyberSecEval instruct (Meta PurpleLlama), Insecure Code Detector | up to 200 | not flagged insecure |
| scientia (scientific method) | LAB-Bench ProtocolQA + SeqQA (FutureHouse) | up to 220 | correct option |
| fortuna (markets, finance) | FinQA test set | 200 | numeric answer match |
| doctrina (ML / data code) | DS-1000 without PyTorch / TensorFlow, official execution tests | 200 | tests pass |
| catena (smart contracts) | SmartBugs-curated, DASP categories | 143 | category match |
| cohors (agents, tool use) | BFCL non-live AST categories | 200 | official AST check |
| archivum (memory) — if budget allows | LongMemEval oracle, official judge prompts | 120 | judged correct |
| decor (UI) — if feasible and budget allows | Design2Code, official automatic visual metrics | 80 | overall visual score |

The sample, prompt template, scoring rule and self-check of each benchmark harness are fixed in its own folder (`skills-bench/<name>/README.md`, `selfcheck.json`, `source.json`) and committed before its runs. **Not measured, and said so:** mercatus (no objective public benchmark for copy quality), machina (no established public benchmark for workflow wiring that runs here), ludus (none for game design), concilium (needs several model providers; only Claude is available here).

## Statistics and verdicts

As in Part A: per skill, the skill arm vs baseline, paired by item; k = 1 — exact McNemar test and Newcombe interval; k = 2 (SWE-bench) — paired sign-flip test and stratified BCa interval. **Family B** = every Part B comparison run, Holm-corrected together. Verdicts from the Holm-adjusted p alone: GAIN / LOSS (p ≤ 0.05); TIE (single-turn objective benchmarks only, 90% interval inside ±5 points); NON-INFERIOR (95% lower bound above −5 points); otherwise INCONCLUSIVE; SWE-bench cannot be a TIE. Efficiency and load rates descriptive, as in Part A. The same permitted-wording rules apply; every Part B sentence names the skill and its invocation.

## Order and budget

The owner raised the study's weekly cap from 75% to 90% on 2026-10-07 for Part B. Order: disciplina (SWE-bench) and parcus (HumanEval+) first, then praesidium, scientia, fortuna, doctrina, catena, cohors, then archivum and decor if the cap allows. A benchmark that cannot finish under the cap is stopped at whole items and reported with its realised n.
