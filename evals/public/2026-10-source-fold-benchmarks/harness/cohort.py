#!/usr/bin/env python3
"""The source-fold continuation cohort (evals/public/2026-10-source-fold-benchmarks/PROTOCOL.md, Codex, 2026-10-10,
and its addendum): three contemporary arms on eleven benchmarks, run with this study's harness.

Active when FB_COHORT=fold. ROOT then comes from FB_ROOT (the cohort's own data root). Arms:
  baseline  — the task verbatim, no package
  old       — the frozen v3.3.0-sealed package (filtered, INPUTS.json), invoked by the benchmark's owner
  candidate — the frozen fold candidate 6fb0ab0 (filtered, INPUTS.json), the same invocation
The owner invocation is /fabius for IFEval (the router) and /fabius:fabius-<owner> elsewhere.

Single-turn runs get Skill plus Read confined to the run's own directory and, in the package arms, that
arm's package directory; every other path stays denied. The schedule is Codex's schedule.jsonl (seed
20261010): item order per benchmark and the arm order of every item/sample block.
"""
import json
import os
from pathlib import Path

ACTIVE = os.environ.get("FB_COHORT") == "fold"
ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
PKG = {"old": "/private/tmp/fbpkg/old/fabius", "candidate": "/private/tmp/fbpkg/candidate/fabius"}
OWNER = {"swebench": "disciplina", "ifeval": None, "humaneval": "parcus", "cyberseceval": "praesidium",
         "labbench": "scientia", "finqa": "fortuna", "ds1000": "doctrina", "smartbugs": "catena",
         "bfcl": "cohors", "longmemeval": "archivum", "design2code": "decor"}
ARM_ORDER = ["baseline", "old", "candidate"]
ASSET_BENCH = {"design2code"}  # the task's asset (the screenshot) is copied into the run directory


def prefix(bench):
    owner = OWNER[bench]
    return "/fabius " if owner is None else f"/fabius:fabius-{owner} "


def arms(bench):
    """{arm: (prompt prefix, plugin dir or None)} for one benchmark."""
    p = prefix(bench)
    return {"baseline": ("", None), "old": (p, PKG["old"]), "candidate": (p, PKG["candidate"])}


def single_turn_access(arm, cwd):
    """(--tools, --allowedTools) for a single-turn run: Skill, and Read confined to the run directory and
    the arm's package. The deny list in claude_run.DENY still applies on top."""
    allowed = ["Skill", f"Read(//{str(cwd).lstrip('/')}/**)"]
    pkg = PKG.get(arm)
    if pkg:
        allowed.append(f"Read(//{pkg.lstrip('/')}/**)")
    return "Skill,Read", allowed


def schedule(path=None):
    """Codex's schedule.jsonl -> {bench: {"items": [...], "blocks": {(item, sample): [arms]}}}; the item list
    keeps first appearance order, samples 1 and 2 of SWE-bench share the item list."""
    path = Path(path or ROOT / "schedule.jsonl")
    out = {}
    for line in open(path):
        r = json.loads(line)
        b = out.setdefault(r["benchmark"], {"items": [], "blocks": {}})
        if r["item_id"] not in b["items"]:
            b["items"].append(r["item_id"])
        b["blocks"][(r["item_id"], int(r.get("sample") or 1))] = list(r["arms"])
    return out


def design2code_prompt(prompt, cwd, item):
    """The frozen prompt names the screenshot by an absolute path under the data root; in a run it is the
    copy inside the run directory. Identical substitution in every arm."""
    import re
    return re.sub(r"(the PNG image file at )\S+?(\.png)", lambda m: f"{m.group(1)}{cwd}/{item}.png", prompt, count=1)
