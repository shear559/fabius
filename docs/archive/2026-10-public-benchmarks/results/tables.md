### Part A — the router, `/fabius` (Family 1) and the README's `fabius:` prefix (Family 2)

| Arm | Benchmark (endpoint) | n | Fabius | Baseline | Difference (points) | 95% CI | only Fabius / only baseline | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `/fabius` | SWE-bench Verified Mini (resolved) | 50 × 2 | 88.0% | 84.0% | +4.0 | -1.0 to +10.0 | — | 0.289 | 0.867 | **INCONCLUSIVE** |
| `/fabius` | IFEval (prompt-level strict) | 540 | 87.4% | 89.1% | -1.7 | -4.6 to +1.2 | 27 / 36 | 0.314 | 0.867 | **TIE** |
| `/fabius` | HumanEval+ (plus tests pass) | 163 | 96.3% | 95.1% | +1.2 | -1.7 to +4.6 | 3 / 1 | 0.625 | 0.867 | **TIE** |
| `fabius:` prefix | HumanEval+ (plus tests pass) | 163 | 96.3% | 95.1% | +1.2 | -1.2 to +4.2 | 2 / 0 | 0.500 | 0.500 | **TIE** |

The `fabius:` prefix on the fixed 10-task SWE-bench subset (descriptive, outside the test families): 80.0% vs 90.0%, n = 10.

### Part B — each skill by its own command, `/fabius:fabius-<skill>` (Family B)

| Arm | Benchmark (endpoint) | n | Fabius | Baseline | Difference (points) | 95% CI | only Fabius / only baseline | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `/fabius:fabius-disciplina` | SWE-bench Verified Mini (resolved) | 50 × 2 | 87.0% | 84.0% | +3.0 | -2.0 to +10.0 | — | 0.531 | 1.000 | **INCONCLUSIVE** |
| `/fabius:fabius-parcus` | HumanEval+ (plus tests pass) | 163 | 95.1% | 95.1% | +0.0 | -2.7 to +2.7 | 1 / 1 | 1.000 | 1.000 | **TIE** |
| `/fabius:fabius-praesidium` | CyberSecEval instruct (Python) (not flagged insecure) | 137 | 86.9% | 82.5% | +4.4 | -0.6 to +9.7 | 9 / 3 | 0.146 | 0.876 | **NON-INFERIOR** |
| `/fabius:fabius-scientia` | LAB-Bench ProtocolQA + SeqQA (correct option) | 128 | 85.2% | 85.9% | -0.8 | -4.8 to +3.1 | 2 / 3 | 1.000 | 1.000 | **TIE** |
| `/fabius:fabius-fortuna` | FinQA (answer matches) | 200 | 83.5% | 85.0% | -1.5 | -4.4 to +1.3 | 2 / 5 | 0.453 | 1.000 | **TIE** |
| `/fabius:fabius-doctrina` | DS-1000 (no PyTorch/TensorFlow) (tests pass) | 200 | 87.5% | 83.5% | +4.0 | +0.1 to +8.2 | 12 / 4 | 0.077 | 0.538 | **NON-INFERIOR** |
| `/fabius:fabius-catena` | SmartBugs-curated (category matches) | 143 | 76.9% | 72.0% | +4.9 | +0.8 to +9.2 | 8 / 1 | 0.039 | 0.312 | **NON-INFERIOR** |
| `/fabius:fabius-cohors` | BFCL non-live AST (official AST check) | 200 | 92.0% | 92.5% | -0.5 | -3.2 to +2.1 | 2 / 3 | 1.000 | 1.000 | **TIE** |

### Did the rules actually load?

| Arm · benchmark | Runs | Contract in context at the first turn | Specialists loaded with the Skill tool |
|---|---|---|---|
| fabius-loaded · swebench | 100 | 100 / 100 (router) | none |
| fabius-doc · swebench | 10 | 0 / 10 (router) | none |
| fabius-loaded · ifeval | 540 | 540 / 540 (router) | fabius:fabius-mercatus ×1 |
| fabius-doc · ifeval | 0 | 0 / 0 (router) | none |
| fabius-loaded · humaneval | 163 | 163 / 163 (router) | none |
| fabius-doc · humaneval | 163 | 0 / 163 (router) | none |
| fabius-disciplina · swebench | 100 | 100 / 100 (the skill) | none |
| fabius-parcus · humaneval | 163 | 163 / 163 (the skill) | none |
| fabius-praesidium · cyberseceval | 137 | 137 / 137 (the skill) | none |
| fabius-scientia · labbench | 128 | 128 / 128 (the skill) | none |
| fabius-fortuna · finqa | 200 | 200 / 200 (the skill) | none |
| fabius-doctrina · ds1000 | 200 | 200 / 200 (the skill) | none |
| fabius-catena · smartbugs | 143 | 143 / 143 (the skill) | none |
| fabius-cohors · bfcl | 200 | 200 / 200 (the skill) | none |

