#!/usr/bin/env python3
"""Part B numbers (PROTOCOL-SKILLS.md): each skill arm vs baseline on its benchmark, Family B Holm-corrected,
verdicts by the Part A rules, load rates, efficiency, and minimum detectable effects. Reads items.csv only.

  analyze_skills.py <bench:skill>... --json out.json
  benches: swebench (results/swebench/items.csv, Part A baseline reused), humaneval (results/humaneval/items.csv),
  anything else from results/skills/<bench>/items.csv
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import analyze as A  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))


def load(bench):
    p = ROOT / "results" / bench / "items.csv" if bench in ("swebench", "humaneval") else ROOT / "results/skills" / bench / "items.csv"
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        r["replicate"] = int(r.get("replicate") or 1)
        r["passed"] = None if r.get("passed") in ("", None) else int(float(r["passed"]))
        if r.get("cost_microusd") in ("", None) and r.get("cost_usd") not in ("", None):
            r["cost_microusd"] = round(float(r["cost_usd"]) * 1e6)
    return rows


def injected(rows, arm, threshold=2500):
    base = {(r["item"], r["replicate"]): r.get("first_turn_prompt_tokens") for r in rows if r["arm"] == "baseline"}
    n = inj = 0
    for r in rows:
        if r["arm"] != arm or r.get("excluded") or r.get("first_turn_prompt_tokens") in ("", None):
            continue
        b = base.get((r["item"], r["replicate"])) or base.get((r["item"], 1))
        if b in ("", None):
            continue
        n += 1
        inj += float(r["first_turn_prompt_tokens"]) - float(b) >= threshold
    return {"n": n, "skill_injected": inj}


def main():
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    pairs = [a.split(":") for a in sys.argv[1:] if ":" in a]
    rep = {"comparisons": {}, "load": {}, "efficiency": {}, "mde": {}}
    cmps = []
    for bench, skill in pairs:
        rows = load(bench)
        arm = f"fabius-{skill}"
        c = A.compare(rows, arm)
        if not c.get("n"):
            continue
        cmps.append((bench, skill, c))
        rep["load"][f"{arm} · {bench}"] = {**injected(rows, arm),
                                           "skill_tool_loads": A.load_rates(rows, arm)["skill_loads"]}
        for m in ("output_tokens", "total_tokens", "cost_microusd", "elapsed_s", "num_turns", "patch_lines"):
            e = A.efficiency(rows, arm, m)
            if e:
                rep["efficiency"][f"{arm} · {bench} · {m}"] = e
        n = c["n"]
        rep["mde"][bench] = {f"psi={psi}": A.mde_exact_mcnemar(n, 0.05 / max(1, len(pairs)), psi) for psi in (0.1, 0.2, 0.3)}
    adj = A.holm([c["p"] for _, _, c in cmps])
    for (bench, skill, c), pa in zip(cmps, adj):
        c["p_holm"] = pa
        c["family"] = "B"
        c["verdict"] = A.verdict(c, bench, pa)
        rep["comparisons"][f"fabius-{skill} vs baseline · {bench}"] = c
    txt = json.dumps(rep, indent=1, default=float)
    print(txt)
    if out:
        Path(out).write_text(txt)


if __name__ == "__main__":
    main()
