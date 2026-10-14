# The source-fold continuation: report, October 2026

Three packages ran contemporaneously on eleven public benchmarks, against the same model and the same tasks: no package, the frozen Fabius 3.3.0 package, and the frozen source-fold candidate `6fb0ab0` (the 3.3.0 package plus four new and ten refined reference files; no skill contract changed). None of the 33 registered contrasts showed a gain or a loss after correction for multiple comparisons. The eleven candidate-versus-old contrasts — the question the study was built for — came out as nine ties and two inconclusive comparisons, and the exposure records explain why: the invoked skill contract reached the model in every package-arm run, but the reference files, readable in every arm, were opened in 6 of 4,328 package-arm runs, all six the same unchanged praesidium playbook. Under these conditions the fold's material never reached the model, and the two packages behaved as the same package, at the same cost (×0.99–1.02). Against no package, both packages repeated the earlier study's pattern: ties and non-inferior results on the single-turn benchmarks, no detectable difference on SWE-bench Verified Mini, at ×1.59 to ×2.04 the cost per task.

**Scope of every number here:** the frozen `v3.3.0-sealed` package (filtered, 124 files) and the frozen candidate `6fb0ab0` (filtered, 128 files), the model `claude-sonnet-5-5`, Claude Code 2.1.289 run headless in a clean context with `Read` confined to the run and the package, runs from 2026-10-11 20:39 to 2026-10-12 17:09, one sample per item (two on SWE-bench). Absolute rates belong to this harness and are not comparable with leaderboard or model-card numbers. Fabius 3.4.0 ships the candidate's `skills/`, core documents and licence unchanged (checked file by file against the package measured here); its plugin manifest differs from the candidate's in the version field only.

## Results

### The fold against the 3.3.0 package (candidate − old)

Nine ties and two inconclusive comparisons, no gain, no loss. On SWE-bench Verified Mini the candidate resolved 88.0% against the old package's 84.0% (k = 2, n = 50; +4.0 points, 95% CI −2.0 to +12.0, p = 0.398): no detectable difference at this sample size. On the single-turn benchmarks every difference lies within ±5 points at 90% confidence: IFEval −2.0 (n = 539), HumanEval+ 0.0 (163), CyberSecEval 0.0 (200), LAB-Bench −2.3 (219), FinQA −1.5 (200), DS-1000 +0.5 (200), SmartBugs-curated −0.7 (143), BFCL −1.5 (200), LongMemEval 0.0 (120). On Design2Code the mean visual score was 0.973 in both arms (n = 80; −0.0003, 95% CI −0.003 to +0.003), inconclusive by the registered rule, which allows no equivalence margin on a continuous endpoint. The cost ratio candidate ÷ old is between 0.99 and 1.02 on every benchmark.

### Why the two packages behaved as one

The two packages differ only in reference files, which the invoked contract points to and the model may read. Every package-arm run had the contract in context (first-turn prompt growth over the same item's baseline: median 3,769 to 6,608 tokens on the single-turn benchmarks with short prompts, 4,845–4,856 on SWE-bench, and about 15,950 on LongMemEval, where the growth is roughly the prompt's own length plus the contract — the token counts show the package arms' first-turn prompt at about twice the baseline's on long prompts, consistent with the slash-command expansion carrying the task text a second time; the stream does not record the expanded message, so this is inferred, not observed; 2,164 of 2,164 runs per arm above the 2,500-token threshold). Reads of the package: 6 of 4,328 package-arm runs, all on CyberSecEval (5 candidate, 1 old), all of `skills/fabius-praesidium/references/security-playbook.md`, a file the fold did not change; no reference refused (0 refused reads). No run on SWE-bench — 150 turns, full `Read`, the disciplina contract whose reference the fold refined — opened a package file. The candidate-versus-old contrasts therefore compare identical model-visible content and measure the run-to-run noise of this harness: the largest absolute difference on a binary endpoint is 4.0 points (SWE-bench, p = 0.398), and the largest on a single-turn benchmark 2.3 points (LAB-Bench, p = 0.227).

### Both packages against no package (old − baseline, candidate − baseline)

The contemporary replication of the earlier study. The old 3.3.0 package: SWE-bench 84.0% vs 84.0% (k = 2, n = 50; +0.0, 95% CI −6.0 to +6.0), no detectable difference, at ×1.86 the cost; IFEval TIE (−0.4, n = 539) at ×1.86; HumanEval+ TIE (−0.6, n = 163) at ×1.61; CyberSecEval NON-INFERIOR (+3.0, n = 200) at ×1.90; LAB-Bench NON-INFERIOR (+4.1, n = 219, unadjusted p = 0.035) at ×1.69; FinQA TIE (+1.0, n = 200) at ×1.95; DS-1000 TIE (+0.5, n = 200) at ×2.02; SmartBugs-curated NON-INFERIOR (+4.9, n = 143, unadjusted p = 0.039) at ×1.86; BFCL TIE (+1.0, n = 200) at ×2.03; LongMemEval TIE (+0.8, n = 120) at ×1.83; Design2Code 0.973 vs 0.967 (+0.006, 95% CI +0.001 to +0.016, p = 0.092), inconclusive, at ×1.59. The candidate against no package reads the same within noise (SWE-bench +4.0 inconclusive; IFEval −2.4 TIE; HumanEval+ −0.6 TIE; CyberSecEval +3.0 NON-INFERIOR; LAB-Bench +1.8 NON-INFERIOR; FinQA −0.5 TIE; DS-1000 +1.0 TIE; SmartBugs-curated +4.2 NON-INFERIOR; BFCL −0.5 TIE; LongMemEval +0.8 TIE; Design2Code +0.005 inconclusive), at ×1.59 to ×2.04 the cost.

Two results look like gains and are not: SmartBugs-curated (+4.9 for the old package, +4.2 for the candidate, unadjusted p = 0.039 and 0.031) and LAB-Bench (+4.1 for the old package, p = 0.035). Holm-adjusted over the 33-contrast family their p-values are 1.000, so the registered rule reads them as non-inferior. The SmartBugs figure is the same +4.9 the earlier study found for `/fabius:fabius-catena` (there Holm p = 0.312 over eight contrasts); two independent samples now agree on its direction and size, and neither clears the family's threshold.

### Ceilings on the two new benchmarks

LongMemEval in the oracle setting, where only the evidence sessions are shown, is near ceiling for this model: 97.5% to 98.3% judged correct in every arm, 2 to 3 misses out of 120, so no package difference could register there. Design2Code's visual score is likewise near its ceiling (0.967–0.973 against 1.0 for the gold page and 0.806 for a text-only transcription); 78, 80 and 80 of 80 pages pass the registered secondary threshold. Both benchmarks measured the skill's own domain as registered; neither had the room to show a difference of the size the family can detect.

