# Fabius Cohors — original role catalogue

Start with the job's acceptance condition, then choose one of six [original role contracts](catalogue/README.md). Each definition includes instructions, a tool allowlist, declared permissions and a closed output shape. The machine-readable definitions live in [roles.json](../examples/roles.json); they are inputs to Fabius's validator, not a claim that every host accepts the same fields.

| Role | Use it for | Return contract |
|---|---|---|
| `researcher` | Trace claims to supplied or authorized sources | Claims with source locations; gaps |
| `builder` | Implement one assigned artifact | Changed paths; observed checks; limitations |
| `reviewer` | Find supported acceptance failures | Accept/revise; located findings; limitations |
| `analyst` | Compute from supplied values | Amount; arithmetic evidence |
| `editor` | Turn approved facts into usable copy | Draft; checks; open questions |
| `coordinator` | Integrate successful task results | Summary; evidence; remaining steps |

A role is a division of work, not a substitute for domain expertise. Add the relevant Fabius specialist instructions when the task needs them. Do not distribute a project into six agents merely because six definitions exist.

For a fixed dependency graph, [the original scheduler](catalogue/scheduler.md) supplies validation, bounded concurrency, checked dependency outputs and cooperative cancellation. Its CLI checks or displays a plan; actual execution requires caller-owned authorization and runner functions. A [deterministic sales demo](../examples/demo.mjs) shows the interface without model calls.

The earlier distribution carried Agency Agents personas, Google ADK samples and Ruflo agent definitions, plus an unregistered OpenCode adaptation note. Those copied trees have been retired from this layer. The useful ideas retained here are role clarity, typed handoffs and dependency-aware coordination; the new implementation is authored for Fabius. This is not a reimplementation of those frameworks, their integrations or their six SDK language packs. Source history and the [migration note](catalogue/README.md#historical-inspiration) retain attribution.
