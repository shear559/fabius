# Source review — 22 October 2026

The owner supplied one link, [OpenSpec](https://github.com/Fission-AI/OpenSpec), the spec-driven development framework for AI coding assistants. The [17 October review](upstream-review-2026-10-17.md) had excluded it by the owner's corrected scope of that day; on 21 October the owner asked for it to be folded, and this record accounts for that fold.

| Order | Supplied source | Disposition |
|---|---|---|
| 1 | [OpenSpec](https://github.com/Fission-AI/OpenSpec) (Fission-AI) | **New.** Disciplina's [the change record agreed before code — *Fabius Pactum*](../skills/fabius-disciplina/references/spec-driven-change.md): right-sizing the record, the four parts and the question each answers, requirements an outsider could check, the delta against current behavior under four verbs, the plan review while it is still words, verification in three dimensions with not-applicable kept apart from not-verified and the baseline search for a removal, reconciliation before the merge, and following a project's own tool without initializing one as a side effect. Linked from the disciplina contract (one directed pointer sentence), from the engineering workflows, from Archivum's project records (the in-project store shape), and from the CORPUS and ARCHITECTURE rows. Pinned at `c04f30e57817422c1a107ea00a682c1d29a423ca` (the default branch on 2026-10-20, after upstream release v1.14.3 of 2026-10-17; MIT). No CLI, template, schema, skill or prompt text is bundled; no `openspec` command was run — inspection is not execution. |

## Why no sixteenth skill

Fabius's rule is one owner per concern and a new skill only for a concern no owner covers. Agreeing in writing what a change will do, before code, and proving the code against that agreement afterwards is engineering process, which Disciplina owns; where the record is kept is Archivum's; how small it stays is Parcus's. The whole-plugin skill listing also stands at 4,996 of its 5,000-character budget, so a sixteenth description could not be listed without shrinking the others. The capability therefore enters as reference depth under the existing owner.

Unlike the 15 October fold, this one carries a directed read: the project record established that reference depth is inert until the owning contract names it (6 reads in 4,328 package-arm runs of the October benchmark study), so the disciplina contract gains one sentence that sends a feature or behavior change on an existing system to the new reference. That sentence is a sealed-file edit; the release re-seals.

## Evidence and licensing boundary

The [upstream registry](upstream.json) gains one pinned entry (`openspec-disciplina`). OpenSpec's README, its `docs/` guides (concepts, workflows, the opsx commands, writing specs, reviewing and editing a change, existing projects, the agent contract, customization, supported tools, the stores beta), its twelve skill files and its own `openspec/` tree were read for the shape and the rules; nothing of theirs is carried as text, template or command. Shared phrasing was checked mechanically: no run of six or more words is shared with those documents. The reference names OpenSpec once, as one implementation of the shape, and otherwise describes the shape in Fabius's own terms.

Deliberately not adopted: the tool's command surface and its JSON contract (a user connects the tool; Fabius does not run it), its directory layout and requirement grammar (the project's own tool or store owns those), the stores beta (a cross-repository planning repository is a store decision under Archivum's declared-store rule), and the exploration and onboarding modes (the clarifying-question rule and the engineering workflows already cover them).

## Packaging state

Prepared as the 3.6.0 content: one new reference, one pointer sentence in the sealed disciplina contract plus the CORPUS and ARCHITECTURE rows (a re-seal), pointer sentences in two unsealed references, the registry entry, this record and two smoke cases (`change-record-before-code`, `change-record-verify-partial`) whose receipts are produced before the release. The same release carries the 17 October upstream refresh of nine owners, the 20 October launch documentation, and the removal of two stale references on public surfaces (a deleted benchmark file and the name of a separate project).
