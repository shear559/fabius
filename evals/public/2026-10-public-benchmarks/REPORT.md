# Fabius on public benchmarks: report, October 2026

Fabius was run against the same model without it on nine established public benchmarks: through its router, `/fabius`, and through each measured skill's own command, `/fabius:fabius-<skill>`. No comparison showed a gain or a loss after correction for multiple comparisons. Of the twelve registered comparisons, seven were ties, three were non-inferior and two, both on SWE-bench, were inconclusive, and every Fabius arm cost more than the baseline, from ×1.33 to ×2.03 per task.

**Scope of every number in this report:** Fabius 3.3.0 (the tree of the signed tag `v3.3.0-sealed`, sealed root `e1958cb5…`), the model `claude-sonnet-5-5`, Claude Code 2.1.289 run headless in a clean context, runs from 2026-10-06 to 2026-10-08. Each result names its arm, its invocation, k (samples per item) and n (items). Absolute rates belong to this harness and are not comparable with leaderboard or model-card numbers. Fabius 3.4.0, the release that publishes this study, changes no skill contract; it adds and refines reference files, and the continuation study beside this one (`../2026-10-source-fold-benchmarks/REPORT.md`) measured that package against the one measured here.

## Results

### The router, `/fabius` (Family 1, Holm-corrected over three)

`/fabius` showed no detectable difference on SWE-bench Verified Mini (88.0% vs 84.0% resolved, k = 2, n = 50) at ×1.60 the baseline's cost, tied on IFEval (87.4% vs 89.1% prompt-level strict, n = 540) at ×1.87 the cost, and tied on HumanEval+ (96.3% vs 95.1%, n = 163) at ×1.98 the cost.

### Each skill by its own command, `/fabius:fabius-<skill>` (Family B, Holm-corrected over eight)

- **Ties:** `fabius-parcus` on HumanEval+ (95.1% vs 95.1%, n = 163) at ×1.61 the cost; `fabius-scientia` on LAB-Bench (85.2% vs 85.9%, n = 128) at ×1.74; `fabius-fortuna` on FinQA (83.5% vs 85.0%, n = 200) at ×1.96; `fabius-cohors` on BFCL (92.0% vs 92.5%, n = 200) at ×2.03.
- **Non-inferior:** `fabius-praesidium` on CyberSecEval (86.9% vs 82.5% not flagged insecure, n = 137) at ×1.69 the cost; `fabius-doctrina` on DS-1000 (87.5% vs 83.5%, n = 200) at ×2.02; `fabius-catena` on SmartBugs-curated (76.9% vs 72.0%, n = 143) at ×1.89.
- **No detectable difference at this sample size:** `fabius-disciplina` on SWE-bench Verified Mini (87.0% vs 84.0% resolved, k = 2, n = 50) at ×1.84 the cost.

Two of these results look like gains and are not. `fabius-catena` scored +4.9 points (unadjusted 95% CI +0.8 to +9.2, exact p = 0.039) and `fabius-doctrina` +4.0 (+0.1 to +8.2, p = 0.077). After Holm correction over the eight skill comparisons their p-values are 0.312 and 0.538, so the registered rule reads both as non-inferior, not as gains.

### The README's earlier `fabius:` prefix (Family 2)

Until 3.3.0 the README told users to start a prompt with the word `fabius:`. That arm tied on HumanEval+ (96.3% vs 95.1%, n = 163) at ×1.33 the cost, but in none of its 186 runs did the router's contract reach the context at the first turn; one IFEval run loaded the router later through the Skill tool. The arm therefore measured the skill listing that the installed plugin adds, not the router. From 3.3.1 the README uses `/fabius` and `/fabius:fabius-<skill>`.

### Did the rules load?

The event stream records no message for a slash command's expansion, so loading is read from the first turn's prompt size against the same item's baseline run: at least 4,500 more tokens for the router, at least 2,500 for a skill.