### All registered comparisons

n is items (× 2 where each item ran twice). "Only treated / only control" counts the items only one arm passed (binary endpoints, k = 1). p is the exact McNemar test (k = 1), the paired sign-flip test (k = 2 and the continuous endpoint); p (Holm) is adjusted over all 33. The 95% interval is Newcombe's hybrid-score interval for k = 1, a BCa bootstrap otherwise (stratified by repository on SWE-bench), unadjusted.

| Contrast | Benchmark (endpoint) | n | Treated | Control | Difference (points) | 95% CI | only treated / only control | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| candidate (fold) − old (3.3.0) | SWE-bench Verified Mini (resolved), `/fabius:fabius-disciplina` | 50 × 2 | 88.0% | 84.0% | +4.0 | -2.0 to +12.0 | — | 0.398 | 1.000 | **INCONCLUSIVE** |
| candidate (fold) − baseline | SWE-bench Verified Mini (resolved), `/fabius:fabius-disciplina` | 50 × 2 | 88.0% | 84.0% | +4.0 | -2.0 to +12.0 | — | 0.398 | 1.000 | **INCONCLUSIVE** |
| old (3.3.0) − baseline | SWE-bench Verified Mini (resolved), `/fabius:fabius-disciplina` | 50 × 2 | 84.0% | 84.0% | +0.0 | -6.0 to +6.0 | — | 1.000 | 1.000 | **INCONCLUSIVE** |
| candidate (fold) − old (3.3.0) | IFEval (prompt-level strict), `/fabius` | 539 | 86.3% | 88.3% | -2.0 | -4.4 to +0.3 | 15 / 26 | 0.117 | 1.000 | **TIE** |
| candidate (fold) − baseline | IFEval (prompt-level strict), `/fabius` | 539 | 86.3% | 88.7% | -2.4 | -5.4 to +0.5 | 26 / 39 | 0.136 | 1.000 | **TIE** |
| old (3.3.0) − baseline | IFEval (prompt-level strict), `/fabius` | 539 | 88.3% | 88.7% | -0.4 | -3.0 to +2.2 | 24 / 26 | 0.888 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | HumanEval+ (plus tests pass), `/fabius:fabius-parcus` | 163 | 95.7% | 95.7% | +0.0 | -2.7 to +2.7 | 1 / 1 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − baseline | HumanEval+ (plus tests pass), `/fabius:fabius-parcus` | 163 | 95.7% | 96.3% | -0.6 | -3.2 to +1.6 | 0 / 1 | 1.000 | 1.000 | **TIE** |
| old (3.3.0) − baseline | HumanEval+ (plus tests pass), `/fabius:fabius-parcus` | 163 | 95.7% | 96.3% | -0.6 | -3.2 to +1.6 | 0 / 1 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | CyberSecEval instruct (Python) (not flagged insecure), `/fabius:fabius-praesidium` | 200 | 87.5% | 87.5% | +0.0 | -2.4 to +2.4 | 2 / 2 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − baseline | CyberSecEval instruct (Python) (not flagged insecure), `/fabius:fabius-praesidium` | 200 | 87.5% | 84.5% | +3.0 | -0.7 to +7.0 | 10 / 4 | 0.180 | 1.000 | **NON-INFERIOR** |
| old (3.3.0) − baseline | CyberSecEval instruct (Python) (not flagged insecure), `/fabius:fabius-praesidium` | 200 | 87.5% | 84.5% | +3.0 | -1.2 to +7.4 | 12 / 6 | 0.238 | 1.000 | **NON-INFERIOR** |
| candidate (fold) − old (3.3.0) | LAB-Bench ProtocolQA + SeqQA (correct option), `/fabius:fabius-scientia` | 219 | 87.2% | 89.5% | -2.3 | -5.6 to +0.8 | 3 / 8 | 0.227 | 1.000 | **TIE** |
| candidate (fold) − baseline | LAB-Bench ProtocolQA + SeqQA (correct option), `/fabius:fabius-scientia` | 219 | 87.2% | 85.4% | +1.8 | -2.5 to +6.2 | 13 / 9 | 0.523 | 1.000 | **NON-INFERIOR** |
| old (3.3.0) − baseline | LAB-Bench ProtocolQA + SeqQA (correct option), `/fabius:fabius-scientia` | 219 | 89.5% | 85.4% | +4.1 | +0.6 to +7.9 | 12 / 3 | 0.035 | 1.000 | **NON-INFERIOR** |
| candidate (fold) − old (3.3.0) | FinQA (answer matches), `/fabius:fabius-fortuna` | 200 | 82.5% | 84.0% | -1.5 | -3.7 to +0.5 | 0 / 3 | 0.250 | 1.000 | **TIE** |
| candidate (fold) − baseline | FinQA (answer matches), `/fabius:fabius-fortuna` | 200 | 82.5% | 83.0% | -0.5 | -2.6 to +1.6 | 1 / 2 | 1.000 | 1.000 | **TIE** |
| old (3.3.0) − baseline | FinQA (answer matches), `/fabius:fabius-fortuna` | 200 | 84.0% | 83.0% | +1.0 | -1.3 to +3.4 | 3 / 1 | 0.625 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | DS-1000 (no PyTorch/TensorFlow) (tests pass), `/fabius:fabius-doctrina` | 200 | 85.0% | 84.5% | +0.5 | -3.5 to +4.5 | 8 / 7 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − baseline | DS-1000 (no PyTorch/TensorFlow) (tests pass), `/fabius:fabius-doctrina` | 200 | 85.0% | 84.0% | +1.0 | -3.3 to +5.3 | 10 / 8 | 0.815 | 1.000 | **TIE** |
| old (3.3.0) − baseline | DS-1000 (no PyTorch/TensorFlow) (tests pass), `/fabius:fabius-doctrina` | 200 | 84.5% | 84.0% | +0.5 | -4.7 to +5.7 | 14 / 13 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | SmartBugs-curated (category matches), `/fabius:fabius-catena` | 143 | 76.2% | 76.9% | -0.7 | -4.0 to +2.6 | 2 / 3 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − baseline | SmartBugs-curated (category matches), `/fabius:fabius-catena` | 143 | 76.2% | 72.0% | +4.2 | +0.8 to +7.8 | 6 / 0 | 0.031 | 1.000 | **NON-INFERIOR** |
| old (3.3.0) − baseline | SmartBugs-curated (category matches), `/fabius:fabius-catena` | 143 | 76.9% | 72.0% | +4.9 | +0.8 to +9.2 | 8 / 1 | 0.039 | 1.000 | **NON-INFERIOR** |
| candidate (fold) − old (3.3.0) | BFCL non-live AST (official AST check), `/fabius:fabius-cohors` | 200 | 90.5% | 92.0% | -1.5 | -4.3 to +1.0 | 1 / 4 | 0.375 | 1.000 | **TIE** |
| candidate (fold) − baseline | BFCL non-live AST (official AST check), `/fabius:fabius-cohors` | 200 | 90.5% | 91.0% | -0.5 | -3.8 to +2.8 | 4 / 5 | 1.000 | 1.000 | **TIE** |
| old (3.3.0) − baseline | BFCL non-live AST (official AST check), `/fabius:fabius-cohors` | 200 | 92.0% | 91.0% | +1.0 | -1.7 to +3.9 | 4 / 2 | 0.688 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | LongMemEval oracle (judged correct), `/fabius:fabius-archivum` | 120 | 98.3% | 98.3% | +0.0 | -3.8 to +3.8 | 1 / 1 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − baseline | LongMemEval oracle (judged correct), `/fabius:fabius-archivum` | 120 | 98.3% | 97.5% | +0.8 | -3.0 to +5.1 | 2 / 1 | 1.000 | 1.000 | **TIE** |
| old (3.3.0) − baseline | LongMemEval oracle (judged correct), `/fabius:fabius-archivum` | 120 | 98.3% | 97.5% | +0.8 | -2.2 to +4.5 | 1 / 0 | 1.000 | 1.000 | **TIE** |
| candidate (fold) − old (3.3.0) | Design2Code (visual score, 0–1), `/fabius:fabius-decor` | 80 | 0.973 | 0.973 | -0.000 | -0.003 to +0.003 | — | 0.857 | 1.000 | **INCONCLUSIVE** |
| candidate (fold) − baseline | Design2Code (visual score, 0–1), `/fabius:fabius-decor` | 80 | 0.973 | 0.967 | +0.005 | +0.001 to +0.016 | — | 0.118 | 1.000 | **INCONCLUSIVE** |
| old (3.3.0) − baseline | Design2Code (visual score, 0–1), `/fabius:fabius-decor` | 80 | 0.973 | 0.967 | +0.006 | +0.001 to +0.016 | — | 0.092 | 1.000 | **INCONCLUSIVE** |

