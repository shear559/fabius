# Fabius on public benchmarks — pre-registration (October 2026)

This folder fixes how Fabius 3.3.0 is measured on three established public benchmarks — **SWE-bench Verified Mini** (50 real GitHub issues, official harness and images), **IFEval** (541 prompts, Google's official scorer) and **HumanEval+** (EvalPlus) — before any scored run. It was committed before the first scored run, so the questions, arms, statistics and the wording allowed for each possible result cannot be adjusted after the results are known.

- `PROTOCOL.md` — the protocol, version 1.1.
- `protocol-review.json` — the four independent methodology reviews of version 1 and the merged list of changes that produced version 1.1.
- `schedule.json` — the seeded item order and per-item arm order, written once.
- `harness/` — the runner, the infrastructure-vs-outcome classifier and its tests, the schedule builder, and the item loader.

Version 1.2 of the protocol (SWE-bench patch reference, prompt identity, run order) and the SWE-bench harness, the scorers, the path audit and the analysis script were added in a second commit, before any SWE-bench run and before any result was scored; HumanEval+ generation had started under version 1.1. The results, with every receipt needed to recompute them, are published beside this folder when the runs finish — whatever they show.
