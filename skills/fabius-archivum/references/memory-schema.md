# Fabius Archivum — wiki schema & conventions

Loaded on demand by `fabius-archivum`. The skill has the loop; this file has the concrete directory schema, the page conventions, and the line formats for the two navigation files.

**Write authorization precedes this schema.** Create or mutate these files only when the workspace opted into Archivum memory and the current request/contract authorizes the write. A read-only query returns a proposed record/diff instead. Preserve history: append log/decision events and supersede stale records; delete only a recoverable, unambiguous duplicate created in the current run.

## Directory schema

```
knowledge/
  index.md          # catalog: every page, its link, a 1-line summary, metadata. READ FIRST.
  log.md            # append-only, prefixed, chronological. grep/tail with unix tools.
  entities/         # one page per concrete thing (a project, a person, a system)
  concepts/         # one page per idea or pattern
  comparisons/      # X-vs-Y pages
  syntheses/        # answers worth keeping, filed back from queries
  raw/              # immutable source-of-truth docs — read, never edit
```

Scale this *down* for a small base: a flat folder of pages plus `index.md` and `log.md` is enough. Don't build the subdirectory tree before the page count demands it (`fabius-parcus`: the structure shouldn't exist until the pages do).

## Page frontmatter

```yaml
---
name: stable-kebab-slug          # the id AND the filename: a wikilink resolves by filename, never by this field
description: one line — this is what index.md shows for retrieval
type: entity | concept | comparison | synthesis | preference   # preference pages file under concepts/ (cross-project tier), never on a project page
updated: 2026-06-21              # absolute dates only, never "last week"
source: stated | inferred        # preference/agreement records only
consented: 2026-06-21            # protected-category facts only — the date the user asked for the record
---
```

Body: the fact or synthesis. Link related pages liberally with `[[slug]]` — a link to a page that doesn't exist yet is a valid forward marker, not an error.

