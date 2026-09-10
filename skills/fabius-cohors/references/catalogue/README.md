# Choose and adapt a Fabius role

Fabius supplies six original definitions in [roles.json](../../examples/roles.json). They capture reusable work boundaries rather than personifying a large collection of professions. Copy the selected JSON definition into a plan, adapt its instructions and output to the task, then validate the complete plan before running it.

## Define the work before tools

1. Write the result that another task will consume. Give required fields types, reject extra fields and make an empty finding list valid.
2. Name the input evidence and the task's owned files or records. Keep that scope in `task.input`; the host must enforce it.
3. List only available tools. The example names are adapter identifiers, not installed tools.
4. Declare `read`, `write`, `execute` and `network` permissions explicitly. The validator rejects missing permission categories. These are policy data; the caller implements enforcement.
5. Bind the task to an agent ID and to explicit upstream task IDs. A task receives only the successful outputs of those direct dependencies.

The `researcher` has read/source-discovery tool names and asks for network access; `builder` asks for writes and execution; `reviewer` is read-only. `analyst`, `editor` and `coordinator` operate on supplied values with no tools. These defaults express the role's intended boundary. They grant no filesystem, network or model authority.

## Adapt for a real host

Map the definition to the host's actual agent and tool schemas. A host can require different model fields, skill registration, approval semantics or sandbox settings. Resolve those through its documented interface. Keep the task result schema stable so the caller can validate the handoff regardless of the host.

Use an existing authorization policy when it already covers the exact task. `authorize(frame)` is a synchronous caller policy function, not a requirement to ask the human again. A false result means that task does not run. A true result approves the caller's runner for that task; the runner remains responsible for honoring the tools, scope and permissions.

A schema-valid answer can still be false. Review facts and cross-field conditions separately: for example, a reviewer returning `accept` with unresolved critical findings needs a semantic check in the host adapter. The scheduler validates shape and dependency state, not the truth of a claim.

## Historical inspiration

| Previous source | Useful capability retained | Original replacement | Explicit limit |
|---|---|---|---|
| [Agency Agents](https://github.com/msitarzewski/agency-agents) | Precise role selection and bounded handoffs | Six Fabius definitions and this adaptation procedure | Does not reproduce hundreds of specialty personas |
| [Google ADK samples](https://github.com/google/adk-samples) | Typed task inputs/results and testable adapters | The JSON contract, output validator and deterministic worked adapter | No provider SDK, retrieval connector or six-language SDK implementation |
| [Ruflo](https://github.com/ruvnet/ruflo) | Dependency coordination and explicit work ownership | The bounded static-DAG scheduler | No distributed service, dynamic agent spawning, persistent queue or process sandbox |

The previous bundles had unknown historical revision pins. Removing their files does not recover those pins or change the origin of past releases. Existing authored research and local-runtime guidance remain alongside this original implementation. No new file is a renamed copy of a retired implementation.
