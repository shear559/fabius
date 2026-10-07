# Fabius on public benchmarks — protocol

**Version 1.3 · 2026-10-07.** Version 1.1 was fixed before the first scored run (commit `842d157`); versions 1.2 (commit `d76d963`) and 1.3 change only the SWE-bench section and the run order, before any SWE-bench run — see *Changes in 1.2* and *Changes in 1.3* at the end. v1 was reviewed by four independent methodology reviewers (statistics, benchmark fidelity and leakage, treatment fairness, claims); their 23 accepted changes are folded in here and the review is kept beside this file (`protocol-review.json`). Anything decided after this version is labelled as such in the report.

## Question

Does Fabius 3.3.0 change the measured performance of a Claude model on established public benchmarks, compared with the same model, the same harness and the same tasks without it? And does the README's documented invocation actually load Fabius?

## What is held constant, and pinned

- **Harness:** Claude Code 2.1.289, the native macOS binary (its SHA-256 is recorded), headless `claude -p`, `--output-format stream-json --verbose`.
- **Clean context, every arm:** `--setting-sources project` (no user settings, enabled plugins, hooks or user skills), `--strict-mcp-config` (no MCP servers), a fresh working directory per run under `/private/tmp` (no CLAUDE.md, no project memory), `--no-session-persistence`. No global CLAUDE.md or AGENTS.md exists on the machine. Before each run the harness asserts that no auto-memory directory exists for that working directory, and after it records whether one was created and deletes it.
- **Identical file-access limits, every arm:** `--disallowedTools 'Read(//Users/**)' 'Edit(//Users/**)' 'Write(//Users/**)' 'Read(//private/var/folders/**)'`, so no run can read the benchmark data, other runs, or the owner's files. Every stream is audited afterwards (`audit_paths.py`): tool inputs outside the run's directory and the plugin directory, and commands that look for answers, are flagged per arm; the primary endpoints are reported with and without flagged items.
- **Model:** `claude-sonnet-5-5`, checked in every run's init record. Default effort. Claude Code exposes no temperature; one sample per item per arm unless the replicate rule below adds a second.
- **Plugin under test:** the exact tree of the signed tag `v3.3.0-sealed` (`git archive`, 322 files), placed at `/private/tmp/fbplugin/fabius`. Its 18 sealed files match the seal manifest (Merkle root `e1958cb5f9e8f36cef0e3f61a7b71b152281cbd0f7c14ae7a6ce370a68c1309d`), and a SHA-256 list of all 322 files (`aee07adb…` for the list) is re-checked at the start and end of every benchmark.
- **Benchmark inputs:** pinned by content — the SWE-bench rows as a local JSON file (SHA-256 recorded) and every image by its registry digest; the IFEval code at a commit; the HumanEval+ dataset version and hash.

## Arms

| Arm | Plugin | Prompt | Reported as |
|---|---|---|---|
| `baseline` | none | the task, verbatim | baseline |
| `fabius-doc` | Fabius 3.3.0 | `fabius: ` + the task, the README's documented invocation | "skill listing present, router loaded in k/N runs" — never as "Fabius" |
| `fabius-loaded` | Fabius 3.3.0 | `/fabius ` + the task, the slash command that puts the router contract in context | "fabius-router (/fabius)" |

Pilot finding recorded before any scored run: on Sonnet 5.5, `fabius: ` + task made zero Skill calls on a coding task and on a real SWE-bench issue (the first-turn context grew only by the 15 skill descriptions, about 1.9k tokens), while `/fabius` + task added the router contract (about 3.8k tokens more). So both treatments are measured.

**How loading is measured.** The stream records no message for a slash expansion, so loading is inferred from the first turn's prompt size: `router_injected` is true when the first assistant turn's prompt tokens (input + cache creation + cache read) exceed the same item's baseline run by at least 4,500 tokens. Skill tool calls are counted per Fabius skill. A specialist is credited with an effect only if it loaded in more than half of that arm's runs. Effects are attributed to "the shipped package plus its invocation", never to individual rules: there is no context-length placebo arm.

