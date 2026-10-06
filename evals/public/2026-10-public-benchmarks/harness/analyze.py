#!/usr/bin/env python3
"""Every published number, from items.csv only (PROTOCOL.md v1.1, Endpoints, tests, and verdicts).

  analyze.py <bench>... [--json out.json]

items.csv columns used: item, arm, replicate, passed (0/1, empty if excluded), excluded,
repo (SWE-bench), router_injected, fabius_skills_loaded, output_tokens, total_tokens,
cost_usd, elapsed_s, num_turns, patch_lines.
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
SEED = 20261006
PRIMARY = {"swebench": "resolved", "ifeval": "prompt-level strict", "humaneval": "plus pass@1"}
FAMILY1 = [("fabius-loaded", b) for b in ("swebench", "ifeval", "humaneval")]
FAMILY2 = [("fabius-doc", b) for b in ("ifeval", "humaneval")]
TIE_MARGIN = 0.05


# ---------------------------------------------------------------- tests and intervals
def mcnemar_exact(b, c):
    m = b + c
    if m == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * stats.binom.cdf(k, m, 0.5))


def wilson(x, n, z):
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def newcombe_paired(a, b, c, d, conf):
    """Newcombe (1998) method 10: hybrid score interval for a difference of paired proportions.
    a both pass, b treated only, c baseline only, d neither. Returns (delta, lower, upper)."""
    n = a + b + c + d
    z = stats.norm.ppf(1 - (1 - conf) / 2)
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = wilson(a + b, n, z)
    l2, u2 = wilson(a + c, n, z)
    delta = p1 - p2
    den = (a + b) * (c + d) * (a + c) * (b + d)
    phi = 0.0
    if den > 0:  # method 10: the plain phi coefficient; 0 when undefined
        phi = (a * d - b * c) / math.sqrt(den)
    dl = math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    du = math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return delta, delta - dl, delta + du


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def sign_flip(d, seed=SEED, mc=100_000):
    d = np.asarray([x for x in d if x != 0], float)
    m = len(d)
    if m == 0:
        return 1.0
    stat = abs(d.sum())
    if m <= 20:
        signs = ((np.arange(2 ** m)[:, None] >> np.arange(m)) & 1) * 2 - 1
        return float((np.abs((signs * d).sum(1)) >= stat - 1e-12).sum() / 2 ** m)
    rng = np.random.default_rng(seed)
    flips = rng.choice([-1, 1], size=(mc, m))
    count = (np.abs((flips * d).sum(1)) >= stat - 1e-12).sum()
    return float((1 + count) / (1 + mc))


def bca(values, stat=np.mean, strata=None, conf=0.95, b=10_000, seed=SEED):
    """BCa bootstrap interval of stat(values); resampling within strata when given."""
    x = np.asarray(values, float)
    n = len(x)
    rng = np.random.default_rng(seed)
    theta = stat(x)
    if strata is None:
        idx = rng.integers(0, n, size=(b, n))
    else:
        strata = np.asarray(strata)
        groups = [np.where(strata == s)[0] for s in sorted(set(strata.tolist()))]
        idx = np.concatenate([g[rng.integers(0, len(g), size=(b, len(g)))] for g in groups], axis=1)
    boot = np.array([stat(x[i]) for i in idx])
    prop = np.clip((boot < theta).mean() + 0.5 * (boot == theta).mean(), 1e-6, 1 - 1e-6)
    z0 = stats.norm.ppf(prop)
    jack = np.array([stat(np.delete(x, i)) for i in range(n)])
    jm = jack.mean()
    num, den = ((jm - jack) ** 3).sum(), 6 * (((jm - jack) ** 2).sum() ** 1.5)
    acc = num / den if den > 0 else 0.0
    zs = stats.norm.ppf([(1 - conf) / 2, 1 - (1 - conf) / 2])
    adj = stats.norm.cdf(z0 + (z0 + zs) / (1 - acc * (z0 + zs)))
    lo, hi = np.quantile(boot, adj)
    return float(theta), float(lo), float(hi)


def mde_exact_mcnemar(n, alpha, psi, power=0.8):
    """Smallest difference (points of n) the exact McNemar test detects with the given power."""
    def pw(delta):
        p_b = (psi + delta) / (2 * psi)
        tot = 0.0
        for m in range(0, n + 1):
            pm = stats.binom.pmf(m, n, psi)
            if pm < 1e-12 or m == 0:
                continue
            ks = np.arange(m + 1)
            pv = np.minimum(1.0, 2 * stats.binom.cdf(np.minimum(ks, m - ks), m, 0.5))
            tot += pm * stats.binom.pmf(ks, m, p_b)[pv <= alpha].sum()
        return tot
    lo, hi = 0.0, psi
    if pw(hi) < power:
        return None
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if pw(mid) < power else (lo, mid)
    return hi


# ---------------------------------------------------------------- data
def load(bench):
    path = ROOT / "results" / bench / "items.csv"
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r["replicate"] = int(r.get("replicate") or 1)
        r["passed"] = None if r.get("passed") in ("", None) else int(float(r["passed"]))
    return rows


def paired(rows, arm):
    """item -> (treated passes list, baseline passes list, repo), items complete in both arms."""
    by = {}
    for r in rows:
        if r.get("excluded") or r["passed"] is None:
            continue
        by.setdefault(r["item"], {}).setdefault(r["arm"], []).append(r["passed"])
        by[r["item"]]["repo"] = r.get("repo") or ""
    return {i: (v[arm], v["baseline"], v["repo"]) for i, v in by.items() if arm in v and "baseline" in v}


def compare(rows, arm):
    pr = paired(rows, arm)
    n = len(pr)
    k = max((len(t) for t, _, _ in pr.values()), default=1)
    out = {"arm": arm, "n": n, "k": k}
    if n == 0:
        return out
    if k == 1:
        a = sum(1 for t, b, _ in pr.values() if t[0] and b[0])
        bb = sum(1 for t, b, _ in pr.values() if t[0] and not b[0])
        c = sum(1 for t, b, _ in pr.values() if not t[0] and b[0])
        d = n - a - bb - c
        delta, lo95, hi95 = newcombe_paired(a, bb, c, d, 0.95)
        _, lo90, hi90 = newcombe_paired(a, bb, c, d, 0.90)
        out.update({"a": a, "b": bb, "c": c, "d": d, "rate_treated": (a + bb) / n, "rate_baseline": (a + c) / n,
                    "delta": delta, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "p": mcnemar_exact(bb, c),
                    "discordance": (bb + c) / n, "test": "exact McNemar", "interval": "Newcombe hybrid score"})
    else:
        dvals = [np.mean(t) - np.mean(b) for t, b, _ in pr.values()]
        strata = [repo for _, _, repo in pr.values()]
        theta, lo95, hi95 = bca(dvals, strata=strata if any(strata) else None)
        _, lo90, hi90 = bca(dvals, strata=strata if any(strata) else None, conf=0.90)
        out.update({"rate_treated": float(np.mean([np.mean(t) for t, _, _ in pr.values()])),
                    "rate_baseline": float(np.mean([np.mean(b) for _, b, _ in pr.values()])),
                    "delta": theta, "ci95": [lo95, hi95], "ci90": [lo90, hi90], "p": sign_flip(dvals),
                    "test": "paired sign-flip", "interval": "BCa bootstrap (stratified)"})
    return out


def verdict(cmp, bench, p_adj):
    if p_adj <= 0.05:
        return "GAIN" if cmp["delta"] > 0 else "LOSS"
    if bench != "swebench":
        if cmp["ci90"][0] > -TIE_MARGIN and cmp["ci90"][1] < TIE_MARGIN:
            return "TIE"
        if cmp["ci95"][0] > -TIE_MARGIN:
            return "NON-INFERIOR"
    return "INCONCLUSIVE"


def efficiency(rows, arm, metric, within_both_passed=False):
    by = {}
    for r in rows:
        if r.get("excluded") or r.get(metric) in ("", None):
            continue
        by.setdefault((r["item"], r["replicate"]), {})[r["arm"]] = (float(r[metric]), r["passed"])
    rs = []
    for v in by.values():
        if arm in v and "baseline" in v:
            if within_both_passed and not (v[arm][1] and v["baseline"][1]):
                continue
            rs.append(math.log((v[arm][0] + 1) / (v["baseline"][0] + 1)))
    if len(rs) < 3:
        return None
    m, lo, hi = bca(rs)
    return {"n": len(rs), "ratio": math.exp(m), "ci95": [math.exp(lo), math.exp(hi)]}


def load_rates(rows, arm):
    rr = [r for r in rows if r["arm"] == arm and not r.get("excluded") and r.get("router_injected") not in ("", None)]
    n = len(rr)
    z = stats.norm.ppf(0.975)
    inj = sum(1 for r in rr if str(r["router_injected"]).lower() == "true")
    skills = {}
    for r in rr:
        for s in json.loads(r.get("fabius_skills_loaded") or "[]"):
            skills[s] = skills.get(s, 0) + 1
    return {"n": n, "router_injected": inj, "router_injected_ci": wilson(inj, n, z) if n else None,
            "skill_loads": {s: {"runs": c, "rate": c / n, "ci": wilson(c, n, z)} for s, c in sorted(skills.items())}}


def main():
    benches = [b for b in sys.argv[1:] if not b.startswith("--")]
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    data = {b: load(b) for b in benches}
    report = {"comparisons": {}, "efficiency": {}, "load": {}, "mde": {}}
    for fam_name, fam in (("family1", FAMILY1), ("family2", FAMILY2)):
        cmps = [(arm, b, compare(data[b], arm)) for arm, b in fam if b in data]
        cmps = [(arm, b, c) for arm, b, c in cmps if c.get("n")]
        adj = holm([c["p"] for _, _, c in cmps]) if cmps else []
        for (arm, b, c), pa in zip(cmps, adj):
            c["p_holm"] = pa
            c["family"] = fam_name
            c["verdict"] = verdict(c, b, pa)
            report["comparisons"][f"{arm} vs baseline · {b}"] = c
    if "swebench" in data:  # descriptive fabius-doc subset
        c = compare(data["swebench"], "fabius-doc")
        if c.get("n"):
            c["family"] = "descriptive"
            report["comparisons"]["fabius-doc vs baseline · swebench (subset, descriptive)"] = c
    for b, rows in data.items():
        for arm in ("fabius-loaded", "fabius-doc"):
            report["load"][f"{arm} · {b}"] = load_rates(rows, arm)
            for metric in ("output_tokens", "total_tokens", "cost_usd", "elapsed_s", "num_turns", "patch_lines"):
                e = efficiency(rows, arm, metric)
                if e:
                    report["efficiency"][f"{arm} · {b} · {metric}"] = e
                if b == "swebench":
                    e2 = efficiency(rows, arm, metric, within_both_passed=True)
                    if e2:
                        report["efficiency"][f"{arm} · {b} · {metric} · both resolved"] = e2
        n = len({r["item"] for r in rows if not r.get("excluded")})
        report["mde"][b] = {f"alpha={al:.4f},psi={psi}": mde_exact_mcnemar(n, al, psi)
                            for al in (0.05 / 3, 0.05) for psi in (0.1, 0.2, 0.3)}
    txt = json.dumps(report, indent=1, default=float)
    print(txt)
    if out_json:
        Path(out_json).write_text(txt)


if __name__ == "__main__":
    main()
