# Fabius on public benchmarks, October 2026

This folder holds the study that measured Fabius 3.3.0 on nine established public benchmarks against the same model without it: the router through `/fabius`, and each measured skill through its own command, `/fabius:fabius-<skill>`. The protocol, harness and analysis were committed and pushed before the runs they govern, so the questions, arms, statistics and the wording allowed for each possible result could not be adjusted after the results were known.

- `REPORT.md` — the results, the method, every deviation from the registered plan, the limitations and how to recompute every number.
- `PROTOCOL.md` — Part A, version 1.4: the router and the README's earlier `fabius:` prefix on SWE-bench Verified Mini, IFEval and HumanEval+. Each version's changes are listed at its end.
- `PROTOCOL-SKILLS.md` — Part B, version 1.0: each skill on a benchmark of its own domain.
- `protocol-review.json` — the four independent methodology reviews of version 1 and the merged list of changes that produced version 1.1.
- `schedule.json`, `schedule-skills.json` — the seeded item order and per-item arm order, written once before the runs.
- `harness/` — the runner, the infrastructure-vs-outcome classifier and its tests, the schedulers, the scorers, the path audit, the analyses and the report generator.
- `skills/<benchmark>/` — each Part B benchmark's preparation, scoring and self-check, with its source pins.
- `swebench/` — the SWE-bench rows hash, image digests, validity runs and the fixed 10-task subset.
- `results/` — every per-item outcome (`items/<benchmark>.csv`), both analyses, the run descriptives, every table in the report (`tables.md`), the path audit and the budget log.

The full receipts (every run's command, prompt, event stream and summary, the SWE-bench patches and evaluation logs, and every scorer's inputs and outputs) are in `fabius-public-benchmarks-2026-10.tar.gz`, attached to the GitHub Release `v3.4.0-sealed`; `REPORT.md` gives its size and SHA-256.