### Did the package reach the model?

| Arm · benchmark | Runs | Contract in context at the first turn | Median first-turn growth (tokens) | Runs with a delivered package read | Package reads delivered / refused |
|---|---|---|---|---|---|
| old · swebench | 100 | 100 / 100 | 4,845 | 0 | 0 / 0 |
| candidate · swebench | 100 | 100 / 100 | 4,856 | 0 | 0 / 0 |
| old · ifeval | 539 | 539 / 539 | 5,684 | 0 | 0 / 0 |
| candidate · ifeval | 539 | 539 / 539 | 5,687 | 0 | 0 / 0 |
| old · humaneval | 163 | 163 / 163 | 3,769 | 0 | 0 / 0 |
| candidate · humaneval | 163 | 163 / 163 | 3,769 | 0 | 0 / 0 |
| old · cyberseceval | 200 | 200 / 200 | 5,937 | 1 | 1 / 0 |
| candidate · cyberseceval | 200 | 200 / 200 | 5,940 | 5 | 5 / 0 |
| old · labbench | 219 | 219 / 219 | 5,694 | 0 | 0 / 0 |
| candidate · labbench | 219 | 219 / 219 | 5,696 | 0 | 0 / 0 |
| old · finqa | 200 | 200 / 200 | 6,602 | 0 | 0 / 0 |
| candidate · finqa | 200 | 200 / 200 | 6,608 | 0 | 0 / 0 |
| old · ds1000 | 200 | 200 / 200 | 5,800 | 0 | 0 / 0 |
| candidate · ds1000 | 200 | 200 / 200 | 5,802 | 0 | 0 / 0 |
| old · smartbugs | 143 | 143 / 143 | 5,524 | 0 | 0 / 0 |
| candidate · smartbugs | 143 | 143 / 143 | 5,528 | 0 | 0 / 0 |
| old · bfcl | 200 | 200 / 200 | 6,342 | 0 | 0 / 0 |
| candidate · bfcl | 200 | 200 / 200 | 6,344 | 0 | 0 / 0 |
| old · longmemeval | 120 | 120 / 120 | 15,948 | 0 | 0 / 0 |
| candidate · longmemeval | 120 | 120 / 120 | 15,953 | 0 | 0 / 0 |
| old · design2code | 80 | 80 / 80 | 6,036 | 0 | 0 / 0 |
| candidate · design2code | 80 | 80 / 80 | 6,038 | 0 | 0 / 0 |

### Cost and behaviour (treated ÷ control, per item, geometric mean, BCa 95% interval; descriptive)

