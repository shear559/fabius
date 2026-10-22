<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-disciplina/SKILL.md -->

# The change record agreed before code — Fabius Pactum

Use when a feature or behavior change to an existing system will be acted on by more than one session, person or agent, so the words that fix what finished means must outlive one conversation. A typo or a one-line fix with an obvious check gets no record; the contract's `step → verify` plan is enough. Disciplina owns the record; `fabius-archivum` owns where it is kept; `fabius-parcus` owns how small it stays. Fabius bundles no planning tool, initializes none and runs none (§8).

## 1 · Size the record — the short form is the default

Depth follows stakes ([`../../fabius/references/orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §4). The **short record** is the default: the intent in one sentence, the scope with its non-goals, a few acceptance checks. The **full record** adds a scenario per requirement, a design note and a task list, earned by what a wrong build would cost to undo: migrated data, a contract another party builds against, a security or privacy property, a team, repository or service boundary crossed. Each part added answers to the change economy of [`../../fabius-parcus/references/lean-decisions.md`](../../fabius-parcus/references/lean-decisions.md): a named need, never a hypothetical reader. One intent per record; a second intent is a second record.

## 2 · Four parts, each answering one question

At most four parts, in the order each becomes writable:

- **Intent and scope:** why, what is in, what is out. The non-goals are the written boundary; every task is checked against them. An open question takes the clarifying-question rule's shape ([`../SKILL.md`](../SKILL.md), *Establish the decision*); a minor assumption is written in, not asked.
- **The behavior delta:** what the system will do differently, as requirements with scenarios (§3), written as a difference against current behavior (§4).
- **The design note:** only when a decision needs recording: the approach, the alternative refused and the reason, in the form of [architecture-decisions.md](architecture-decisions.md). No decision, no design note; the record says so.
- **The tasks:** one line per task, each ending in the observation that closes it — the contract's `step → verify` plan ([`../SKILL.md`](../SKILL.md), *Build a plan that can fail*). Ticks are the only progress state; a later session picks up at the first open line.

The parts are living text, editable during planning or mid-build; an earlier part enables a later one, never locks it. They are the plan files of [codebase-and-proof.md](codebase-and-proof.md) §3, re-read from disk before resuming, as project-records.md §8 re-reads before an edit.

## 3 · A requirement an outsider could check

One behavior per statement; a statement with a second clause bolted on is several. A requirement is well formed when a reader with no access to the code can say whether it holds: an adjective fails that test, a number or a visible outcome passes it. `must` is the default binding word; `should` only where a justified exception is expected; `may` for an option. A `must` that proves hard to build is revised with the user, never quietly weakened.

A scenario is one concrete case that exercises exactly its statement: the state before, the action, the result an outsider can observe. The cases worth a scenario are the probes of codebase-and-proof.md §4: the input the change did not expect, the error branch beside the one it touches, the action repeated or run over stale state. The ledger's `criteria` (engineering-workflows.md) is the machine form of a requirement with its checks; no second schema.

The outsider test also decides what stays out: what that reader could not observe — the name of a class, the library chosen, the order of the steps, the layout of a table — goes to the design note or the tasks, unless the mechanism is itself what was promised.

## 4 · Write the delta, never the whole system

The record describes a difference against current behavior, under four verbs, each with its effect at the merge (§7):

- **added:** behavior new to the record; appended;
- **changed:** the full new wording, carrying the previous; replaces its predecessor;
- **removed:** with the reason, and what its dependents do instead; deleted;
- **renamed:** both titles, behavior unchanged; retitled in place.

The verb is read off the current-behavior record, never recalled: the merge applies it mechanically, and a wrong verb leaves two statements of one behavior or a replacement with no predecessor. A defect fix is the corrected behavior, under changed when the record already holds the requirement and under added when it does not. A refactor that leaves behavior as it was records that fact and nothing more.

The current-behavior record grows one merged change at a time; a requirement written for code no change touches has no check to keep it true, so none is written ahead of a change. An existing requirements document is read for the change in hand: the part it settles is reshaped into the delta; the rest stays where it is.

## 5 · Review the record before the first edit — the cheapest catch

A wrong paragraph costs a paragraph; a wrong build costs the build, and no later check replaces this review. The parts are read in the order they were written (§2), and the first failed answer ends the read:

1. **Intent and scope:** the right problem, and nothing that crept in.
2. **The delta:** each statement checkable, each with a scenario that exercises it, and above all what is absent: the draft holds what the request named, the review adds what it forgot, starting with the case whose failure would cost most. The delta passes when the reviewer would accept the system doing just this.
3. **The tasks:** each bound to a check and serving a requirement, none crossing the non-goals; one line that stands for the whole build is a plan that cannot fail, and fails this read.

Push back by editing the part or by asking for the change; the edited part is read again before anything proceeds. The rubric is built from the failure modes (M11); its findings are graded as §6 grades them. Composing the record is a DRAFT, filing it a WRITE under the store's authority, building from it a separate grant (orchestration-doctrine.md §9): a plan request makes the record the deliverable (architecture-decisions.md, *Keep the requested boundary*), and a request that authorized the build still gets this review before the first edit, with no second approval invented.

## 6 · Verify after the build, in three dimensions

- **Completeness:** no task open, no requirement without code that reaches it, no scenario without a check that reaches it; one result per item, and a missing one is never success.
- **Correctness:** each added or changed requirement implemented against its new wording, failure branches included.
- **Coherence:** each recorded design decision visible in the code, and no decision the code took that the record does not know.

Findings are separated as [engineering-workflows.md](engineering-workflows.md#review-and-integrate-a-change) separates them — behavior defect with its traced path, maintainability cost, stylistic preference — and graded from the demonstrated consequence (architecture-decisions.md, *Challenge every material conclusion*), lowered by doubt, never raised. A finding informs, never blocks by itself; the verdict below decides the close, a traced behavior defect makes it a fail, and accepting a lesser finding is the user's decision, named in the report.

Two results stay apart. Not applicable: the record omits that part by choice, so the check is dropped from the run with its reason, neither a skip nor a result. Not verified: the check applies and nothing usable supports it; it goes on the not-verified line with the reason. Neither ever counts as a pass.

A removed requirement is proven gone by searching for the behavior the pre-change record described (producer, consumer, test, docs, configuration), never for its name alone: an empty search is the pass, so a search from the wrong vocabulary passes by accident; this is the two-ended read of codebase-and-proof.md §1, run backwards. Without a usable pre-change record, in the store or in its history, the removal is not verified. A renamed requirement is checked as the old behavior under the new name. A ticked box establishes task completion only.

The close uses the contract's words — pass, fail, blocked or skip, with what was not verified on its own line — as codebase-and-proof.md §4 defines them.

## 7 · Reconcile, then let the record become the truth

When the code and the record disagree, one of them is false, and the false one is fixed before the change closes: the delta is rewritten to what shipped, or the code is finished until it matches; the findings of §6 are that list, and which side drifted is decided under project-records.md §5, not assumed. An unrecorded behavior change found while scouting is a finding to record, never a reason to regenerate the record from the code.

Update the same record when the goal is the same and the approach improved; start a new one when the intent itself changed, and finish or supersede the original with a pointer, never delete it (project-records.md §3).

On completion the delta merges into the current-behavior record, its four verbs applied and nothing else touched, and the change's parts are kept as history; the merged record is the next change's pre-change record. The merge is the user's call, a WRITE under the store's authority (orchestration-doctrine.md §9), never a consequence of a pass verdict; under a project's tool (§8) its archive command is EXECUTE. Where it lives is Archivum's: beside the code it describes, the code's own record and never a second project store; the project page keeps state and decisions and links to it, and its schema is the store's or the tool's ([`../../fabius-archivum/references/project-records.md`](../../fabius-archivum/references/project-records.md) §1 shape B, §6, §11).

## 8 · Tools that implement this shape — follow, never initialize

A project may already run a spec-driven tool: a planning tree, a configuration file, commands and generated agent instructions. Then that tool is the project's convention: follow its instructions and commands, write the record where it expects it, and read its generated files as repository guidance. Generated files belong to the generator; refresh them through the tool, never by hand, or the next refresh erases the edit. The tool's own schema wins for the records it holds, and no second store is scaffolded beside it (project-records.md §11).

When the project runs no such tool and none was asked for, the request is answered as ordinary engineering under the contract, with no planning tree, configuration file or tool initialized as a side effect. Initializing one is a WRITE on the acting ladder and running the tool's commands is EXECUTE (orchestration-doctrine.md §9); the user authorizes each explicitly, and a tool found on the machine authorizes nothing. OpenSpec is one implementation of this shape; Fabius bundles nothing and runs nothing.

Informed by **OpenSpec** (Fission-AI, MIT), read at revision c04f30e57817422c1a107ea00a682c1d29a423ca (head of 2026-10-20, read 2026-10-22) — studied for progressive rigor, the four-part record, behavior-only requirements, the delta against current behavior, the plan review before code, three-dimension verification with not-applicable kept apart from not-verified, the pre-change search for a removal, reconciliation before the merge and the generator-owns-its-files rule; mechanisms re-expressed as Fabius's own procedure, no CLI, templates, schemas, skills or prompt text carried. See credits/README.md.