A preference or lesson record states what the user holds and why — *migrations land under review before the code that depends on them; one release went the other way and paged everyone* — in the only form M12 can weigh: a witness, not a command. Written as an instruction, the record returns next session with an authority the store never had and pulls against the live request; the write side therefore matches the read side. Record a choice the user let stand as readily as one they reversed — a store fed only by reversals teaches every later session to hedge. `source:` says whether the user stated the fact or fabius inferred it from observed behaviour: a stated record is `[pin]`ned under the [never-drop floor](external-recall.md#the-never-drop-floor); an inferred one is provisional (acting on it, `fabius-parcus` names the assumption), and a stated record beats an inferred one whenever they conflict — recency breaks ties only between records of the same provenance (the newest verified value, per [`../SKILL.md`](../SKILL.md#auto-recall--surface-memory-without-being-asked)).

**What never enters the store without consent.** The write gates ask *may I write* (the authorization above) and *is it worth writing* (M7); one class of fact also needs *did the user ask for this to be kept*. Three classes need it: a fact that can be used to discriminate (a protected personal category — belief, origin, orientation, a status of residence or membership), one that can be used to impersonate or defraud (a state-issued or account identifier), and one that locates or diagnoses the person (where they live, what they are treated for). Each enters only on the user's explicit ask, carries `consented:` with the date of that ask, and is never inferred to round out a profile — verified, reusable and non-obvious still leaves it out uninvited. The ask unlocks a fact, never a credential: secrets stay out even on request, per [`external-recall.md`](external-recall.md#when-memory-must-be-a-tool-use-the-standard-one) and `fabius-praesidium` (*No secret in the artifact* — a memory page is an artifact). The gate is regime-neutral; the local statute's own sensitivity list stays with `fabius-decor` [`israel-localization.md`](../../fabius-decor/references/israel-localization.md).

## index.md line format

```
- [Title](entities/thing.md) — one-line hook (type, updated)
```

Read the index before reading any page. Index-based retrieval scales to hundreds of pages without loading them — the index is small, the pages are not.

## log.md line format

```
2026-06-21 INGEST  added entities/vector-index.md; revised concepts/retrieval.md
2026-06-21 QUERY   "how does X scale" → filed syntheses/x-scaling.md
2026-06-21 LINT    archived 2 duplicate orphans; superseded 3 stale claims
```

One prefix per operation (INGEST / QUERY / LINT), one line per event. Grep the log to reconstruct what happened and when, with no tooling beyond `grep` and `tail`.

## Ranked retrieval over explicit source files

Use the original [local retrieval tool](local-retrieval.md) when a recurring question benefits from ranked excerpts. It requires an explicit absolute root, selected Markdown/text files, and a local index destination. Its BM25 results carry source paths and line ranges; changed bytes or missing files reject a stale index before results are returned. It installs no dependency and scans no directory automatically.

For semantic misses or larger-scale storage, use the [retrieval decision guide](retrieval-stack.md). The local tool does not implement embeddings, quantized vectors, or external database adapters. Keep the source pages canonical and every retrieval artifact reproducible from the permitted selection.

## Why maintenance stays near zero

Inside an authorized, opted-in store, the agent does the bookkeeping — summarize, cross-reference, file back, and lint. Outside it, offer the record without mutation.

## Per-project opted-in memory (the cross-session contract)

For a project that opted in, memory lives *with the project* and fabius tends it within the authorized contract. This is the in-project shape only — where one store serves many projects, the topology, the read gate and the write-back contract are in [`project-records.md`](project-records.md), and no second store is created beside it:

```
<project>/
  MEMORY.md           # the index: live URLs, stack, current goal, open threads, links to pages. READ FIRST, every session.
  wiki/
    log.md            # append-only: one line per session/decision/fix
    decisions/        # why we chose X over Y (the thing the code never records)
    gotchas/          # the traps that cost an hour; how to avoid them next time
    <topic>.md        # architecture, domain, integrations — one page per thing
```

Small project → collapse `wiki/` into a flat folder beside `MEMORY.md`. Don't build the tree before the pages exist.

### `MEMORY.md` template (scaffold only after opt-in)

```markdown
# <Project> — memory

> Read this first. Update on every milestone. Plain markdown — open in Obsidian if you like.

- **Live:** <url> · **Stack:** <one line> · **Repo:** <url>
- **Goal now:** <the current objective>
- **Open threads:** <what's unfinished, with the next step>

## Index
- [Architecture](wiki/architecture.md) — how it fits together
- [Decisions](wiki/decisions/) — why, not just what
- [Gotchas](wiki/gotchas/) — traps + avoidance
- [Log](wiki/log.md) — chronological
```

### The authorized loop, applied to a project

1. **Session start** — if the index exists and the recall dial permits, read it. If absent, offer setup once; do not scaffold implicitly.
2. **On a milestone** — when ongoing memory writes are authorized, update current state and append one `log.md` line. Supersede old decisions; never erase their reason or event history.
3. **Session end** — under the same authorization, refresh `Goal now` + `Open threads` so the next session opens mid-stride.
4. **Periodic lint** — link orphans, mark contradictions, and supersede stale claims; do not silently rewrite history.

### Three session-memory hygiene rules

- **Dump before compaction.** When a large tool output — a fetched page, an API response, a research result — will be needed later, write it to a memory file *immediately*: compaction/truncation destroys unpersisted tool results mid-session. This is the store-side twin of the pre-compaction lifeboat in [`external-recall.md`](external-recall.md).
- **Bookkeeping files are marked, not hidden.** Prefix them (`_index.md`, `_meta/`) and skip that prefix in the store's read rule — nothing can hide a file from `ls`, so the convention has to be explicit.
- **Cap the auto-maintained index** at a fixed entry count (~50); regenerate it and inject it every turn, so the model always knows *what memories exist* without reading them. Past the cap, consolidate rather than append.

### Obsidian onboarding steps (offer once, never block)

The vault is just the project's memory folder — no migration, no export:

1. Install Obsidian (obsidian.md) — free, local, no account.
2. *Open folder as vault* → pick the project's `wiki/` (or the project root).
3. Enable **Graph view** (see the link structure) and the **Dataview** community plugin (query frontmatter — e.g. list every page by `updated`).
4. Done. fabius writes the markdown from the conversation; the human browses, follows `[[links]]`, reads the graph. If they'd rather not install anything, the same files work with `grep` + any editor.

Informed by **system_prompts_leaks** (asgeirtj, CC0-1.0 compilation; the collected vendor prompts remain their vendors' text) — studied for declarative preference records with a stated-vs-inferred provenance, confirmations recorded like corrections, and the consent gate on protected-category facts, re-expressed in fabius's own voice; no prompt text carried, nothing bundled. See credits/README.md.
