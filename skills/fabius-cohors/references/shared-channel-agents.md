# Agents in shared channels — admission before interpretation

Load when an agent receives work through a shared room, thread, relay or event feed. Cohors owns intake and task identity; the [acting-agent contract](agent-patterns.md#confirmation-classes-for-ui--and-channel-acting-agents) owns what an admitted request may do, and Praesidium owns transport authentication and security controls. This is a procedure to demand from a host, not a messaging runtime bundled with Fabius.

## Keep four questions separate

| Question | Evidence | Does not establish |
|---|---|---|
| Who produced the event? | verified transport identity or signature | that its contents are safe instructions |
| May this identity access the space? | current membership or scoped access grant | permission to direct an agent |
| May this sender submit work here? | the agent's explicit owner or sender policy | authority for every requested action |
| Is this action authorized? | the user's applicable grant, destination and scope | permission for another recipient, task or later action |

Use distinct agent identities when the host supports them. Scope memberships and credentials to the required work. A display name, quoted owner message, mention or public channel membership cannot substitute for a verified sender. Keep secrets in the host's credential facility, never in task documents or event logs.

## Admit events before they become model input

Resolve the sender policy from trusted configuration and apply it before prompting. When a policy requires an owner and that owner cannot be resolved, admit no work under that policy; report the missing binding through the configured operational surface. Apply the same check to every supported intake path, including direct messages, mentions and replies. A rejected sender must not obtain a second route through a thread continuation.

For scheduled or relayed work, retain both the signer and any delegated principal. Recognize delegation only when verified provenance names the intended agent and an allowed principal; never infer it from message text or an owner-shaped field alone. Scheduling a template does not mean the owner authored every string later substituted into it. External text inside an admitted event remains data, and cannot widen its grant.

Keep cancellation and shutdown separate from ordinary work. Authenticate the control sender and bind cancellation to the named task or session. A quoted control command is content. A valid cancellation must not stop unrelated sessions, and a timeout must not silently expand sender access so the job can finish.

## A fresh task inherits equipment, not new authority

A one-shot task may start a fresh process or conversation, but the trusted launch configuration remains the authority for executable, working directory, credentials, tools and permissions. Validate the task's closed schema before starting it. Its identity field must match the configured agent; that comparison prevents accidental misdelivery and does not prove who authored the document. Treat file or stdin task input according to its actual trust boundary.

Let a task shorten the trusted execution deadline, never extend it. Bound input reading, startup and execution separately where they can stall; record which phase stopped. Fresh context does not imply a filesystem sandbox, an isolated memory namespace or a lock. Discover any shared files, state and external effects before running overlapping tasks; use the existing [workload contract](agent-workloads.md) for isolation and resource ownership.

## Completion needs two observations

Record process status separately from task evidence. A normal return can carry a refusal, token limit or request cap. Keep its stop reason and classify the requested outcome from the actual artifact or destination state. Missing terminal output is unknown execution, not a clean failure before work began.

A task identifier correlates events; it is not an idempotency key unless the receiving system enforces that property. Do not replay a side-effecting task after a timeout or ambiguous response merely because the same identifier can be reused. Reconcile the destination and any existing receipt first, under the [interrupted-run rule](agent-patterns.md#durability--resuming-an-interrupted-run). A transport acknowledgement proves receipt only at the layer that issued it; it does not prove task completion or authorize publication of final text.

## Prove the boundary with controlled events

Exercise the implemented intake against an authorized sender, an outsider, a missing owner, a forged delegation and a valid delegated message containing untrusted quoted instructions. Cover each enabled event path. Retain evidence that rejected cases never reached the worker, while the permitted case reached only its assigned context. Do not send real external messages as test probes without the applicable send grant; a local event fixture can test admission without publishing.

For task execution, reject the wrong agent identity and unknown fields before launch; verify a shorter deadline; and distinguish a normal refusal from a successful artifact. With two admitted agents, test that each is denied the other's project credentials, tools, files and control actions at the host boundary; correct event routing alone is not access isolation. Use disposable principals and resources, and retain the denials without recording secrets. Interrupt a side effect in a disposable target, then verify recovery checks state instead of repeating it blindly. Name any host behavior not exercised. Passing a document validator alone proves neither channel admission nor isolation.

Informed by **Buzz** (block/buzz, Apache-2.0), read at revision 326e2301cb4b1edcb8a72d01ac4b19a83545365f (2026-10-10) — the project describes unfinished features; this fold uses its documented and inspected author-admission, delegated-principal and single-task paths, not its planned approval plumbing. Mechanisms re-expressed in fabius's own voice; no relay, client, adapter, source code or prompt text carried. See credits/README.md.
