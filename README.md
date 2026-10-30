<div align="center">
<img src="assets/fabius-contour.webp" alt="Fabius" width="100%" />
</div>

# Fabius

**Scout wide. Strike narrow.**

Fabius is a model-agnostic working method for AI agents, created by **Ariel Shemesh**. It coordinates fifteen skills so that research, engineering, design, memory and verification have clear responsibilities within the same task.

Your agent application loads the instructions, supplies the tools and enforces permissions. Fabius provides the working contracts; it does not replace the host or guarantee identical behavior across models.

[Quickstart](QUICKSTART.md) · [Architecture](ARCHITECTURE.md) · [Examples](examples/README.md) · [Website](https://fabius-landing.vercel.app)

## What it does

- Routes a task to the relevant specialist contracts.
- Gives each concern a defined owner instead of duplicating instructions.
- Uses project records and source evidence when available.
- Keeps implementation focused on the requested outcome.
- Requires verification and explicit reporting of missing capabilities.

A small task should remain small. A broader task can combine several specialists without giving every specialist the same job.

## Fifteen skills, coordinated

The **router** selects responsibilities and execution depth. **Parcus**, the lean core, keeps the work focused while preserving essential checks.

| Specialist | Responsibility |
| --- | --- |
| Disciplina | Engineering, architecture, debugging and verification |
| Decor | Interfaces, design systems and visual communication |
| Cohors | Agent design, tool contracts and orchestration |
| Archivum | Project records, retrieval and continuity |
| Mercatus | Positioning, copy, launch flows and SEO |
| Praesidium | Defensive security and evidence-based audits |
| Ludus | Game behavior, state machines and interaction |
| Catena | On-chain development and provenance |
| Machina | Deterministic automation and integrations |
| Scientia | Research methods and reproducible analysis |
| Doctrina | Model training, serving and evaluation |
| Fortuna | Sourced market research and risk analysis |
| Concilium | Independent model opinions, review and synthesis |

<img src="assets/readme/fabius-system.svg" alt="The Fabius router coordinates thirteen specialists above the lean core." width="100%" />

Contracts and their references live in [skills/](skills/). Automatic discovery and activation vary by application; inspect what loaded rather than assuming every specialist ran.

## Install in your agent app

The commands below are the packaged setup routes documented in [QUICKSTART.md](QUICKSTART.md). See [COMPATIBILITY.md](COMPATIBILITY.md) for the scope of recorded host checks.

### Claude Code

```text
/plugin marketplace add shear559/fabius
/plugin install fabius@fabius
/reload-plugins
```

Start a request with `/fabius` to invoke the router.

### Codex

```sh
codex plugin marketplace add shear559/fabius
codex plugin add fabius@fabius
codex plugin list --marketplace fabius
```

Restart the application or session as directed by the host.

### Grok Build

```sh
grok plugin install shear559/fabius --trust
grok plugin enable fabius
```

Review a plugin's contents and permissions before trusting it.

### Other instruction-reading hosts

[AGENTS.md](AGENTS.md) is the portable core. Where separately authorized under [LICENSE](LICENSE), load it through the host's supported instruction mechanism. The full method also needs the router, Parcus and the relevant specialist contracts and references.

The portable core alone does not install the specialist library, enable tools or create persistent memory.

## Try a bounded task

```text
Use Fabius to improve this signup page. Preserve the existing brand,
clarify the message, fix the mobile form and verify it in a browser.
Explain which specialists the task needs before editing.
```

Mercatus can own the message, Decor the interface and Disciplina the implementation checks. Archivum can supply project context when an authorized record exists. The final result should distinguish completed checks from checks the host could not perform.

[Prepared examples](examples/README.md) include inputs, outputs and verification steps; they are demonstrations, not comparative benchmark results.

## Optional local runner

The repository also contains a Node.js runner:

```sh
node runtime/fabius.mjs help
node runtime/fabius.mjs doctor
```

Use Node.js 22 or newer and follow [runtime/README.md](runtime/README.md) for provider configuration and commands. The runner can use local tools and external providers; it is not an operating-system sandbox. A successful doctor check is not cryptographic provenance verification.

## Evidence and maintenance

[CHECKS.md](CHECKS.md) explains verification. [CLAIMS.md](CLAIMS.md) separates supported claims from broader ambitions. [PROVENANCE.md](PROVENANCE.md) describes the signed content boundary and its verification procedure. Research and paper artifacts are indexed in [RESEARCH.md](RESEARCH.md) and [paper/README.md](paper/README.md).

For changes and issue reports, follow [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## License

Fabius is publicly readable proprietary work. [LICENSE](LICENSE) provides a narrow personal, non-commercial agent-plugin installation grant; other reuse, modification, distribution or commercial/client use requires the applicable written permission. Third-party material retains its own terms and attribution.
