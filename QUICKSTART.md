# Quickstart: install Fabius, then run one task you can check by hand

Install Fabius into the agent app you already use, open a fresh session, and give it a task whose right answer you know.

## 1 · Install

**Claude Code** (type these inside Claude Code)

```
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

```
grok plugin install shear559/fabius --trust
grok plugin enable fabius
```

It worked when your plugin manager lists **fabius** as installed. Claude Code and Grok Build also show its fifteen skills; in Codex, restart and look for the Fabius skills in a fresh task.

## 2 · Run a task with a known answer

Paste this into a fresh session:

```
fabius: summarize this CSV. Show each line total, the sum, and the largest product by revenue.
Do not assume a currency. Show the arithmetic.

product,quantity,unit_price
coffee,3,40
tea,5,18
mug,2,35
```

The right answer: coffee 120, tea 90, mug 70; total 280; ten items; coffee is the largest line. The currency stays unspecified, because the file never names one.

Starting a prompt with `fabius:` calls the router by name. Agent apps differ in how readily they pick up skills from a plain sentence.

## 3 · Try three more

[Meeting notes into next steps, a 30-second video shot list, and a Python bug fix with boundary tests](examples/README.md). Each one ships with its input, the result, and the check.

## If something is missing

| You see | Do this |
|---|---|
| No plugin commands | Update your agent app through its normal channel, then check its help or version command |
| Fabius is listed but no skills appear | Confirm it is enabled, restart, and check you are in the workspace you installed it for |
| Old behavior after an update | Check the installed version and open a fresh session; a running session keeps the version it loaded |
| The task needed a file, browser or renderer you have not connected | Fabius is built to report a missing tool, never to fake the result. Connect the tool, or ask for a clearly labeled draft |
| A record was saved that you did not expect | Stop the task and check the project-memory folder you set up (one page per project). Fabius writes there only with your permission |

## Update, turn off, remove

**Claude Code:** `/plugin update fabius@fabius`, then `/reload-plugins`. Disable it from `/plugin`. Remove it with `/plugin uninstall fabius@fabius`. [Claude Code plugin docs](https://code.claude.com/docs/en/discover-plugins).

**Codex:** `codex plugin marketplace upgrade fabius`, then `codex plugin add fabius@fabius`, then restart. To turn it off without removing it, use Codex's own plugin controls. Remove it with `codex plugin remove fabius@fabius`.

**Grok Build:** `grok plugin update fabius` updates an install that is not pinned to a release tag (a pinned install is moved to the new tag by hand). `grok plugin disable fabius` turns it off; `grok plugin uninstall fabius` removes it.

In any session, say `stop fabius` and Fabius stops applying its rules for the rest of that conversation. It does not disable or uninstall the plugin; your plugin manager does that.

Fabius is free to install for personal, non-commercial use. Your model, connected services and compute are your own costs. Professional or client work needs permission: see [LICENSE](LICENSE).

[Which app versions were tested](COMPATIBILITY.md) · [Get help](SUPPORT.md)