- `/fabius` put the router's contract in context in 803 of 803 runs. The router then loaded a specialist through the Skill tool in 1 of those runs (`fabius-mercatus`, on one IFEval prompt). The `/fabius` results therefore measure the router's own rules, not the specialists'.
- Each skill's own command put that skill's contract in context in all 1,271 of its runs, with no further skill loaded.
- The `fabius:` prefix put the router in context at the first turn in 0 of 186 runs.
- The baseline loaded no Fabius skill, as it could not. In the CyberSecEval baseline, 16 of 137 runs loaded one of Claude Code's bundled skills through the Skill tool (18 calls: `claude-api` ×8, `init` ×4, `simplify` ×3, `run` ×2, `dataviz` ×1); no baseline run on any other benchmark called the Skill tool.

### All registered comparisons

n is items (× 2 where each item ran twice). "Only Fabius / only baseline" counts the items that only one arm passed (k = 1). p is the exact McNemar test for k = 1 and the paired sign-flip test for k = 2; p (Holm) is adjusted within the family. The 95% interval is Newcombe's hybrid score interval for k = 1 and a BCa bootstrap stratified by repository for k = 2, unadjusted.

| Arm | Benchmark (endpoint) | n | Fabius | Baseline | Difference (points) | 95% CI | only Fabius / only baseline | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `/fabius` | SWE-bench Verified Mini (resolved) | 50 × 2 | 88.0% | 84.0% | +4.0 | -1.0 to +10.0 | — | 0.289 | 0.867 | **INCONCLUSIVE** |
| `/fabius` | IFEval (prompt-level strict) | 540 | 87.4% | 89.1% | -1.7 | -4.6 to +1.2 | 27 / 36 | 0.314 | 0.867 | **TIE** |
| `/fabius` | HumanEval+ (plus tests pass) | 163 | 96.3% | 95.1% | +1.2 | -1.7 to +4.6 | 3 / 1 | 0.625 | 0.867 | **TIE** |
| `fabius:` prefix | HumanEval+ (plus tests pass) | 163 | 96.3% | 95.1% | +1.2 | -1.2 to +4.2 | 2 / 0 | 0.500 | 0.500 | **TIE** |
| `/fabius:fabius-disciplina` | SWE-bench Verified Mini (resolved) | 50 × 2 | 87.0% | 84.0% | +3.0 | -2.0 to +10.0 | — | 0.531 | 1.000 | **INCONCLUSIVE** |
| `/fabius:fabius-parcus` | HumanEval+ (plus tests pass) | 163 | 95.1% | 95.1% | +0.0 | -2.7 to +2.7 | 1 / 1 | 1.000 | 1.000 | **TIE** |
| `/fabius:fabius-praesidium` | CyberSecEval instruct (Python) (not flagged insecure) | 137 | 86.9% | 82.5% | +4.4 | -0.6 to +9.7 | 9 / 3 | 0.146 | 0.876 | **NON-INFERIOR** |
| `/fabius:fabius-scientia` | LAB-Bench ProtocolQA + SeqQA (correct option) | 128 | 85.2% | 85.9% | -0.8 | -4.8 to +3.1 | 2 / 3 | 1.000 | 1.000 | **TIE** |
| `/fabius:fabius-fortuna` | FinQA (answer matches) | 200 | 83.5% | 85.0% | -1.5 | -4.4 to +1.3 | 2 / 5 | 0.453 | 1.000 | **TIE** |
| `/fabius:fabius-doctrina` | DS-1000 (no PyTorch/TensorFlow) (tests pass) | 200 | 87.5% | 83.5% | +4.0 | +0.1 to +8.2 | 12 / 4 | 0.077 | 0.538 | **NON-INFERIOR** |
| `/fabius:fabius-catena` | SmartBugs-curated (category matches) | 143 | 76.9% | 72.0% | +4.9 | +0.8 to +9.2 | 8 / 1 | 0.039 | 0.312 | **NON-INFERIOR** |
| `/fabius:fabius-cohors` | BFCL non-live AST (official AST check) | 200 | 92.0% | 92.5% | -0.5 | -3.2 to +2.1 | 2 / 3 | 1.000 | 1.000 | **TIE** |

The `fabius:` prefix also ran on a fixed 10-task SWE-bench subset, outside the test families and descriptive only: 80.0% vs 90.0% resolved, n = 10.

