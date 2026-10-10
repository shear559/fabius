<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-archivum/SKILL.md -->

# Offline knowledge — prove the corpus survives disconnection

Use when a corpus must remain searchable without an external service. Archivum owns completeness, provenance, freshness and recovery; `fabius-disciplina` owns deployment, `fabius-doctrina` model selection, `fabius-praesidium` access controls. No server or library is bundled.

## Define the offline promise

Name the required questions, period without updates and target machine. Downloaded documents, a searchable index and an answer model are separate capabilities. Audit remote model calls and first-run downloads before promising offline operation.

Keep a corpus manifest: source URL/id, edition date, retrieval date, licence, path, hash, format, scope and omissions. A downloaded catalog does not prove its collection is present. Readable originals stay canonical; chunks, vectors and summaries are derivatives.

## Prepare and inspect while connected

1. **Budget against the machine.** Measure disk, RAM, CPU and actual accelerator support. Budget corpus, model, index, extraction and an update copy separately. Measure retrieval and inference latency separately. Fitting on disk does not prove the model fits in memory. Use direct reading or lexical retrieval when sufficient.
2. **Track readiness per source.** Distinguish downloaded, readable, extracted, indexed, failed, stalled and browse-only. Reconcile expected files, successful parses and indexed ids; vector presence alone cannot prove completeness. Inspect representative passages, OCR and tables; expose missing pages and partial extraction.
3. **Bind the index to its inputs.** Record source hashes, parser/chunker versions, embedding model and dimensions. Changed inputs mark affected results stale until verified rebuild. Preserve browse-only choices across updates. Verify replacements before switching, or mark needs-rebuild; never silently query mixed versions.

## Verify with the network unavailable

Block external access within an authorized test boundary, preserving the intended local network. Use a fresh client and restart services so warm caches cannot hide missing assets. Record these probes:

| Probe | Pass observation |
|---|---|
| Known passage and exact identifier | Correct local source and locator open without an external request |
| Paraphrase and cross-document question | Relevant evidence returns; unsupported synthesis is marked as such |
| Missing or excluded source | Honest no-answer or unavailable result, never a fabricated citation |
| Updated or removed document | Old index entries are rejected or visibly stale; current citation matches current bytes |
| Model unavailable | Reading/search still works if promised; generation reports its dependency |

Retain the manifest, commands, output and gaps. A loaded UI does not prove retrieval works. Display the source date so offline evidence does not appear refreshed today.

## Prove recovery before relying on it

Back up originals, manifest and non-secret configuration; record index rebuild steps and required models. Restore into a fresh location without overwriting the working store, compare hashes, resolve links and repeat the disconnected queries. Report recovery time only when measured.

Review any external server's OS, downloads, privileges and exposure separately: offline-oriented software may probe connectivity or omit authentication. Retrieval choices → [retrieval-stack.md](retrieval-stack.md); record authority → [memory-schema.md](memory-schema.md).

Informed by **Project NOMAD** (Crosstalk Solutions, Apache-2.0), commit `54ee30a44902e5c252b477f8685c26ec3064ab72`, inspected 2026-10-10 — offline collections, ingest states and source replacement, re-expressed as Fabius's own readiness and recovery workflow; no upstream files, applications, models or packs bundled. See credits/README.md.
