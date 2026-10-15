# Quickstart: install Fabius and use the right skills

Install Fabius into the agent app you already use, open a fresh session, and start with a task whose result you can check.

## 1 · Install

**Claude Code** (type these inside Claude Code)

```text
/plugin marketplace add shear559/fabius
/plugin install fabius@fabius
/reload-plugins
```

**Codex** (in a terminal, then restart Codex)

```text
codex plugin marketplace add shear559/fabius
codex plugin add fabius@fabius
codex plugin list --marketplace fabius
```

**Grok Build** (in a terminal)

```text
grok plugin install shear559/fabius --trust
grok plugin enable fabius
```

Confirm that your plugin manager lists **fabius** as installed. Claude Code and Grok Build also show its fifteen skills; in Codex, restart and look for the Fabius skills in a fresh task.

## 2 · Invoke the router or a specialist

The router's job is to identify the needed skill owners, combine their responsibilities and choose sufficient tools and checks. Your app controls which contracts it actually loads.

| App | Start a request |
|---|---|
| Claude Code | `/fabius` for the router; `/fabius:fabius-disciplina` for engineering, or another specialist's command |
| Codex | “Use Fabius to…”; name the relevant specialist when needed |
| Grok Build | Name Fabius or the relevant specialist in the request |

For a task spanning several concerns, ask it to state which skills are needed and why. A signup-page change may need Mercatus for the message, Decor for the interface and Disciplina for implementation and verification, with Parcus underneath.

Automatic specialist activation is not assured. If a needed skill remains unloaded, invoke it explicitly through the app's supported mechanism. Merely typing `fabius:` is not equivalent to Claude Code's `/fabius` command. The [compatibility record](COMPATIBILITY.md) distinguishes installation, discovery and observed task behavior.

## 3 · Run a task with a known answer

Paste this into a fresh Claude Code session. In Codex or Grok Build, replace `/fabius` with “Use Fabius to”.

```text
/fabius summarize this CSV. Show each line total, the sum, and the largest product by revenue.
Do not assume a currency. Show the arithmetic.

product,quantity,unit_price
coffee,3,40
tea,5,18
mug,2,35
```

Check the answer: coffee 120, tea 90, mug 70; total 280; ten items; coffee is the largest line. The currency stays unspecified because the file never names one.

This checks the artifact you receive. It does not by itself prove that a skill loaded; inspect the app's skill invocation or activity record for that.

[More prepared examples](examples/README.md): meeting notes into next steps, a video shot list and a Python bug fix. Each includes the input, result and check.

## If something is missing

| You see | Do this |
|---|---|
| No plugin commands | Update your agent app through its normal channel, then check its help or version command |
| Fabius is listed but no skills appear | Confirm it is enabled, restart, and check the workspace where it was installed |
| A needed specialist did not load | Invoke its command in Claude Code, or name it explicitly in the app; inspect the resulting activity |
| Several skills appear to repeat or conflict | Ask which concern each owns. Keep one owner per concern and retain the host's instruction hierarchy and permissions |
| Old behavior after an update | Check the installed version and open a fresh session; a running session keeps what it loaded |
| A file, browser or renderer is unavailable | Connect an authorized tool, use an equivalent that can establish the same result, or keep the missing check explicit |
| A record was saved that you did not expect | Stop the task and inspect the configured project-memory store; writes require authorization |

## Update, turn off, remove

**Claude Code:** `/plugin update fabius@fabius`, then `/reload-plugins`. Disable it from `/plugin`. Remove it with `/plugin uninstall fabius@fabius`. [Claude Code plugin docs](https://code.claude.com/docs/en/discover-plugins).

**Codex:** `codex plugin marketplace upgrade fabius`, then `codex plugin add fabius@fabius`, then restart. To turn it off without removing it, use Codex's own plugin controls. Remove it with `codex plugin remove fabius@fabius`.

**Grok Build:** `grok plugin update fabius` updates an install that is not pinned to a release tag; a pinned install must be moved to the new tag. `grok plugin disable fabius` turns it off, and `grok plugin uninstall fabius` removes it.

Say `stop fabius` to stop applying its rules until you invoke it again. Your plugin manager handles disabling or uninstalling the plugin.

Fabius is free to install for personal, non-commercial use. Your model, services and compute have their own costs. Professional or client work needs permission: [LICENSE](LICENSE).

[Tested apps](COMPATIBILITY.md) · [Get help](SUPPORT.md) · [Historical evaluations](docs/archive/README.md)
