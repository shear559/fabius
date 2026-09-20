<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-decor/SKILL.md -->

# Fabius Pictor — generated video and the paid media request

Loaded on demand by `fabius-decor`. [`generative-imagery.md`](generative-imagery.md) owns the prompt for a still. This file owns what a still lacks: motion (Part A) and the billable request around any generated medium (Part B). A rule marked *(ours)* is fabius's own — observed in no studied source.

## Part A · 1 — Name the source mode first

Classify the request into ONE mode before prompting: the mode fixes the mandatory inputs and the eligible variants.

| Mode | Mandatory media |
|---|---|
| text-to-video — the no-mode default | none |
| still-to-motion | one start frame |
| frame pair | start frame AND end frame |
| reference-guided | a reference set, no frame anchor; minimum is per model |
| motion transfer | a character image AND a driving video |
| edit a clip | one source video + the instruction |
| extend a clip | the source clip or its prior job (§5) |

- A start frame and a reference image are different roles.
- Never assume a model supports a mode — check what it declares.
- Reference-guided and motion transfer: state what is retained from the footage and what is substituted BEFORE any style word.
- Missing input → refused once, in §4. A person-bearing asset + a driver → stop: [praesidium supply-chain §8](../../fabius-praesidium/references/supply-chain-and-ai-artifacts.md).

## Part A · 2 — Motion slots and the start-frame route

**Start-frame route.** When brand or character consistency matters, generate from a still already approved under [`generative-imagery.md`](generative-imagery.md). The start frame is the anchor; the prompt describes only what CHANGES.

**Motion slots** *(ours — craft doctrine, credited to no source)*, ordered after the still slots: subject action → ONE camera move per shot in plain film language (static · pan · dolly in · orbit) → intensity → duration. Multi-shot = a shot list of single-move shots.

**Kinetic axis** *(ours)* — a fifth axis of the conflict pass: a move that leaves the framed start image · a violent move on a static portrait · two moves in one shot. Same route: explain → correct → override.

## Part B · 3 — A parameter change can be a model change

Extends "never silently rewrite" to parameters and cost tier. Resolution, speed tier and quality profile are often separate ENDPOINTS with their own limits and prices — resolve from the settings the user stated, never from a remembered id.

- One setting changes → show the plan before running: the model now used and every other value that moves, old → new.
- A setting the user stated never moves. An unset one may move only inside the same quality profile, only as a listed change. Nothing fits → "not available".
- A source-mode switch keeps the chosen tier. *(ours)* No variant of the new mode shares it → "not available", never the first-listed one.
- Parameter sets and model identifiers are read from the live schema, never recalled or constructed → [machina §1](../../fabius-machina/references/automation-playbook.md). Delta: snap the brief to the declared set and say so.

## Part B · 4 — Preflight before anything billable

Run locally, in order, after the prompt checklist.

1. **Capability per media type.** Read from the declared inputs, by the schema's type tag and never a guessed name: whether the end frame has its own field, whether a field takes one item or several (and the cap), which field carries the media. Zero capability → refuse by name. De-duplicate, keep the user's order, cap — *(ours)* and report any media the cap drops. End frame → its own field where declared; array-only → appended last.
2. **Input contract per (mode, model).** Prompt required? Mandatory auxiliary images? The WIRE KEY the instruction travels under — read it, never assume. Name the first missing item by its human label, §1's media included.
3. **Source-media limits are data** the provider publishes — format, file size, length, frame dimensions. Check what is locally measurable; NAME what only the provider can verify.
4. **Normalise through the target schema** — invalid enum → default, clamp, round integers; on a model switch carry values only through the new schema. DISCLOSE every changed value, old → new (§3).
5. **Cost gate.** Before submitting know unit cost and count for the exact model + parameters, from the live catalogue or the provider's own estimate. Else "no estimate available" — never extrapolate (token calls differ: `fabius-cohors`, local-agent-runtime §8). Print the total; stop for a yes above the ceiling the user set; none set → ask before the first paid submit.

**Draft ladder** *(ours — the media instance of [R11](../../fabius/references/routing-policy.md))*: draft at the cheapest tier that answers the question → approve → render the approved prompt + start frame ONCE at final settings. Escalate once.

Per provider, check: credit reserved at submit? · cancel only while queued? · prepaid credit expires? · concurrency counts queued + running?

## Part B · 5 — After submit: outcomes, custody, lineage

**Job mechanics** are machina's: persisted job id, timeout ≠ failure ([playbook, Day-2](../../fabius-machina/references/automation-playbook.md)); unsigned callback ([toolkit](../../fabius-machina/references/automation-toolkit.md)).

**Moderation block.** Report whether it concerns the INPUT (prompt or media) or the OUTPUT; route the revision through explain → correct → override. Handling the refusal itself is the router's ([doctrine §2](../../fabius/references/orchestration-doctrine.md)). "Not charged" is a per-provider check.

**Custody.** A result URL is a loan. On success, in the same run: download → plain content hash → own asset store → ONE provenance row. Shipped work never links the provider URL.

> **Provenance row** — prompt · full parameters · model identifier · job id · source-media ids · date · terms date. Defined here only.

**Inputs.** Upload URLs expire — read when. The API credential never goes to the pre-signed storage origin (`fabius-praesidium`). A public-URL input is fetched by a third party: no signed or private links.

**Lineage.** Extend and re-render act on a prior JOB — the row's job id + model id are the handle. A continuation is valid only when the source job's model is one the continuation variant accepts; the prior job is then the sole source. *(ours)* Id not kept → say the clip cannot be extended in place; never present a re-generation as an extension.

## Pairs with

[`design-assets.md`](design-assets.md) (output rights, hosted-generator terms), [`motion-libraries.md`](motion-libraries.md) (the deterministic storyboard — authored, not generated) and `fabius-parcus` (the cheapest render that answers the question).

Studied (2026-09-20): a hosted multi-model image-and-video generation API — its public developer docs and vendor-published interface description (a commercial product; nothing carried) — observed for per-endpoint parameter contracts, start-image endpoints, moderation and billing outcomes, result retention and upload handling; no value, name or sentence taken.

Informed by **Open-Generative-AI** (Anil-matcha, MIT) — studied for video source modes and their mandatory media, the disclosed-change plan, schema-derived media capability, the local request preflight and job-keyed continuation lineage, re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
