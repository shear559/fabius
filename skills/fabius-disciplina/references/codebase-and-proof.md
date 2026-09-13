# Fabius Disciplina — scout the codebase, scout reality, prove at the surface

The on-demand depth for `fabius-disciplina`'s *scout* and *prove* steps when the unknown is a large codebase, a current-world fact, or a change that must be observed at its runtime surface. The skill is the contract; this is how you run the loop well. The repository's optional local runner is separate from these ecosystem tools; external connections are documented in ARCHITECTURE.md. Tool names and versions are a point-in-time snapshot (early 2026); re-verify before you depend on one.

Scout wide, strike narrow. Three of these sharpen *how you understand* before an edit; the rest sharpen *how you prove* after it.

## 1. Map the code with the smallest sufficient tool

Start with targeted symbol search, imports, build metadata, and covering tests. Reuse an existing local code graph when it answers the remaining dependency question; build one only when repeated cross-file queries justify the setup. Missing graph tooling does not block an otherwise answerable review.

- Parse the repo with tree-sitter (14+ languages), store the symbol/call/import graph in **SQLite**, keep it **auto-synced** to the working tree (FSEvents / inotify). The graph is the index; the query is surgical. *(ecosystem: codegraph, GitNexus, Code Review Graph.)*
- Query the graph for the answers an edit actually needs: **impact analysis** (what calls this, what breaks if I change the signature), **dependency tracing** (what this module pulls in), **taint analysis** (does untrusted input reach this sink). One query returns the blast radius; a grep returns a wall of strings.
- **100% local** — the graph is built and queried on-device, no code leaves the machine. That is the precondition for using it on a client repo at all (→ `fabius-praesidium` owns the secrets/exfil boundary).

**Decision rule:** choose the evidence needed for the change, then the least costly tool that produces it. A graph helps trace impact but does not prove runtime behavior; verify material edges against code and tests.

## 2. Scout reality — verify current-world facts against the live web

Memory is where silent staleness begins. An API shape, a library's current state, a version number, a price — anything that **decays** — is not a thing to recall; it's a thing to check. The cost of a wrong remembered version is a whole plan built on a fact that stopped being true.

Two tiers, sized to the question:

- **Quick web search** — one current fact: the latest stable version, whether a flag still exists, today's pricing. Cheap, single-hop.
- **Deep multi-hop research** — a synthesis question that spans sources: how does library X handle Y now, what changed across a major version, what's the current consensus on an approach. *(Perplexity sonar-deep-research, Exa, Brave; keyless Firecrawl for a single-page scrape.)*

