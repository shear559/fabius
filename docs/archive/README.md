# Historical evaluations

This archive preserves earlier Fabius experiments, their limitations and the code used to run them. Start with the [product overview](../../README.md) for current capabilities and the router, or the [check index](../../evals/README.md) for current repository verification.

## Study index

| Record | Scope |
|---|---|
| [Historical benchmark overview](benchmark-history.md) | June–October 2026 results, panel definitions, retained receipts and evidence gaps. |
| [Public benchmarks, October 2026](2026-10-public-benchmarks/REPORT.md) | Fabius 3.3.0, one specified model and host; router and explicitly invoked specialist comparisons. |
| [Reference-fold continuation](2026-10-source-fold-benchmarks/REPORT.md) | Comparison of the frozen 3.3.0 package and source-fold candidate `6fb0ab0`, including observed reference-file loading. |

The October studies did not establish gains after multiple-comparison correction. Preserve that conclusion alongside their cost and activation findings. Historical scores do not certify current-release performance or automatic skill selection across hosts.

The full retained run archives are attached to [release v3.4.0-sealed](https://github.com/shear559/fabius/releases/tag/v3.4.0-sealed). No new model experiment was run for this reorganization.

## Historical paths

The following directories moved as complete, byte-identical trees on 2026-10-15. Internal receipt strings and previously published paper captions retain the paths used at the time of the experiments.

| Original path | Current path |
|---|---|
| `evals/public/2026-10-public-benchmarks/` | [`2026-10-public-benchmarks/`](2026-10-public-benchmarks/) |
| `evals/public/2026-10-source-fold-benchmarks/` | [`2026-10-source-fold-benchmarks/`](2026-10-source-fold-benchmarks/) |

Their relative depth and sibling relationship are preserved for the historical harnesses. Run a harness only as a deliberately scoped new experiment; its old provider or environment assumptions may no longer hold.

## What remains active

Structural, security, runtime, helper, packaging and release checks remain in their existing locations. Historical score files required by deterministic receipt replay also remain under `evals/`. The archive is still tracked and included in the distribution; this move simplifies the active tree and reading path, not package size.
