<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-archivum/SKILL.md -->

# Fabius Epitomator — distilling a book-length source into a knowledge pack

A book-length source lands in the wiki shape of any other ingest ([`memory-schema.md`](memory-schema.md)); what pages in, and what stays outside the install, is R9 and M9 ([`routing-policy.md`](../../fabius/references/routing-policy.md)). Below: only what a long source adds.

## 1 · Two routing keys, head first

Beside the page catalog keep a second key — the source's own vocabulary → page ids — so a question in the author's terms routes to its page without reading bodies. The pages loaded first — the two keys and the decision aid — run most load-bearing first (any partial read favours the head) and, under a size cap, are reserved before page bodies: the reserve-against-the-cap pattern of [`video-ingest.md`](video-ingest.md) §5.

## 2 · The capped decision aid

Rank entries by how directly they settle a choice: what says which action to take outranks what only helps recognise the situation. Fill from the top, stop at the cap. A line that only defines a term is never on it — definitions live on their term's page; the vocabulary key only routes there.

## 3 · Depth is derived, length is bought

Ask the intended use once — lookup or study — and derive depth from it. A longer page must add material the short one lacks — where the idea breaks, a procedure spelled out, or something worked through — never more words on the same points; with none of that it stays short, marked `sparse`.

## 4 · Ground before writing

- Before writing that the source contains a named concept, count its occurrences in the extracted text. Zero → drop it or mark it `unverified` (memory of the book is not the file) — the mechanical form of disciplina's [source-support rule](../../fabius-disciplina/references/architecture-decisions.md).
- Splitting by headings: a heading string repeats (contents list, running heads) — split at the match followed by the most text, not the earliest.
- Media the extractor could not read is disclosed before distilling and on the pack's index page.

## 5 · Boundaries

- A private study pack may keep the author's names for retrieval; anything entering Fabius doctrine is re-expressed.
- A pack distilled from a source the user does not own is private by default; the release test is the router's → [`skill-maintenance.md`](../../fabius/references/skill-maintenance.md) (Non-code sources).
- A pack someone else built is an artifact to adopt, not to trust → praesidium's [adoption gate](../../fabius-praesidium/references/supply-chain-and-ai-artifacts.md) (§3).

Informed by **book-to-skill** (virgiliojr94, MIT) — studied for a vocabulary routing key, a decision aid ranked by decision value, use-derived depth and occurrence-count grounding, re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
