<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-doctrina/SKILL.md -->

# Fabius Legatus — the hosted-model tier in depth

Loaded on demand by `fabius-doctrina`. Depth under the playbook's *Serving via someone else's API* ([`ml-engineering-playbook.md`](ml-engineering-playbook.md) §3): what a client or proxy owes a hosted model's stream, a fallback, a queue and a model id. The typed failure codes and the retry policy they drive stay with cohors ([`agent-evaluation-and-durability.md`](../../fabius-cohors/references/agent-evaluation-and-durability.md)). **Boundary:** a credential here is the caller's own authorized key, one per provider account — fabius never rotates keys or accounts around a provider's limit, never impersonates a client, never automates a limit reset. A queue exists to honour a limit.

## 1 · Once the client has seen output, a retry is no longer invisible

- **A stream that ends without its terminal marker is a truncation**, whatever the status.
- **The first client-visible byte is the commit boundary.** Before it an attempt reopens invisibly — the exact scope of the playbook's one silent retry; after it a resend duplicates output.
- **An opening hold** (withholding first bytes) costs first-token latency on every request: off by default, priced.
- **After commit the only repair is an append-only continuation**, only where the target accepts an assistant prefix and output is plain text: re-request with the emitted text as prefix, trim the overlap. Else refuse with a typed reason — tool call in flight · budget spent · not continuable. A finish reason closing a tool call does not end the turn.
- **A seam is booked; a second author is never invisible.** Every continuation is recorded on the turn: which model wrote each side, and the offset where they join. A same-model resume after a visible pause needs only that record. When a *different* model writes the continuation, the join is also marked for the client — mid-answer, a change of author is not a retry the reader may be left to miss.
- **Three clocks:** idle timeout · hard attempt deadline · useful-output rate (rolling, after warm-up). On the last (the upstream attempt's) progress means answer bytes: keep-warm and accounting frames don't count; a turn thinking or building a tool call is not stalled. The playbook's heartbeat quiets the *client's* watchdog and never resets this clock. A stall ends that one attempt; usage is booked and the slot freed **once**.

## 2 · Crossing to another model is a re-serialization

Run the pass at **one outbound choke point**. Parameters (rows 1–2) come from one outbound table keyed by target that only removes or lowers, never adds: the lower ceiling wins (e.g. the playbook's thinking budget). Structural repairs run there too. Report every value that moved, old → new.

| Rejection class | Rule |
|---|---|
| Sampling params it refuses | drop |
| Output cap above its ceiling | clamp |
| System message not first | merge into the lead, never drop; byte-identical no-op when compliant, so the cached prefix survives |
| Tool declarations | object-schema root · validate every name — ONE bad one rejects every tool · sanitised names collide — dedupe deterministically · drop lookaround from `pattern` · coerce numeric constraints sent as strings · strip a `default` on an optional property (it gets injected) · strict modes force optional→required: widen to nullable out, strip null back |
| Reasoning state bound to the target | some thinking targets reject a follow-up whose prior assistant turn lacks its reasoning block (clients strip it): restore from a server-side store keyed by tool-call id, same target only; on a miss verify documented behaviour |
| Foreign-family tool ARGUMENTS | stringified numbers, absurd magnitudes: coerce and clamp, or the agent loops |

- **Eligibility** — test the target against what THIS request uses (beyond tools: fabius's own extension).
- **Context sizing** — operator-declared window > the executing model's > min of siblings, last resort; record which. Sizing to the smallest sibling silently compresses history.
- **Context overflow is its own class** — larger window or less input; the same window cannot succeed.
- **Not found** → ordered same-family siblings before leaving the family.

## 3 · Admission: two clocks that never feed each other

A queue in front of a model API runs a **queue-wait budget** (cleared at dispatch) and an **execution backstop** (starts at dispatch, never shorter than the call's own upstream-start timeout). Feeding the first into the second kills healthy long non-streamed calls. The two expiries take distinct codes, owned by cohors (linked above). An opt-in queue-depth cap is a pure function checked BEFORE compression or translation work; pipeline order can void that saving — say so.

## 4 · Model-id lifecycle

A hosted model id is a dated dependency: **deprecated** = callable until shutdown, warn · **past shutdown** = reject, name the published replacement as guidance · **untracked** = pass through.

- **Fabius's rule: never rewrite the requested model silently** — a rewrite invalidates the eval that justified the choice (playbook §2, §4 registry).
- An alias table is audited — no entry forwards a retired id to another retired id or to an unroutable spelling — and carries a dated verification stamp.
- A shutdown date belongs to the vendor surface that published it, not to a reseller still serving the id; strip the reseller prefix before matching retirements.
- Conflicting official dates → omit the row.

## 5 · Probes, stream readers, inline reasoning

- **A credential probe reports only what the response proves:** rejected key · key lacking permission · rate-limited = the credential works · model-not-found after auth = the key is valid. Probe with the cheapest model or a list-models ping; the probe's model id is roster data that rots.
- **Decode a stream incrementally and hold each chunk's unfinished tail until its line ends.** Network chunks respect neither line nor character boundaries; a reader that assumes they do loses events silently.
- **Reasoning can arrive in the text channel:** strip a well-formed block; strip up to an orphan closer; treat an unclosed opener as no answer. Parse structured output only after.

## Pairs with

`fabius-cohors` (typed failure codes; it authors the tools §2 re-serializes), [`judgment-models.md`](judgment-models.md) (a judge called through this tier), `fabius-praesidium` (key hygiene), `fabius` (fallback preserves the capability — [`orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §2).

Informed by **OmniRoute** (diegosouzapw/OmniRoute, MIT; commit 7a92129, 2026-09-20) — studied in it (several mechanisms are self-declared ports; that lineage was not verified) for stream commit and recovery, request portability, admission clocks and model-id lifecycle — its limit-evasion, client-impersonation and account-pooling material was not carried, and it is never a recommended gateway; and **open-notebook** (lfnovo/open-notebook, Luis Novo, MIT; commit 3127f14) — studied for credential-probe semantics, chunk-safe stream reading and inline-reasoning handling; re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
