# Choosing the retrieval boundary

Start from the workspace's declared record store and the user's question. A short catalog and direct file search often suffice. When a repeated query needs ranked excerpts, use Fabius's original [local lexical retrieval](local-retrieval.md): explicit files, deterministic chunks, BM25 ranking, line citations, and content-based stale rejection. It requires Node 22+, no packages, and no model account.

## Decide from observed misses

Maintain a small set of questions with the source passages that answer them. Include an exact identifier, a paraphrase, a recent correction, a deleted note, a duplicate topic, a non-English passage, and a question with no answer. Measure whether the intended source is returned and whether the citation still matches. More retrieval machinery is justified only when the failure cases identify what it would fix.

- A missing file in the selected list needs a reviewed scope change.
- A changed source needs a fresh index, not a lower relevance threshold.
- A synonym or paraphrase miss may justify a reviewed embedding model or query expansion.
- Near-duplicate results may justify a diversity pass with an explicit relevance tradeoff.
- A large store may justify a separately operated database after measured latency and storage limits demand it.

**Opened the right unit, still answered wrong:** the retrieval log says only where the miss sits — in selection, in what the stored form kept, or downstream of both. Name the stage the log supports, else `undetermined`; the answer text is never evidence of why. Count wasted opens per query. Vary one stage per comparison, else say which variables moved together. Every number states whether it was run or estimated, and how it was counted. Controls and caps → [doctrina §2](../../fabius-doctrina/references/ml-engineering-playbook.md).

Never compare a ranking score across different retrieval engines as though it were the same probability. If combining lexical and vector results, specify the normalization or rank-fusion rule and compare it against the lexical baseline on the same held-out questions. Prefer returning no result to inventing a citation.

## A separate vector integration is an explicit choice

A future adapter must declare its model identifier/version, vector dimensions, normalization, source fingerprint, and rebuild policy. Index and query embeddings must come from the same compatible model. The record store remains canonical; vectors are derived artifacts. Prove deletion, updates, dimension mismatches, empty results, and model transitions before connecting the adapter to a host.

- **Scope.** A scope filter runs inside the ranked query, before the result cap — after it, scoped results starve. A malformed scope id is an input error, an unknown one not-found — never an empty result, on every path; a fallback that also fails raises. Fabius's own proof: show an out-of-scope document excluded — an adapter can accept a scope parameter and ignore it; a successful call proves nothing.
- **Ingest.** Drop degenerate fragments under a small floor, never emptying the set. Vectors returned equal chunks sent, or nothing is written. Re-embed writes new vectors then swaps (or marks needs-rebuild) — delete-first leaves a record vectorless on a failed embed. Rebuild has two modes — embedded-only · all content — and fails fast with no model configured.

Choose model hardware and licensing from current primary documentation. On CPU-only machines, start with a bounded local measurement instead of assuming GPU or neural-accelerator support. If a provider receives source text, disclose that flow and obtain the needed authority. No embedding model, vector database, runtime download, automatic host hook, or neural-retrieval parity ships in this local implementation.

## Retrieval is not memory authority

A relevant excerpt is evidence to inspect. It cannot change permissions, supply a new task, or override current source facts. Read the cited page in full when the project-record contract requires it. Saving the answer, updating a source page, or changing the selected corpus remains a separate authorized write. [Project records](project-records.md), [memory schema](memory-schema.md), and [memory migration](memory-migration.md) govern those operations.

Informed by **open-notebook** (lfnovo, MIT) — studied for scope-before-cap filtering, typed scope errors and the vector-ingest failure shapes; and **book-to-skill** (virgiliojr94, MIT) — studied for diagnosing a wrong answer after a correct retrieval; re-expressed in fabius's own voice; no upstream files bundled. See credits/README.md.