**Minimum detectable effect** at 80% power under the exact McNemar test, for the share of items on which the arms disagree (ψ): on IFEval (n = 540) 4.5, 6.3 and 7.7 points at ψ = 0.1, 0.2 and 0.3 (α = 0.05/3); on HumanEval+ (n = 163) 7.9, 11.5 and 14.0; on SWE-bench (n = 50) none at ψ = 0.1, then 19.1 and 24.5. In Family B (α = 0.05/8) it is 7.9 to 9.5 points at ψ = 0.1 on the single-turn benchmarks and 26.6 points on SWE-bench at ψ = 0.3. On SWE-bench the arms disagreed on 4 of 50 tasks per replicate for `/fabius` and on 6 and 7 for `fabius-disciplina`; at that discordance no effect is detectable with 80% power, which is why both SWE-bench rows are inconclusive rather than ties. All values: `results/analysis-part-a.json` and `results/analysis-part-b.json`, key `mde`.

### Cost and behaviour

Each ratio is Fabius ÷ baseline per item, as a geometric mean with a BCa 95% interval; cost is what Claude Code reported for the run. The contract text travels with every prompt, so on a short single-turn task most of the extra cost is input.

| Arm · benchmark | Verdict | Cost | Total tokens | Output tokens | Wall time |
|---|---|---|---|---|---|
| `/fabius` · SWE-bench Verified Mini | INCONCLUSIVE | ×1.60 (1.53–1.66) | ×1.60 (1.51–1.71) | ×1.17 (1.10–1.24) | ×1.26 (1.18–1.35) |
| `/fabius` · IFEval | TIE | ×1.87 (1.85–1.89) | ×1.86 (1.85–1.88) | ×1.12 (1.08–1.16) | ×1.08 (1.06–1.10) |
| `/fabius` · HumanEval+ | TIE | ×1.98 (1.97–1.99) | ×1.91 (1.91–1.92) | ×1.20 (1.15–1.27) | ×1.08 (1.05–1.11) |
| `fabius:` prefix · HumanEval+ | TIE | ×1.33 (1.32–1.34) | ×1.29 (1.29–1.30) | ×1.03 (0.99–1.08) | ×1.03 (1.00–1.06) |
| `/fabius:fabius-disciplina` · SWE-bench Verified Mini | INCONCLUSIVE | ×1.84 (1.73–1.96) | ×2.07 (1.88–2.26) | ×1.92 (1.74–2.12) | ×1.83 (1.65–2.05) |
| `/fabius:fabius-parcus` · HumanEval+ | TIE | ×1.61 (1.60–1.62) | ×1.59 (1.58–1.59) | ×1.04 (0.99–1.09) | ×0.94 (0.91–0.97) |
| `/fabius:fabius-praesidium` · CyberSecEval | NON-INFERIOR | ×1.69 (1.53–1.80) | ×1.59 (1.44–1.71) | ×1.37 (1.28–1.48) | ×1.19 (1.11–1.28) |
| `/fabius:fabius-scientia` · LAB-Bench | TIE | ×1.74 (1.70–1.80) | ×1.76 (1.74–1.80) | ×1.48 (1.36–1.64) | ×1.20 (1.13–1.29) |
| `/fabius:fabius-fortuna` · FinQA | TIE | ×1.96 (1.95–1.96) | ×1.91 (1.90–1.91) | ×1.65 (1.54–1.78) | ×1.15 (1.11–1.20) |
| `/fabius:fabius-doctrina` · DS-1000 | NON-INFERIOR | ×2.02 (2.01–2.03) | ×1.91 (1.91–1.92) | ×1.27 (1.16–1.40) | ×1.09 (1.04–1.16) |
| `/fabius:fabius-catena` · SmartBugs-curated | NON-INFERIOR | ×1.89 (1.87–1.90) | ×1.84 (1.83–1.84) | ×1.89 (1.80–1.98) | ×1.34 (1.23–1.46) |
| `/fabius:fabius-cohors` · BFCL | TIE | ×2.03 (2.03–2.04) | ×1.95 (1.95–1.95) | ×1.34 (1.26–1.44) | ×1.08 (1.03–1.14) |

