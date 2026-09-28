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
- **One roster, asked by name.** A model id lives in exactly one roster — keyed by provider and tier, beside a *reference* to its credential (never the value; `fabius-praesidium` §3) — and a consumer asks for a tier or the named binding, never a literal id. A hardcoded id in a caller is a defect: it silently defeats the one place operators rotate (this section's lifecycle) and voids the eval that justified the choice. Provider-specific sampling settings ride inside the binding as an opaque bag the shared schema never enumerates — a typed field is earned only by a setting every supported target shares — and §2's outbound pass is the only place they are removed or lowered. A serialisation of that bag that cannot carry a value fails and names the key; a partial write is a silent loss of configuration, proven loud by a round-trip test. Gate: grep consumers for a literal model id — zero hits outside the roster.

## 5 · Probes, stream readers, inline reasoning

- **A credential probe reports only what the response proves:** rejected key · key lacking permission · rate-limited = the credential works · model-not-found after auth = the key is valid. Probe with the cheapest model or a list-models ping; the probe's model id is roster data that rots.
- **A client has exactly two honest outputs: the provider's completion, or a typed failure.** A missing, rejected or under-scoped key, a quota wall, an outage and a transport error all reach the caller as the typed code cohors defines (linked above) — the client never manufactures a body in their place, because once the error is gone no downstream check can tell a manufactured answer from a served one; the caller owns the fallback decision. An offline or rehearsal mode is a switch the caller sets, and every response it yields carries a synthetic marker that each consumer either propagates or refuses — a plan, summary or record built from unmarked synthetic text is a claim that the missing call succeeded. A usage field holds only the provider's own accounting; when none arrived it stays empty — an estimate lives in its own labelled field, never in the measured one. Proof: a wrapper test feeds a rejected credential and asserts a typed failure, not content; a grep of consumers finds no path that reads unmarked synthetic text as a real result.
- **Decode a stream incrementally and hold each chunk's unfinished tail until its line ends.** Network chunks respect neither line nor character boundaries; a reader that assumes they do loses events silently.
- **Reasoning can arrive in the text channel:** strip a well-formed block; strip up to an orphan closer; treat an unclosed opener as no answer. Parse structured output only after.

## Pairs with

`fabius-cohors` (typed failure codes; it authors the tools §2 re-serializes), [`judgment-models.md`](judgment-models.md) (a judge called through this tier), `fabius-praesidium` (key hygiene), `fabius` (fallback preserves the capability — [`orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §2).

Informed by **OmniRoute** (diegosouzapw/OmniRoute, MIT; commit 7a92129, 2026-09-20) — studied in it (several mechanisms are self-declared ports; that lineage was not verified) for stream commit and recovery, request portability, admission clocks and model-id lifecycle — its limit-evasion, client-impersonation and account-pooling material was not carried, and it is never a recommended gateway; and **open-notebook** (lfnovo/open-notebook, Luis Novo, MIT; commit 3127f14) — studied for credential-probe semantics, chunk-safe stream reading and inline-reasoning handling; re-expressed in fabius's own voice; no upstream files bundled; and **AX** (google, Apache-2.0), read at revision ac2332829f22360ff97b0ba34d94dd0dd782f17e (2026-09-26) — the project declares itself pre-stable with breaking changes ahead, so only mechanisms whose code path exists at that revision were folded and its roadmap is recorded as its plan; studied for its model client's error path — §5's two-honest-outputs rule is the inverse of what that path returns — and the single named model binding read from one store (§4's literal-id gate is fabius's own extension); mechanisms re-expressed, no source text carried. See credits/README.md.
