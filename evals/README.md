# Repository checks

This directory holds the current structural and evidence checks, plus the fixtures they replay. The dated public-benchmark studies live in the [historical archive](../docs/archive/README.md).

## Run the current checks

Run commands from the repository root. These checks require no model-provider calls.

```bash
bash scripts/verify-all.sh --mode=dev
```

The aggregate gate runs structural, helper, runtime, security, evidence, distribution and release checks. It prints current totals; a green result verifies those tested boundaries, not automatic skill activation in every agent app.

| Check | What it verifies |
|---|---|
| `node evals/structural.mjs` | Exactly fifteen declared contracts; discovery, ownership, frontmatter budgets, references and the content-bound seal. |
| `node evals/verify-maintenance-smoke.mjs --mode=release` | Retained maintenance cases and whether their input hashes still match the current rules. |
| `node evals/verify-receipts.mjs` | Arithmetic and declared limitations of retained historical score receipts. |
| `node --test evals/text-eval.test.mjs` | Preparation, validation and replay of text-evaluation evidence using local fixtures. |
| `node evals/suite/validate.mjs` | Integrity of the versioned evaluation task fixtures. |

Runtime and helper tests remain beside their implementations in [`runtime/`](../runtime/) and [`skills/`](../skills/). Packaging and provenance checks live in [`scripts/`](../scripts/) and [`provenance/`](../provenance/).

## Retained experimental material

The [archive index](../docs/archive/README.md) separates the dated studies from current checks. Older `results.*.json` files remain here because the receipt verifier and figure sources read them directly. They retain their original dates and limitations; missing candidate answers or execution logs are not reconstructed.

The older `harness.*.workflow.js`, `eval.mjs` and `portable_eval.py` files are experiment adapters. The aggregate gate uses only offline self-tests. Provider-backed runs are separate experiments with their own cost and credentials; they are not required to install or use Fabius.

For the maintained text-evaluation adapter and fixture/replay commands, see [`suite/README.md`](suite/README.md). New experiments must use new output paths and preserve answers, hashes and execution evidence. Never overwrite a dated receipt.