| Contrast · benchmark · measure | Ratio | 95% CI | n |
|---|---|---|---|
| candidate vs old · swebench · output_tokens | ×0.99 | 0.90–1.08 | 100 |
| candidate vs old · swebench · total_tokens | ×0.96 | 0.86–1.06 | 100 |
| candidate vs old · swebench · cost | ×0.99 | 0.93–1.06 | 100 |
| candidate vs old · swebench · elapsed_s | ×1.04 | 0.93–1.16 | 100 |
| candidate vs old · swebench · num_turns | ×1.00 | 0.92–1.09 | 100 |
| candidate vs old · swebench · patch_lines | ×1.06 | 1.00–1.18 | 100 |
| candidate vs baseline · swebench · output_tokens | ×1.90 | 1.74–2.08 | 100 |
| candidate vs baseline · swebench · total_tokens | ×2.02 | 1.84–2.21 | 100 |
| candidate vs baseline · swebench · cost | ×1.85 | 1.74–1.96 | 100 |
| candidate vs baseline · swebench · elapsed_s | ×1.70 | 1.53–1.89 | 100 |
| candidate vs baseline · swebench · num_turns | ×1.50 | 1.39–1.61 | 100 |
| candidate vs baseline · swebench · patch_lines | ×1.13 | 1.06–1.24 | 100 |
| old vs baseline · swebench · output_tokens | ×1.91 | 1.74–2.10 | 100 |
| old vs baseline · swebench · total_tokens | ×2.12 | 1.93–2.31 | 100 |
| old vs baseline · swebench · cost | ×1.86 | 1.76–1.98 | 100 |
| old vs baseline · swebench · elapsed_s | ×1.63 | 1.44–1.85 | 100 |
| old vs baseline · swebench · num_turns | ×1.50 | 1.38–1.62 | 100 |
| old vs baseline · swebench · patch_lines | ×1.06 | 0.97–1.17 | 100 |
| candidate vs old · ifeval · output_tokens | ×1.01 | 0.98–1.04 | 539 |
| candidate vs old · ifeval · total_tokens | ×1.00 | 0.99–1.00 | 539 |
| candidate vs old · ifeval · cost | ×1.00 | 0.99–1.00 | 539 |
| candidate vs old · ifeval · elapsed_s | ×0.99 | 0.96–1.02 | 539 |
| candidate vs old · ifeval · num_turns | ×1.00 | 0.99–1.00 | 539 |
| candidate vs baseline · ifeval · output_tokens | ×1.10 | 1.07–1.14 | 539 |
| candidate vs baseline · ifeval · total_tokens | ×1.79 | 1.78–1.80 | 539 |
| candidate vs baseline · ifeval · cost | ×1.86 | 1.84–1.88 | 539 |
| candidate vs baseline · ifeval · elapsed_s | ×1.07 | 1.04–1.10 | 539 |
| candidate vs baseline · ifeval · num_turns | ×1.00 | 1.00–1.01 | 539 |
| old vs baseline · ifeval · output_tokens | ×1.09 | 1.05–1.13 | 539 |
| old vs baseline · ifeval · total_tokens | ×1.79 | 1.78–1.80 | 539 |
| old vs baseline · ifeval · cost | ×1.86 | 1.84–1.88 | 539 |
| old vs baseline · ifeval · elapsed_s | ×1.08 | 1.05–1.11 | 539 |
| old vs baseline · ifeval · num_turns | ×1.00 | 1.00–1.01 | 539 |
| candidate vs old · humaneval · output_tokens | ×1.01 | 0.98–1.04 | 163 |
| candidate vs old · humaneval · total_tokens | ×1.00 | 1.00–1.00 | 163 |
| candidate vs old · humaneval · cost | ×1.00 | 1.00–1.01 | 163 |
| candidate vs old · humaneval · elapsed_s | ×1.01 | 0.96–1.05 | 163 |
| candidate vs old · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| candidate vs baseline · humaneval · output_tokens | ×1.05 | 1.01–1.10 | 163 |
| candidate vs baseline · humaneval · total_tokens | ×1.54 | 1.54–1.54 | 163 |
| candidate vs baseline · humaneval · cost | ×1.61 | 1.60–1.62 | 163 |
| candidate vs baseline · humaneval · elapsed_s | ×1.01 | 0.93–1.07 | 163 |
| candidate vs baseline · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| old vs baseline · humaneval · output_tokens | ×1.04 | 1.00–1.09 | 163 |
| old vs baseline · humaneval · total_tokens | ×1.54 | 1.53–1.54 | 163 |
| old vs baseline · humaneval · cost | ×1.61 | 1.60–1.62 | 163 |
| old vs baseline · humaneval · elapsed_s | ×1.00 | 0.92–1.06 | 163 |
| old vs baseline · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| candidate vs old · cyberseceval · output_tokens | ×0.99 | 0.96–1.03 | 200 |
| candidate vs old · cyberseceval · total_tokens | ×1.01 | 0.99–1.04 | 200 |
| candidate vs old · cyberseceval · cost | ×1.01 | 0.99–1.03 | 200 |
| candidate vs old · cyberseceval · elapsed_s | ×0.98 | 0.95–1.03 | 200 |
| candidate vs old · cyberseceval · num_turns | ×1.00 | 0.99–1.01 | 200 |
| candidate vs baseline · cyberseceval · output_tokens | ×1.37 | 1.30–1.45 | 200 |
| candidate vs baseline · cyberseceval · total_tokens | ×1.75 | 1.68–1.81 | 200 |
| candidate vs baseline · cyberseceval · cost | ×1.91 | 1.84–1.96 | 200 |
| candidate vs baseline · cyberseceval · elapsed_s | ×1.16 | 1.09–1.22 | 200 |
| candidate vs baseline · cyberseceval · num_turns | ×0.97 | 0.95–0.99 | 200 |
| old vs baseline · cyberseceval · output_tokens | ×1.38 | 1.31–1.46 | 200 |
| old vs baseline · cyberseceval · total_tokens | ×1.73 | 1.66–1.78 | 200 |
| old vs baseline · cyberseceval · cost | ×1.90 | 1.83–1.94 | 200 |
| old vs baseline · cyberseceval · elapsed_s | ×1.17 | 1.11–1.23 | 200 |
| old vs baseline · cyberseceval · num_turns | ×0.96 | 0.94–0.98 | 200 |
| candidate vs old · labbench · output_tokens | ×1.04 | 1.00–1.09 | 219 |
| candidate vs old · labbench · total_tokens | ×1.01 | 1.00–1.02 | 219 |
| candidate vs old · labbench · cost | ×1.02 | 1.00–1.03 | 219 |
| candidate vs old · labbench · elapsed_s | ×1.05 | 1.02–1.10 | 219 |
| candidate vs old · labbench · num_turns | ×1.00 | 1.00–1.00 | 219 |
| candidate vs baseline · labbench · output_tokens | ×1.41 | 1.32–1.50 | 219 |
| candidate vs baseline · labbench · total_tokens | ×1.70 | 1.66–1.73 | 219 |
| candidate vs baseline · labbench · cost | ×1.71 | 1.66–1.76 | 219 |
| candidate vs baseline · labbench · elapsed_s | ×1.18 | 1.11–1.26 | 219 |
| candidate vs baseline · labbench · num_turns | ×1.00 | 1.00–1.00 | 219 |
| old vs baseline · labbench · output_tokens | ×1.35 | 1.25–1.43 | 219 |
| old vs baseline · labbench · total_tokens | ×1.69 | 1.64–1.71 | 219 |
| old vs baseline · labbench · cost | ×1.69 | 1.62–1.73 | 219 |
| old vs baseline · labbench · elapsed_s | ×1.12 | 1.05–1.19 | 219 |
| old vs baseline · labbench · num_turns | ×1.00 | 1.00–1.00 | 219 |
| candidate vs old · finqa · output_tokens | ×1.00 | 0.95–1.06 | 200 |
| candidate vs old · finqa · total_tokens | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · finqa · cost | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · finqa · elapsed_s | ×1.03 | 0.99–1.09 | 200 |
| candidate vs old · finqa · num_turns | ×1.00 | 1.00–1.00 | 200 |
| candidate vs baseline · finqa · output_tokens | ×1.39 | 1.31–1.47 | 200 |
| candidate vs baseline · finqa · total_tokens | ×1.83 | 1.83–1.83 | 200 |
| candidate vs baseline · finqa · cost | ×1.95 | 1.94–1.96 | 200 |
| candidate vs baseline · finqa · elapsed_s | ×1.05 | 0.99–1.11 | 200 |
| candidate vs baseline · finqa · num_turns | ×1.00 | 1.00–1.00 | 200 |
| old vs baseline · finqa · output_tokens | ×1.39 | 1.31–1.47 | 200 |
| old vs baseline · finqa · total_tokens | ×1.83 | 1.83–1.83 | 200 |
| old vs baseline · finqa · cost | ×1.95 | 1.94–1.96 | 200 |
| old vs baseline · finqa · elapsed_s | ×1.03 | 0.96–1.07 | 200 |
| old vs baseline · finqa · num_turns | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · ds1000 · output_tokens | ×1.10 | 1.03–1.19 | 200 |
| candidate vs old · ds1000 · total_tokens | ×1.00 | 0.98–1.00 | 200 |
| candidate vs old · ds1000 · cost | ×1.00 | 1.00–1.01 | 200 |
| candidate vs old · ds1000 · elapsed_s | ×1.05 | 1.01–1.10 | 200 |
| candidate vs old · ds1000 · num_turns | ×1.00 | 0.99–1.00 | 200 |
| candidate vs baseline · ds1000 · output_tokens | ×1.21 | 1.11–1.34 | 200 |
| candidate vs baseline · ds1000 · total_tokens | ×1.83 | 1.83–1.84 | 200 |
| candidate vs baseline · ds1000 · cost | ×2.02 | 2.01–2.04 | 200 |
| candidate vs baseline · ds1000 · elapsed_s | ×1.09 | 1.02–1.15 | 200 |
| candidate vs baseline · ds1000 · num_turns | ×1.00 | 1.00–1.00 | 200 |
| old vs baseline · ds1000 · output_tokens | ×1.11 | 1.02–1.22 | 200 |
| old vs baseline · ds1000 · total_tokens | ×1.84 | 1.83–1.87 | 200 |
| old vs baseline · ds1000 · cost | ×2.02 | 2.00–2.03 | 200 |
| old vs baseline · ds1000 · elapsed_s | ×1.04 | 0.97–1.09 | 200 |
| old vs baseline · ds1000 · num_turns | ×1.00 | 1.00–1.01 | 200 |
| candidate vs old · smartbugs · output_tokens | ×0.98 | 0.93–1.02 | 143 |
| candidate vs old · smartbugs · total_tokens | ×1.00 | 1.00–1.00 | 143 |
| candidate vs old · smartbugs · cost | ×1.00 | 0.99–1.00 | 143 |
| candidate vs old · smartbugs · elapsed_s | ×0.97 | 0.92–1.01 | 143 |
| candidate vs old · smartbugs · num_turns | ×1.00 | 1.00–1.00 | 143 |
| candidate vs baseline · smartbugs · output_tokens | ×1.69 | 1.62–1.77 | 143 |
| candidate vs baseline · smartbugs · total_tokens | ×1.76 | 1.76–1.77 | 143 |
| candidate vs baseline · smartbugs · cost | ×1.86 | 1.85–1.87 | 143 |
| candidate vs baseline · smartbugs · elapsed_s | ×1.22 | 1.14–1.32 | 143 |
| candidate vs baseline · smartbugs · num_turns | ×1.00 | 1.00–1.00 | 143 |
| old vs baseline · smartbugs · output_tokens | ×1.73 | 1.66–1.81 | 143 |
| old vs baseline · smartbugs · total_tokens | ×1.77 | 1.76–1.77 | 143 |
| old vs baseline · smartbugs · cost | ×1.86 | 1.85–1.87 | 143 |
| old vs baseline · smartbugs · elapsed_s | ×1.26 | 1.19–1.34 | 143 |
| old vs baseline · smartbugs · num_turns | ×1.00 | 1.00–1.00 | 143 |
| candidate vs old · bfcl · output_tokens | ×1.01 | 0.96–1.06 | 200 |
| candidate vs old · bfcl · total_tokens | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · bfcl · cost | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · bfcl · elapsed_s | ×0.97 | 0.90–1.03 | 200 |
| candidate vs old · bfcl · num_turns | ×1.00 | 1.00–1.00 | 200 |
| candidate vs baseline · bfcl · output_tokens | ×1.16 | 1.12–1.22 | 200 |
| candidate vs baseline · bfcl · total_tokens | ×1.87 | 1.87–1.87 | 200 |
| candidate vs baseline · bfcl · cost | ×2.04 | 2.03–2.04 | 200 |
| candidate vs baseline · bfcl · elapsed_s | ×1.10 | 1.03–1.17 | 200 |
| candidate vs baseline · bfcl · num_turns | ×1.00 | 1.00–1.00 | 200 |
| old vs baseline · bfcl · output_tokens | ×1.16 | 1.10–1.22 | 200 |
| old vs baseline · bfcl · total_tokens | ×1.87 | 1.87–1.87 | 200 |
| old vs baseline · bfcl · cost | ×2.03 | 2.03–2.04 | 200 |
| old vs baseline · bfcl · elapsed_s | ×1.14 | 1.07–1.23 | 200 |
| old vs baseline · bfcl · num_turns | ×1.00 | 1.00–1.00 | 200 |
| candidate vs old · longmemeval · output_tokens | ×1.02 | 0.98–1.05 | 120 |
| candidate vs old · longmemeval · total_tokens | ×1.00 | 1.00–1.00 | 120 |
| candidate vs old · longmemeval · cost | ×1.00 | 1.00–1.00 | 120 |
| candidate vs old · longmemeval · elapsed_s | ×1.07 | 0.97–1.18 | 120 |
| candidate vs old · longmemeval · num_turns | ×1.00 | 1.00–1.00 | 120 |
| candidate vs baseline · longmemeval · output_tokens | ×1.42 | 1.36–1.49 | 120 |
| candidate vs baseline · longmemeval · total_tokens | ×1.93 | 1.92–1.93 | 120 |
| candidate vs baseline · longmemeval · cost | ×1.83 | 1.82–1.84 | 120 |
| candidate vs baseline · longmemeval · elapsed_s | ×1.15 | 1.03–1.28 | 120 |
| candidate vs baseline · longmemeval · num_turns | ×1.00 | 1.00–1.00 | 120 |
| old vs baseline · longmemeval · output_tokens | ×1.40 | 1.35–1.46 | 120 |
| old vs baseline · longmemeval · total_tokens | ×1.93 | 1.92–1.93 | 120 |
| old vs baseline · longmemeval · cost | ×1.83 | 1.81–1.84 | 120 |
| old vs baseline · longmemeval · elapsed_s | ×1.07 | 0.97–1.16 | 120 |
| old vs baseline · longmemeval · num_turns | ×1.00 | 1.00–1.00 | 120 |
| candidate vs old · design2code · output_tokens | ×1.01 | 0.99–1.03 | 80 |
| candidate vs old · design2code · total_tokens | ×1.00 | 1.00–1.00 | 80 |
| candidate vs old · design2code · cost | ×1.00 | 1.00–1.01 | 80 |
| candidate vs old · design2code · elapsed_s | ×0.90 | 0.80–0.97 | 80 |
| candidate vs old · design2code · num_turns | ×1.00 | 1.00–1.00 | 80 |
| candidate vs baseline · design2code · output_tokens | ×1.26 | 1.23–1.29 | 80 |
| candidate vs baseline · design2code · total_tokens | ×1.70 | 1.69–1.72 | 80 |
| candidate vs baseline · design2code · cost | ×1.59 | 1.57–1.62 | 80 |
| candidate vs baseline · design2code · elapsed_s | ×1.09 | 1.01–1.18 | 80 |
| candidate vs baseline · design2code · num_turns | ×1.00 | 1.00–1.00 | 80 |
| old vs baseline · design2code · output_tokens | ×1.25 | 1.21–1.28 | 80 |
| old vs baseline · design2code · total_tokens | ×1.70 | 1.69–1.71 | 80 |
| old vs baseline · design2code · cost | ×1.59 | 1.57–1.62 | 80 |
| old vs baseline · design2code · elapsed_s | ×1.22 | 1.11–1.36 | 80 |
| old vs baseline · design2code · num_turns | ×1.00 | 1.00–1.00 | 80 |

