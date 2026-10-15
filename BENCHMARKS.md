<!-- fabius-release: 3.5.1 -->
# Checks and historical evaluations

Fabius is a coordinated set of agent skills. Start with the [capabilities and router](README.md), or [install it](QUICKSTART.md). Benchmark history is retained separately from the product introduction.

## Current repository checks

Run the offline development gate from the repository root:

```bash
bash scripts/verify-all.sh --mode=dev
```

It checks the declared fifteen-skill surface, references, helper and runtime behavior, security boundaries, package contents, release integrity and retained evidence. It does not call model providers or establish universal gains in model quality. The [check index](evals/README.md) explains the smaller commands.

## Historical evaluations

The [archive](docs/archive/README.md) keeps the dated protocols, results, limitations and experiment code. The [historical overview](docs/archive/benchmark-history.md) includes the older panels and their retained receipts.

The October studies did not establish a benchmark gain after multiple-comparison correction and incurred additional model cost. Those results remain available with their scope and activation limitations; they are not claims about a new release.

- [Public-benchmark study](docs/archive/2026-10-public-benchmarks/REPORT.md)
- [Reference-fold study](docs/archive/2026-10-source-fold-benchmarks/REPORT.md)
- [Claims and evidence boundaries](CLAIMS.md)

Historical score receipts needed by the integrity checks remain in `evals/`. Archiving the studies changes navigation and ownership, not the recorded results.