### Cost and behaviour (Fabius ÷ baseline, per item, BCa 95% interval; descriptive)

| Arm · benchmark · measure | Ratio | 95% CI | n |
|---|---|---|---|
| fabius-loaded · swebench · output_tokens | ×1.17 | 1.10–1.24 | 100 |
| fabius-loaded · swebench · output_tokens · both resolved | ×1.19 | 1.12–1.26 | 82 |
| fabius-loaded · swebench · total_tokens | ×1.60 | 1.51–1.71 | 100 |
| fabius-loaded · swebench · total_tokens · both resolved | ×1.64 | 1.54–1.75 | 82 |
| fabius-loaded · swebench · elapsed_s | ×1.26 | 1.18–1.35 | 100 |
| fabius-loaded · swebench · elapsed_s · both resolved | ×1.32 | 1.22–1.42 | 82 |
| fabius-loaded · swebench · num_turns | ×1.15 | 1.09–1.20 | 100 |
| fabius-loaded · swebench · num_turns · both resolved | ×1.17 | 1.11–1.23 | 82 |
| fabius-loaded · swebench · patch_lines | ×1.01 | 0.95–1.07 | 100 |
| fabius-loaded · swebench · patch_lines · both resolved | ×1.02 | 0.97–1.08 | 82 |
| fabius-doc · swebench · output_tokens | ×1.02 | 0.94–1.19 | 10 |
| fabius-doc · swebench · output_tokens · both resolved | ×0.97 | 0.92–1.09 | 8 |
| fabius-doc · swebench · total_tokens | ×1.15 | 1.13–1.19 | 10 |
| fabius-doc · swebench · total_tokens · both resolved | ×1.15 | 1.13–1.20 | 8 |
| fabius-doc · swebench · elapsed_s | ×1.04 | 0.96–1.15 | 10 |
| fabius-doc · swebench · elapsed_s · both resolved | ×1.06 | 0.98–1.20 | 8 |
| fabius-doc · swebench · num_turns | ×0.99 | 0.93–1.11 | 10 |
| fabius-doc · swebench · num_turns · both resolved | ×0.99 | 0.92–1.14 | 8 |
| fabius-doc · swebench · patch_lines | ×1.04 | 0.93–1.38 | 10 |
| fabius-doc · swebench · patch_lines · both resolved | ×1.05 | 0.91–1.50 | 8 |
| fabius-loaded · ifeval · output_tokens | ×1.12 | 1.08–1.16 | 540 |
| fabius-loaded · ifeval · total_tokens | ×1.86 | 1.85–1.88 | 540 |
| fabius-loaded · ifeval · elapsed_s | ×1.08 | 1.06–1.10 | 540 |
| fabius-loaded · ifeval · num_turns | ×1.00 | 1.00–1.01 | 540 |
| fabius-loaded · humaneval · output_tokens | ×1.20 | 1.15–1.27 | 163 |
| fabius-loaded · humaneval · total_tokens | ×1.91 | 1.91–1.92 | 163 |
| fabius-loaded · humaneval · elapsed_s | ×1.08 | 1.05–1.11 | 163 |
| fabius-loaded · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| fabius-doc · humaneval · output_tokens | ×1.03 | 0.99–1.08 | 163 |
| fabius-doc · humaneval · total_tokens | ×1.29 | 1.29–1.30 | 163 |
| fabius-doc · humaneval · elapsed_s | ×1.03 | 1.00–1.06 | 163 |
| fabius-doc · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| fabius-loaded · swebench · cost | ×1.60 | 1.53–1.66 | 100 |
| fabius-doc · swebench · cost | ×1.17 | 1.13–1.24 | 10 |
| fabius-loaded · ifeval · cost | ×1.87 | 1.85–1.89 | 540 |
| fabius-loaded · humaneval · cost | ×1.98 | 1.97–1.99 | 163 |
| fabius-doc · humaneval · cost | ×1.33 | 1.32–1.34 | 163 |
| fabius-disciplina · swebench · output_tokens | ×1.92 | 1.74–2.12 | 100 |
| fabius-disciplina · swebench · total_tokens | ×2.07 | 1.88–2.26 | 100 |
| fabius-disciplina · swebench · cost | ×1.84 | 1.73–1.96 | 100 |
| fabius-disciplina · swebench · elapsed_s | ×1.83 | 1.65–2.05 | 100 |
| fabius-disciplina · swebench · num_turns | ×1.51 | 1.39–1.63 | 100 |
| fabius-disciplina · swebench · patch_lines | ×1.04 | 0.97–1.12 | 100 |
| fabius-parcus · humaneval · output_tokens | ×1.04 | 0.99–1.09 | 163 |
| fabius-parcus · humaneval · total_tokens | ×1.59 | 1.58–1.59 | 163 |
| fabius-parcus · humaneval · cost | ×1.61 | 1.60–1.62 | 163 |
| fabius-parcus · humaneval · elapsed_s | ×0.94 | 0.91–0.97 | 163 |
| fabius-parcus · humaneval · num_turns | ×1.00 | 1.00–1.00 | 163 |
| fabius-praesidium · cyberseceval · output_tokens | ×1.37 | 1.28–1.48 | 137 |
| fabius-praesidium · cyberseceval · total_tokens | ×1.59 | 1.44–1.71 | 137 |
| fabius-praesidium · cyberseceval · cost | ×1.69 | 1.53–1.80 | 137 |
| fabius-praesidium · cyberseceval · elapsed_s | ×1.19 | 1.11–1.28 | 137 |
| fabius-praesidium · cyberseceval · num_turns | ×0.91 | 0.86–0.94 | 137 |
| fabius-scientia · labbench · output_tokens | ×1.48 | 1.36–1.64 | 128 |
| fabius-scientia · labbench · total_tokens | ×1.76 | 1.74–1.80 | 128 |
| fabius-scientia · labbench · cost | ×1.74 | 1.70–1.80 | 128 |
| fabius-scientia · labbench · elapsed_s | ×1.20 | 1.13–1.29 | 128 |
| fabius-scientia · labbench · num_turns | ×1.00 | 1.00–1.00 | 128 |
| fabius-fortuna · finqa · output_tokens | ×1.65 | 1.54–1.78 | 200 |
| fabius-fortuna · finqa · total_tokens | ×1.91 | 1.90–1.91 | 200 |
| fabius-fortuna · finqa · cost | ×1.96 | 1.95–1.96 | 200 |
| fabius-fortuna · finqa · elapsed_s | ×1.15 | 1.11–1.20 | 200 |
| fabius-fortuna · finqa · num_turns | ×1.00 | 1.00–1.00 | 200 |
| fabius-doctrina · ds1000 · output_tokens | ×1.27 | 1.16–1.40 | 200 |
| fabius-doctrina · ds1000 · total_tokens | ×1.91 | 1.91–1.92 | 200 |
| fabius-doctrina · ds1000 · cost | ×2.02 | 2.01–2.03 | 200 |
| fabius-doctrina · ds1000 · elapsed_s | ×1.09 | 1.04–1.16 | 200 |
| fabius-doctrina · ds1000 · num_turns | ×1.00 | 1.00–1.00 | 200 |
| fabius-catena · smartbugs · output_tokens | ×1.89 | 1.80–1.98 | 143 |
| fabius-catena · smartbugs · total_tokens | ×1.84 | 1.83–1.84 | 143 |
| fabius-catena · smartbugs · cost | ×1.89 | 1.87–1.90 | 143 |
| fabius-catena · smartbugs · elapsed_s | ×1.34 | 1.23–1.46 | 143 |
| fabius-catena · smartbugs · num_turns | ×1.00 | 1.00–1.00 | 143 |
| fabius-cohors · bfcl · output_tokens | ×1.34 | 1.26–1.44 | 200 |
| fabius-cohors · bfcl · total_tokens | ×1.95 | 1.95–1.95 | 200 |
| fabius-cohors · bfcl · cost | ×2.03 | 2.03–2.04 | 200 |
| fabius-cohors · bfcl · elapsed_s | ×1.08 | 1.03–1.14 | 200 |
| fabius-cohors · bfcl · num_turns | ×1.00 | 1.00–1.00 | 200 |

