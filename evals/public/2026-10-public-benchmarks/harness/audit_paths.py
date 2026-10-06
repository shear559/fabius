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

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
PLUGIN = "/private/tmp/fbplugin/fabius"
SUSPECT = re.compile(r"fabius-benchmark|\.cache/huggingface|swebench|test_patch|FAIL_TO_PASS", re.I)
HISTORY = re.compile(r"git\s+(log|rev-list)\s+[^|;&]*--all|reflog|fsck\s+--lost-found|git\s+cat-file\s+--batch-all", re.I)
PATH_RE = re.compile(r"(/(?:Users|private|tmp|var|opt|etc|home|root)[^\s'\"`)]*)")


def audit_stream(stream, cwd):
    flags = []
    allowed = (str(cwd), PLUGIN, "/private/tmp/fbplugin", "/testbed", "/tmp/claude", "/private/tmp/claude",
               "/opt/miniconda3", "/usr/local/bin/docker")
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
            blob = json.dumps(b.get("input", {}))
            if SUSPECT.search(blob):
                flags.append({"tool": b["name"], "why": "suspect term", "input": blob[:300]})
            if b["name"] == "Bash" and HISTORY.search(blob):
                flags.append({"tool": b["name"], "why": "history search", "input": blob[:300]})
            for p in PATH_RE.findall(blob):
                if not p.startswith(allowed):
                    flags.append({"tool": b["name"], "why": "path outside run", "input": p[:200]})
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