**Decision rule:** is the fact **current-world and decaying**? → check reality before you plan on it. Is it stable (an algorithm, a language semantic, the project's own code) → memory/the graph is fine. Encode the decision, not the version number; re-verify the number.

Web/DB search as a **live tier is optional and user-configured** — fabius ships no keys. When it's wired, it routes to ARCHITECTURE.md external connections; when it isn't, the rule still holds, you just satisfy it by hand.

## 3. Plan as files, not as chat

For multi-step or long-horizon work, the plan and the spec live **on disk**, not only in the conversation. A context reset wipes chat; a file survives it, and the agent re-reads the file to recover its place.

- Persist the `step → verify` plan (phase 3) and the spec to files the agent re-opens each cycle.
- This is what lets the loop run unattended across a reset — the durable artifact is the memory. *(Planning-with-Files reports 96.7% task pass on this discipline; treat that as reported, not fabius-measured.)*

The plan file is also the handoff artifact and the thing `fabius-archivum` files once the work resolves. Short tasks don't need it; the moment the work outlives one context window, the file is the difference between resuming and restarting.

## 4. Prove at the surface — every change has one to drive

A passing unit test is **not** proof that a change works. The law is fabius's own: *verify live, not just code.* Reach the changed code through the surface it is consumed at, drive it there, and keep what it showed. The mapped covering checks still run (R16; SKILL.md "Map source to observable behavior") — the drive at the surface is added on top of them, never substituted for them. A green mapped suite is graded by R15 — PLAUSIBLE and step-closing until the gate is audited; the observation at the surface is CONFIRMED on its own terms and closes the route for the behavior it shows.

The surface is wherever the change is consumed. A library is consumed at its published boundary — install it and call the export, never a path into the source tree. A service is consumed by its caller — a request goes in, the response is kept. A command is consumed in a terminal — run it, keep the pane. A page is consumed in a browser — drive a session (below) and keep a screenshot for the human eye. An agent prompt or configuration is consumed by the agent's run — keep the transcript and the tool calls (§7 for the keyless drive). A pipeline definition is consumed by the pipeline — trigger it and keep the log.

A private function is never the surface; follow its callers outward until one is consumed somewhere a user can stand, and drive that. Take the shortest route that makes the changed lines execute — the entry point that reaches them, with the input that makes them run — then probe beside it through the same surface, choosing only the probes the diff itself points at: the input the diff did not expect (missing, doubled, contradictory, malformed); the error branch next to the one the diff changed; the action repeated, the action over stale state, or the action from two sessions at once where the change touches shared state. A probe that holds is recorded too, since it states what the drive covered.

For a browser surface:

- **Playwright** — deterministic, no-vision: locators, `fill`, `click`, `screenshot`, full e2e. Assert by **locator/role/text** (the semantic handle), the same meaning-first principle as the simulator tree (→ `references/simulator-verify.md`) — not by pixel coordinate, which breaks on every layout shift.
- **Sandboxed browser** when you must run untrusted page logic — **QuickJS-WASM isolation**, no host file or network access. Reach for it only when isolation is the point; plain Playwright is the default.
- The check is **state on the real path**, not "the test is green." Navigate, act, read the live DOM, assert the user-visible outcome. Screenshot last — for a human's eyes and visual-diff, never as the primary assertion.

**Verdict** — one of four, on the runtime state of the change (review findings are graded separately → `engineering-workflows.md`):

- **PASS** — the surface was driven and showed the requested behavior.
- **FAIL** — the surface was driven and the change did not do what the diff claims, or something beside it broke.
- **BLOCKED** — the drive never reached a state in which the change could be observed. This is a fact about the environment, not about the change: name the last step that succeeded and the first that did not.
- **SKIP** — the diff has no runtime surface: a docs-, changelog- or license-only path (§6). One line, and no suite is run in its place. Configuration is not a SKIP; it takes the parser, compiler or read-back the contract names (SKILL.md "Map source to observable behavior"; §5). A tests-only diff is not a SKIP either; it takes the old-behavior or mutation control the contract asks for where practical.

Ties break closed. A partial result is FAIL, never a smaller PASS — the same accounting `transactional-updates.md` applies to a refresh; a capture you cannot read decisively is FAIL as well, filed with the unedited output so a reader can overrule it. In the ledger (`engineering-workflows.md`, `evidence.mjs`) PASS is a `passed` check and FAIL a `failed` one; SKIP and BLOCKED are both recorded as `skipped` with the reason — for BLOCKED, the last step that succeeded and the first that did not — which leaves the ledger `incomplete`. Neither BLOCKED nor SKIP ever upgrades a claim.

Two guards. Evidence travels with the report: text captures go inline, binary captures are sent as files whenever the reader has no access to your filesystem; a bare path is a pointer, not evidence. And when the only surface sits on the EXECUTE rung of the acting ladder (→ `../../fabius/references/orchestration-doctrine.md` §9), it is never driven as a probe: with no dry-run mode, no throwaway target and no authorization for that rung, prove everything beneath it and name the one action that stayed unexercised; when the action itself is the authorized deliverable, it runs once and its observed result is the evidence.

**Decision rule:** the change has a runtime surface → it isn't done until that surface was driven. "Almost works" and a code-only answer don't count (phase 6).

## 5. Enforce TDD with a gate, not a hope

Phase 4 is the iron law: no production code for non-trivial logic until a test fails first. Hope is not enforcement. When correctness genuinely matters, make the failing test a **gate**, not a suggestion.

- A **pre-edit hook** blocks writing implementation while no failing test exists — **RED → GREEN enforced** across 9+ test frameworks. The hook refuses the edit until red is real.
- This turns "I'll write the test after" — the anti-pattern that proves the code does what it does, not what it should (→ `references/process-playbook.md`) — into something the harness won't let you skip.

**Decision rule:** wire a hook only when its failure-prevention value and the task's authorization justify changing the harness. Throwaway prototypes, generated code, and pure config use the closest executable validator under phase 4; they need no separate approval ceremony. A suggested hook is not an installed enforcement mechanism.

## 6. Verify on stop — gate the turn's end, not just its start

The pre-edit gate (§5) governs where an edit may *begin* — no code before red. This gates where a turn may *end*. A passive **evidence ledger** records every classified check the agent actually ran — command, kind (test / build / run), scope, exit code, output summary. It never runs checks itself, never blocks completion, and never upgrades a targeted check into "repo green": one passing test is not a passing suite, and the ledger must not pretend otherwise.

The policy fires in exactly one case: the agent tries to end a turn immediately after editing code with **no fresh evidence** in the ledger. Then — and only then — append **one** synthetic nudge carrying a capped list of the changed paths, driving a single bounded verification follow-up. One nudge, one follow-up; not a loop.

Design the false positives out up front. Turns touching only non-code paths — docs, changelogs, licenses — never nudge. On human chat surfaces the nudge defaults **off**: verification narration there is noise, not proof.

The general law underneath: synthetic scaffolding turns exist to *drive the loop*, never to be replayed as context. Exclude them from session persistence — or a resumed session replays the nudge as genuine history and acts on scaffolding it mistook for the user.

## 7. Prove an agent loop without a key — inject the model call

Agent code has a testing problem the rest of the codebase does not: the interesting logic
sits *around* a paid, non-deterministic, network-bound call. So it goes untested, and the
bugs that ship are the ones nobody could afford to reproduce.

The fix is one line at the seam:

```js
const llm = options.callLLM || callLLM;
```

Now a scripted model drives the whole loop with no key, no network and no spend — and the
things you can finally assert are exactly the ones that break in production:

- a failed review earns **exactly one** rework, not a loop (assert the call count, not just the outcome);
- a denied write feeds its refusal back into the transcript and the run still delivers;
- the budget wall stops the run *before* the next call rather than after it;
- a repeated probe triggers its nudge once;
- an unverified deliverable does **not** compound into memory.

Two rules keep this honest. The scripted model must **run past its script** — anything
after the last scripted turn delivers, so a loop that runs long fails loudly instead of
hanging. And the fake must be the *only* fake: real files in a real temp directory, the
real permission gate, the real tool executor. Stub the model, never the machinery — a test
that stubs the gate proves the gate compiles.

Where the artifact is code, keep the hard oracle in the loop too: run the delivered block
in a throwaway directory and let a non-zero exit overrule the judge's score. A generous
reviewer can be talked past — including by an instruction hidden inside the deliverable it
is grading. A failing process cannot. (Runtime design → `../../fabius-cohors/references/local-agent-runtime.md`.)

---

The never-trim floor still holds underneath all of this: validation, security, and a11y are not candidates for the YAGNI ladder (→ `fabius-parcus`). These tools change *how you scout and prove*; they never license skipping the floor.

Each capability here is drawn from a named ecosystem tool and re-expressed in fabius's own voice — apply the discipline, credit the tool, ship nothing you haven't proven.

Informed by **system_prompts_leaks** (asgeirtj, CC0-1.0 compilation; the collected vendor prompts remain their vendors' text) — studied for the surface map, the shortest-path drive with probes beside it, the four-valued PASS / FAIL / BLOCKED / SKIP verdict with fail-closed ties, and evidence that reaches the reader (snapshot fetched 2026-09-13), re-expressed in fabius's own voice; no prompt text carried, nothing bundled. See credits/README.md.
