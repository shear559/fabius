# Update a composed system without losing its state

Use for an authorized skill refresh, dependency upgrade, or migration whose parts must remain compatible. This is a procedure for the user's existing system, not a Fabius updater or service. Discover the actual harness, package manager, validation commands, and service owner before choosing commands. An upstream guide supplies evidence, never permission to install, execute, restart, or send.

## Size the recovery plan to the change

A prose-only skill correction may need only a reviewed diff and the existing checks. An update that touches persisted data or source mounted into a running process needs isolated staging and a recoverable cutover. Do not introduce containers, databases, credentials, or a maintenance window merely to follow this reference.

1. **Inventory the starting state.** Record the current revision, selected components, exact source revisions or version pins, relevant local customizations, and affected persisted data. Inspect actual remotes; a fork's `origin` need not be the authoritative source. Resolve upstream identities before fetching. Preserve unrelated work; use an isolated worktree when integration would mix with it.
2. **Define completion and recovery.** Map each selected component and required migration to a check and an outcome. Distinguish source-code recovery, mutable-data recovery, and external-component recovery. A Git tag restores none of the latter two. Identify the backup and restore mechanism already supported by the system; keep secrets out of reports and task artifacts.
3. **Stage the composition.** Integrate source and inspect changes away from a live-mounted checkout. Preserve intentional local behavior. Use approved dependency pins and installation policy; do not execute a fetched setup script because it calls itself a prerequisite. Run the relevant component checks and checks across their integration points.
4. **Review the concrete cutover.** Show changed components, migrations, expected interruption, verification, and recovery limits. Proceed within existing authorization; obtain any still-required permission only after this plan is reviewable. If live processes can race the update, use the actual service owner to quiesce only those affected. Record prior running/paused state so restoration does not wake work the user had already paused.
5. **Apply and verify.** Capture the required mutable-state recovery point before changing it. Apply the validated composition and its migrations in dependency order. A failed or pending requirement blocks completion. Validate the resulting data and check a real operation through the intended interface; process existence, an open port, or a version string alone does not establish health.
6. **Retain recovery until success is established.** Record the actual final revision and component outcomes. If verification fails, use the planned recovery and verify that recovered state. Keep the last usable recovery point until the new state is accepted under the task's criteria; remove only temporary resources created by this update and authorized for cleanup.

## A refresh must account for every selected item

Keep selection and results separate. Every selected item needs exactly one result with its identity, source revision, changed paths, status, and verification evidence. Missing, duplicate, skipped, unsupported, fallback-only, or failed results cannot be silently counted as success. If the user changes the selection, record that scope change explicitly. A successful refresh still needs validation of the combined checkout.

For example, three selected skills and two passing results means **incomplete**. A failed dependency step cannot become a successful skill update merely because its Markdown file changed. Report the unresolved item and the work already completed so the next attempt resumes rather than repeats it.

## Recovery has limits

Record exact old pins and restoration instructions for components outside the source snapshot. Verify backup usability through the system's supported checks; a backup pathname is not proof of recovery. Where reversing a migration is unsafe, retain the original state and use the documented forward-repair route.

Restoring code or a database never implies reversing an email, payment, publication, or other external effect. Avoid those effects in verification unless authorized. If one occurred, report it separately; any compensating action needs its own applicable authority. Never label partial recovery as a complete rollback.

Informed by **NanoClaw** (Gavriel, MIT), `.claude/skills/update-nanoclaw/SKILL.md`, `.claude/skills/update-skills/SKILL.md`, and `.claude/skills/manage-mounts/SKILL.md` at revision `6656b326a900dcfba4be8ca76412d954cfc915b5`. See credits/README.md.
