# Compatibility and acceptance evidence

Checked 2026-09-10. The published host baseline is **2.8.3**, commit `b31628684fed2267a58eb7afa530aed0215fc80e`. Version **3.0.0** replaces the imported capability trees with original local implementations. A package test, a fresh-session task and a model-quality comparison are separate evidence.

| Surface | Observed evidence | Boundary |
|---|---|---|
| Claude Code 2.1.260 | Clean profile installed 2.8.3 from the public marketplace, discovered 15 skills, updated, disabled, enabled and removed it | No clean-profile model task; lifecycle commands do not establish natural-language routing |
| Codex CLI 0.153.4 | Native 2.8.3 installation and two fresh existing-account task sessions; explicit Fabius request loaded router, Parcus and Disciplina and produced a checked fix | Ordinary-language task did not show Fabius loading; no clean-profile lifecycle receipt |
| Codex desktop | Maintainer sessions expose the installed skills | Does not establish an independent user's first-use experience |
| Codex IDE | No current execution receipt | CLI and desktop results do not establish IDE loading |
| Grok Build 0.2.103 | Clean profile installed 2.8.3, discovered 15 skills, updated and removed it; disable/enable commands completed | Listing did not expose disabled state; no fresh-session absence or model task claim; updater skips pinned refs |
| ChatGPT Work / directory | Skills-only Claude archive import mechanism is documented | No submitted, approved or clean-imported Fabius listing |
| Other instruction-reading tools | Portable core is present in `AGENTS.md` | Host-specific paths and tasks are untested; copying/adapting outside current marketplace permission needs separate authorization |
| Local capability helpers | Original scheduler, selected-file retrieval, tokens/scenes and evidence ledger have executable positive and negative tests | Deterministic helper correctness does not measure model judgment or enforce an OS sandbox |
| Optional Node runner | Executed deterministic routing, tool gates and runtime tests | Live provider calls need a configured account; standalone use needs separate licence permission |

Model families are examples of engines a host may supply, not independently tested integrations. Claude Code is distinct from other Claude surfaces; Grok Build is distinct from a Grok model endpoint.

## Bounded native tasks — September 10

Two fresh existing-account Codex CLI sessions used disposable Python bug-fix workspaces. Both produced a correct result that passed six independently rerun tests. The ordinary-language request did not leave observable evidence of Fabius loading. The explicit “Use Fabius” request did: the retained trace shows the 2.8.3 router, Parcus and Disciplina being read, five failing tests before the fix, and all six passing afterward. This verifies one task and its observed route. It does not establish automatic routing, a clean install, a user study or a gain over another model.

Clean Claude and Grok lifecycle checks used their documented isolated profile controls. Synthetic user-created records survived removal. No real account profile was reset, and no credentials were copied into test artifacts. Raw logs remain private because host output can include account and workspace context.

## Local 3.0.0 candidate acceptance

Fresh disposable Claude Code 2.1.260 and Grok Build 0.2.103 profiles installed the local candidate, reported version 3.0.0 and discovered all fifteen public skills. Both managers completed disable, enable and uninstall; each ended empty and preserved the synthetic user-created record. Grok's listing does not expose enabled state, so command completion is the boundary of that observation.

Each installed copy contained all 110 skill files. The four original helper implementations matched the tested source bytes. Six helper/demo invocations per host passed, including generated scene-template closure; required Markdown resource links resolved. A prose reference changed after those installation snapshots, so these receipts do not certify the final sealed tree byte-for-byte. They test the local-directory installation mechanism, not downloading the future public release. No clean-profile model task was run.

A separate fresh existing-account Codex CLI session explicitly read the local 3.0.0 router, Parcus and Disciplina contracts before repairing a seeded Python average function. The retained trace contains all three complete file reads and matching SHA-256 values. Six tests passed in the task and in an independent rerun. This is one explicitly routed local-candidate task, not automatic skill discovery or a clean-profile model trial. The host reported shortening some skill descriptions to fit its context budget; full contract reads were still observed.

## Repeatable host acceptance

Use a disposable workspace and profile supplied through that host's documented controls. Do not reset the user's real profile or copy credentials into a test artifact.

Record host/version, OS, account surface, exact release SHA and installed contract hashes. Follow the public install steps; verify the manager entry, then open a **fresh session**. Run an ordinary-language prompt from [examples](examples/README.md), retain the raw response and actual output, and verify the task's acceptance condition. Record which skills were actually discovered/loaded rather than asking the model to assert they were loaded.

Then update to the candidate, reopen and recheck its version; disable and confirm absence in a new session; uninstall and confirm absence. Check that user-created records were not unexpectedly erased. Restore only the test profile. Preserve failures alongside successes.

## Package scope

The full distribution includes credits and required references. A prior Codex sparse marketplace checkout omitted root `credits/`, developer directories and one internal README symlink; never claim a sparse cache equals the whole repository. Inspect actual package contents. `codex plugin marketplace add --help` exposes repeated `--sparse` paths; an explicitly sparse installation must include every required directory, including `credits`. Do not manually fill the native cache.

## Primary references

- [Claude installation and lifecycle](https://code.claude.com/docs/en/discover-plugins)
- [Grok plugin documentation](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/09-plugins.md)
- [OpenAI plugin surfaces and workspace permissions](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex)
- [OpenAI direct Claude archive conversion](https://developers.openai.com/plugins/guides/submit-claude-plugin)

Documentation establishes a supported mechanism. Only the retained host receipt establishes that it worked for Fabius in a particular environment.