On SWE-bench, where `/fabius` showed no detectable difference, its runs took ×1.15 the turns (1.09–1.20) and wrote patches of the same size (×1.01, 0.95–1.07); where `fabius-disciplina` showed no detectable difference, its runs took ×1.51 the turns (1.39–1.63), again with patches of the same size (×1.04, 0.97–1.12). Every row, with the interval for each measure: `results/tables.md`.

### What changed in the agent's behaviour (exploratory, not registered)

On SWE-bench the Fabius rules changed how the agent worked even though the resolved rate showed no detectable difference. The baseline attempted a command in the task's test container in 14 and 15 of 50 runs (replicates 1 and 2) and had one execute in 6 and 10; `/fabius` attempted in 39 and 38 and executed in 31 and 32; `fabius-disciplina` attempted in 39 and 40 and executed in 18 and 20. The difference between attempted and executed is the permission check: a container command chained to a host-side edit or scratch-file write (for example `cat > /tmp/t/file.py … && <wrapper> "cd /testbed && pytest …"`) is refused as a whole, and `fabius-disciplina` did that most often (37 of 50 runs in each replicate had at least one refusal, against 23 and 21 for the baseline and 18 and 20 for `/fabius`). The `fabius:` prefix attempted none in its 10 runs. These counts come from `harness/descriptives.py` (a Bash call naming the run's wrapper; executed = its tool result was not an error); nothing about them was registered in advance.

## Registered sensitivity analyses

| Analysis | Result |
|---|---|
| SWE-bench · `/fabius` vs baseline · replicate 1 only | +4.0 points, 95% CI -4.7 to +13.4, n = 50, p = 0.625 |
| SWE-bench · `/fabius` vs baseline · replicate 2 only | +4.0 points, 95% CI -4.7 to +13.4, n = 50, p = 0.625 |
| SWE-bench · baseline replicate 1 vs replicate 2 (A/A) | disagree on 8 of 50 tasks (16%) |
| SWE-bench · `/fabius` replicate 1 vs replicate 2 | disagree on 2 of 50 tasks |
| SWE-bench · `/fabius` vs baseline · without the 9 audit-flagged items | +3.7 points, 95% CI -1.2 to +9.8, n = 41, p = 0.375 |
| SWE-bench · `/fabius:fabius-disciplina` vs baseline · without the 15 audit-flagged items | +1.4 points, 95% CI -2.9 to +11.4, n = 35, p = 1.000 |
| IFEval · prompt-level loose | -0.2 points, 95% CI -2.6 to +2.3, n = 540, p = 1.000 |
| IFEval · strict, without the `repeat_prompt` prompts | -0.6 points, 95% CI -3.6 to +2.4, n = 499, p = 0.791 |
| IFEval · strict, scoring all assistant text blocks | -1.5 points, 95% CI -4.4 to +1.4, n = 540, p = 0.374 |
| HumanEval+ · `/fabius` vs baseline · base tests | +0.6 points, 95% CI -1.7 to +3.4, n = 163, p = 1.000 |
| HumanEval+ · `fabius:` prefix vs baseline · base tests | +0.6 points, 95% CI -1.7 to +3.4, n = 163, p = 1.000 |

The baseline disagreed with itself between its two SWE-bench replicates on more tasks (8) than `/fabius` disagreed with the baseline in either replicate (4).

## Run outcomes

No run in any arm hit its turn cap or its time limit. On IFEval, prompt 143 was refused by the model's safeguards filter ("API Error: Sonnet 5.5's safeguards flagged this message…") in all three attempts in each arm; the registered classifier reads that text as an infrastructure failure, so the prompt was dropped from both arms. Two other baseline attempts (prompts 1934 and 2887) were cut short when IFEval was stopped and restarted for the gate correction at 04:18:20 (deviation 1), were discarded, and those prompts were rerun; the tables count them among "INFRA attempts retried". No other benchmark had an infrastructure failure. On SWE-bench no patch was empty, one patch in each of baseline and `/fabius` (replicate 2) failed to apply and counts as unresolved, and no scoring error occurred. EvalPlus evaluated every HumanEval+ arm twice with no outcome changing between the two evaluations. Per-arm counts, including runs whose final text ends on a question: `results/tables.md`, *Run outcomes per arm*.

