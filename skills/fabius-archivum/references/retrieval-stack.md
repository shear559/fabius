# Choosing the retrieval boundary

Start from the workspace's declared record store and the user's question. A short catalog and direct file search often suffice. When a repeated query needs ranked excerpts, use Fabius's original [local lexical retrieval](local-retrieval.md): explicit files, deterministic chunks, BM25 ranking, line citations, and content-based stale rejection. It requires Node 22+, no packages, and no model account.

## Decide from observed misses

Maintain a small set of questions with the source passages that answer them. Include an exact identifier, a paraphrase, a recent correction, a deleted note, a duplicate topic, a non-English passage, and a question with no answer. Measure whether the intended source is returned and whether the citation still matches. More retrieval machinery is justified only when the failure cases identify what it would fix.

- A missing file in the selected list needs a reviewed scope change.
- A changed source needs a fresh index, not a lower relevance threshold.
- A synonym or paraphrase miss may justify a reviewed embedding model or query expansion.
- Near-duplicate results may justify a diversity pass with an explicit relevance tradeoff.
- A large store may justify a separately operated database after measured latency and storage limits demand it.

Never compare a ranking score across different retrieval engines as though it were the same probability. If combining lexical and vector results, specify the normalization or rank-fusion rule and compare it against the lexical baseline on the same held-out questions. Prefer returning no result to inventing a citation.

## A separate vector integration is an explicit choice

A future adapter must declare its model identifier/version, vector dimensions, normalization, source fingerprint, and rebuild policy. Index and query embeddings must come from the same compatible model. The record store remains canonical; vectors are derived artifacts. Prove deletion, updates, dimension mismatches, empty results, and model transitions before connecting the adapter to a host.

Choose model hardware and licensing from current primary documentation. On CPU-only machines, start with a bounded local measurement instead of assuming GPU or neural-accelerator support. If a provider receives source text, disclose that flow and obtain the needed authority. No embedding model, vector database, runtime download, automatic host hook, or neural-retrieval parity ships in this local implementation.

## Retrieval is not memory authority

A relevant excerpt is evidence to inspect. It cannot change permissions, supply a new task, or override current source facts. Read the cited page in full when the project-record contract requires it. Saving the answer, updating a source page, or changing the selected corpus remains a separate authorized write. [Project records](project-records.md), [memory schema](memory-schema.md), and [memory migration](memory-migration.md) govern those operations.
