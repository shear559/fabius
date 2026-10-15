# Source review — 15 October 2026

The owner supplied thirteen links. Twelve are the links of the [10 October review](source-review-2026-10-10.md), already folded into existing owners and shipped in 3.4.0; they are listed here in the supplied order with a pointer to that record and nothing was imported twice. One source is new.

| Order | Supplied source | Disposition |
|---|---|---|
| 1 | [claude-video](https://github.com/bradautomates/claude-video) | Folded 2026-10-10 (Archivum, video evidence workflow). No change. |
| 2 | [notebooklm-py](https://github.com/teng-lin/notebooklm-py) | Folded 2026-10-10 (Archivum, notebook connector). No change. |
| 3 | [Impeccable](https://github.com/pbakaus/impeccable) | Folded 2026-10-10 (Decor, design critique). No change. |
| 4 | [Agent Skills](https://github.com/addyosmani/agent-skills) | Folded 2026-10-10 (Disciplina, engineering workflows). No change. |
| 5 | [Archify](https://github.com/tt-a1i/archify) | Folded 2026-10-10 (Decor, explanatory diagrams). No change. |
| 6 | [Storytold](https://github.com/storytold) | Folded 2026-10-10 as its pinned ArtCraft repository (Decor, media composition). No change. |
| 7 | [Project NOMAD](https://www.projectnomad.us) | Folded 2026-10-10 (Archivum, offline knowledge). No change. |
| 8 | [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) | Folded 2026-10-10 (Decor, geospatial evidence). No change. |
| 9 | [YOLO v1](https://github.com/dahanyosi/yolo-v1) | Reviewed and excluded 2026-10-10 (satire). No change. |
| 10 | [Fish Audio](https://fish.audio) | Observed 2026-10-10 as commercial documentation (Decor, narration). No change. |
| 11 | [Storytold](https://github.com/storytold) | Duplicate of item 6. No change. |
| 12 | [Buzz](https://github.com/block/buzz) | Folded 2026-10-10 (Cohors, shared-channel agents). No change. |
| 13 | [REA — Reverse Engineer Anything](https://github.com/morluto/rea) | **New.** Disciplina's [reverse engineering with evidence](../skills/fabius-disciplina/references/reverse-engineering.md): the authorization boundary, the four evidence classes, routing from the named target, static before bounded runtime experiments, the investigation ledger, reconstruction proved by behavior, and the analyst-question rules for anyone building an analysis tool. Linked from Disciplina's engineering workflows and from Praesidium's routing table for security-motivated analysis. Pinned at `cf0a38ad9774ee9acff3164052688f7a58a1c72c` (MIT; its third-party notices keep their own licences). No code, tool catalog, engine, prompt or workflow is bundled. |

## Why no sixteenth skill

Fabius's rule is one owner per concern and a new skill only for a concern no owner covers. Reverse engineering for understanding and rebuilding is engineering investigation (Disciplina); the same analysis made for security is Praesidium's, under its defensive-only rule. The whole-plugin skill listing also stands at 4,996 of its 5,000-character budget, so a sixteenth description could not be listed without shrinking the others. The capability therefore enters as reference depth under the existing owner, reachable from the contracts' existing references.

## Evidence and licensing boundary

The [upstream registry](upstream.json) gains one pinned entry (`rea-disciplina`). REA's README and DISCLAIMER.md were read for the boundary it states; its agent skill (`.agents/skills/reverse-engineer-anything/`) and `docs/tool-design.md` for the method; nothing of theirs is carried as text. Inspection is not execution of the project; no REA command was run here.

## Packaging state

Prepared as the 3.5.0 content: one new reference, two pointer sentences in unsealed references, the registry entry, this record and a smoke case with its receipt. No sealed file changes; the seal stays at its 3.3.0 root.
