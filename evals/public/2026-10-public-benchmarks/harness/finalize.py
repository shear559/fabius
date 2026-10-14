#!/usr/bin/env python3
"""Final numbers for the report (PROTOCOL.md v1.4): the pre-registered analysis plus the declared
sensitivities, and clearly labelled exploratory descriptions.

1. results/swebench/items.csv = replicate 1 + replicate 2 rows; cost_microusd added to every items.csv
   (the pre-registered efficiency formula adds 1 to each value, which is meaningless for costs in dollars;
   the cost ratio is therefore also computed in millionths of a dollar — both are reported).
2. analyze.py over the three benchmarks -> results/analysis.json (families, Holm, verdicts, MDE, loads,
   efficiency).
3. Declared sensitivities: SWE-bench per replicate (k = 1 each); the baseline's replicate-to-replicate
   disagreement; the primary endpoints without audit-flagged items; IFEval loose / no repeat_prompt /
   all text blocks; HumanEval+ base tests; the unfiltered SWE-bench patches when scored.
4. Exploratory (not pre-registered): how often the SWE-bench agent attempted a command in the test container, and how often one executed.
"""
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import analyze as A  # noqa: E402

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
RES = ROOT / "results"


def rewrite_with_micro(path):
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return
    fields = list(rows[0].keys()) + (["cost_microusd"] if "cost_microusd" not in rows[0] else [])
    for r in rows:
        r["cost_microusd"] = "" if r.get("cost_usd") in ("", None) else round(float(r["cost_usd"]) * 1e6)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def merge_swe():
    rows = []
    for rep in (1, 2):
        p = RES / "swebench" / f"items-r{rep}.csv"
        if p.exists():
            rows += list(csv.DictReader(open(p)))
    with open(RES / "swebench" / "items.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def cmp_rows(rows, arm, keep=lambda r: True, col="passed"):
    rr = [dict(r, passed=(None if r.get(col) in ("", None) else int(float(r[col])))) for r in rows if keep(r)]
    for r in rr:
        r["replicate"] = int(r.get("replicate") or 1)
    return A.compare(rr, arm)


def short(c):
    if not c.get("n"):
        return None
    keys = ("n", "k", "a", "b", "c", "d", "rate_treated", "rate_baseline", "delta", "ci95", "ci90", "p", "test")
    return {k: c[k] for k in keys if k in c}


def main():
    merge_swe()
    for b in ("swebench", "ifeval", "humaneval"):
        rewrite_with_micro(RES / b / "items.csv")
    out = RES / "analysis.json"
    os.system(f"{sys.executable} {Path(__file__).parent / 'analyze.py'} swebench ifeval humaneval --json {out} > /dev/null")
    analysis = json.load(open(out))
    data = {b: A.load(b) for b in ("swebench", "ifeval", "humaneval")}
    for b, rows in data.items():  # cost ratio in micro-dollars (see docstring)
        for arm in ("fabius-loaded", "fabius-doc"):
            e = A.efficiency(rows, arm, "cost_microusd")
            if e:
                analysis["efficiency"][f"{arm} · {b} · cost_microusd"] = e
    sens = {}
    swe = data["swebench"]
    for rep in (1, 2):
        sens[f"swebench · fabius-loaded vs baseline · replicate {rep} only"] = short(
            cmp_rows(swe, "fabius-loaded", lambda r, rep=rep: int(r["replicate"]) == rep))
    base = {}
    for r in swe:
        if r["arm"] == "baseline" and r["passed"] is not None:
            base.setdefault(r["item"], {})[int(r["replicate"])] = r["passed"]
    pairs = [v for v in base.values() if 1 in v and 2 in v]
    sens["swebench · baseline replicate 1 vs replicate 2 disagreement (A/A)"] = {
        "n": len(pairs), "disagree": sum(1 for v in pairs if v[1] != v[2]),
        "rate": sum(1 for v in pairs if v[1] != v[2]) / len(pairs) if pairs else None}
    loaded = {}
    for r in swe:
        if r["arm"] == "fabius-loaded" and r["passed"] is not None:
            loaded.setdefault(r["item"], {})[int(r["replicate"])] = r["passed"]
    lp = [v for v in loaded.values() if 1 in v and 2 in v]
    sens["swebench · fabius-loaded replicate 1 vs replicate 2 disagreement"] = {
        "n": len(lp), "disagree": sum(1 for v in lp if v[1] != v[2])}
    audit = json.load(open(RES / "audit.json")) if (RES / "audit.json").exists() else {}
    # an item is flagged for a comparison when a run of either compared arm was flagged, in either replicate
    for arm in ("fabius-loaded", "fabius-disciplina"):
        flagged = {k.split("/")[2] for k in audit if k.startswith("swebench") and k.split("/")[3] in ("baseline", arm)}
        sens[f"swebench · {arm} vs baseline · without audit-flagged items"] = short(
            cmp_rows(swe, arm, lambda r: r["item"] not in flagged))
        sens[f"swebench · {arm} vs baseline · audit-flagged items"] = sorted(flagged)
    unf = RES / "swebench" / "items-unfiltered-r1.csv"
    if unf.exists():
        ur = list(csv.DictReader(open(unf)))
        for r in ur:
            r["passed"] = None if r["passed"] == "" else int(r["passed"])
        sens["swebench · unfiltered patches · replicate 1"] = short(A.compare(ur, "fabius-loaded"))
    ife = data["ifeval"]
    sens["ifeval · loose prompt-level"] = short(cmp_rows(ife, "fabius-loaded", col="loose_passed"))
    sens["ifeval · strict, excluding repeat_prompt prompts"] = short(
        cmp_rows(ife, "fabius-loaded", lambda r: r.get("has_repeat_prompt") == "0"))
    sens["ifeval · strict, all assistant text blocks"] = short(cmp_rows(ife, "fabius-loaded", col="passed_concat"))
    he = data["humaneval"]
    for arm in ("fabius-loaded", "fabius-doc"):
        sens[f"humaneval · {arm} vs baseline · base tests"] = short(cmp_rows(he, arm, col="base_passed"))
    analysis["sensitivities"] = sens
    # exploratory: did the SWE-bench agent attempt a command in the test container, and did one execute?
    from descriptives import container_calls
    expl = {}
    for rep in (1, 2):
        for arm in ("baseline", "fabius-loaded", "fabius-doc", "fabius-disciplina"):
            calls = []
            for res in (ROOT / "runs" / "swebench" / f"r{rep}").glob(f"*/{arm}/result.json"):
                rj = json.loads(res.read_text())
                if rj.get("scored_attempt"):
                    calls.append(container_calls(res.parent / f"attempt-{rj['scored_attempt']}"))
            if calls:
                n = len(calls)
                expl[f"swebench r{rep} · {arm} · test container"] = {
                    "runs": n, "attempted": sum(1 for a, _ in calls if a), "executed": sum(1 for _, e in calls if e),
                    "executed_rate": sum(1 for _, e in calls if e) / n}
    analysis["exploratory"] = expl
    out.write_text(json.dumps(analysis, indent=1, default=float))
    print(json.dumps({"comparisons": {k: {kk: v.get(kk) for kk in ("n", "k", "rate_treated", "rate_baseline", "delta",
                                                                     "ci95", "ci90", "p", "p_holm", "verdict")}
                                      for k, v in analysis["comparisons"].items()},
                      "sensitivities": sens, "exploratory": expl}, indent=1, default=float))


if __name__ == "__main__":
    main()