## How it was measured

### Arms

| Arm | Plugin | Prompt |
|---|---|---|
| baseline | none | the task, verbatim |
| `fabius:` prefix | Fabius 3.3.0 | `fabius: ` + the task (the README's documented form until 3.3.0) |
| `/fabius` | Fabius 3.3.0 | `/fabius ` + the task |
| `/fabius:fabius-<skill>` | Fabius 3.3.0 | `/fabius:fabius-<skill> ` + the task |

### Held constant in every arm

- **Harness.** Claude Code 2.1.289 (native macOS binary, its SHA-256 recorded), `claude -p --output-format stream-json --verbose`, the model `claude-sonnet-5-5` checked in every run's init record, default effort. Claude Code exposes no temperature.
- **Clean context.** `--setting-sources project` (no user settings, user plugins, hooks or user skills), `--strict-mcp-config` (no MCP servers), `--no-session-persistence`, and a fresh working directory per run with no CLAUDE.md or project memory. Claude Code's own bundled skills (19 in this version) and built-in plugins remain in every arm; they are part of the harness, not of Fabius.
- **File access.** `--disallowedTools 'Read(//Users/**)' 'Edit(//Users/**)' 'Write(//Users/**)' 'Read(//private/var/folders/**)'`, so no run could read the benchmark data, another run or the owner's files. Every stream was audited afterwards (see *Path audit*).
- **Plugin.** The exact tree of `v3.3.0-sealed` (`git archive`, 322 files), its 18 sealed files matching the seal manifest, re-hashed at the start and end of every benchmark.
- **Tools.** Single-turn benchmarks (IFEval, HumanEval+ and every Part B benchmark except SWE-bench): the Skill tool only, 8 turns, 300 seconds. SWE-bench: Read, Edit, Write, Glob, Grep, TodoWrite and Skill, plus Bash only through a wrapper that runs each command inside a network-less container of the task's official image; 150 turns, 40 minutes.
- **Order.** Items ran in a seeded random order (numpy `default_rng(20261006)`), all arms of an item back to back, so a budget stop removes whole items, never single arms.
- **Failures.** An attempt with no result, an API or usage error, the wrong model or the wrong skill set is infrastructure and is retried up to twice; everything else, including time-outs and turn caps, is an outcome and is never rerun. An item with no scored attempt after retries is dropped from every arm.

### Benchmarks

| Benchmark | Arm(s) | Source, pinned | Sample | Primary endpoint and scorer |
|---|---|---|---|---|
| SWE-bench Verified Mini | `/fabius` (k = 2), `/fabius:fabius-disciplina` (k = 2), `fabius:` prefix (fixed 10) | `MariusHobbhahn/swe-bench-verified-mini`, rows checked identical to `SWE-bench/SWE-bench_Verified`; official images by digest | all 50 (25 Django, 25 Sphinx), all valid | resolved, by `swebench` 5.0.2 `run_evaluation` |
| IFEval | `/fabius` | `google-research/instruction_following_eval` @ `e6890f8` | all 541; 540 scored (prompt 143 dropped) | prompt-level strict, by the official `evaluation_main` (langdetect seeded) |
| HumanEval+ | `/fabius`, `fabius:` prefix, `/fabius:fabius-parcus` | EvalPlus HumanEval+ v0.1.10 | 163 of 164 (HumanEval/32 excluded: its canonical solution fails EvalPlus's own sandbox) | plus tests pass, by EvalPlus 0.3.1 in a Linux container |
| CyberSecEval instruct, Python | `/fabius:fabius-praesidium` | Meta PurpleLlama @ `172c107`, `instruct-v2.json` | 200 of 282 drawn; 137 ran before the budget stop | no issue reported by the official Insecure Code Detector |
| LAB-Bench ProtocolQA + SeqQA | `/fabius:fabius-scientia` | `futurehouse/lab-bench` @ `5c77cec`; harness @ `998a8e0` | 220 drawn (108 + 112); 128 ran (67 + 61) before the budget stop | correct option, by the official template and answer parser |
| FinQA | `/fabius:fabius-fortuna` | `czyssrs/FinQA` @ `0f16e28`, test split | 200 of 1,147 | answer within 1% of the gold value (yes/no exact) |
| DS-1000 | `/fabius:fabius-doctrina` | `xlangai/DS-1000` @ `4416080` | 200 of the 887 without PyTorch or TensorFlow | hidden tests pass, by the official execution check in a network-less container |
| SmartBugs-curated | `/fabius:fabius-catena` | `smartbugs/smartbugs-curated` @ `230e649` | all 143 contracts | the one named DASP category is an annotated one |
| BFCL v4, non-live AST | `/fabius:fabius-cohors` | `bfcl-eval` 2026.3.23 (= gorilla @ `6ea5797`) | 200, 40 per category | the official AST checker's verdict |

Each Part B benchmark's prompt template, scoring rule, self-check and every deviation from its official protocol are written in `skills/<benchmark>/README.md`, with hashes in `source.json`, committed before its runs.

### Statistics and verdicts

Each arm is compared with the baseline, paired by item. Verdicts come from the Holm-adjusted p alone: **GAIN** or **LOSS** at p ≤ 0.05; otherwise **TIE** if the 90% interval lies inside ±5 points, **NON-INFERIOR** if the 95% interval's lower bound is above −5 points, and **INCONCLUSIVE** otherwise. SWE-bench (n = 50) can only be GAIN, LOSS or INCONCLUSIVE. The families are Family 1 (`/fabius` on its three benchmarks), Family 2 (the `fabius:` prefix) and Family B (the eight skill comparisons).

### Registration

The protocol, harness and analysis were committed and pushed before the runs they govern. Push times are GitHub's repository activity, converted to UTC+3; run starts are from `results/budget-log.md`.

| Commit | Pushed | What it fixed | First run it governs |
|---|---|---|---|
| `842d157` | 2026-10-06 19:35:47 | protocol 1.1, runner, classifier, schedule | HumanEval+, 19:36:02 |
| `d76d963` | 2026-10-06 22:20:12 | protocol 1.2, SWE-bench harness, scorers, analysis | every SWE-bench run and all scoring |
| `2fafb77` | 2026-10-07 03:31:29 | protocol 1.3 | SWE-bench |
| `53379f7` | 2026-10-07 04:08:04 | SWE-bench validity receipts, the fixed `fabius:` subset | SWE-bench |
| `74b7c9d` | 2026-10-07 04:13:34 | protocol 1.4 | SWE-bench replicate 1, 04:13:40 |
| `e2976cd` | 2026-10-07 09:01:10 | Part B protocol 1.0 | `fabius-disciplina` and `fabius-parcus`, 09:01:10 |
| `90f302b` | 2026-10-07 22:20:23 | the six remaining skill harnesses and the Part B analysis | the six skills, 22:20:24 |

## Deviations from the registered plan

1. **IFEval gate.** A scripting error started IFEval with three arms before the registered cost gate was logged, and the first log line misread its own projection (6.6 points against a 5-point gate). The correction, 23 seconds later, applied the gate as registered: the `fabius:` prefix was dropped from IFEval and IFEval restarted with two arms. The 13 `fabius:` runs completed in that minute are kept in the receipts and not analysed, so Family 2 holds HumanEval+ only.
2. **Order.** SWE-bench replicate 1 ran before IFEval, by the owner's choice before any result (protocol 1.2). Scheduling only.
3. **Machine sleep.** The Mac slept overnight and froze a paused runner; it was restarted with no partial item, and `caffeinate` kept the machine awake from then on (protocol 1.3).
4. **Budget.** The owner raised the study's weekly usage cap from 75% to 90% before Part B and to 97% before the last six skills, and moved the five-hour pause from 60% to 90% for those six; each decision was logged before the block it affected. At 97% no new item started: CyberSecEval stopped at 137 of 200 items and LAB-Bench at 128 of 220. Because items ran in a seeded random order, the realised items are the first 137 and 128 of that order, not a selection.
5. **Reused baselines.** As Part B registered, `fabius-disciplina` and `fabius-parcus` are compared with the Part A baseline runs of the same day, model, harness and plugin tree, which did not run back to back with them.
6. **Verdict rule for SWE-bench in Part B.** Part B's text says only that SWE-bench cannot be a TIE, which would allow NON-INFERIOR; the Part B analysis code applies Part A's stricter rule (GAIN, LOSS or INCONCLUSIVE only), and it was committed before `fabius-disciplina` was scored. Under the literal text `fabius-disciplina` (95% lower bound −2.0) would read NON-INFERIOR. The report keeps the stricter verdict.
7. **Code changed or committed after registration.** `analyze.py` (a command-line parsing fix), `collect.py` (item ids that contain `/`, as in LAB-Bench, FinQA and SmartBugs) and `audit_paths.py` (narrowed to host-side paths after false positives). `analyze_skills.py` was last edited at 09:02 on 2026-10-07, before any Part B result, but committed only at 22:20, after `fabius-parcus` had been scored (09:08); `fabius-disciplina` and the six later skills were scored after that commit. Written after the runs: `score_ifeval.py` (the registered IFEval scoring), `finalize.py` (the registered Part A analysis and sensitivities), `make_report.py`, `descriptives.py`, `sanitize.py` and `check_ifeval_public.py`. None changes a prompt, a scoring rule or an exclusion, and the diff of each is in this repository's history.
8. **Two IFEval prompts are scored at random by the official code.** Prompts 1122 and 1129 ask for at least four `#` and at least six `!`; IFEval's letter-frequency check accepts only letters, so the official code counts a randomly chosen letter instead. Their outcomes can change from one scoring pass to the next whatever the response; together they can move the IFEval difference by at most 0.4 points. Found while preparing the public receipts.
9. **The path audit was first run before Part B.** That first run (08:17 on 2026-10-07) covered Part A only. For this report it was re-run over every stream; it added 16 `fabius-disciplina` runs and changed nothing else. `finalize.py` now takes the flagged items per comparison, meaning the items where a run of either compared arm was flagged. This leaves the `/fabius` result unchanged and adds the matching sensitivity for `fabius-disciplina`, as the registered protocol requires for every primary endpoint.
10. **Cost unit.** The protocol's efficiency formula adds 1 to each value before the log; applied to the cost Claude Code reports in dollars, the +1 swamps every value (the ratio then comes out between 1.02 and 1.05 for every arm, whatever its result). `finalize.py` therefore computes the cost ratio in millionths of a dollar as well, and the tables show that one as "cost"; both are in `results/analysis-part-a.json` (`cost_usd` and `cost_microusd`). This is a change of unit decided after the runs, not a change of formula.
11. **Identity masking in the public receipts.** Claude Code puts the account holder's name and email into the model's context in every arm, and some answers used them. The public copy masks them letter for letter (see *Receipts*); scores were computed on the original text.

## Path audit

The audit scans every stream of every benchmark. It flagged 35 SWE-bench runs on 15 items (11 baseline, 8 `/fabius`, 16 `fabius-disciplina`) for a tool call naming a path outside the run's workspace, and nothing on the single-turn benchmarks, where the only tool was Skill. Each flagged call was read by hand:

- 30 were host commands that the permission rules refused: 23 of them chained a host-side edit or scratch-file write (`python - <<EOF`, `mkdir -p /tmp/t && cat > …`, `sed -i`) to a container command, and the whole call was refused; most named scratch paths such as `/tmp/t/file.py`, and 8 were relative repository paths (`django/contrib/admin/options.py`, `tests/roots/…`) that the audit's parser read as absolute ones;
- 8 were read-only host commands (`grep`, `cat`, `sed -n`, `ls`) on the run's own repository, again through relative paths the parser took for absolute; Claude Code approves read-only commands on its own, and every write attempt on the host was refused;
- 2 were single tool calls: a baseline Glob that searched the host's `/usr` for the docutils source and found nothing, and a `/fabius` Grep with a mistyped copy of the run's own workspace path that got back "Path does not exist".

That is 40 flagged tool calls; `audit.json` holds 99 entries because a call is listed once per matched path. None read benchmark data, a gold patch, another run or the owner's files. Without the flagged items the SWE-bench differences are +3.7 points for `/fabius` (n = 41) and +1.4 for `fabius-disciplina` (n = 35); see the sensitivity table.

## Limitations

- **One model, one host, one sample.** One model (`claude-sonnet-5-5`) in one host (Claude Code 2.1.289, headless), one sample per item (two on SWE-bench). Another model, host or effort setting can behave differently.
- **No placebo of equal length.** No arm added neutral text of the same length, so any effect would belong to "the package plus its invocation", not to particular rules.
- **Single-turn tasks gave the rules little to act on.** These benchmarks allowed only the Skill tool and 8 turns. Rules about running code, checking sources or using tools had no tool to act through.
- **Narrow endpoints.** CyberSecEval counts code that a static detector does not flag, which is not the same as secure code. SmartBugs-curated asks for one category label, not an audit. LAB-Bench, FinQA and BFCL match a single answer or call.
- **Power.** At n = 50, SWE-bench can detect only effects of roughly 18 to 27 points; on the single-turn benchmarks a difference of a few points can go undetected (*Minimum detectable effect* above).
- **Reused baselines and budget cuts.** See deviations 4 and 5.
- **Loading is inferred** from the first turn's prompt size, not observed directly.

## Not measured

- **`fabius-archivum`** (LongMemEval, oracle setting, 120 questions) and **`fabius-decor`** (Design2Code, 80 pages): both harnesses were built and committed before any run (`90f302b`, `skills/longmemeval/`, `skills/design2code/`) and not run, because the weekly usage cap was reached.
- **`fabius-mercatus`, `fabius-machina`, `fabius-ludus`:** no established public benchmark with an objective score for marketing copy, workflow wiring or game design that runs here.
- **`fabius-concilium`:** needs several model providers; only Claude was available.

## Receipts

**In this folder:** `PROTOCOL.md` (v1.4) and `PROTOCOL-SKILLS.md` (v1.0); `protocol-review.json` (the four methodology reviews of v1); `schedule.json` and `schedule-skills.json`; `harness/`; `skills/<benchmark>/` (prepare, score, self-check, source pins); `swebench/` (rows hash, image digests, validity runs, the fixed subset); `results/` with every per-item outcome (`items/<benchmark>.csv`), both analyses (`analysis-part-a.json`, `analysis-part-b.json`), `descriptives.json`, every table (`tables.md`), the path audit (`audit.json`) and the budget log.

**Full receipts:** `fabius-public-benchmarks-2026-10.tar.gz`, attached to the GitHub Release `v3.4.0-sealed`: 36,322,207 bytes, SHA-256 `d89bab37330c3f05787e761c15fe924675b65b4a3702bdc994063e6537beadda`, 27,540 files. It holds every attempt's command, prompt, full event stream and summary, the SWE-bench patches and official evaluation logs, every scorer's inputs and outputs, and the harness. The account holder's name, email and username are masked letter for letter (`X`/`x`, digits `0`), keeping length and case; a check over every file, binaries included, found no remaining occurrence. Re-scoring IFEval on the masked text with the random state held equal reproduces all 2,164 outcomes; `harness/check_ifeval_public.py` re-scores it from the archive.

**Recompute every number.** The scripts read only the per-item files and expect the archive at `~/Documents/fabius-benchmark` (`ROOT` at the top of each script). Both analyses below regenerate the published files byte for byte:

```text
python harness/finalize.py
python harness/analyze_skills.py swebench:disciplina humaneval:parcus cyberseceval:praesidium labbench:scientia finqa:fortuna ds1000:doctrina smartbugs:catena bfcl:cohors --json results/skills-analysis.json
python harness/descriptives.py
python harness/make_report.py > results/tables.md
```
