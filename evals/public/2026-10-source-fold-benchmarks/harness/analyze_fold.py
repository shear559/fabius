#!/usr/bin/env python3
"""The continuation's analysis, fixed before generation (PROTOCOL.md of the source-fold cohort + ADDENDUM.md).

  FB_COHORT=fold FB_ROOT=<root> analyze_fold.py --json results/fold-analysis.json

One quality family of 33 contrasts: candidate − old, candidate − baseline and old − baseline on each of the
eleven benchmarks, Holm-corrected together; a contrast with no paired observations keeps its place in the
family as INCOMPLETE. Procedures as registered: one binary result per item -> exact McNemar + Newcombe
hybrid-score interval; two samples per item (SWE-bench) -> paired sign-flip test + BCa interval stratified by
repository; the continuous Design2Code score -> paired mean difference, sign-flip test, BCa interval.
Verdicts from the Holm-adjusted p alone: GAIN / LOSS at p <= 0.05; on the binary single-turn benchmarks TIE
when the 90% interval lies inside +-5 points and NON-INFERIOR when the 95% lower bound is above -5 points;
INCONCLUSIVE otherwise, and always so for SWE-bench and Design2Code short of GAIN / LOSS (no margin there).
Descriptive: cost, tokens, time and turns per contrast (geometric mean ratio, BCa interval), exposure (first-turn
prompt growth, package reads delivered), and the minimum detectable effect at the realised n.
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import analyze as A  # noqa: E402

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
BENCHES = ["swebench", "ifeval", "humaneval", "cyberseceval", "labbench", "finqa", "ds1000", "smartbugs", "bfcl",
           "longmemeval", "design2code"]
CONTRASTS = [("candidate", "old"), ("candidate", "baseline"), ("old", "baseline")]
CONTINUOUS = {"design2code": "score_score"}
MARGIN_BENCHES = {"ifeval", "humaneval", "cyberseceval", "labbench", "finqa", "ds1000", "smartbugs", "bfcl", "longmemeval"}
TIE = 0.05


def load(bench):
    p = ROOT / "results" / bench / "items.csv" if bench in ("swebench", "ifeval", "humaneval") \
        else ROOT / "results" / "skills" / bench / "items.csv"
    if bench == "swebench":  # one file per replicate from score_swe.py; both samples of an item pair together
        rows = []
        for rep in (1, 2):
            q = ROOT / "results" / "swebench" / f"items-r{rep}.csv"
            if q.exists():
                rows += list(csv.DictReader(open(q)))
        if not rows:
            return []
    elif not p.exists():
        return []
    else:
        rows = list(csv.DictReader(open(p)))
    for r in rows:
        r["replicate"] = int(r.get("replicate") or 1)
        r["passed"] = None if r.get("passed") in ("", None) else int(float(r["passed"]))
        if r.get("cost_microusd") in ("", None) and r.get("cost_usd") not in ("", None):
            r["cost_microusd"] = round(float(r["cost_usd"]) * 1e6)
    return rows


def paired(rows, arm, control, col="passed"):
    by = {}
    for r in rows:
        v = r.get(col)
        if r.get("excluded") or v in ("", None):
            continue
        by.setdefault(r["item"], {}).setdefault(r["arm"], []).append(float(v))
        by[r["item"]]["repo"] = r.get("repo") or ""
    return {i: (v[arm], v[control], v["repo"]) for i, v in by.items() if arm in v and control in v}


def compare_binary(rows, arm, control):
    pr = paired(rows, arm, control)
    n = len(pr)
    k = max((len(t) for t, _, _ in pr.values()), default=1)
    out = {"arm": arm, "control": control, "n": n, "k": k}
    if n == 0:
        return out
    if k == 1:
        a = sum(1 for t, b, _ in pr.values() if t[0] and b[0])
        bb = sum(1 for t, b, _ in pr.values() if t[0] and not b[0])
        c = sum(1 for t, b, _ in pr.values() if not t[0] and b[0])
        d = n - a - bb - c
        delta, lo95, hi95 = A.newcombe_paired(a, bb, c, d, 0.95)
        _, lo90, hi90 = A.newcombe_paired(a, bb, c, d, 0.90)
        out.update({"a": a, "b": bb, "c": c, "d": d, "rate_treated": (a + bb) / n, "rate_control": (a + c) / n,
                    "delta": delta, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "p": A.mcnemar_exact(bb, c),
                    "discordance": (bb + c) / n, "test": "exact McNemar", "interval": "Newcombe hybrid score"})
    else:
        dvals = [np.mean(t) - np.mean(b) for t, b, _ in pr.values()]
        strata = [repo for _, _, repo in pr.values()]
        theta, lo95, hi95 = A.bca(dvals, strata=strata if any(strata) else None)
        _, lo90, hi90 = A.bca(dvals, strata=strata if any(strata) else None, conf=0.90)
        out.update({"rate_treated": float(np.mean([np.mean(t) for t, _, _ in pr.values()])),
                    "rate_control": float(np.mean([np.mean(b) for _, b, _ in pr.values()])),
                    "delta": theta, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "p": A.sign_flip(dvals),
                    "test": "paired sign-flip", "interval": "BCa bootstrap (stratified)"})
    return out


def compare_continuous(rows, arm, control, col):
    pr = paired(rows, arm, control, col)
    n = len(pr)
    out = {"arm": arm, "control": control, "n": n, "k": 1, "endpoint": col}
    if n == 0:
        return out
    dvals = [t[0] - b[0] for t, b, _ in pr.values()]
    theta, lo95, hi95 = A.bca(dvals)
    _, lo90, hi90 = A.bca(dvals, conf=0.90)
    out.update({"mean_treated": float(np.mean([t[0] for t, _, _ in pr.values()])),
                "mean_control": float(np.mean([b[0] for _, b, _ in pr.values()])),
                "delta": theta, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "p": A.sign_flip(dvals),
                "test": "paired sign-flip", "interval": "BCa bootstrap"})
    return out


def verdict(c, bench, p_adj):
    if c.get("n", 0) == 0:
        return "INCOMPLETE"
    if p_adj <= 0.05:
        return "GAIN" if c["delta"] > 0 else "LOSS"
    if bench in MARGIN_BENCHES:
        if c["ci90"][0] > -TIE and c["ci90"][1] < TIE:
            return "TIE"
        if c["ci95"][0] > -TIE:
            return "NON-INFERIOR"
    return "INCONCLUSIVE"


def efficiency(rows, arm, control, metric):
    by = {}
    for r in rows:
        if r.get("excluded") or r.get(metric) in ("", None):
            continue
        by.setdefault((r["item"], r["replicate"]), {})[r["arm"]] = float(r[metric])
    rs = [math.log((v[arm] + 1) / (v[control] + 1)) for v in by.values() if arm in v and control in v]
    if len(rs) < 3:
        return None
    m, lo, hi = A.bca(rs)
    return {"n": len(rs), "ratio": math.exp(m), "ci95": [math.exp(lo), math.exp(hi)]}


def exposure(rows, arm):
    rr = [r for r in rows if r["arm"] == arm and not r.get("excluded")]
    base = {(r["item"], r["replicate"]): r.get("first_turn_prompt_tokens") for r in rows if r["arm"] == "baseline"}
    grow, inj = [], 0
    reads_del = reads_den = runs_reading = 0
    for r in rr:
        b, t = base.get((r["item"], r["replicate"])), r.get("first_turn_prompt_tokens")
        if b not in ("", None) and t not in ("", None):
            g = float(t) - float(b)
            grow.append(g)
            inj += g >= 2500
        d, x = int(r.get("package_reads_delivered") or 0), int(r.get("package_reads_denied") or 0)
        reads_del += d
        reads_den += x
        runs_reading += d > 0
    return {"n": len(rr), "contract_injected": inj, "first_turn_growth_median": float(np.median(grow)) if grow else None,
            "runs_with_a_delivered_package_read": runs_reading, "package_reads_delivered": reads_del,
            "package_reads_denied": reads_den}


def main():
    out_path = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    rep = {"family": "all 33 contrasts, Holm over the complete family", "comparisons": {}, "efficiency": {},
           "exposure": {}, "mde": {}}
    cmps = []
    for bench in BENCHES:
        rows = load(bench)
        for arm, control in CONTRASTS:
            if bench in CONTINUOUS:
                c = compare_continuous(rows, arm, control, CONTINUOUS[bench]) if rows else {"arm": arm, "control": control, "n": 0}
            else:
                c = compare_binary(rows, arm, control) if rows else {"arm": arm, "control": control, "n": 0}
            cmps.append((bench, arm, control, c))
            for m in ("output_tokens", "total_tokens", "cost_microusd", "elapsed_s", "num_turns", "patch_lines"):
                e = efficiency(rows, arm, control, m) if rows else None
                if e:
                    rep["efficiency"][f"{arm} vs {control} · {bench} · {m}"] = e
        if rows:
            for arm in ("old", "candidate"):
                rep["exposure"][f"{arm} · {bench}"] = exposure(rows, arm)
            n = max((c["n"] for b, _, _, c in cmps if b == bench), default=0)
            if n and bench not in CONTINUOUS:
                rep["mde"][bench] = {f"psi={psi}": A.mde_exact_mcnemar(n, 0.05 / 33, psi) for psi in (0.1, 0.2, 0.3)}
    ps = [c["p"] if c.get("n") else 1.0 for _, _, _, c in cmps]  # an incomplete contrast keeps its place (p = 1)
    adj = A.holm(ps)
    for (bench, arm, control, c), pa in zip(cmps, adj):
        c["p_holm"] = pa if c.get("n") else None
        c["verdict"] = verdict(c, bench, pa)
        rep["comparisons"][f"{arm} vs {control} · {bench}"] = c
    txt = json.dumps(rep, indent=1, default=float)
    print(txt)
    if out_path:
        Path(out_path).write_text(txt)


if __name__ == "__main__":
    main()
