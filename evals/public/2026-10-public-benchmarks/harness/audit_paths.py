#!/usr/bin/env python3
"""Audit every scored stream for out-of-bounds access and answer-seeking (PROTOCOL.md v1.2).

Flags, per (benchmark, item, arm): a tool input naming a path outside the run's working
directory and the plugin directory; any input containing the benchmark directory, a
HuggingFace cache, 'swebench', 'test_patch' or 'FAIL_TO_PASS'; and wrapper commands that
search history beyond the workspace (git log --all, reflog, fsck --lost-found). Writes
results/audit.json. The primary endpoints are reported with and without flagged items.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
PLUGIN = "/private/tmp/fbplugin/fabius"
SUSPECT = re.compile(r"fabius-benchmark|\.cache/huggingface|swebench|test_patch|FAIL_TO_PASS", re.I)
HISTORY = re.compile(r"git\s+(log|rev-list)\s+[^|;&]*--all|reflog|fsck\s+--lost-found|git\s+cat-file\s+--batch-all", re.I)
PATH_RE = re.compile(r"(/(?:Users|private|tmp|var|opt|etc|home|root)[^\s'\"`)]*)")


def audit_stream(stream, cwd):
    """Host-side access is what matters. Read/Edit/Write/Glob/Grep paths and Bash commands that do not go
    through the run's wrapper run on the host; a wrapper command runs inside the network-less container,
    so the paths in it are container paths (/testbed, /tmp, /opt) and only answer-seeking is checked there."""
    flags = []
    root = str(Path(cwd).parent) if cwd else ""
    wrapper = root + "/run"
    allowed = (str(cwd), root, PLUGIN, "/private/tmp/fbplugin", "/private/tmp/fbpkg", "/private/tmp/claude-501",
               "/tmp/claude-501")  # /private/tmp/fbpkg: the continuation's package directories (cohort.PKG)
    for line in open(stream):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for b in ev.get("message", {}).get("content", []) or []:
            if b.get("type") != "tool_use":
                continue
            inp = b.get("input", {}) or {}
            blob = json.dumps(inp)
            if SUSPECT.search(blob):
                flags.append({"tool": b["name"], "why": "suspect term", "input": blob[:300]})
            if b["name"] == "Bash":
                cmd = (inp.get("command") or "").strip()
                if HISTORY.search(cmd):
                    flags.append({"tool": "Bash", "why": "history search", "input": cmd[:300]})
                if cmd.startswith(wrapper):
                    continue  # runs in the container
                for p in PATH_RE.findall(cmd):
                    if not p.startswith(allowed):
                        flags.append({"tool": "Bash", "why": "host path outside run", "input": p[:200]})
            else:
                for key in ("file_path", "path", "notebook_path"):
                    p = inp.get(key)
                    if p and p.startswith("/") and not p.startswith(allowed):
                        flags.append({"tool": b["name"], "why": "host path outside run", "input": p[:200]})
    return flags


def main():
    out = {}
    for stream in ROOT.glob("runs/**/attempt-*/stream.jsonl"):
        adir = stream.parent
        res = adir.parent / "result.json"
        if not res.exists() or json.loads(res.read_text()).get("scored_attempt") != int(adir.name.split("-")[1]):
            continue
        cwd = json.loads((adir / "cmd.json").read_text()).get("cwd", "")
        flags = audit_stream(stream, cwd)
        if flags:
            out[str(adir.relative_to(ROOT / "runs"))] = flags
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/audit.json").write_text(json.dumps(out, indent=1))
    print(f"flagged scored attempts: {len(out)}")
    for k, v in list(out.items())[:20]:
        print(" ", k, v[0]["why"], v[0]["input"][:120])


if __name__ == "__main__":
    main()