## Benchmarks

### 1 · SWE-bench Verified Mini, 50 tasks (primary)

- **Tasks:** `MariusHobbhahn/swe-bench-verified-mini`, all 50 instances (25 Django, 25 Sphinx), published by its author as matched to SWE-bench Verified's difficulty and per-model pass-rate distribution (not re-verified here). Each task's base commit, gold patch, test patch, FAIL_TO_PASS and PASS_TO_PASS were checked identical to the official `SWE-bench/SWE-bench_Verified` row.
- **Environment:** the official prebuilt images `swebench/sweb.eval.x86_64.<instance>`, used by digest, for the agent's environment and for scoring.
- **Workspace, one per run (retries included):** `/testbed` is streamed as a tar archive out of a fresh, network-less container of the pinned image into `/private/tmp/fbw/<random>/repo`, a path that names no instance. Every tag and every ref except the current branch is deleted, reflogs are expired and the object store is pruned; the harness then asserts that HEAD is the base commit or the image's own child commit of it (the official images add one commit, "SWE-bench", holding their environment setup: file modes everywhere, and for Sphinx the official spec's `tox.ini` and `setup.py` edits — asserted by comparing every blob hash, with content changes allowed only in `tox.ini`, `setup.py`, `setup.cfg` and `pyproject.toml`, and recorded per run), `git rev-list --all` equals `git rev-list HEAD`, `git fsck --unreachable --no-reflogs` is empty and `git status --porcelain` is empty (on a case-sensitive volume if needed). An instance failing any assertion is excluded from every arm. Past history stays, as in the official image; no later commit is reachable.
- **Container, one per run:** `docker run -d --rm --network none --memory 3g -v <workspace>:/testbed <image@digest> sleep infinity`. All Bash goes through one wrapper that runs the command inside this container (`Bash(<wrapper>:*)` is the only Bash permission); git, ls and test runs happen there. Other tools: Read, Edit, Write, Glob, Grep, TodoWrite, Skill. No web tools, no subagents. Limits: 150 turns, 40 minutes wall clock. The container is killed before the patch is taken.
- **Prompt, identical in every arm apart from the prefix:** the issue's `problem_statement`, verbatim (the `hints_text` field is never shown), then one paragraph that names the repository path and the wrapper, asks to resolve the issue by changing non-test source files, and says: *"This run is non-interactive: nobody can answer questions or grant permissions; state any assumption and finish the task."* The rendered prompts are stored and asserted byte-identical across arms apart from the prefix and the run's random workspace path.
- **Scored patch:** after the kill, `git add -A` and `git diff --cached --binary HEAD` — the workspace HEAD, which is the state the official harness applies the patch to — excluding `.claude`, `tests`, `testing`, `**/test_*.py`, `**/*_tests.py`, `**/conftest.py` (no gold-patch file matches these and every test-patch file does). The unfiltered patch through the same harness is a declared secondary.
- **Scoring:** the official harness, `swebench==5.0.2` `run_evaluation`, dataset = the pinned local rows file, official eval scripts and log parsers. Resolved rate = resolved / all valid instances, the same denominator for every arm. Empty, apply-failed, timed-out and turn-capped patches count as unresolved and are reported per arm. A harness error not caused by the patch (Docker, out of memory) is re-scored up to twice with one worker, then reported.
- **Validity, before any agent run, through the full production pipeline:** (a) the gold patch applied to a prepared workspace, extracted by the same code and scored, must resolve; (b) an untouched workspace, after one wrapper command, must give an empty patch that does not resolve. Instances failing either are excluded from every arm and reported.
- **Arms on SWE-bench:** `baseline` and `fabius-loaded` on every valid instance. `fabius-doc` on a fixed stratified 10: a seeded permutation (numpy `default_rng(20261006)`) of the sorted Django IDs and of the sorted Sphinx IDs, first 5 valid of each — written into this file after the validity check and before any scored SWE-bench run. That subset is descriptive (load rate, resolved count), outside the test families. **Fixed 2026-10-07 after the validity check (all 50 valid), before any SWE-bench run:** `django__django-12276`, `django__django-11815`, `django__django-12155`, `django__django-12308`, `django__django-12774`, `sphinx-doc__sphinx-10466`, `sphinx-doc__sphinx-9698`, `sphinx-doc__sphinx-10673`, `sphinx-doc__sphinx-8035`, `sphinx-doc__sphinx-7985`.
- **Replicate rule:** `baseline` and `fabius-loaded` get a second sample per instance (k = 2) only if the usage meter allows it (see Budget). That decision is logged before any SWE-bench result is scored.

