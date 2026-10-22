<!-- © 2026 shear559 · fabius · reference depth for skills/fabius-disciplina/SKILL.md -->

# The change record agreed before code — Fabius Pactum

Use when a feature or behavior change to an existing system will be acted on by more than one session, person or agent, so the words that define "done" must outlive one conversation. A typo or a one-line fix with an obvious check gets no record; the contract's `step → verify` plan is enough. Disciplina owns the record; `fabius-archivum` owns where it is kept; `fabius-parcus` owns how small it stays. Fabius bundles no planning tool, initializes none and runs none (§8).

## 1 · Right-size the record — the short form is the default

Depth follows stakes ([`../../fabius/references/orchestration-doctrine.md`](../../fabius/references/orchestration-doctrine.md) §4). The **short record** is the default: the intent in one sentence, the scope with its non-goals, a few acceptance checks. The **full record** (a scenario per requirement, a design note, a task list) is earned by a change that crosses a team, repository or service boundary, alters a contract or an API, migrates data, touches security or privacy, or would be expensive to redo. The dial is the cost of a mistake, never the size of the diff. Each part added answers to the change economy in [`../../fabius-parcus/references/lean-decisions.md`](../../fabius-parcus/references/lean-decisions.md): a named need justifies it; a hypothetical reader does not. One intent per record; a second intent is a second record.

## 2 · Four parts, each answering one question

At most four parts, in the order each becomes writable:

- **Intent and scope:** why, what is in, what is out. The non-goals are the written boundary; every task is checked against them. An open question takes the clarifying-question rule's shape ([`../SKILL.md`](../SKILL.md), *Establish the decision*); a minor assumption is written in, not asked.
- **The behavior delta:** what the system will do differently, as requirements with scenarios (§3), written as a difference against current behavior (§4).
- **The design note:** only when a decision needs recording: the approach, the alternative refused and the reason, in the form of [architecture-decisions.md](architecture-decisions.md). No decision, no design note, and the record says so.
- **The tasks:** one line per task, each ending in the observation that closes it — the contract's `step → verify` plan ([`../SKILL.md`](../SKILL.md), *Build a plan that can fail*). A group's checks sit inside the group, never in a final group that gets skipped. The tick state is the progress record; a later session resumes at the first unticked line.

The parts are living text, editable during planning or mid-build; an earlier part enables a later one and never locks it. The agent re-reads them from disk before resuming, because the user edits them too (the plan files of [codebase-and-proof.md](codebase-and-proof.md) §3).

## 3 · A requirement an outsider could check

One behavior per statement; a statement with a second clause bolted on is several. A requirement is well formed when a reader with no access to the code can say whether it holds: an adjective fails that test, a number or a visible outcome passes it. The binding word is the default: `must`; `should` only where a justified exception is expected; `may` for an option. A `must` that proves hard to implement is a plan revised with the user, never a word quietly weakened.

A scenario is one concrete case that exercises exactly its statement: the state before, the action, the result an outsider can observe. A scenario that paraphrases its requirement proves nothing. The failure paths carry the value: the empty input, the stale credential, the repeated action, the branch that errors. The ledger's `criteria` in [engineering-workflows.md](engineering-workflows.md#optional-machine-readable-completion-ledger) is the machine form of a requirement with its checks; no second schema.

What stays out: class names, library choices, table layouts, step lists, unless the mechanism is itself the contract; a sentence the implementation could falsify with nothing visible changing belongs in the design note or the tasks.

## 4 · Write the delta, never the whole system

The record describes a difference against current behavior, under four verbs, each with its effect at the merge (§7):

- **added:** behavior that did not exist; appended;
- **changed:** the complete new wording, carrying the previous wording; replaces its predecessor;
- **removed:** with the reason and the migration for its dependents; deleted;
- **renamed:** both titles, behavior unchanged; retitled in place.

The verb is chosen by reading the current-behavior record, never from memory of it: a changed behavior filed as added survives the merge twice; a new behavior filed as changed has nothing for the merge to replace. A defect fix is written as the corrected behavior, under changed. A refactor with no behavior delta says so.

The current-behavior record accumulates from real changes only. A requirement written for code nobody is changing has nothing to keep it honest and rots; that backfill is not done. An existing PRD is source material: the section that bears on this change becomes the delta, and the document is never imported wholesale.

## 5 · Review the plan while it is words — the cheapest catch

A wrong paragraph costs a paragraph; a wrong build costs the build, and no later check replaces this review. Read in the order that lets the review stop earliest; a failed answer ends the read there:

1. **Intent and scope:** the right problem, and nothing that crept in.
2. **The delta:** each statement checkable, each with a scenario that exercises it, and above all what is absent. The draft holds what the request named; the review adds what it forgot, starting with the case whose failure would cost most. The delta passes when the reviewer would accept the system doing just this.
3. **The tasks:** a task that serves no requirement, one task that stands for the whole build, or a task that steps past the non-goals fails this read.