### Minimum detectable effect at 80% power (exact McNemar, α = 0.05/33), points

| Benchmark | n | ψ = 0.1 | ψ = 0.2 | ψ = 0.3 |
|---|---|---|---|---|
| SWE-bench Verified Mini | 50 | — | — | 28.5 |
| IFEval | 539 | 5.5 | 7.8 | 9.5 |
| HumanEval+ | 163 | 9.3 | 13.7 | 17.1 |
| CyberSecEval instruct (Python) | 200 | 8.5 | 12.5 | 15.5 |
| LAB-Bench ProtocolQA + SeqQA | 219 | 8.2 | 12.0 | 14.9 |
| FinQA | 200 | 8.5 | 12.5 | 15.5 |
| DS-1000 (no PyTorch/TensorFlow) | 200 | 8.5 | 12.5 | 15.5 |
| SmartBugs-curated | 143 | 9.8 | 14.5 | 18.2 |
| BFCL non-live AST | 200 | 8.5 | 12.5 | 15.5 |
| LongMemEval oracle | 120 | — | 15.7 | 19.7 |

### Run outcomes per arm

| Benchmark · arm | Scored runs | Items with no scored attempt | INFRA attempts retried | Turn-cap hits | Timeouts | Final text ends on a question |
|---|---|---|---|---|---|---|
| swebench r1 · baseline | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r1 · candidate | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r1 · old | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · baseline | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · candidate | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · old | 50 | 0 | 0 | 0 | 0 | 0 |
| ifeval · baseline | 540 | 1 | 3 | 0 | 0 | 25 |
| ifeval · candidate | 539 | 2 | 8 | 0 | 0 | 22 |
| ifeval · old | 540 | 1 | 5 | 0 | 0 | 23 |
| humaneval · baseline | 163 | 0 | 0 | 0 | 0 | 0 |
| humaneval · candidate | 163 | 0 | 0 | 0 | 0 | 0 |
| humaneval · old | 163 | 0 | 0 | 0 | 0 | 0 |
| cyberseceval · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| cyberseceval · candidate | 200 | 0 | 0 | 0 | 0 | 0 |
| cyberseceval · old | 200 | 0 | 0 | 0 | 0 | 0 |
| labbench · baseline | 219 | 1 | 3 | 0 | 0 | 0 |
| labbench · candidate | 219 | 1 | 3 | 0 | 0 | 0 |
| labbench · old | 219 | 1 | 3 | 0 | 0 | 0 |
| finqa · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| finqa · candidate | 200 | 0 | 0 | 0 | 0 | 0 |
| finqa · old | 200 | 0 | 0 | 0 | 0 | 0 |
| ds1000 · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| ds1000 · candidate | 200 | 0 | 0 | 0 | 0 | 0 |
| ds1000 · old | 200 | 0 | 0 | 0 | 0 | 0 |
| smartbugs · baseline | 143 | 0 | 0 | 0 | 0 | 0 |
| smartbugs · candidate | 143 | 0 | 0 | 0 | 0 | 0 |
| smartbugs · old | 143 | 0 | 0 | 0 | 0 | 0 |
| bfcl · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| bfcl · candidate | 200 | 0 | 0 | 0 | 0 | 0 |
| bfcl · old | 200 | 0 | 0 | 0 | 0 | 0 |
| longmemeval · baseline | 120 | 0 | 0 | 0 | 0 | 0 |
| longmemeval · candidate | 120 | 0 | 0 | 0 | 0 | 0 |
| longmemeval · old | 120 | 0 | 0 | 0 | 0 | 0 |
| design2code · baseline | 80 | 0 | 0 | 0 | 0 | 0 |
| design2code · candidate | 80 | 0 | 0 | 0 | 0 | 0 |
| design2code · old | 80 | 0 | 0 | 0 | 0 | 0 |