### 2 · IFEval, 541 prompts

- **Tasks:** `google-research/instruction_following_eval` at commit `e6890f85757dd84e27ca6df2dd30651dafad28e0`.
- **Generation:** the prompt verbatim; tools limited to `Skill` (so the Fabius arms can load specialists); 8 turns; 300 s. The scored response is the final result text, or the last assistant text block if there is none.
- **Scoring:** the official `evaluation_main`, unchanged, called through a three-line wrapper that sets `langdetect.DetectorFactory.seed = 0` first (a documented deviation that makes language detection deterministic). All arms are scored in one process.
- **Declared sensitivities:** excluding the `combination:repeat_prompt` instructions (the `fabius: ` prefix changes the request text being repeated); scoring all assistant text blocks concatenated instead of the final one.
- **Canary (not scored):** three `/fabius` runs with a multi-line IFEval prompt, session persistence on in a scratch directory, to check that the expanded request contains the prompt byte for byte.

### 3 · HumanEval+, 164 problems

- **Tasks:** EvalPlus HumanEval+ v0.1.10 (dataset hash `fe585eb4df8c88d844eeb463ea4d0302`).
- **Generation:** EvalPlus's own chat instruction ("Please provide a self-contained Python script that solves the following problem in a markdown code block:" + the problem in a code block); tools limited to `Skill`; 8 turns; 300 s.
- **Scoring:** `evalplus.sanitize` then `evalplus.evaluate` (EvalPlus 0.3.1) inside a Linux container (`python:3.11-slim`, no network), all arms in one session after generation, with no other containers running, evaluated twice; items that flip are reported. EvalPlus cannot apply its sandbox limits on macOS, which is why scoring runs in Linux.
- **Validity:** the canonical solutions must pass in the same session. **HumanEval/32 is excluded from every arm:** its canonical solution fails EvalPlus 0.3.1's own sandboxed check in this container before any input is evaluated (verified 2026-10-06; the same solution satisfies the task's oracle on all 888 inputs when called directly), so 163 problems are scored.
- **Secondary:** non-blank lines of the sanitized solution.

## Schedule

Items are run in a seeded random order (numpy `default_rng(20261006)`); SWE-bench alternates Django and Sphinx. All arms of an item run back to back, in an order drawn from the same generator and written to `schedule.json` before the first run, so a budget stop removes whole items, never single arms. Concurrency is fixed: 6 workers for IFEval and HumanEval+, 2 for SWE-bench.

## Runs, failures, and integrity

- Every attempt is kept in its own directory (`attempt-<n>/`: command, full event stream, stderr) and never overwritten; the item summary names the scored attempt.
- **Outcome or infrastructure, decided from the stream and stderr before any scoring:** an attempt is INFRA if there is no result record; the result carries an API error status; the result subtype is anything other than `success` or `error_max_turns`; it is an error whose text names a usage limit, a rate limit, an overload or an API error; the last usage event says `rejected`; the init model is not `claude-sonnet-5-5`; or the init skills do not match the arm (exactly 15 `fabius:*` skills in the Fabius arms, none in baseline). Everything else is an OUTCOME and is never rerun, including turn-cap hits and timeouts; their scored text is the last assistant text, and on SWE-bench the workspace as it stood when the run was killed.
- INFRA attempts are retried up to twice with the same inputs; a SWE-bench retry starts from a fresh workspace and container. A usage-limit INFRA pauses the whole pool until the reset time without using a retry. An item still missing after retries is dropped from every arm. Turn-cap hits, timeouts and runs that ended on a question are reported per arm.
- No prompt, check, scorer or exclusion rule changes after the first scored run of a benchmark. A necessary change becomes a new protocol version with a diff, keeps the original, and applies to every arm.

