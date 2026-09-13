# Fabius change economy

Use these questions when a solution is expanding without a corresponding requirement.

| Decision | Evidence that justifies more work | Smaller option to examine first |
|---|---|---|
| Add a dependency | A named requirement the current stack cannot meet | Existing helper, standard library or native host feature |
| Create an abstraction | Multiple current consumers need the same stable behavior | Keep the behavior near its only caller |
| Add configuration | Real deployments require different values | A documented constant |
| Add accounts / sign-in | The request names identity: data that belongs to one person, sharing between people, a save that follows the user to another device, a profile, a login | Local state, no identity |
| Add a database | Durable data must outlive the session or be shared across devices or users | Local storage or an in-memory store; a database without accounts holds public rows → praesidium [security-playbook.md §4](../../fabius-praesidium/references/security-playbook.md) |
| Delegate a task | An independent result can be specified and reviewed | Complete the next bounded step locally |
| Run another investigation | Its outcome can change the implementation or verdict | Decide from existing evidence |
| Expand a test run | A changed dependency, a failure or a still-uncovered risk | The mapped regression set |
| Store a memory | A verified fact will be needed again and storage is authorized | Return the finding in the current answer |

An example: a user requests a second export format. First inspect the existing serializer boundary and its consumers. If a second formatter fits that boundary, implement it there. A generic export registry, remote rendering service and configurable pipeline require their own demonstrated needs.

An error path is not optional merely because it lengthens the patch. Preserve authentication, input validation, data-loss handling and accessibility. Prefer a clear failure with its cause over a fallback value that looks successful. Concision concerns unnecessary work, never missing evidence or hidden failure.

Informed by **system_prompts_leaks** (asgeirtj, CC0-1.0 compilation; the collected vendor prompts remain their vendors' text) — studied for the off-by-default posture of accounts and durable storage in a greenfield build and the evidence that switches each on, re-expressed in fabius's own voice; no prompt text carried, nothing bundled. See credits/README.md.
