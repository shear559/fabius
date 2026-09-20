<!-- © 2026 shear559 · fabius · provenance fab1-6bbf82d118bce2cee9d7ac71f034fa26 · release evidence: PROVENANCE.md · github.com/shear559/fabius -->
# Fabius Corpus — the indexed body

One index over the Fabius procedures and helpers owned by the fifteen public skills. The router holds this small map, resolves one owner, reads that owner's entry page, and pages in only the matching slice (routing-policy **M9 · R9 · M7**). Retrieval is symbolic by default (`rg`, catalog links, and exact paths); an owner may opt into a tested vector index when corpus size and semantic queries justify it. There is no universal runnable `fabius-vec` dependency. Research inputs and inspirations are recorded in [credits/](credits/README.md).

---

## The libraries — all under one fabius index

| Library | Owner skill | Holds | Index (read first) | Status |
|---|---|---|---|---|
| **fabius-agents** | `fabius-cohors` | original agent roles, output contracts and dependency scheduling, the confirmation classes for agents that act through a screen or channel, the standing-job shape and the live-voice split | [`skills/fabius-cohors/references/agent-catalog.md`](skills/fabius-cohors/references/agent-catalog.md) | Fabius procedures |
| **fabius-design** | `fabius-decor` | semantic tokens, the visual-system template (captured before, written at finish), original layout recipes, deterministic scenes, RTL/BiDi and critique procedures, generated video and the paid media request (*Fabius Pictor* — source modes, preflight, cost before run, custody, lineage) | [`skills/fabius-decor/references/design-system.md`](skills/fabius-decor/references/design-system.md) | Fabius procedures |
| **fabius-knowledge** | `fabius-archivum` | LLM-wiki pattern, memory schema, the multi-project record contract (read-first gate · staleness cross-check · sync-back · two-writer rules), cross-session auto-recall, meeting capture, video ingest, source-grounded notebook connector, capture integrity and anchored meeting records, citation gates, book-length source distillation (*Fabius Epitomator*), and selected-file lexical retrieval | [`skills/fabius-archivum/references/memory-schema.md`](skills/fabius-archivum/references/memory-schema.md) | original rules and runnable local retrieval |
| **fabius-figura** | `fabius-decor` | chart-selection, data-ink, palette, SVG, and diagram guidance | [`skills/fabius-decor/references/visualization.md`](skills/fabius-decor/references/visualization.md) | entry guidance; no promised full component library |
| **fabius-disciplina** | `fabius-disciplina` | impact-mapped testing, systematic debugging, planning, and verification | [`skills/fabius-disciplina/references/process-playbook.md`](skills/fabius-disciplina/references/process-playbook.md) | Fabius procedures |
| **fabius-mercatus** | `fabius-mercatus` | channel playbooks, swipe references, and launch frames, the prose tell lint (*Fabius Emendator*) and the existing-site SEO audit method (*Fabius Explorator*) | [`skills/fabius-mercatus/references/marketing-playbook.md`](skills/fabius-mercatus/references/marketing-playbook.md) | Fabius procedures |
| **fabius-praesidium** | `fabius-praesidium` | defensive hardening guides and audit checklists, the personal-agent trust boundaries and grant lifecycle, audit closure and the cleared-surface record (*Fabius Quaestor*), the likeness and voice consent gate (*Fabius Custos*), endpoints that spend money upstream | [`skills/fabius-praesidium/references/security-playbook.md`](skills/fabius-praesidium/references/security-playbook.md) | Fabius procedures |
| **fabius-ludus** | `fabius-ludus` | engine recipes, feel patterns, and pixel-art references | [`skills/fabius-ludus/references/game-playbook.md`](skills/fabius-ludus/references/game-playbook.md) | Fabius procedures |
| **fabius-catena** | `fabius-catena` | EVM/Solana development and provenance sealing | [`onchain-playbook.md`](skills/fabius-catena/references/onchain-playbook.md) · [`sealing.md`](skills/fabius-catena/references/sealing.md) | Fabius procedures |
| **fabius-machina** | `fabius-machina` | automation build/verify discipline and silent-failure catalog | [`skills/fabius-machina/references/automation-playbook.md`](skills/fabius-machina/references/automation-playbook.md) | Fabius procedures |
| **fabius-scientia** | `fabius-scientia` | scientific-method loop, database lookup, and reproducibility | [`skills/fabius-scientia/references/science-playbook.md`](skills/fabius-scientia/references/science-playbook.md) | Fabius procedures |
| **fabius-doctrina** | `fabius-doctrina` | serving, MLOps/experiment tracking, and model evaluation, judge wiring (*Fabius Iudex*) and the hosted-model tier (*Fabius Legatus*) | [`skills/fabius-doctrina/references/ml-engineering-playbook.md`](skills/fabius-doctrina/references/ml-engineering-playbook.md) | Fabius procedures |
| **fabius-fortuna** | `fabius-fortuna` | market/economic analysis, valuation, backtesting, and risk | [`skills/fabius-fortuna/references/markets-and-quant-playbook.md`](skills/fabius-fortuna/references/markets-and-quant-playbook.md) | Fabius procedures |
| **fabius-concilium** | `fabius-concilium` | strongest-seat baseline, council protocol, and runnable reference | [`council-protocol.md`](skills/fabius-concilium/references/council-protocol.md) · [`council.mjs`](skills/fabius-concilium/references/council.mjs) | Fabius procedures |
| **fabius-lean** | `fabius-parcus` | overcomplication tells, surgical-change discipline, assumptions, the reporting shape for a reader who must act (*Fabius Nuntius*) | [lean-decisions.md](skills/fabius-parcus/references/lean-decisions.md) · [reader-fit-reporting.md](skills/fabius-parcus/references/reader-fit-reporting.md) | Fabius procedures |