## Endpoints, tests, and verdicts

- **Primary endpoints:** SWE-bench resolved rate; IFEval prompt-level strict accuracy; HumanEval+ plus pass@1.
- **Families:** Family 1 = `fabius-loaded` vs `baseline` on the three benchmarks (Holm over 3). Family 2 = `fabius-doc` vs `baseline` on IFEval and HumanEval+ (Holm over 2). The `fabius-doc` SWE-bench subset is descriptive only.
- **Tests:** k = 1 — the exact two-sided binomial test on the discordant counts (McNemar's exact test). k ≥ 2 — the paired sign-flip test on d_i = mean over replicates (Fabius_i) − mean (baseline_i), statistic |Σ d_i|, exact enumeration when at most 20 d_i are nonzero, otherwise 100,000 seeded Monte Carlo flips with p = (1 + count)/(1 + N).
- **Intervals:** k = 1 binary — Newcombe's hybrid-score interval for paired proportions (method 10), at 95% and at 90%. k ≥ 2 and continuous measures — a BCa item bootstrap, 10,000 resamples, seed 20261006, stratified by repository on SWE-bench and resampled by prompt on IFEval (instruction-level too). Intervals are labelled "unadjusted 95%".
- **Verdicts, one per comparison, from the Holm-adjusted p alone:**
  - **GAIN / LOSS** — adjusted p ≤ 0.05, by the sign of the difference.
  - **TIE** — IFEval and HumanEval+ only: the 90% interval lies inside ±5 points.
  - **NON-INFERIOR** — IFEval and HumanEval+ only: not a GAIN, and the 95% interval's lower bound is above −5 points.
  - **INCONCLUSIVE** — everything else, printed as "no detectable difference at this sample size (95% CI a to b; MDE ≈ X points)".
  - SWE-bench (n ≤ 50) can only come out GAIN, LOSS or INCONCLUSIVE.
- **Power, stated up front:** a table from `analyze.py` gives the minimum detectable effect at 80% power under the exact McNemar test for each benchmark's n, at α = 0.05/3 and α = 0.05, for discordance 0.1, 0.2 and 0.3; for SWE-bench at n = 50 it is roughly 17–20 points. The report recomputes it from the observed discordance with the same code, and with k = 2 also reports the baseline's own replicate-to-replicate disagreement.
- **Efficiency (descriptive, no p-values):** per item, r_i = log((Fabius_i + 1)/(baseline_i + 1)) for output tokens, total tokens, the cost Claude Code reports, wall time and turns; reported as exp(mean r_i) with a BCa 95% interval, and on SWE-bench also within the items both arms resolved. Router-load rate and per-skill load rates get Wilson intervals.

## Permitted wording (fixed now)

Every public sentence about these results carries the scope: *Fabius 3.3.0 (sealed root e1958cb5…), claude-sonnet-5-5, Claude Code 2.1.289 headless, <arm and invocation>, k = <k>, n = <n>, <dates>*. All Family 1 results appear in one table at equal weight, and a headline names every benchmark ("gained on X, no detectable difference on Y, lost on Z"). "Tie", "matches", "quality held" and "no regression" are used only with a TIE or NON-INFERIOR verdict. "Less waste" is used only with a GAIN, TIE or NON-INFERIOR verdict and a total-token or cost interval entirely below 1. An efficiency number appears only in the same sentence as that benchmark's verdict. Absolute rates are specific to this harness (Claude Code's system prompt, no temperature control, wrapper-only Bash, no network, 150 turns / 40 minutes) and are never compared with leaderboard or model-card numbers.

