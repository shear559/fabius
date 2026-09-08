# Fabius — SKILL frontmatter contract

The authored frontmatter contract for every public `SKILL.md` in this plugin. It keeps common discovery fields consistent across supported hosts; host-specific fields still need host-specific verification. Consult it before changing frontmatter or adding a host to the support matrix.

> **Evidence scope — 2026-09-08.** Documentation establishes advertised fields; local installation checks establish the files and versions present. Neither alone proves that a running model selected the intended skill. Recheck host behavior after an update. The byte budgets below are Fabius's own conservative constraints, not universal host limits.

---

## The canonical key set

Five keys, each earning its bytes:

| Key | Why it exists |
|---|---|
| `name` | Identity. Must equal the skill directory name and follow the Agent Skills naming rules: at most 64 characters, lowercase letters/digits and hyphens, no leading, trailing or consecutive hyphens. |
| `description` | Primary discovery text, including the essential trigger. Fabius enforces **≤ 1024 UTF-8 bytes flattened**; the Agent Skills specification describes a 1024-**character** limit. Keeping a byte budget is conservative for non-ASCII text. |
| `when_to_use` | Complementary trigger phrases for hosts that read this extension. Fabius enforces combined `description` + `when_to_use` **≤ 1536 UTF-8 bytes flattened**. Claude Code documents a configurable 1536-**character** listing cap. Essential routing must remain understandable from `description` alone. |
| `license` | Provenance in-band. The skill file travels alone when a harness copies it out of the repo; the license must travel with it. |
| `metadata.author` | Attribution in-band. The specification reserves `metadata` for string-valued extensions; Grok documents author display. Rendering in other hosts is not assumed. |

Keep procedural detail in the body and references. Specification source: [Agent Skills frontmatter](https://agentskills.io/specification#frontmatter).

## Discovery boundary — fifteen contracts, no nested skills

Only `skills/<contract>/SKILL.md` is a public plugin skill. Any vendored or supporting instruction below a contract — even when its upstream project called it a skill — is stored as `REFERENCE.md` and paged explicitly through the owning root contract. Do not rely on `.gitignore` or an index omission to hide a nested `SKILL.md`: recursive scanners still discover it. The structural gate must compare the manifest against the **recursive** `SKILL.md` set and fail on any nested file.

## Per-harness field matrix — checked 2026-09-08

| Harness | Behavior |
|---|---|
| **Claude Code** | Documents `when_to_use` appended to `description`, with a default 1536-character cap configurable through `skillListingMaxDescChars`. The documented standard fields include `license` and `metadata`; these are not permission grants. [Skills reference](https://code.claude.com/docs/en/skills#frontmatter-reference). |
| **Grok Build** | Documents `when-to-use` with `when_to_use` as an alias, and displays `metadata.author` / `metadata.short-description`. Extra keys are ignored; accepting `license`, `model` or `effort` does not apply them. Enabled plugin skills are discovered separately from hook/MCP trust. Local 0.2.103 reported fifteen skill directories for Fabius 2.8.0. [Host reference](https://docs.x.ai/build/features/skills-plugins-marketplaces). |
| **Cursor** | Documents Agent Skills discovery from `.cursor/skills/`, `.agents/skills/` and compatibility locations including `.claude/skills/`. This establishes discovery locations, not that `when_to_use` controls routing. [Skill directories](https://cursor.com/docs/skills). |
| **Codex** | CLI 0.153.4 exposes separate `plugin marketplace add` and `plugin add` commands; `plugin list` reports installed/enabled state. The local 2.8.0 installation preserved all fifteen root contracts, but its sparse package omitted some repository paths. File presence does not establish use of every frontmatter extension or automatic loading of plugin-root `AGENTS.md`. Evidence: native CLI help, installed inventory and contract comparison on 2026-09-08; installation steps are in the root README. |

Keep snake_case `when_to_use` for the hosts that document it. Do not infer universal unknown-key tolerance from those hosts. For a new integration, verify parsing, discovery, a positive route and a near-neighbor separately; confirm the active session after installation or refresh.

Claude Code's plugin format is not the claude.ai upload or Skills API format: those specification-only paths reject unsupported top-level fields such as `when_to_use`. They require a separately validated export. [Distribution-path limits](https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code).

## Keys fabius deliberately does not use

`allowed-tools`, `model`, `effort`, `disable-model-invocation`, `argument-hint`. Two reasons, both structural:

- **Compact discovery.** Conditional procedure belongs in the body rather than repeated host-specific settings on fifteen contracts.
- **Single-owner routing within host authority.** The router recommends layers and available machinery (see [routing-policy.md](routing-policy.md)). The host and the user retain control over permissions, tool access and model availability; omitting frontmatter grants does not confer those powers on Fabius.

## Enforcement

The structural gate (`evals/structural.mjs`) enforces this contract mechanically — name↔directory match, required keys, and the flattened description budget fail the build, not a review.

The gate validates the deliberately small authored subset used here: unquoted names and license identifiers, folded descriptions, inline or block trigger text, and a metadata mapping with one non-empty author. Inline text may be plain or quoted; comments, collection values, aliases, and null/boolean/number sentinels are not accepted as text. This is not a general YAML parser. `node scripts/test-structural.mjs` exercises the real gate against isolated missing, duplicate, empty, malformed, and oversized fixtures.
