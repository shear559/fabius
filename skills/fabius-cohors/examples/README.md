# Original Fabius Cohors examples

[roles.json](roles.json) contains six reusable role definitions. [sales-plan.json](sales-plan.json) embeds two of them in a five-task dependency graph: three line totals, an aggregate, then a review.

Run the deterministic adapter from the repository root:

```sh
node skills/fabius-cohors/examples/demo.mjs
```

The result must contain amounts 120, 90, 70 and 280, followed by an `accept` review. Currency is unspecified. The adapter calls no model, shell or remote service and writes no output files. It demonstrates the caller-owned execution seam and checked dependency handoffs; it does not measure an agent's quality.

For another workload, define the task output first, supply a scoped host runner and use an authorization function that reflects the caller's existing authority. See [the scheduler contract](../references/catalogue/scheduler.md).