## Budget

The account's weekly usage meter stood at 55% before this study (5-hour meter 35%). The study stops when the weekly meter reaches 75%, leaving at least 25 points for the owner's other work until the reset. A new run starts only while the 5-hour meter is below 60%; otherwise the pool pauses until it resets. Meters are read from every run's last usage event; every scale-down is decided from meter readings alone and logged in `budget-log.md` before the block it affects. No benchmark is scored until its generation has finished and every budget decision is logged.

Order (1.2): canaries (not scored) → HumanEval+, 3 arms → SWE-bench replicate 1 → IFEval, 3 arms (gate: if the projected cost of all three arms exceeds 5 meter points, drop `fabius-doc`; if two arms still exceed 5 points, run a seeded prefix of at least 271 prompts) ; the first two SWE-bench items calibrate the per-run cost, whole items only, stopping at the cap → SWE-bench replicate 2 for `baseline` and `fabius-loaded`, only if the projection fits. Cuts, in order: replicate 2, then `fabius-doc` on IFEval, then the IFEval item count, then SWE-bench items. `fabius-loaded` vs `baseline` on HumanEval+ is never cut.

## Receipts

Per benchmark: `items.csv` (item, arm, replicate, scored attempt, outcome class, pass/fail, router_injected, skill calls, all token fields, cost, wall time, turns, exclusion reason); the generation records; the scorer inputs and outputs (SWE-bench predictions and run_evaluation reports with per-instance logs; IFEval response data and evaluation output; EvalPlus samples, sanitized samples and eval results); the pin records; the meter readings before and after each block; the path audit; and `analyze.py`, which reads only `items.csv` and prints every published number. This protocol and the harness are committed to the Fabius repository before the first scored run, and the report cites that commit.

## Changes in 1.2 (before any SWE-bench run)

1. **Patch reference.** Version 1.1 said the patch is taken against the base commit. Building the validity check showed that the official images (rebuilt 2026-08) place one extra commit, "SWE-bench", on top of the base commit; it changes the modes of every file and no content (all 6,130 blob hashes identical on the first instance checked). A diff against the base commit therefore carried thousands of mode lines into every patch, while the official harness applies patches to the image's HEAD. The patch is now taken against the workspace HEAD, and the workspace assertion accepts HEAD = base or HEAD = the base's mode-only child. No run had been made under the old rule.
2. **Prompt identity.** Each run has its own random workspace path (no state can carry between runs through a shared path), so the prompt identity check normalises that path.
3. **Order.** SWE-bench replicate 1 runs before IFEval. The 5-hour usage window, not the weekly meter, turned out to bind; the owner chose to continue automatically with the main benchmark first. This is a scheduling decision made before any result; cuts still follow the order above.

## Changes in 1.3 (before any SWE-bench run)

1. **Environment files in the image's setup commit.** The Sphinx images' "SWE-bench" commit also changes content: `tox.ini` (`pytest -rA`, so the official log parser can read the results) and, for older versions, `setup.py` dependency pins (`Jinja2<3.0` and similar). These are the official environment the harness evaluates against, not the issue's fix; no gold patch in the 50 touches these files. The assertion now allows content changes only in `tox.ini`, `setup.py`, `setup.cfg` and `pyproject.toml`, and records them per run.
2. **Workspace copy.** `docker cp` failed intermittently on macOS (`chtimes … no such file or directory`); the workspace is now streamed out of a network-less container as a tar archive, with up to three attempts.
3. **Machine sleep.** The Mac slept overnight, which froze the paused HumanEval+ runner past its 22:30 resume; it was restarted (no item was partial; completed items were kept) and `caffeinate` keeps the machine awake for the rest of the study. Logged in `budget-log.md`.
