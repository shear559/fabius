#!/usr/bin/env python3
"""Write schedule.json before the first scored run (PROTOCOL.md v1.1, Schedule).

Each benchmark gets a fresh numpy default_rng(20261006). Items run in a seeded order and all
arms of an item run back to back in a seeded order, so a stop removes whole items.
SWE-bench: permute the sorted Django IDs, then the sorted Sphinx IDs (the same two
permutations define the fabius-doc subset: first 5 valid of each), then alternate the two
repositories starting with Django.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
SEED = 20261006
ARMS3 = ["baseline", "fabius-doc", "fabius-loaded"]
EXCLUDED = {"humaneval": {"HumanEval_32": "canonical solution fails EvalPlus 0.3.1's own sandboxed check in the "
                                          "Linux scoring container before any input is evaluated (verified 2026-10-06)"}}


def arm_orders(rng, items):
    return {i: [ARMS3[j] for j in rng.permutation(len(ARMS3))] for i in items}


def single(bench, items):
    rng = np.random.default_rng(SEED)
    order = [items[j] for j in rng.permutation(len(items))]
    return {"items": order, "arm_order": arm_orders(rng, order), "excluded": EXCLUDED.get(bench, {})}


def swe(ids):
    rng = np.random.default_rng(SEED)
    dj = sorted(i for i in ids if i.startswith("django__"))
    sp = sorted(i for i in ids if i.startswith("sphinx-doc__"))
    dj_perm = [dj[j] for j in rng.permutation(len(dj))]
    sp_perm = [sp[j] for j in rng.permutation(len(sp))]
    order = [x for pair in zip(dj_perm, sp_perm) for x in pair]
    return {"items": order, "arm_order": arm_orders(rng, order),
            "django_permutation": dj_perm, "sphinx_permutation": sp_perm,
            "fabius_doc_rule": "first 5 valid instances of django_permutation and of sphinx_permutation",
            "excluded": {}}


def main():
    sys.path.insert(0, str(ROOT / "harness"))
    from bench_items import load_items  # noqa: E402
    sched = {"seed": SEED, "written_before_first_scored_run": True}
    for bench in ("humaneval", "ifeval"):
        items = [i for i, _ in load_items(bench) if i not in EXCLUDED.get(bench, {})]
        sched[bench] = single(bench, items)
    ids = [l.strip() for l in open(ROOT / "swebench-mini-ids.txt") if l.strip()]
    sched["swebench"] = swe(ids)
    out = ROOT / "schedule.json"
    if out.exists() and "--force" not in sys.argv:
        raise SystemExit("schedule.json exists; it is written once")
    out.write_text(json.dumps(sched, indent=1))
    s = sched["swebench"]
    print("humaneval items:", len(sched["humaneval"]["items"]), "| ifeval items:", len(sched["ifeval"]["items"]),
          "| swe items:", len(s["items"]))
    print("django permutation head:", [x.split("-")[-1] for x in s["django_permutation"][:7]])
    print("sphinx permutation head:", [x.split("-")[-1] for x in s["sphinx_permutation"][:7]])
    print("first humaneval items:", sched["humaneval"]["items"][:4], sched["humaneval"]["arm_order"][sched["humaneval"]["items"][0]])


if __name__ == "__main__":
    main()
