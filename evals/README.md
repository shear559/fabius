# Repository checks

These checks support maintenance of the working skill system. They do not publish comparative model scores.

Run from the repository root without model-provider calls:

```bash
bash scripts/verify-all.sh --mode=dev
```

| Check | Scope |
|---|---|
| `node evals/structural.mjs` | Fifteen declared skills, discovery, ownership, frontmatter, references and seals. |
| `node evals/verify-maintenance-smoke.mjs --mode=release` | Maintenance-case input identity and freshness. |
| `node --test evals/text-eval.test.mjs` | Input preparation, validation and replay using synthetic fixtures. |
| `node evals/suite/validate.mjs` | Integrity of the developer task fixtures. |
| `python3 examples/verify.py` | The prepared starter examples. |

Helper tests live beside their implementations in `skills/`; runtime tests are in `runtime/test/`. Packaging and provenance checks are in `scripts/` and `provenance/`.

The [text-evaluation tools](suite/README.md) remain available for new, explicitly scoped developer experiments. Offline self-tests validate those tools; they are not evidence that a model improves. New provider-backed experiments require their own credentials, budget and retained inputs and outputs.
