# Start with one checkable task

Fabius supplies reusable operating rules for the model you use through a compatible agent app. Model access, connected services and compute are provided separately. The current license permits personal, non-commercial installation and use through the published marketplace command. See [LICENSE](LICENSE) before professional or client work.

1. Follow the [installation commands](README.md#install-in-your-agent-app) for your host. Claude Code commands run inside Claude Code; Codex and Grok commands shown as shell commands run in a terminal.
2. Check the plugin manager shows **fabius**, its version and enabled state. Open a fresh session after installing or updating. A downloaded repository or marketplace entry alone is insufficient.
3. Pick one [example](examples/README.md), supply its input and ask the task in ordinary language. You do not need to name every specialist. Save only where you have granted permission.
4. Inspect the result and its evidence. Ask for the missing file or actual test output if a completion claim has no artifact. A plan for an image, video or integration is not that finished artifact.

## A first prompt

> Summarize this CSV: product,quantity,unit_price; coffee,3,40; tea,5,18; mug,2,35. Show each line total, the sum, and the largest product by revenue. Do not assume a currency. Show the arithmetic.

Expected arithmetic: coffee 120, tea 90, mug 70; total 280; ten items; coffee has the largest line revenue. This is a synthetic arithmetic example, not market or financial advice.

## When something is missing

| Symptom | Next check |
|---|---|
| No plugin commands | Run your host's help/version command and update through its supported channel |
| Plugin listed but skills absent | Confirm enabled state; restart; check the selected workspace and host surface |
| Old behavior after update | Check installed version and start a fresh session; marketplace refresh alone does not activate new files |
| Copy button fails | Use the selected manual-copy text field or select the visible command directly |
| No file, browser or renderer | Ask for a clearly labelled draft, or grant/configure the required tool; never infer execution |
| Unexpected memory write | Stop the task, inspect the declared record store and follow the host's data controls |

## Update, disable and remove

Claude Code: use `/plugin` to inspect and disable; `/plugin update fabius@fabius` updates the plugin and `/reload-plugins` reloads it. `/plugin uninstall fabius@fabius` removes it. Read [host documentation](https://code.claude.com/docs/en/discover-plugins).

Codex CLI: `codex plugin marketplace upgrade fabius`, then `codex plugin add fabius@fabius`; inspect with `codex plugin list --marketplace fabius`. Use the host's plugin controls to disable, or `codex plugin remove fabius@fabius` to uninstall. Restart and verify. CLI, desktop and IDE are separate acceptance targets.

Grok Build: `grok plugin update fabius` updates an unpinned install; `grok plugin disable fabius` and `grok plugin uninstall fabius` manage activation/removal. Version 0.2.103 skips pinned refs on update: review the intended new release before transitioning a pin. Start a fresh session.

`stop fabius` asks the model to drop the stance for the conversation. It does not uninstall the plugin, erase host chat history or revoke connected-account permissions. Host controls remain authoritative. Removing a plugin is not a promise to erase records you asked it to save.

[Compatibility evidence](COMPATIBILITY.md) · [Help](SUPPORT.md)
