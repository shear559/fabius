# Compatibility and acceptance evidence

Checked 2026-09-09. Published baseline: **2.8.1**, commit `e224daccd393ac2081b38d4a804aa70637b90095`. The follow-up working tree is a release candidate; publication and fresh-install acceptance of it are separate steps.

| Surface | Evidence available | Remaining acceptance |
|---|---|---|
| Claude Code plugin | September 8 installed 2.8.1 inventory and byte comparison; 15 public skills | Clean profile, fresh-session natural prompt, output, update/disable/remove on candidate; `claude` executable was not found on current PATH |
| Codex CLI 0.153.4 | September 9 manager lists enabled 2.8.1; one fresh ephemeral CLI session produced a checked CSV summary | Candidate install and full lifecycle; that task did not establish Fabius routing |
| Codex desktop | This maintainer session exposes Fabius 2.8.1 skill files | Independent fresh account/workspace and candidate acceptance |
| Codex IDE | No candidate execution receipt | Test separately; CLI success does not cover IDE loading |
| Grok Build 0.2.103 | Native binary help and installed 2.8.1 inventory available; earlier byte verification | Candidate clean-profile task and lifecycle; update skips pinned refs on this version |
| ChatGPT Work / directory | Official skills-only Claude archive import path documented | Owner access, portal conversion/scan, clean import and actual task; no approval/listing claim |
| Other instruction-reading tools | Portable `AGENTS.md` core available | Host-specific instruction path and task tests; the single file does not install all specialists |
| Optional Node runner | Separate deterministic routing, capability gates and tests in `runtime/` | Live provider calls require configured account/key; do not confuse with host integration |

Model families are examples of engines a host may supply, not independently tested integrations. Claude Code is distinct from other Claude surfaces; Grok Build is distinct from a Grok model endpoint.

## Bounded native task — September 9

An existing-account Codex CLI session ran an ordinary-language request in a disposable workspace with a synthetic three-row CSV. It wrote `summary.json` and executed a local arithmetic check: line totals 120, 90 and 70, total 280, ten items and unspecified currency. The process exited successfully within the 180-second limit. The installed plugin was **2.8.1**, not this candidate. The session announced the spreadsheets skill; the retained trace does not establish that the Fabius router was loaded. This is a host artifact smoke check, not clean-install acceptance, a user study or evidence of a Fabius performance gain. Raw host logs remain private task outputs because they may contain account and workspace context.

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
