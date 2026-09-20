<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-mercatus/SKILL.md -->

# Fabius Emendator — prose tell lint and audit

## 1 · Scope and the split with parcus and decor

Emendator edits or audits a **deliverable draft** — the user's or a generated one — for the
sentence shapes that read as machine-made. `fabius-parcus` governs the model's own reply, and
its *Change less* governs any edit of someone else's prose. Vocabulary tells stay with decor's
`marketing-buzzword` id
([design-critique.md](../../fabius-decor/references/design-critique.md)); no second word list
lives here. The lint is a heuristic: it buys clearer prose, never a detector result. An edit
runs under router rule M11 ([routing-policy.md](../../fabius/references/routing-policy.md)) as
a **capped pass** — one audit, one repair pass, one re-check; never loop until clean.

## 2 · Read first — core point and voice inventory

Read the whole draft and write its core point in one sentence before flagging anything. Then
note, from the text alone, what makes it the writer's:

- **Commits to** — the opinions, blunt calls and word choices they stand behind.
- **Qualifies** — where, and how, they state doubt.
- **Wanders** — detours, humour, long spoken sentences.
- **Finish** — how polished it is, and how unevenly.

Touch a sentence only when it shows a tell, is wrong, repeats, or cannot be followed. Repairs
scale with the tells found — never a compression pass. Do not level polish across paragraphs
or sand a blunt line into a polite one. Any reorganisation carries its reason in the change
note. Exit test: the writer would recognise it as theirs.

## 3 · Shape → repair table

| Shape | Repair |
|---|---|
| **Rhythm** | |
| Stacked fragments; every sentence or paragraph cut to one shape | full sentences — and the repair pass adds no symmetry of its own |
| **Evasive wording** | |
| One referent, several names | one name throughout |
| An aside steering what the reader should notice or feel | nothing, when the point is already shown; otherwise a fact the draft or the user supplied — never a new one |
| A grand verb standing in for *is* / *has* | the plain verb, then what the thing does |
| **Asserted significance** | |
| A closing maxim or metaphor | cut it and stop at the last sentence that states a fact; never trade it for a better flourish or a line of the same beat. Recap endings → SKILL.md §5, *End on the action* |
| A sentence announcing importance | the fact that makes it important |
| A trailing clause declaring what the fact signifies ("…, cementing its role") | the concrete consequence for the reader |
| **False contrast and staging** | |
| A question staged to answer itself | state the answer |
| A colon used as a drum-roll | fold into one sentence |
| A setup that flatters the speaker | start at the claim |
| A denial raised only to be corrected ("this isn't a calendar, it's a promise") | the positive claim alone |

The closing-maxim row is the repair for decor's `aphoristic-cadence` id.

## 4 · Keep-test and the no-invention branch

**Keep-test.** Qualifiers fall under the hedge keep-test parcus owns
([reader-fit-reporting.md](../../fabius-parcus/references/reader-fit-reporting.md) §4) — apply
it, never restate it. Intensifiers and connectives likewise: cut a word only when the sentence
means the same without it; a word doing tonal work stays.

**No invention.** Concreteness comes only from what the draft or the user supplied
(honest-claim rule: SKILL.md §3 · [seo-and-discoverability.md](seo-and-discoverability.md) §4).
Evidence present → use it; absent → cut the sentence or ask — never manufacture a number, a
quotation, an instance or a view. An authority with no name ("research suggests") gets a name
from the user or goes.

## 5 · Audit-only mode

Fires on "does this read as generated?" or "flag it, change nothing" — **prose** only;
surfaces stay with `fabius-decor`. Findings are evidence about the **text**, never a verdict on
who or what wrote it: a line can be checked, its author cannot. Output uses cohors's finding
schema ([agent-patterns.md](../../fabius-cohors/references/agent-patterns.md)) cut to prose:
Risk = the §3 shape · Evidence = the quoted line · Fix = the §3 repair direction; Blocks-merge
does not apply. In this mode: no authorship call, no number (decor's critique is scored; this
is not), no rewrite — the edit is offered, not performed. No detector promise either;
provenance-mark hygiene is praesidium's
([supply-chain-and-ai-artifacts.md](../../fabius-praesidium/references/supply-chain-and-ai-artifacts.md)
§7).

Informed by **no-ai-slop** (petergyang, MIT; commit 000650b) — studied for sentence-shape tells paired with repairs, a voice read taken from the draft, the absent-evidence branch and a verdict-free audit mode, re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
