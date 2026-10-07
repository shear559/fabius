#!/usr/bin/env python3
"""Seeded schedule for the Part B benchmarks (PROTOCOL-SKILLS.md): item order and per-item arm order
from numpy default_rng(20261006) per benchmark, written once per benchmark before its first run.

  schedule_skills.py <bench> <skill>
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))


def main():
    bench, skill = sys.argv[1], sys.argv[2]
    items = [json.loads(l)["item"] for l in open(ROOT / "skills-bench" / bench / "items.jsonl")]
    path = ROOT / "schedule-skills.json"
    sched = json.load(open(path)) if path.exists() else {}
    if bench in sched:
        raise SystemExit(f"{bench} is already scheduled; a schedule is written once")
    rng = np.random.default_rng(20261006)
    order = [items[j] for j in rng.permutation(len(items))]
    arms = ["baseline", f"fabius-{skill}"]
    sched[bench] = {"skill": skill, "items": order,
                    "arm_order": {i: [arms[j] for j in rng.permutation(2)] for i in order}, "excluded": {}}
    path.write_text(json.dumps(sched, indent=1))
    print(bench, skill, len(order), "items scheduled")


if __name__ == "__main__":
    main()
