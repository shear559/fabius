<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-mercatus/SKILL.md -->

# Fabius Explorator — auditing an existing site's search presence

The audit method; what good looks like per layer stays in
[seo-and-discoverability.md](seo-and-discoverability.md). Every band, depth and table size here
is a starting default, declared in the report — never a law. Order of work: §2 (when
connected) and §5 gather · §1 verifies the positions a recommendation rests on · §3 chooses ·
§4 sizes · §6 only for a business with a physical location.

## 1 · Reading a position — the evidence contract

- A position that drives a recommendation is checked **live, in this job**. Cached and
  third-party rows guide discovery only.
- Before quoting a provider's rank field, establish whether it is absolute (counts every result
  block) or organic-only. State the position with its results page.
- Check to a **declared depth N**. Unseen → "outside the first N checked". A failed lookup
  → *unknown*, never *absent*.
- Log per check: query · market · language · date · organic listings returned · matched URL.
- Keep three dates apart: when fetched, when observed, when the volume metric was computed.
- Absence from a capped sample, or from a provider's rows, is absence of data — not a finding.
- Repeat the decisive checks. Two same-day checks that disagree are reported together as
  **spread** — never a trend, never a baseline.
- Co-occurrence proves nothing: similar copy with uneven positions, or a crawler warning
  beside a drop, establishes neither a penalty nor an indexing cause.

## 2 · First-party query data before paid discovery

When the site's own search-performance data is connected, start there; buy discovery after.
Its averaged position shortlists; a position quoted in a recommendation still passes §1 and
is reported beside the average — the live check dates it, never overrides it.

- **Near-ranking set:** collapse each query to the page that ranks best for it (impressions
  settle a tie); keep those in a declared band just off the first results, above a declared
  impression floor.
- If any page already serves the query near the top, lifting a lesser page gains nothing —
  drop the row.
- **Cannibalisation** is claimed only when one query's impressions are split across several
  URLs: list the query, the URLs and the keeper.
- An aggregate position is impression-weighted, never a plain mean of rows.
- Compare against the equal-length period immediately before.
- Lag, history floor, filter wrapping and pagination traps →
  [marketing-toolkit.md](marketing-toolkit.md) (dated).

## 3 · Families, shortlist, choice rule

**Families.** List the site's page families off the sitemap — a crawl sample misses whole
ones. Per family that can bring buyers, read the strongest page beside a weak or typical
sibling. The test: an answer to the searcher's decision, or a template with the name changed?

**Shortlist.** Before drafting, build a candidate table that spans more than one kind of move
— fix · build · defend · convert — each row carrying its evidence and what is still unknown.

**Choice.**

- Rank by strength of diagnosis times buyer relevance, not raw volume or ease; a single weak
  signal never carries a recommendation alone.
- Whatever stops pages being reached or indexed goes first — a retired domain whose
  replacement is live included.
- A page already near the top is defended, not rewritten.
- No candidate vanishes: each is recommended or rejected on the record with a concrete reason,
  and the report says why the second choice lost.
- A search competitor is not a business competitor: out-answer whoever holds the query, even
  if they sell nothing the client sells.

**Stopping** is the router's
([orchestration-doctrine.md](../../fabius/references/orchestration-doctrine.md) §5–6). One
job-specific clause: if a budget cut research short, name the comparison it prevented.

## 4 · Honest traffic sizing

A size claim shows its assumption, its baseline and its overlap, or it is labelled gross
potential (honest-claim rule: [seo-and-discoverability.md](seo-and-discoverability.md) §4). Say
whether the gain is new visibility or a better yield from visibility the page already has, and
net out what it already captures. Size one query cluster in one market; overlapping variants
are the same searchers, never a sum. Demand becomes visits only through a click-share
assumption the report shows, in a table labelled *hypothetical*. Conversion and revenue
figures come from the client or not at all. No defensible number → a directional call with
its reason.

## 5 · Crawl-audit honesty

1. **Classify each fetch first** — read · access-challenged · rate-limited · transport failure
   — and suppress every content finding for anything not actually read. A challenged page is
   "could not be audited", never thin or untitled (edge rule:
   [seo-and-discoverability.md](seo-and-discoverability.md) §6).
2. A crawl cut short is labelled **incomplete**; unfetched URLs are never marked broken.
   Pacing and back-off are machina's
   ([automation-toolkit.md](../../fabius-machina/references/automation-toolkit.md)).
3. Status-class checks precede content checks; content checks run on HTML documents only.
4. Read index directives from the meta tag **and** the response header; read the canonical
   from the HTML link **and** the `Link` header. Disagreement is its own finding — the engine's
   choice is then unpredictable. `noindex` and canonicalised-elsewhere are notices, not errors.
5. Duplicate groups exclude owner-deduplicated, non-200 and empty pages.
6. One finding per redirect chain, from its head; a second pass catches headless cycles.
7. Orphan = reachable only through the sitemap.
8. The audit's home origin is the start URL's **final** one, after redirects.

Order findings by what they block: anything that stops a page being read or reached outranks
how a readable page is duplicated or directed, which outranks cosmetic notices.

## 6 · Local / map visibility

Its own evidence base: never read map-result strength from national organic data, and keep
two winner lists — organic pages, map listings.

Two dependencies bind. Identify the listing by its stable platform id before any lookup —
never by name. Spend on a position grid only after the listing-level comparison, and only to
tell storefront-only reach from area-wide reach and who leads where the target does not.
Compare the facts the owner controls before the signals they earn; fix the former before any
activity cadence, and confirm the listing links to that location's own page.

- Verify the grid centre is the storefront before paying.
- Read a blank grid point against how many results it returned: a full set means outranked,
  a thin one means few results exist there.
- A grid bills per point — quote size and cost first, start small.
- Chains: snapshot every location, deep-dive a few chosen with the user.

Prohibited: any manufactured listing signal — reviews or names engineered for rank (the
*don't game* rule of [seo-and-discoverability.md](seo-and-discoverability.md), *When NOT to
optimize*).

Informed by **open-seo** (every-app, MIT; commit 0ffff93) — studied for position-evidence conventions, first-party query analysis, audit shortlisting and sizing, crawl-outcome classification and the local-listing procedure, re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
