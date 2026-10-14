### The 33 contrasts (one family, Holm-corrected together)

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
