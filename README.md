<div align="center">

<img src="assets/fabius-pixel.svg" alt="fabius" width="440" />

#### scout wide · strike narrow

*A plugin, not a platform — one set of rules above every model.*

<br/>

<img src="assets/hero.webp" alt="fabius — one set of rules above every model: the install command and the model marks it runs above" width="100%" />

<br/>
<br/>

[![Plugin](https://img.shields.io/badge/plugin-install_in_Claude_Code_%C2%B7_Codex_%C2%B7_Grok_Build-76b900?style=for-the-badge)](#install-in-your-agent-app)
[![Runs above every model](https://img.shields.io/badge/runs_above-every_model-76b900?style=for-the-badge)](#runs-above-every-model-exactly-the-same-rules)
[![Benchmark](https://img.shields.io/badge/benchmark-blind,_reproducible-2ea44f?style=for-the-badge)](BENCHMARKS.md)
[![Whitepaper](https://img.shields.io/badge/whitepaper-proofs_+_coherence-76b900?style=for-the-badge)](paper/fabius-as-a-system.pdf)

</div>

---

## one set of rules. above every model.

fabius is a plugin — **fifteen coordinated public skills and twenty-two core routing rules**, loaded through a compatible agent environment. Mathematical arguments and operational heuristics are distinguished in the research. The model supplies the capability; fabius supplies the discipline. **You choose the goal; fabius chooses the machinery** — capability-first routing, research that stops the moment another step can no longer change the decision, verification before anything ships, and permissioned memory that stops re-deriving. Nothing to host. Nothing to sign up for.

The contract is written down, not implied: [IDENTITY.md](IDENTITY.md) defines the testable objective—whether the same model can produce a better outcome with less waste—not a universal result claimed in advance. The orchestration doctrine (the flow, provider selection, stopping logic, and acting ladder) is [`skills/fabius/references/orchestration-doctrine.md`](skills/fabius/references/orchestration-doctrine.md); the site is **[fabius-landing.vercel.app](https://fabius-landing.vercel.app)**.

---

## Runs above every model. Exactly the same rules.

fabius has no required model roster, hosted service, or external runtime: its core is a set of rules the harness hands to whichever model you choose. The repository also includes an optional zero-dependency local runner for use without a harness. Frontier or open-weight, hosted, routed or local: the contract is identical. Thirty-six model families are shown as examples below. Their names do not establish host integration or tested compatibility: skill loading, tool access and instruction-following capability determine what can run.

<table align="center"><tr>
<td align="center" title="Anthropic"><img src="assets/brands/s/anthropic.webp" width="30" /><br/><sub><b>Claude</b></sub></td>
<td align="center" title="OpenAI"><img src="assets/brands/s/openai.webp" width="30" /><br/><sub><b>GPT</b></sub></td>
<td align="center" title="Google"><img src="assets/brands/gemini.svg" width="30" /><br/><sub><b>Gemini</b></sub></td>
<td align="center" title="DeepSeek"><img src="assets/brands/s/deepseek.webp" width="30" /><br/><sub><b>DeepSeek</b></sub></td>
<td align="center" title="Z.ai · Zhipu"><img src="assets/brands/s/glm.webp" width="30" /><br/><sub><b>GLM</b></sub></td>
<td align="center" title="Alibaba"><img src="assets/brands/s/qwen.webp" width="30" /><br/><sub><b>Qwen</b></sub></td>
</tr><tr>
<td align="center" title="Meta"><img src="assets/brands/s/llama.webp" width="30" /><br/><sub><b>Llama</b></sub></td>
<td align="center" title="Mistral AI"><img src="assets/brands/s/mistral.webp" width="30" /><br/><sub><b>Mistral</b></sub></td>
<td align="center" title="Moonshot AI"><img src="assets/brands/s/kimi.webp" width="30" /><br/><sub><b>Kimi</b></sub></td>
<td align="center" title="xAI"><img src="assets/brands/s/xai.webp" width="30" /><br/><sub><b>Grok</b></sub></td>
<td align="center" title="Cohere"><img src="assets/brands/s/cohere.webp" width="30" /><br/><sub><b>Command</b></sub></td>
<td align="center" title="Google"><img src="assets/brands/s/google.webp" width="30" /><br/><sub><b>Gemma</b></sub></td>
</tr><tr>
<td align="center" title="Microsoft"><img src="assets/brands/s/microsoft.webp" width="30" /><br/><sub><b>Phi</b></sub></td>
<td align="center" title="NVIDIA"><img src="assets/brands/s/nvidia.webp" width="30" /><br/><sub><b>Nemotron</b></sub></td>
<td align="center" title="IBM"><img src="assets/brands/s/ibm.webp" width="30" /><br/><sub><b>Granite</b></sub></td>
<td align="center" title="Amazon"><img src="assets/brands/s/aws.webp" width="30" /><br/><sub><b>Nova</b></sub></td>
<td align="center" title="Perplexity"><img src="assets/brands/s/perplexity.webp" width="30" /><br/><sub><b>Sonar</b></sub></td>
<td align="center" title="MiniMax"><img src="assets/brands/s/minimax.webp" width="30" /><br/><sub><b>MiniMax</b></sub></td>
</tr><tr>
<td align="center" title="Tencent"><img src="assets/brands/s/hunyuan.webp" width="30" /><br/><sub><b>Hunyuan</b></sub></td>
<td align="center" title="Baidu"><img src="assets/brands/s/baidu.webp" width="30" /><br/><sub><b>ERNIE</b></sub></td>
<td align="center" title="ByteDance"><img src="assets/brands/s/bytedance-seed.webp" width="30" /><br/><sub><b>Seed</b></sub></td>
<td align="center" title="StepFun"><img src="assets/brands/s/stepfun.webp" width="30" /><br/><sub><b>Step</b></sub></td>
<td align="center" title="01.AI"><img src="assets/brands/s/yi.webp" width="30" /><br/><sub><b>Yi</b></sub></td>
<td align="center" title="TII"><img src="assets/brands/s/tii.webp" width="30" /><br/><sub><b>Falcon</b></sub></td>
</tr><tr>
<td align="center" title="AI21 Labs"><img src="assets/brands/s/ai21.webp" width="30" /><br/><sub><b>Jamba</b></sub></td>
<td align="center" title="Reka AI"><img src="assets/brands/s/reka.webp" width="30" /><br/><sub><b>Reka</b></sub></td>
<td align="center" title="Ai2"><img src="assets/brands/s/allenai.webp" width="30" /><br/><sub><b>OLMo</b></sub></td>
<td align="center" title="Nous Research"><img src="assets/brands/s/nous.webp" width="30" /><br/><sub><b>Hermes</b></sub></td>
<td align="center" title="Liquid AI"><img src="assets/brands/s/liquid.webp" width="30" /><br/><sub><b>LFM</b></sub></td>
<td align="center" title="LG AI Research"><img src="assets/brands/s/exaone.webp" width="30" /><br/><sub><b>EXAONE</b></sub></td>
</tr><tr>
<td align="center" title="Upstage"><img src="assets/brands/s/upstage.webp" width="30" /><br/><sub><b>Solar</b></sub></td>
<td align="center" title="Xiaomi"><img src="assets/brands/s/xiaomi-mimo.webp" width="30" /><br/><sub><b>MiMo</b></sub></td>
<td align="center" title="Sarvam AI"><img src="assets/brands/s/sarvam.webp" width="30" /><br/><sub><b>Sarvam</b></sub></td>
<td align="center" title="Hugging Face"><img src="assets/brands/s/huggingface.webp" width="30" /><br/><sub><b>SmolLM</b></sub></td>
<td align="center" title="OpenAI · open weights"><img src="assets/brands/s/openai.webp" width="30" /><br/><sub><b>GPT-OSS</b></sub></td>
<td align="center" title="Swiss AI"><img src="assets/brands/s/swiss-ai.webp" width="30" /><br/><sub><b>Apertus</b></sub></td>
</tr></table>

<sub>Model, maker and platform marks identify compatible engines only ([sources](assets/brands/README.md)); example families change with each vendor's roster. No affiliation or endorsement is implied. Served any way you like — hosted, via a router, or local. Harnesses: **Claude Code · Codex · Grok Build** natively, anywhere else through [AGENTS.md](AGENTS.md).</sub>

---

## Install in your agent app

The rules load into a compatible harness. Installation is free for personal use; your model, connected services and compute may have separate costs.

**Claude Code**

```
/plugin marketplace add shear559/fabius
/plugin install fabius@fabius
/reload-plugins
```

For background updates, select `/plugin` → Marketplaces → fabius → **Enable auto-update**. An update on disk takes effect after `/reload-plugins` or the next launch; the running session keeps its loaded version until then. [Claude Code update behavior](https://code.claude.com/docs/en/discover-plugins#configure-auto-updates).

**Codex** — use a Codex CLI that supports `codex plugin`:

```sh
codex plugin marketplace add shear559/fabius
codex plugin add fabius@fabius
codex plugin list --marketplace fabius
```

Confirm that the listing reports the plugin installed and enabled, then restart Codex and check that its skills appear in a fresh task. Adding a marketplace or an enabled config entry alone is not an installation check. If `codex plugin --help` is unavailable, update the host before using these commands. The command syntax was checked with Codex CLI 0.153.4 on 2026-09-08.

To update an existing installation, run `codex plugin marketplace upgrade fabius`, then `codex plugin add fabius@fabius`, and repeat the listing and restart checks. Marketplace refresh, installed files and active-session loading are separate states. The host may use a sparse package; do not assume every repository file or a plugin-root `AGENTS.md` becomes active instructions.

**Grok Build**

```
grok plugin install shear559/fabius --trust
grok plugin enable fabius
```

Run `grok plugin details fabius` to inspect its version and component inventory, then reload plugins or start a fresh session. Checked with Grok Build 0.2.103 on 2026-09-08. `grok plugin update fabius` updates an unpinned installation; in this version it skips a saved `@ref`, including a release tag. A pinned installation needs an explicit release transition, followed by another version check. [Grok plugin commands](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/09-plugins.md).

**Anywhere else** — review [`AGENTS.md`](AGENTS.md) and merge its portable core rules into the instruction path your tool supports. Preserve existing project instructions; do not download over an existing `AGENTS.md`, `GEMINI.md` or rules file. This single file carries the core stance. Full specialist workflows also need the relevant skill files and tools.

Without a harness, the repository includes an optional zero-dependency local runner that reads the sealed contracts: `node runtime/fabius.mjs run "…"`. Its available providers, tools and routing implementation are described in [runtime/README.md](runtime/README.md); they are separate from a host's plugin integration.

Try a concrete task after loading the plugin:

- “Review this architecture. Preserve the working boundaries, compare alternatives, and separate design advice from evidence we still need.”
- “Improve this skill from these sources. Update its existing owner, preserve attribution, and test both the intended route and a near-neighbor.”
- “Plan this upgrade. Account for every selected component and show how code, data, and external version pins can be recovered.”

These workflows use your harness's available tools and permissions. Missing execution or live access is reported explicitly. [Architecture decisions](skills/fabius-disciplina/references/architecture-decisions.md) · [Skill maintenance](skills/fabius/references/skill-maintenance.md) · [Transactional updates](skills/fabius-disciplina/references/transactional-updates.md).

---

## The system

<img src="assets/architecture.svg" alt="How fabius works: your prompt goes to the fabius router, which dispatches by layer, machinery, and model-tier to thirteen specialists — disciplina (process), decor (design + data-viz), cohors (agents), archivum (memory), mercatus (marketing), praesidium (defensive security), ludus (games), catena (on-chain + sealing), machina (automation), scientia (science), doctrina (ML engineering), fortuna (markets & finance), concilium (cross-model council) — all running on the always-on fabius-parcus lean core, producing the smallest correct result." width="100%" />

**Fifteen coordinated, zero-overlap capability layers** — a router that dispatches by layer · machinery · model-tier, an always-on lean core, and thirteen specialists:

| Layer | Owns |
|---|---|
| `fabius` | the router — selects layers, machinery and model tier; maintains skill ownership and source-backed refinement |
| `fabius-parcus` | the always-on lean core — terse output, the YAGNI ladder, surgical change |
| `fabius-disciplina` | architecture planning/review, state-aware updates, impact-mapped implementation and root-cause debugging |
| `fabius-decor` | ship-grade design — tokens, one accent, data-viz, decks + infographics, RTL, review against the generated-UI tells |
| `fabius-cohors` | agent engineering — least privilege, orchestration up to a swarm |
| `fabius-archivum` | permissioned memory — canonical records, legacy migration, gated recall and history; video and source-grounded notebooks as sources |
| `fabius-mercatus` | go-to-market — positioning, converting copy, SEO, draft-only outreach |
| `fabius-praesidium` | defensive security — STRIDE, OWASP, severity → fix → regression test |
| `fabius-ludus` | game craft — core loop first, deliberate juice, jam-sized scope |
| `fabius-catena` | on-chain + sealing — EVM/Solana money-safety, verifiable provenance |
| `fabius-machina` | automation — deterministic workflow wiring, verify before it runs live |
| `fabius-scientia` | science — competing hypotheses, grounded lookups, reproducibility |
| `fabius-doctrina` | AI/ML engineering — train → evaluate → serve → monitor |
| `fabius-fortuna` | markets & finance — risk-first analysis, honest backtests; never advice |
| `fabius-concilium` | cross-model council — blind peer-review across N models, chairman synthesis |

Depth on demand: [ARCHITECTURE.md](ARCHITECTURE.md) · [CORPUS.md](CORPUS.md) · the decision policy in [`skills/fabius/references/routing-policy.md`](skills/fabius/references/routing-policy.md).

---

## The proof

One versioned benchmark, four panels, every miss printed: blind-judged quality, a mixed track of executed checks and explicitly model-graded factual checklists, cross-family demonstrations, and the 100-task FBS run of the identity contract. Results are reported per model, panel, and task; they do not establish that every model or domain improves. Reproducibility is limited to the artifacts actually committed, and those limits are printed beside the numbers. Method and receipts: [BENCHMARKS.md](BENCHMARKS.md) · formal arguments and coherence analysis: [the whitepaper](paper/fabius-as-a-system.pdf) (50 pp).

Run the repository checks with `bash scripts/verify-all.sh --mode=dev`. Routing regressions exercise real input phrases; frontmatter controls remove, duplicate and corrupt required fields to test the gate itself. Separate [maintenance smoke scenarios](evals/maintenance-smoke/README.md) retain prompts and observed responses; they are not an additional benchmark panel or a measured quality gain.

---

## Provenance

The fifteen public contracts are content-sealed with SHA-256 and a Merkle root; releases use a signed tag and an OpenTimestamps proof whose verifier reports whether Bitcoin confirmation is complete or still pending. Verify the exact state with `bash provenance/verify.sh`. Details: [PROVENANCE.md](PROVENANCE.md).

---

**Boundaries** — fabius governs *how* the work is done, never *what* you want; `stop fabius` drops the stance. `fabius-praesidium` and `fabius-catena` are defensive only. Lean never trims validation, security, or accessibility.

**License** — proprietary, free to install for personal use ([LICENSE](LICENSE)). Third-party reference material is credited in [`credits/`](credits/).
