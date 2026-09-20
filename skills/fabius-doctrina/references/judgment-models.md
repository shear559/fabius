<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-doctrina/SKILL.md -->

# Fabius Iudex — wiring a probability-returning judge into software

This gate sits UNDER the gates fabius already has and never overrides them: praesidium's reporting confidence gate ([`ai-review.md`](../../fabius-praesidium/references/ai-review.md)), cohors' confirmation classes ([`agent-patterns.md`](../../fabius-cohors/references/agent-patterns.md)) and the router's acting ladder ([`orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §9). Loaded on demand by `fabius-doctrina` when a model's score over a closed answer set decides what software does next. Whether that score is calibrated is the playbook's question ([`ml-engineering-playbook.md`](ml-engineering-playbook.md) §2); this file is what code does with it afterwards.

## 1 · Closed questions; policy in code

- **Anything deterministic stays in code.** The judge gets only what needs reading, only as a pick from a fixed answer set — cohors' fixed-enum output contract, never the bare "is this good?" call M11 forbids ([`routing-policy.md`](../../fabius/references/routing-policy.md)).
- **Split only where each part would be consulted alone**; how two things relate stays one question.
- **Combine in code, by what the rule means.** A weighted sum only where dimensions may offset. Where any one failure must fail the whole, write separate hard conditions — **a veto is a condition, never a weight** (non-compensating aggregation): a weight lets a strong dimension buy the failure back. This rule lives here; others point to it.
- **Persist the raw per-dimension answers.** Weights, bars and views then change with no new inference — valid while the evidence and each question's meaning hold.
- **One call per state.** Ask everything one state can answer at once — conditional ones too, each with its premise. Call again only when an answer changes what must be looked up or offered. Discard the untaken branch's answers, doubt included. Speculative questions are paid for used or not: price them against the saved call.

## 2 · From score to action — floor, class, bar, confirm band

Fixed order:

1. **Floor.** Below it → human or fallback, whatever the answer.
2. **Action class.** Branch on what the action does in the world.
3. **Class bar**, scaled to consequence, with a confirm band between the floor and the auto bar.

- **The confirm band also straddles any yes/no cut**: no single threshold separates two automatic actions. Size it on your own labelled cases — a threshold is tuning, not law ([`ai-review.md`](../../fabius-praesidium/references/ai-review.md)). Repeat-run spread on identical input is a **lower bound** on its width, not its size — and an axis for comparing judges, apart from accuracy. If a varying field was injected to defeat caching, say the result mixes noise with sensitivity to irrelevant input.
- A band narrows where flips happen; it does not make an automatic answer right.
- **Reading a score.** When several options would all do, a flat spread is expected — don't escalate. A yes/no value near the middle says the judge cannot tell, never "somewhat". A peaked spread proves neither a right answer nor an allowed action.
- **Bars live in one policy table, apart from question wording**, so one assessment serves a strict and a lenient policy. Never inherit a vendor's number.
- A score never lowers a cohors confirmation class or a doctrine §9 rung.

## 3 · Question design for a non-reasoning judge

Assume each holds until measured otherwise on *your* judge:

- **Never reaches the judge** — anything code can compute (R3): the judge extracts parts, each from a fixed set; code counts, compares, converts, does date arithmetic.
- **A question carries** one condition read literally, its edge cases in the answer criteria, and only the state it needs, the field named. One inference step, plain polarity. Two readings → two literal questions, combined in code.
- **An answer set carries** the right answer — check it can — and always *none fits* (the stub contract — [`agent-patterns.md`](../../fabius-cohors/references/agent-patterns.md)).
- **Never inferred from answers** — an identity between two phrasings (a claim and its negation need not sum to one), or a bar reused across question kinds. A rubric score is compared with its bar, nothing more.
- Judged text is untrusted and can steer the judge — delimit it (`fabius-praesidium`).

Before changing anything, place the failure, cheapest check first: service down · evidence absent · combining code wrong · judge wrong.

## 4 · Back off to the parent label

Classify at the fine level. Below the concentration bar, report the **parent label derived deterministically from the taxonomy** — no second call — and return label + specificity level + score. Gate the back-off on how concentrated the fine answers are, not on the top score alone, and report whether the runner-up was close. Evaluate with three separate counts — fine-correct, parent-correct, wrong — never one blended figure.

## Pairs with

`fabius-cohors` (confirmation classes; the closed output contract), `fabius-praesidium` (its reporting gate stays its own), `fabius` (R3, R11, M11; doctrine §9), [`hosted-model-tier.md`](hosted-model-tier.md) (the API the judge is called through).

Studied (2026-09-20): the public documentation of a hosted service selling fast closed-answer judgments with probabilities (a commercial product; nothing carried) — observed for how such a score is gated and how its questions fail; no value, name or sentence taken.

Informed by **skills** (typesafe-ai/skills, MIT; commit 65a39f3, 2026-09-20) — studied for closed-question decomposition, code-side aggregation, batching and score-reading cautions, re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