### Declared sensitivity analyses

| Analysis | Result |
|---|---|
| swebench · fabius-loaded vs baseline · replicate 1 only | +4.0 points, 95% CI -4.7 to +13.4, n = 50, p = 0.625 |
| swebench · fabius-loaded vs baseline · replicate 2 only | +4.0 points, 95% CI -4.7 to +13.4, n = 50, p = 0.625 |
| swebench · baseline replicate 1 vs replicate 2 disagreement (A/A) | n 50, disagree 8, rate 0.16 |
| swebench · fabius-loaded replicate 1 vs replicate 2 disagreement | n 50, disagree 2 |
| swebench · fabius-loaded vs baseline · without audit-flagged items | +3.7 points, 95% CI -1.2 to +9.8, n = 41, p = 0.375 |
| swebench · fabius-loaded vs baseline · audit-flagged items | django__django-12143, django__django-12325, django__django-12406, django__django-12713, sphinx-doc__sphinx-11510, sphinx-doc__sphinx-7590, sphinx-doc__sphinx-8548, sphinx-doc__sphinx-9229, sphinx-doc__sphinx-9461 |
| swebench · fabius-disciplina vs baseline · without audit-flagged items | +1.4 points, 95% CI -2.9 to +11.4, n = 35, p = 1.000 |
| swebench · fabius-disciplina vs baseline · audit-flagged items | django__django-11885, django__django-12143, django__django-12325, django__django-12406, django__django-12713, sphinx-doc__sphinx-10673, sphinx-doc__sphinx-11510, sphinx-doc__sphinx-7590, sphinx-doc__sphinx-7748, sphinx-doc__sphinx-7985, sphinx-doc__sphinx-8035, sphinx-doc__sphinx-8548, sphinx-doc__sphinx-8551, sphinx-doc__sphinx-9229, sphinx-doc__sphinx-9461 |
| ifeval · loose prompt-level | -0.2 points, 95% CI -2.6 to +2.3, n = 540, p = 1.000 |
| ifeval · strict, excluding repeat_prompt prompts | -0.6 points, 95% CI -3.6 to +2.4, n = 499, p = 0.791 |
| ifeval · strict, all assistant text blocks | -1.5 points, 95% CI -4.4 to +1.4, n = 540, p = 0.374 |
| humaneval · fabius-loaded vs baseline · base tests | +0.6 points, 95% CI -1.7 to +3.4, n = 163, p = 1.000 |
| humaneval · fabius-doc vs baseline · base tests | +0.6 points, 95% CI -1.7 to +3.4, n = 163, p = 1.000 |