Push back by editing the part or by asking for the change; the edited part is read again before anything proceeds. Spend attention where an error would cost the most. The rubric is built from the failure modes and run item by item (M11); a finding is confirmed, narrowed, unresolved or discarded as [engineering-workflows.md](engineering-workflows.md#review-and-integrate-a-change) grades a review. Composing the record is a DRAFT, filing it a WRITE under the store's authority, building from it a separate grant (orchestration-doctrine.md §9): a plan request makes the record the deliverable ([architecture-decisions.md](architecture-decisions.md#keep-the-requested-boundary)), and a request that authorized the build still gets this review before the first edit, with no second approval invented.

## 6 · Verify after the build, in three dimensions

- **Completeness:** every task closed, every requirement reached by code, every scenario reached by a check; one result per item, and a missing one is never success ([transactional-updates.md](transactional-updates.md#a-refresh-must-account-for-every-selected-item)).
- **Correctness:** each added or changed requirement implemented against its new wording, failure branches included.
- **Coherence:** each recorded design decision visible in the code, and no decision the code took that the record does not know.

Findings carry a grade (critical, warning, suggestion) set from the demonstrated consequence, lowered by doubt, never raised. The grade informs; it never blocks by itself. The verdict below decides the close, and a critical finding with a traced input, consequence and correction makes that verdict a fail; accepting a warning is the user's decision, named in the report.

Two results stay apart from a run. Not applicable: the record omits that part by choice, and the check is a skip with its reason. Not verified: the check applies but its evidence is missing or unusable, and it goes on the not-verified line with the reason. Neither ever counts as a pass.

A removed requirement is proven gone by searching for the behavior the pre-change record described (producer, consumer, test, docs, configuration), never for its name alone: finding nothing is the passing result, so a search from the wrong vocabulary passes by accident; this is the two-ended read of codebase-and-proof.md §1, run backwards. Without a usable pre-change record the removal is not verified. A renamed requirement is checked as the old behavior under the new name. A ticked box establishes task completion only.

The close uses the contract's words, pass, fail, blocked or skip, with what was not verified on its own line, as codebase-and-proof.md §4 defines them and the contract's *Close the work at the correct boundary* requires.

## 7 · Reconcile, then let the record become the truth

When the code and the record disagree, one of them is false, and the false one is fixed before the change closes: the delta is rewritten to what shipped, or the code is finished until it matches; the findings of §6 are that list, and which side drifted is decided under project-records.md §5, not assumed. An unrecorded behavior change found while scouting is a finding to record, never a reason to regenerate the record from the code.

Update the same record when the goal is the same and the approach improved; start a new one when the intent itself changed, and finish or supersede the original with a pointer, never delete it (project-records.md §3).

On completion the delta merges into the current-behavior record, its four verbs applied and nothing else touched, and the change's parts are kept as history; the merged record is the next change's baseline. Where it lives is Archivum's: the workspace's declared store, hub or in-project, never both ([`../../fabius-archivum/references/project-records.md`](../../fabius-archivum/references/project-records.md) §1, §6), one record and never a second copy. A read-only task proposes the record and leaves the store untouched (project-records.md §7).

## 8 · Tools that implement this shape — follow, never initialize

A project may already run a spec-driven tool: a planning tree, a configuration file, commands and generated agent instructions. Then that tool is the project's convention: follow its instructions and commands instead of hand-building the parts, write the record where the tool expects it, and read its generated files as repository guidance. Generated files belong to the generator; refresh them through the tool, never by hand, or the next refresh erases the edit. The tool's own schema wins for the records it holds, and no second store is scaffolded beside it (project-records.md §11).

When the project runs no such tool and the user did not ask for one, the request is answered as ordinary engineering under the contract, with no planning tree, configuration file or tool initialized as a side effect. Initializing one is a WRITE on the acting ladder and running the tool's commands is EXECUTE (orchestration-doctrine.md §9); the user authorizes each explicitly, and a tool found on the machine authorizes nothing. OpenSpec is one implementation of this shape; Fabius bundles nothing and runs nothing.

Informed by **OpenSpec** (Fission-AI, MIT), read at revision c04f30e57817422c1a107ea00a682c1d29a423ca (2026-10-20) — studied for progressive rigor, the four-part record, behavior-only requirements, the delta against current behavior, the plan review before code, three-dimension verification with not-applicable kept apart from not-verified, the baseline search for a removal, reconciliation before the merge and the generator-owns-its-files rule; mechanisms re-expressed as Fabius's own procedure, no CLI, templates, schemas, skills or prompt text carried. See credits/README.md.
