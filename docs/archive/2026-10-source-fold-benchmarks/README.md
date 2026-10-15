# The source-fold continuation, October 2026

A second pre-registered study, run after the [first](../2026-10-public-benchmarks/REPORT.md): three contemporary arms — no package, the frozen Fabius 3.3.0 package and the frozen source-fold candidate `6fb0ab0` (3.3.0 plus four new and ten refined reference files) — on eleven public benchmarks, with the reference files readable by the model. `REPORT.md` has the results; in one line, no gain and no loss anywhere, and the fold's reference files were opened in 6 of 4,328 package-arm runs, so the two packages behaved as one.

- `REPORT.md` — results, method, every deviation, limitations, receipts.
- `PROTOCOL.md` — the registered design (Codex, 2026-10-10, `d077cef`): arms, benchmarks, frozen samples, the confined-`Read` variant, the 33-contrast family and its statistics.
- `ADDENDUM.md` — v1.1 (2026-10-11, `f2972a5` and `b91338e`, pushed before the first scored run): the budget record, the executing harness, the package builds, the exact confined-Read rule and its canaries, the LongMemEval judge substitute and its calibration, every departure from the protocol.
- `INPUTS.json`, `schedule.jsonl` — the two filtered packages (every file's hash), the frozen samples and the seeded order of every block; `build-report.json` — both packages rebuilt and verified against it.
- `canaries/` — the three-arm confined-read canary and the SWE-bench canary.
- `harness/` — the harness that ran, scored and analysed the study (the earlier study's, extended; final state).
- `results/` — every per-item outcome (`items/<benchmark>.csv`), the analysis (`fold-analysis.json`), the run descriptives, every table in the report (`fold-tables.md`), the path audit, the judge calibration and the budget log.
- `controller.py`, `runtime.py`, `scoring.py`, `items.py`, `analysis.py`, `swe_*.py`, `test_*.py`, `VALIDATION.json` — Codex's preparation, kept as committed and not executed.

The full receipts — every attempt's command, prompt, event stream and summary, the SWE-bench patches and evaluation logs, every scorer's inputs and outputs, the judge prompts and judgements — are in `fabius-source-fold-benchmarks-2026-10.tar.gz`, attached to the GitHub Release `v3.4.0-sealed`; `REPORT.md` gives its size and SHA-256.