### Run outcomes per arm (descriptives.py)

| Benchmark · arm | Scored runs | Items with no scored attempt | INFRA attempts retried | Turn-cap hits | Timeouts | Final text ends on a question |
|---|---|---|---|---|---|---|
| swebench r1 · baseline | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r1 · fabius-disciplina | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r1 · fabius-doc | 10 | 0 | 0 | 0 | 0 | 0 |
| swebench r1 · fabius-loaded | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · baseline | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · fabius-disciplina | 50 | 0 | 0 | 0 | 0 | 0 |
| swebench r2 · fabius-loaded | 50 | 0 | 0 | 0 | 0 | 0 |
| ifeval · baseline | 540 | 1 | 5 | 0 | 0 | 27 |
| ifeval · fabius-doc | 13 | 0 | 0 | 0 | 0 | 0 |
| ifeval · fabius-loaded | 540 | 1 | 3 | 0 | 0 | 23 |
| humaneval · baseline | 163 | 0 | 0 | 0 | 0 | 0 |
| humaneval · fabius-doc | 163 | 0 | 0 | 0 | 0 | 0 |
| humaneval · fabius-loaded | 163 | 0 | 0 | 0 | 0 | 0 |
| humaneval · fabius-parcus | 163 | 0 | 0 | 0 | 0 | 0 |
| cyberseceval · baseline | 137 | 0 | 0 | 0 | 0 | 0 |
| cyberseceval · fabius-praesidium | 137 | 0 | 0 | 0 | 0 | 0 |
| labbench · baseline | 128 | 0 | 0 | 0 | 0 | 0 |
| labbench · fabius-scientia | 128 | 0 | 0 | 0 | 0 | 0 |
| finqa · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| finqa · fabius-fortuna | 200 | 0 | 0 | 0 | 0 | 0 |
| ds1000 · baseline | 200 | 0 | 0 | 0 | 0 | 0 |
| ds1000 · fabius-doctrina | 200 | 0 | 0 | 0 | 0 | 0 |
| smartbugs · baseline | 143 | 0 | 0 | 0 | 0 | 0 |
| smartbugs · fabius-catena | 143 | 0 | 0 | 0 | 0 | 0 |
| bfcl · baseline | 200 | 0 | 0 | 0 | 0 | 1 |
| bfcl · fabius-cohors | 200 | 0 | 0 | 0 | 0 | 0 |

### Exploratory, SWE-bench (not pre-registered)

| Replicate · arm | Runs that attempted a command in the test container | Runs where one executed | Runs with at least one permission denial |
|---|---|---|---|
| r1 · baseline | 14 / 50 | 6 / 50 (12.0%) | 23 / 50 |
| r1 · fabius-disciplina | 39 / 50 | 18 / 50 (36.0%) | 37 / 50 |
| r1 · fabius-doc | 0 / 10 | 0 / 10 (0.0%) | 6 / 10 |
| r1 · fabius-loaded | 39 / 50 | 31 / 50 (62.0%) | 18 / 50 |
| r2 · baseline | 15 / 50 | 10 / 50 (20.0%) | 21 / 50 |
| r2 · fabius-disciplina | 40 / 50 | 20 / 50 (40.0%) | 37 / 50 |
| r2 · fabius-loaded | 38 / 50 | 32 / 50 (64.0%) | 20 / 50 |
