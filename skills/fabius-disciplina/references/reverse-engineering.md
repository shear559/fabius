<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-disciplina/SKILL.md -->

# Understand software you cannot read — reverse engineering with evidence

Use when the behavior to explain, match or rebuild lives in a shipped artifact — a native binary, a packaged JavaScript or Electron app, a managed assembly, a mobile package, firmware, a recorded capture — and the available source does not establish it. For a complete source repository, use ordinary code tools; opening a disassembler on code you can read is waste. Disciplina owns the investigation and the rebuild; `fabius-praesidium` owns any analysis made for security (malware, vulnerabilities, incident forensics) and the boundary below applies there without exception.

## 1 · Establish authorization before the first byte

Lawful analysis is interoperability, preservation, debugging or auditing software you own or are authorized to examine, education, and security research inside an agreed scope. Possessing a file, finding a public download or reaching a debugging endpoint establishes none of that. Before opening a target, name the authority: ownership, a licence that permits the analysis, a written engagement, or a legal exception for interoperability that applies in the user's jurisdiction — and state it in the plan.

Refuse, and say why, when the purpose is to circumvent DRM, licence checks, anti-cheat or other technical protection, to bypass authentication or access controls on systems the user is not authorized to test, to build cheats or tamper with a live service, or to copy protected code and assets into another product. Understanding how a feature works and building one's own is engineering; lifting the original's code or assets is not.

Authorization to inspect an artifact does not authorize executing it, attaching to its runtime, intercepting its traffic or changing a device; each of those is its own grant. Commercial engines (IDA, Hopper, JEB) must be legitimately licensed by the user; a trial's terms bind the output too. A decompilation or a report grants no rights to the original program, and generated output may carry the original's rights — check before publishing or shipping it.

## 2 · Route from the target the user named

Pick the first instrument from the artifact in hand, not from habit:

| Target | First look | What it yields |
|---|---|---|
| Packaged JavaScript or Electron tree, ASAR | static module graph | modules, imports, source maps, IPC and preload boundaries, native add-on edges |
| Archive or package (zip, apk, ipa, dmg, installer) | member inventory and digests | what shipped, resources, plists, nested artifacts |
| Managed assembly (.NET) | metadata and CIL | types, methods, declared native dependencies |
| Android package | manifest, classes, decompiled methods | declarations, entry points, incoming references |
| Native binary | a read-only engine (Ghidra, Hopper, IDA, objdump, Rizin) | strings, symbols, call graph, pseudocode |
| Firmware image | region map, then extraction into a fresh directory | file systems, kernels, embedded binaries for native hand-off |
| Running app, page, process | a bounded capture (§4) | network, IPC, UI and filesystem observations with declared effects |
| Saved capture (HAR, pcap, logic trace) | the recording itself | requests, fields, repeated values — never a claim about live traffic |

"My app" without a name, path or already-selected target is a question, not a search: ask which. A path found in an unrelated report, a fixture or a nearby test does not select the user's target, and an example app is never chosen on the user's behalf.

## 3 · Keep four kinds of statement apart

