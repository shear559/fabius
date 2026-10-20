<!-- fabius-release: 3.5.1 -->
# Verify the working system

Fabius is a skill system by **Ariel Shemesh**. Explore the [interactive demonstrations](https://fabius-landing.vercel.app/#trials), [install the plugin](QUICKSTART.md), or inspect its [architecture](ARCHITECTURE.md).

## Repository checks

```bash
bash scripts/verify-all.sh --mode=dev
```

This offline gate checks skill discovery, references, local helpers, runtime behavior, package contents and release provenance. [The check index](evals/README.md) lists focused commands. No model-provider calls are required.

## Demonstrations

The four working examples cover mathematical visualization, agent-team coordination, project memory and readable code. They include controls, source downloads and checks of their local behavior. They illustrate workflows; they do not measure a model-quality gain.

The current presentation contains no model rankings, comparison scores or performance claims. Earlier experiments were removed from the current tree on 20 October 2026; previous commits remain in Git history. Installation and task behavior depend on the model, host, available tools and permissions.
