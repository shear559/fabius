# Source-fold benchmark continuation

An isolated continuation comparing no Fabius, the old signed package and source candidate `6fb0ab0`. [The protocol](PROTOCOL.md) covers eleven public benchmarks and preserves the earlier study unchanged.

Status: preparation; no model generations or results yet. Provider execution is disabled pending a new quota authorization, a bounded loading/access canary and per-benchmark scorer readiness. Historical usage-limit exceptions do not authorize this cohort.

The new references need readable files to enter the model context. This is a declared tool-access variant with the same capabilities in all three arms. It measures packages under these conditions, not an automatic claim of improved or unique behavior across all models.

Execution paths, copied data, filtered package snapshots and raw receipts belong in an explicit private experiment root. No code in this directory may default to writing the original study. Machine-specific configuration and identity-bearing transcripts are not public artifacts.

## Frozen inputs and verification

[`INPUTS.json`](INPUTS.json) records both filtered package inventories, scorer/input file hashes, fixed image identities, exclusions and the private manifest digest. [`schedule.jsonl`](schedule.jsonl) fixes all 2,167 item/sample blocks and 6,501 scheduled invocations. These counts describe the plan, not completed calls.

[`VALIDATION.json`](VALIDATION.json) records offline control checks. Synthetic CLI tests are not model evaluations. The real scorer controls use known correct or incorrect answers solely to verify scoring infrastructure; they are not participant results.

Python 3.11 with the existing NumPy/SciPy environment runs the offline harness suite:

```sh
python -B -m unittest discover -s evals/public/2026-10-source-fold-benchmarks -p 'test_*.py'
```

## Private execution

Build the private manifest with `items.py --data-root ... --legacy-public-root ... --out ...`. Supply an explicit private JSON configuration with `runtime`, `scoring`, `manifest`, `authorization` and `judge_acceptance` fields. `RuntimeConfig` defines required paths, model, limits, authorization flags and old/candidate package sources. Scoring additionally requires every copied file hash, fixed Docker image IDs, interpreter paths and existing certificate/tokenizer resources. None is installed automatically.

Before model use, resolve the pending quota choice and freeze the protocol, harness, configuration and input manifest at a committed revision. The private `freeze` record contains `commit`, `input_manifest_sha256`, `configuration_sha256` and `files` (each file in this directory with a Python, Markdown, JSON or JSONL extension). Configuration hashing uses `runtime.binding()` and excludes the freeze record itself; only explicit authorization booleans are exempt from runtime identity. Changing frozen bytes requires a new registration, not relabelling existing outputs.

The controller takes `--config /absolute/private/config.json` plus one command:

| Command | Effect |
|---|---|
| `preflight` | Verify frozen source bytes and actual local scoring prerequisites; no provider call |
| `status` | Read counts and the last observed quota; no provider call |
| `probe` | One explicitly authorized, non-scored, no-tools quota probe |
| `canary` | Bound three-arm read/reference/denial check |
| `canary-swe` | Separate real repository editing/execution/denial check |
| `run --benchmark NAME --max-blocks 1` | Resume one complete three-arm block in the frozen order, subject to quota and readiness |
| `close --benchmark NAME` | Close generation only after every condition terminates or exhausts its infrastructure retries |
| `score --benchmark NAME` | Score closed, receipt-verified outputs; resume completed scoring batches without rerunning them |
| `analyze` | Keep all 33 planned contrasts, missing observations and descriptive execution cost |

Run long authorized batches under the operating system's sleep inhibitor. The controller never spins waiting for quota and never launches another account/model/key. An absent or stale usage meter pauses it. Refresh after the one-call probe has been used still requires a separately authorized, documented meter observation; this preparation does not implement unattended quota resets.

LongMemEval remains blocked until the official judge is available, its settings are frozen and gold/wrong controls pass. The current harness prepares official judge prompts only. Both live CLI canaries also remain unexecuted while provider authorization is pending. Do not mark the study complete or use it as a performance claim at this stage.