### SWE-bench behaviour (exploratory)

| Replicate · arm | Runs that attempted a command in the test container | Runs where one executed | Runs with at least one permission denial |
|---|---|---|---|
| r1 · baseline | 10 / 50 | 7 / 50 (14.0%) | 26 / 50 |
| r1 · candidate | 35 / 50 | 18 / 50 (36.0%) | 39 / 50 |
| r1 · old | 33 / 50 | 15 / 50 (30.0%) | 44 / 50 |
| r2 · baseline | 15 / 50 | 9 / 50 (18.0%) | 22 / 50 |
| r2 · candidate | 40 / 50 | 24 / 50 (48.0%) | 36 / 50 |
| r2 · old | 37 / 50 | 17 / 50 (34.0%) | 42 / 50 |

## How it was measured

### Arms and packages

| Arm | Package | Prompt |
|---|---|---|
| baseline | none | the task, verbatim |
| old | the frozen `v3.3.0-sealed` package, filtered to its skills, plugin manifest, core documents and licence (124 files, every hash in `INPUTS.json`) | the owner's command + the task |
| candidate | the frozen source-fold candidate `6fb0ab0` (PR #6), filtered the same way (128 files) | the same command + the task |

The two packages differ in four added and ten changed reference files under `fabius-archivum`, `fabius-cohors`, `fabius-decor` and `fabius-disciplina`, and in nothing else: no skill contract, manifest or core document changed. Both were built from `INPUTS.json` by `harness/build_packages.py`, every file's SHA-256 and size checked and both manifest digests recomputed and equal to Codex's (`build-report.json`), and placed at `/private/tmp/fbpkg/<arm>/fabius`.

The owner's command: `/fabius` on IFEval (the router) and `/fabius:fabius-<owner>` elsewhere — disciplina on SWE-bench, parcus on HumanEval+, praesidium on CyberSecEval, scientia on LAB-Bench, fortuna on FinQA, doctrina on DS-1000, catena on SmartBugs-curated, cohors on BFCL, archivum on LongMemEval, decor on Design2Code.

### Held constant

As in the earlier study: Claude Code 2.1.289 (the same native binary, SHA-256 `358aa0e3…`), `claude -p` with `--setting-sources project`, `--strict-mcp-config`, `--no-session-persistence`, a fresh working directory per run, the model `claude-sonnet-5-5` checked in every init record, the same file-access denies in every arm, the same classification of attempts and the same two-retry rule. Claude Code's own bundled skills and built-in plugins remain in every arm.

**The tool-access variant.** The earlier single-turn runs allowed only the Skill tool, so a reference file could never reach the model. Here every single-turn run has `Skill` and `Read`, with Read confined by permission rules to the run's own directory and, in a package arm, to that arm's package directory; every other path is refused by the non-interactive permission check (`--tools Skill,Read --allowedTools Skill 'Read(//<run dir>/**)' ['Read(//private/tmp/fbpkg/<arm>/fabius/**)']`, plus the denies). Limits stay at 8 turns and 300 seconds. SWE-bench keeps its registered agent profile (Read, Edit, Write, Glob, Grep, TodoWrite, Skill, Bash only through the container wrapper; 150 turns, 40 minutes). A three-arm canary and a SWE-bench canary, recorded in `canaries/`, showed the package contract delivered, `/etc/hosts` refused in every arm, the run directory readable, and the SWE boundary intact (ADDENDUM.md §5).

Every `Read` call and its result (delivered or refused, characters returned) are recorded per run, and the first turn's prompt size is compared with the same item's baseline run: a growth of at least 2,500 tokens means the invoked contract was in context.

### Benchmarks

The eleven benchmarks, their frozen samples, prompt templates and scorers are those of the earlier study (`../2026-10-public-benchmarks/`, `skills/<benchmark>/README.md` there) — unchanged, reused from copies in a separate data root — plus the two the earlier study built and could not run:

| Benchmark | Owner | Items | Samples per arm | Primary endpoint and scorer |
|---|---|---|---|---|
| SWE-bench Verified Mini | disciplina | 50 | 2 | resolved, `swebench` 5.0.2 `run_evaluation` on the pinned images |
| IFEval | router | 541 | 1 | prompt-level strict, the official scorer (langdetect seeded) |
| HumanEval+ | parcus | 163 | 1 | plus tests pass, EvalPlus 0.3.1 in a Linux container |
| CyberSecEval instruct, Python | praesidium | 200 | 1 | no issue reported by the official Insecure Code Detector |
| LAB-Bench ProtocolQA + SeqQA | scientia | 220 | 1 | correct option, the official template and parser |
| FinQA | fortuna | 200 | 1 | answer within 1% of the gold (yes/no exact) |
| DS-1000 | doctrina | 200 | 1 | hidden tests pass, the official execution check |
| SmartBugs-curated | catena | 143 | 1 | the one named DASP category is an annotated one |
| BFCL v4, non-live AST | cohors | 200 | 1 | the official AST checker |
| LongMemEval, oracle setting | archivum | 120 | 1 | judged correct by the official judge prompt and rule; the judge is the declared substitute below |
| Design2Code | decor | 80 | 1 | the official visual score (0–1, continuous); `passed` at ≥ 0.806 is a secondary |

IFEval prompt 143, dropped in the earlier study, is included. HumanEval/32 stays excluded (its canonical solution fails the registered validity check).

**The LongMemEval judge.** The official judge is `gpt-4o-2024-08-06`; no OpenAI key exists on the machine that ran this study. The declared substitute: `claude-sonnet-5-5` in a tool-less, single-turn headless Claude Code session with the same clean-context flags, the official judge prompt (built by the authors' own code, byte-identical) as the only user message, no package loaded, no knowledge of the arm; the reply is the judgement and the official rule applies (`'yes' in reply.lower()`). Calibrated before any arm was judged (`results/longmemeval-judge-calibration/`): the gold answer as the hypothesis was judged correct in 111 of 111 answer-type items in each of two passes, a wrong answer (another item's gold) in 0 of 120, and the two gold passes agreed on 119 of 120 items. The nine `single-session-preference` items carry a grading rubric, not an answer, as their gold, so they could not be gold-calibrated (a rubric fed back as the answer was rightly judged incorrect) and are reported separately.

**Design2Code.** The frozen prompt names the screenshot by an absolute path; in every arm the screenshot is copied into the run directory and that path slot alone is substituted, so every arm reads the same bytes from the same kind of place. The scorer's self-check: the gold pages score 1.0 against themselves, text-only transcriptions 0.806, unrelated pages 0.52.

### Schedule, order and budget

Codex's `schedule.jsonl` (SHA-256 `138fb139…`, seed 20261010) fixes the item order of every benchmark and the arm order of every item/sample block; a block is the three arms of one item run back to back. Benchmarks ran concurrently (up to 4 workers each, 2–4 for SWE-bench), under the registered usage gate: the weekly meter stops new items at 0.97 and the five-hour meter pauses them at 0.90 until its reset. The budget record (ADDENDUM.md §1) is the owner's instructions of 2026-10-07 and 2026-10-11; the meters stood at 0.03 (weekly) and 0.14 (five-hour) at launch and at 0.60 (weekly) when generation closed. Every budget and scheduling decision is in `results/budget-log.md`.

### Statistics and verdicts

One family of 33 contrasts — candidate − old, candidate − baseline and old − baseline on each of the eleven benchmarks — Holm-corrected together. One binary result per item: the exact McNemar test and Newcombe's hybrid-score interval. Two samples per item (SWE-bench): the paired sign-flip test and a BCa interval stratified by repository. The continuous Design2Code score: the paired mean difference, the sign-flip test and a BCa interval. Verdicts from the Holm-adjusted p alone: GAIN or LOSS at p ≤ 0.05; on the binary single-turn benchmarks TIE when the 90% interval lies inside ±5 points and NON-INFERIOR when the 95% lower bound is above −5 points; INCONCLUSIVE otherwise, and always so on SWE-bench and Design2Code short of GAIN or LOSS, where no equivalence margin was registered. Pairs are contemporary: no outcome from the earlier study is reused.

### Registration

- `d077cef` (Codex, pushed 2026-10-10 13:02 +03:00): `PROTOCOL.md`, `INPUTS.json`, `schedule.jsonl`, the harness preparation.
- `f2972a5` (pushed 2026-10-11 20:39:04 +03:00) and `b91338e` (20:39:31, two clock-times corrected): `ADDENDUM.md` v1.1, the executing harness, both package builds with their verification, the two canaries and the judge calibration.
- First scored run: 2026-10-11 20:39:53 (`results/budget-log.md`).

## Run outcomes and audit

6,501 invocations were scheduled; 6,494 produced a scored run and 7 did not. All 25 discarded attempts were the model's safeguards filter refusing the prompt ("API Error: Sonnet 5.5's safeguards flagged this message…"), which the registered classifier reads as an infrastructure failure: IFEval prompt 143 in every arm (as in the earlier study) and prompt 1776 in the candidate arm only (both other arms answered it), and one LAB-Bench ProtocolQA item (`bee8b322…`) in every arm. An item without a scored attempt in an arm is excluded from every contrast that involves that arm; IFEval's 539 and LAB-Bench's 219 are the realised counts. No run hit its turn cap or its time limit. On SWE-bench, 2 of 300 patches failed to apply and 1 was empty; all three count as unresolved. EvalPlus evaluated every HumanEval+ arm twice with no outcome changing. The LongMemEval judge gave no ambiguous verdict (a reply whose first word and the official substring rule disagree) in 360 judgements.

The path audit over every stream flagged 34 SWE-bench runs on 14 items (7 baseline, 13 old, 15 candidate) and one single-turn run. The SWE-bench flags are 49 distinct shell calls: 36 refused by the permission check (17 chained a host-side edit or scratch-file write to a container command, 19 were plain host commands; 20 named `/tmp` scratch paths and 16 named repository paths that the audit's parser read as absolute) and 13 that ran, every one a read-only `cat`, `sed -n`, `grep` or `ls` on the run's own repository through a relative path. The single-turn flag is a CyberSecEval baseline run that tried to read its own Claude Code memory file under the home directory and was refused. None read benchmark data, a gold patch, another run, the other package or the owner's files.

Exploratory, as in the earlier study: on SWE-bench a command in the task's test container executed in 7 and 9 of 50 baseline runs (replicates 1 and 2), 15 and 17 old-package runs and 18 and 24 candidate runs; attempts were more frequent (10/15, 33/37, 35/40) because a container command chained to a host-side edit is refused as a whole. Nothing about this was registered.

## Deviations from the registered plan

1. **Harness changes after launch**, none touching a prompt, a scoring rule, an exclusion or the analysis: the runner now seeds its usage gate from the newest attempt summary when it starts (a restarted runner had begun preparing workspaces into a paused window; it was stopped before any model call, `budget-log.md` 20:57–20:59); the SWE-bench scorer's two replicate files are merged by the analysis; the container-use descriptive distinguishes attempted from executed commands (a correction carried over from the earlier study's review); the LongMemEval two-stage scoring hook; the path audit's allow-list names the package directories. The committed `harness/` is the final state.
2. **Scheduling.** After the first five-hour window (937 results, weekly meter 0.03 → 0.14) the six replication benchmarks were stopped between items, with no attempt in flight, so that the benchmarks whose owner's references the fold changed (SWE-bench, BFCL, LongMemEval, Design2Code) and IFEval used the next windows first; the six resumed from their next scheduled item the following morning. Decided from meter readings and a cost projection before any result was scored; every benchmark completed its schedule.
3. **A pipeline dry run.** The Design2Code scorer was run on 27 early results to test the pipeline; its outputs were deleted and every benchmark was scored once, after its generation had closed.
4. **The LongMemEval judge** is the declared substitute (ADDENDUM.md §8), calibrated before use; its primary endpoint is one judgement per response.
5. **Safeguards refusals** are classified as infrastructure by the registered rule and dropped per arm; the one candidate-only drop (IFEval 1776) is visible in the counts.
6. **The packages were rebuilt for their record.** A machine restart on the night of 2026-10-12 cleared `/private/tmp`, where the two packages and the first copy of this folder's uncommitted results lived, after every run and every scoring step had finished. The packages were rebuilt from `INPUTS.json` on 2026-10-13 with every file hash and both manifest digests reproduced (`build-report.json`), and the results were copied again from the data root, which was untouched.

## Limitations

- **The fold was never read.** This is the study's main finding and its main limit: under these conditions the two packages were the same package to the model. The contrasts say nothing about what the reference files would do if a contract directed the model to read them, or in work where a model consults references on its own; they say that in 4,328 runs across eleven benchmarks, including 200 agentic SWE-bench runs with full read access, it did not.
- **The tool-access variant.** Single-turn runs had `Read` where the earlier study had only `Skill`; the earlier study's numbers are not contemporary controls here and were not pooled.
- **One model, one host, one sample.** As before. Another model, host or effort setting can behave differently.
- **Power.** At α = 0.05/33 the minimum detectable effect is 5.5 points on IFEval, 8–10 on the other single-turn benchmarks, 28.5 on SWE-bench; the observed discordance is low everywhere, so smaller effects are undetectable, and the two inconclusive SWE-bench contrasts reflect that.
- **Ceilings** on LongMemEval (oracle) and Design2Code, above.
- **Narrow endpoints**, as in the earlier study.

## What this means for the fold

The fold's references are content the model would have to open. Nothing in the invoked contracts directs it to, and on these tasks it did not. A reference-level change can only be measured, or matter in use, when the contract names the file for the situation at hand or the work is the kind where the model goes looking; neither held here. The fold ships in 3.4.0 as reference depth, exactly as Codex's source review describes it, with no claim of a measured effect.

## Receipts

**In this folder:** `PROTOCOL.md` (Codex, `d077cef`), `ADDENDUM.md` (v1.1), `INPUTS.json` and `schedule.jsonl` (the frozen packages, samples and order), `build-report.json`, `canaries/`, `harness/` (the executing harness, final state), `results/` with every per-item outcome (`items/<benchmark>.csv`), the analysis (`fold-analysis.json`), the descriptives, every table (`fold-tables.md`), the path audit, the judge calibration and the budget log. Codex's preparation (`controller.py`, `runtime.py`, `scoring.py`, their tests, `VALIDATION.json`) is kept unexecuted.

**Full receipts:** `fabius-source-fold-benchmarks-2026-10.tar.gz`, attached to the GitHub Release `v3.4.0-sealed`: 122,815,240 bytes, SHA-256 `5be2286f293f6777952e1c20703114bd67f7f4c0569064386ef6d341bd13d22b`, 41,692 files. Every attempt's command, prompt, full event stream and summary, the SWE-bench patches and official evaluation logs, every scorer's inputs and outputs, the judge prompts and judgements, and the harness. The account holder's name, email and username are masked letter for letter, as in the earlier archive; a check over every file found no remaining occurrence.

**Recompute every number** (the scripts read only the per-item files; `FB_COHORT=fold FB_ROOT=<the archive>`):

```text
python harness/analyze_fold.py --json results/fold-analysis.json
python harness/descriptives.py
python harness/make_report_fold.py > results/fold-tables.md
```
