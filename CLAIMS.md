# Claims and the evidence required

This table governs current descriptions of Fabius. A capability describes instructions or an implemented path; a verified result must name its artifact, environment and scope.

| Claim | Supported wording | Boundary / evidence |
|---|---|---|
| Product | Fifteen public skills: router, lean core, thirteen specialists | `node evals/structural.mjs`; ownership is declared, routing accuracy needs behavior tests |
| Original capabilities | Fabius-authored scheduler, selected-file retrieval, token/scene tools and an evidence-consistency ledger | `credits/capabilities.json` maps code to tests and limits; retained public test vectors and third-party assets remain attributed |
| Self-development | Fabius rules guided the development process through the selected model and host tools | The model generates code; Fabius supplies rules and local checks; no autonomous self-improvement or model-independent agency claim |
| Research | Twenty-two core rules, represented by 26 blocks: 22 conditional mathematical arguments and four qualitative rules | `paper/proofs.json`; assumptions matter; a count is not a proof of every statement |
| Host compatibility | Native installation paths for the tested versions of Claude Code, Codex CLI and Grok Build | `COMPATIBILITY.md`; distinguish package installation, session loading and task execution |
| Model choice | Rules can be supplied to different models by a compatible host | A model logo is not an integration test or endorsement |
| Improved results | Dated, panel-specific measurements with printed regressions | `BENCHMARKS.md`; never call old scores a gain for the current release |
| Public benchmarks | On nine public benchmarks (October 2026), no gain or loss after correction: ties, non-inferior or inconclusive per comparison, at 1.33 to 2.03 times the baseline's cost | `docs/archive/2026-10-public-benchmarks/REPORT.md`; Fabius 3.3.0, `claude-sonnet-5-5`, Claude Code 2.1.289 headless; never "improves benchmark scores"; absolute rates are never compared with leaderboards |
| Reference files | The 3.4.0 reference fold had no measured effect: nine ties and two inconclusive contrasts against the 3.3.0 package, and the reference files were opened in 6 of 4,328 package-arm runs | `docs/archive/2026-10-source-fold-benchmarks/REPORT.md`; never "the new references improve X"; a reference-level change is measurable only where a contract directs the read or the work calls for it |
| Invocation | In Claude Code, `/fabius` loads the router and `/fabius:fabius-<skill>` loads one skill | Measured in 803 of 803 and 1,271 of 1,271 runs; a prompt that only begins with the word `fabius:` loaded the router in 1 of 186; other hosts: `COMPATIBILITY.md` |
| Reproducibility | Retained score aggregates can be replayed; new harness receipts retain more evidence | Historical answers and some execution artifacts are absent; a rerun is a new measurement |
| Panel D | BASE / FAB / FAB_MEMORY text-output experiment | No generic terse arm, tool execution or growing cross-session memory test |
| Execution | Say a file, image, video or action was produced only when it exists and was inspected | A plan, tool call request or model claim is insufficient |
| Security | Instructions plus separate host/runtime controls | Written rules do not enforce an OS sandbox; approved shell execution is not one |
| Memory | Uses a declared record store with granted permission | Does not silently create a second store or guarantee host history deletion |
| Provenance | Hashes bind bytes; signed tags bind a release to a key; verified timestamps bound existence time | Not proof of originality, legal ownership, safety or improved model quality |
| Cost and license | Personal non-commercial plugin use is permitted by current LICENSE | Model/service costs are separate; professional permission is unresolved |
| Demonstrations | Maintainer-prepared inputs, artifacts and executable checks | Not independent users, adoption figures, a controlled trial or conversion data |

No invented users, reviews, stars, installs, savings, accuracy gains or launch deadlines. Mark illustrative numbers as examples. Future host or store claims enter this table only after acceptance evidence is recorded.