Every finding is one of: an **observation** (bytes, symbols, a captured request — with the artifact's identity and the location in it), a **derivation** (a decoded structure, a reconstructed call path), an **inference** (what the code probably does, from naming, constants or shape), or an **unknown**. Write which it is. Missing coverage is unknown, not absence: an engine that could not resolve a callee did not prove there is none; a static read never observed execution. Completeness is derived from what was examined — the functions traced, the modules walked, the search bounds — never from an empty failure list.

Carry provenance with every conclusion: the artifact's digest, the engine and its version, the procedure address or module id, the capture's identity. Keep the complete evidence reachable and quote the smallest piece that answers the question; summary first, then the one function or module that the summary left open. Do not repeat an identical analysis hoping for a different answer; change an input or resolve the blocker first.

## 4 · Static before runtime; runtime is a bounded experiment

Static inspection reads files without running anything and answers most questions. Reach for execution only when static evidence cannot settle the question and the host, OS access and authorization exist. Then design the experiment before running it: the exact target and lifecycle (launch or attach, how it ends), the declared effects on processes, files, network, UI and devices, the environment (an untrusted target runs in one built for it), what will be observed, and how the observation is read back. A plan that was not executed establishes nothing about runtime behavior, and a probe against the real app establishes only what that run showed. A process capture is opt-in behavioral evidence, not a sandbox: it does not contain the target.

Engines stay read-only: analysis databases are ephemeral or private, an attached GUI database is never saved or closed on the user's behalf, and the executable's bytes are never modified. Evidence keeps the user's selected inputs and local facts (paths, URLs, digests); transport credentials and values the user marked sensitive are redacted, and secrecy is not inferred from a name or a pattern. The ambient environment is not persisted into a record merely because a child process inherited it.

## 5 · The investigation loop

1. **Question.** Turn the request into a checklist: each question, and the kind of evidence that would answer it. Resolve the target's identity from the conversation and workspace before asking again.
2. **Reuse.** Check what is already known — open sessions, saved analysis, bookmarks, prior evidence. Do not open a duplicate session or repeat an identical analysis.
3. **Overview, then trace.** Start from the smallest useful inventory, follow each question from its entry point through the data and state it touches to its result, and batch the reads around one hypothesis; widen only when the returned evidence leaves a concrete gap. Read packaged resources and configuration beside the code when they shape the answer; a filename, a string or a layout alone is not behavior.
4. **Corroborate with the evidence type the claim needs.** A derivation from pseudocode is confirmed by a second path to the same fact, or by a bounded runtime observation; a match between a static pattern and a runtime event is a hypothesis until the mapping is explicit. A conclusion about a version difference is confirmed by comparing the two artifacts' identities over comparable coverage and reporting only supported deltas; a static difference is a candidate cause of changed behavior, not proof of it, and absence is unknown wherever the compared frontier is incomplete.
5. **Divide only when independent.** Split questions across parallel workers when they do not depend on one another; give each a distinct scope and the existing evidence, and ask for sources, conclusions and unresolved gaps back. Otherwise work sequentially.
6. **Ledger.** Keep one finding ledger: each conclusion with its evidence references, its kind (§3), its search boundary and its remaining unknowns, written so a later pass starts from it instead of from zero.
7. **Close against the checklist.** Mark every question answered, partially answered or unresolved by its evidence. A bounded negative search stays bounded in the report, and a broad investigation is not called complete while a required question is open.

## 6 · Rebuild from understanding, prove by behavior

When the request is to build the feature, the hand-off from investigation to engineering is a written specification of observed behavior — inputs, outputs, edge cases, the exact formats and constants that were observed — separated from the design choices the new implementation makes. The new code is Fabius's own; it does not transcribe the original's decompilation.

A reconstruction is finite and verified against evidence, not by resemblance: a case set drawn from the original's observed behavior (hundreds or thousands of inputs where the function is numeric), byte-exact comparison where the output is bytes, and a named list of the cases that were not covered. A pass covers the declared comparable claims and nothing more; it is never global equivalence. Residual unknowns are audited, not forgotten: list each unknown head, the evidence that would resolve it and whether it affects the rebuilt behavior. The verdict is pass, fail, blocked or skip, with what was not verified on its own line, as the engineering contract requires.

## 7 · If you build an analysis tool for agents

Design around the analyst's question, not the engine's API. Prefer primitives that report a reusable fact about an identified object (inspect, search, trace, compare, observe) and compose workflows only where repeated use shows a joined outcome; keep a format-specific decoder in, and one application's business interpretation out. Return the requested facts inline with artifact and provider identity, locations, coverage and limitations, so the caller needs no second lookup to understand provenance; keep observed, derived and inferred relationships distinct in the result. Declare effects truthfully; add limits only for real format, protocol, authority or measured resource constraints, report pagination, truncation and partial failure, and never let an assumed token budget stand in for a measured one. Spend in this order: the agent's tokens and context first (the smallest sufficient answer with its provenance), then analysis time (cached results keyed on every result-affecting input, with freshness checked before a cached state is reported as current), then CPU and memory.

Informed by **REA — Reverse Engineer Anything** (morluto/rea, MIT; its third-party notices keep their own licences), commit `cf0a38ad9774ee9acff3164052688f7a58a1c72c`, inspected 2026-10-15 — the evidence classes, the authorization boundary, target routing, bounded runtime experiments, the investigation ledger, reconstruction verification and the analyst-question tool rules, re-expressed as Fabius's own procedure. No REA code, tool catalog, engine, prompt or workflow is bundled; the project is a tool a user may connect, not a dependency. See credits/README.md.