**Current package.** The imported example corpora have been replaced with original Fabius procedures and executable helpers. Public discovery still exposes exactly fifteen skill contracts. Read the [capability map](credits/capabilities.json) for the replacement code, tests and limits, and [source history](credits/README.md) for the removed bundles. The current package contains no nested `SKILL.md` or renamed `REFERENCE.md` contracts.

**Resource toolkits.** Some references point to external tools, papers, databases and services. Those links are research and integration guidance, not bundled dependencies, ownership claims or a guarantee of current availability. Inspect the current authoritative source before using an external tool. Figura retains chart and diagram guidance; it does not claim a complete component library.

**Architecture and maintenance.** Disciplina owns [architecture decisions](skills/fabius-disciplina/references/architecture-decisions.md) and [transactional updates](skills/fabius-disciplina/references/transactional-updates.md). The router owns [skill maintenance](skills/fabius/references/skill-maintenance.md); Archivum owns [memory migration](skills/fabius-archivum/references/memory-migration.md). Read only the relevant procedure. Their inspected upstream revisions and licenses are recorded in the source registry; no NanoClaw runtime or channel adapter is bundled.

## Retrieval contract — how the brain reaches the corpus

1. **Classify** the task (routing-policy R1) → the owning skill → its library above.
2. **Read the index first** (R9 · M7) — one-line summaries and metadata, never the bulk.
3. **Page in only the matching slice**; if it still exceeds the budget, **summarize-then-link**, don't inline.
4. Use symbolic search first. For a selected note set, Archivum's [local retrieval](skills/fabius-archivum/references/local-retrieval.md) provides bounded lexical ranking with source citations and byte-based freshness checks. It does not download embeddings or promise approximate vector-search performance.

## Package discipline

Keep entry rules small and select references by the task. Original helpers live beside their owner and run only when their required host capability and authority exist. No source repository, model provider or dependency is fetched automatically. Separately managed corpora remain an optional future integration that needs retrieval and offline-availability evidence of its own.

## Run the original helpers

- **Agent workflow:** [scheduler contract](skills/fabius-cohors/references/catalogue/scheduler.md), with the executable [Cohors demo](skills/fabius-cohors/examples/demo.mjs).
- **Knowledge:** [local retrieval](skills/fabius-archivum/references/local-retrieval.md), with the executable [selected-notes demo](skills/fabius-archivum/examples/retrieval/demo.mjs).
- **Design:** [token and scene system](skills/fabius-decor/references/design-system.md), with original [tokens](skills/fabius-decor/examples/tokens.json) and [storyboard](skills/fabius-decor/examples/storyboard.json).
- **Completion evidence:** [engineering workflows](skills/fabius-disciplina/references/engineering-workflows.md), with the [evidence ledger](skills/fabius-disciplina/scripts/evidence.mjs).
