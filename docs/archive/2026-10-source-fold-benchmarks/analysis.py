#!/usr/bin/env python3
"""Paired analysis of the new cohort only, using the registered legacy procedures.

Input rows: benchmark, item_id (or item), sample (or replicate), arm, passed for
binary outcomes / score for Design2Code, and optional excluded/repo. Missing,
unscored, and infrastructure rows are missing observations, never zeroes.
Multiplicity families must be supplied by the new frozen protocol.
"""
import argparse
import json
import math
from collections import defaultdict
from statistics import NormalDist

from items import ARMS, METRICS, SKILLS

SEED = 20261006
CONTRASTS = (("old", "baseline"), ("candidate", "old"), ("candidate", "baseline"))
TIE_MARGIN = 0.05  # Registered only for objective single-turn binary endpoints.
PRIMARY_FAMILIES = {"primary_quality_33": [[b, t, c] for b in SKILLS for t, c in CONTRASTS]}


def mcnemar_exact(b, c):
    n = b + c
    if not n:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / (2 ** n))


def wilson(x, n, z):
    p, den = x / n, 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def newcombe_paired(a, b, c, d, conf=0.95):
    n = a + b + c + d
    z = NormalDist().inv_cdf(1 - (1 - conf) / 2)
    p1, p2 = (a + b) / n, (a + c) / n
    l1, u1 = wilson(a + b, n, z)
    l2, u2 = wilson(a + c, n, z)
    den = (a + b) * (c + d) * (a + c) * (b + d)
    phi = (a * d - b * c) / math.sqrt(den) if den > 0 else 0.0
    dl = math.sqrt(max(0.0, (p1-l1)**2 - 2*phi*(p1-l1)*(u2-p2) + (u2-p2)**2))
    du = math.sqrt(max(0.0, (u1-p1)**2 - 2*phi*(u1-p1)*(p2-l2) + (p2-l2)**2))
    return p1 - p2, p1 - p2 - dl, p1 - p2 + du


def holm(ps):
    adjusted, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(sorted(range(len(ps)), key=ps.__getitem__)):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adjusted[i] = running
    return adjusted


def mde_exact_mcnemar(n, alpha, discordance, power=0.8):
    """Registered 80%-power binary MDE, conditional on a specified discordance.

    This does not apply to SWE replicate means or the continuous visual score.
    None means even the largest admissible difference cannot achieve this power.
    """
    import numpy as np
    from scipy import stats
    if n <= 0 or not 0 < discordance <= 1 or not 0 < alpha < 1:
        raise ValueError("Invalid MDE parameters")
    terms = []
    for m in range(1, n + 1):
        pm = stats.binom.pmf(m, n, discordance)
        if pm < 1e-12:
            continue
        ks = np.arange(m + 1)
        ps = np.minimum(1.0, 2*stats.binom.cdf(np.minimum(ks, m-ks), m, 0.5))
        terms.append((m, pm, ks[ps <= alpha]))

    def achieved(delta):
        probability = (discordance + delta) / (2*discordance)
        return sum(pm*stats.binom.pmf(ks, m, probability).sum() for m, pm, ks in terms)

    lo, hi = 0.0, discordance
    if achieved(hi) < power:
        return None
    for _ in range(40):
        mid = (lo+hi)/2
        if achieved(mid) < power:
            lo = mid
        else:
            hi = mid
    return hi


def sign_flip(values, seed=SEED, mc=100_000):
    import numpy as np
    values = np.asarray([v for v in values if v != 0], dtype=float)
    n = len(values)
    if not n:
        return 1.0
    observed = abs(values.sum())
    if n <= 20:
        signs = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1) * 2 - 1
        return float((np.abs((signs * values).sum(axis=1)) >= observed - 1e-12).mean())
    rng = np.random.default_rng(seed)
    count = 0
    # Chunking bounds memory; draws still follow the same seeded sequence.
    for offset in range(0, mc, 1000):
        flips = rng.choice([-1, 1], size=(min(1000, mc-offset), n))
        count += int((np.abs((flips * values).sum(axis=1)) >= observed - 1e-12).sum())
    return (1 + count) / (1 + mc)


def bca(values, strata=None, conf=0.95, resamples=10_000, seed=SEED):
    """Registered BCa item bootstrap; no interval can be estimated from one item."""
    import numpy as np
    from scipy import stats
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n < 2:
        return float(x.mean()) if n else None, None, None
    rng = np.random.default_rng(seed)
    theta = x.mean()
    if strata is None:
        idx = rng.integers(0, n, size=(resamples, n))
    else:
        strata = np.asarray(strata)
        groups = [np.where(strata == s)[0] for s in sorted(set(strata.tolist()))]
        idx = np.concatenate([g[rng.integers(0, len(g), size=(resamples, len(g)))] for g in groups], axis=1)
    boot = x[idx].mean(axis=1)
    prop = np.clip((boot < theta).mean() + 0.5*(boot == theta).mean(), 1e-6, 1-1e-6)
    z0 = stats.norm.ppf(prop)
    jack = (x.sum() - x) / (n - 1)
    centered = jack.mean() - jack
    denominator = 6 * ((centered ** 2).sum() ** 1.5)
    acc = (centered ** 3).sum() / denominator if denominator > 0 else 0.0
    zs = stats.norm.ppf([(1-conf)/2, 1-(1-conf)/2])
    adjusted = stats.norm.cdf(z0 + (z0 + zs) / (1 - acc * (z0 + zs)))
    lo, hi = np.quantile(boot, adjusted)
    return float(theta), float(lo), float(hi)


def _value(row, benchmark):
    if row.get("excluded") or row.get("status") in ("INFRA", "MISSING", "UNSCORED", "BLOCKED"):
        return None
    raw = row.get("score" if METRICS[benchmark] == "continuous" else "passed")
    if raw in (None, ""):
        return None
    value = float(raw)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Outcome must be finite and within [0, 1]")
    if METRICS[benchmark] == "binary" and value not in (0, 1):
        raise ValueError("A binary endpoint must be exactly 0 or 1")
    return value


def compare(rows, benchmark, treated, control, manifest=None):
    """Require complete, matching replicate sets before calculating item differences."""
    if benchmark not in SKILLS or treated not in ARMS or control not in ARMS or treated == control:
        raise ValueError("Unknown benchmark or invalid contrast")
    expected_samples = {1, 2} if benchmark == "swebench" else {1}
    expected_ids = {str(i["item_id"]) for i in (manifest or {}).get("items", [])
                    if i["benchmark"] == benchmark}
    by, repos, seen = defaultdict(dict), {}, set()
    for row in rows:
        if row.get("benchmark", benchmark) != benchmark or row["arm"] not in (treated, control):
            continue
        ident = str(row.get("item_id", row.get("item")))
        sample = int(row.get("sample", row.get("replicate", 1)))
        if sample not in expected_samples or (manifest is not None and ident not in expected_ids):
            raise ValueError("Outcome is outside the frozen schedule")
        key = (ident, sample, row["arm"])
        if key in seen:
            raise ValueError("Duplicate item/sample/arm outcome")
        seen.add(key)
        by[ident][(sample, row["arm"])] = _value(row, benchmark)
        if row.get("repo"):
            if ident in repos and repos[ident] != row["repo"]:
                raise ValueError("Repository stratum differs across arms")
            repos[ident] = row["repo"]
    expected_ids = expected_ids if manifest is not None else set(by)
    pairs, incomplete = [], []
    for ident in sorted(expected_ids):
        values = by.get(ident, {})
        if any(values.get((s, arm)) is None for s in expected_samples for arm in (treated, control)):
            incomplete.append(ident)
            continue
        t = sum(values[(s, treated)] for s in expected_samples) / len(expected_samples)
        c = sum(values[(s, control)] for s in expected_samples) / len(expected_samples)
        repo = repos.get(ident, ident.split("__", 1)[0] if benchmark == "swebench" else "")
        pairs.append((t, c, repo))
    out = {"benchmark": benchmark, "treated": treated, "control": control,
           "metric_kind": METRICS[benchmark], "n": len(pairs), "expected_n": len(expected_ids),
           "samples_per_item": len(expected_samples), "missing_pair_count": len(incomplete),
           "complete": not incomplete and bool(expected_ids), "ci_label": "unadjusted 95%",
           "delta": None, "ci95": None, "ci90": None, "p": None,
           "verdict": "INCOMPLETE" if incomplete or not expected_ids else "INCONCLUSIVE"}
    if not pairs:
        return out
    n = len(pairs)
    out.update(mean_treated=sum(t for t, _, _ in pairs)/n, mean_control=sum(c for _, c, _ in pairs)/n)
    if METRICS[benchmark] == "binary" and len(expected_samples) == 1:
        a = sum(t == 1 and c == 1 for t, c, _ in pairs)
        b = sum(t == 1 and c == 0 for t, c, _ in pairs)
        c = sum(t == 0 and c == 1 for t, c, _ in pairs)
        d = n - a - b - c
        delta, lo, hi = newcombe_paired(a, b, c, d)
        _, lo90, hi90 = newcombe_paired(a, b, c, d, 0.90)
        out.update(delta=delta, ci95=[lo, hi], ci90=[lo90, hi90], p=mcnemar_exact(b, c),
                   discordant_treated=b, discordant_control=c, test="exact McNemar",
                   interval="Newcombe hybrid score (method 10)")
    else:
        differences = [t-c for t, c, _ in pairs]
        strata = [repo for _, _, repo in pairs] if benchmark == "swebench" else None
        delta, lo, hi = bca(differences, strata=strata)
        _, lo90, hi90 = bca(differences, strata=strata, conf=0.90)
        out.update(delta=delta, ci95=[lo, hi] if lo is not None else None,
                   ci90=[lo90, hi90] if lo90 is not None else None,
                   p=sign_flip(differences) if n >= 2 else None, test="paired sign-flip",
                   interval="BCa item bootstrap" + (" (stratified by repository)" if strata else ""))
    return out


def verdict(comparison, adjusted_p):
    if not comparison["complete"]:
        return "INCOMPLETE"
    if comparison["p"] is None or comparison["ci95"] is None:
        return "INCONCLUSIVE"
    if adjusted_p <= 0.05 and comparison["delta"] != 0:
        return "GAIN" if comparison["delta"] > 0 else "LOSS"
    # No equivalence margin is registered for the continuous visual score or SWE.
    if comparison["metric_kind"] == "binary" and comparison["benchmark"] != "swebench":
        if comparison["ci90"][0] > -TIE_MARGIN and comparison["ci90"][1] < TIE_MARGIN:
            return "TIE"
        if comparison["ci95"][0] > -TIE_MARGIN:
            return "NON-INFERIOR"
    return "INCONCLUSIVE"


def analyze(rows, manifest, families=None):
    """families: {name: [[benchmark, treated, control], ...]} from the frozen protocol.

    Every one of the 33 planned comparisons must occur exactly once. Incomplete
    comparisons occupy their planned Holm slot with p=1 and cannot claim a gain.
    """
    families = PRIMARY_FAMILIES if families is None else families
    planned = {(b, t, c) for b in SKILLS for t, c in CONTRASTS}
    flat = [tuple(c) for comparisons in families.values() for c in comparisons]
    if len(flat) != len(set(flat)) or set(flat) != planned:
        raise ValueError("Families must cover each of the 33 planned contrasts exactly once")
    report = {"manifest_sha256": manifest["manifest_sha256"], "comparisons": [],
              "scope": "Contemporary baseline/old/candidate cohort only; no historical outcomes reused.",
              "limits": ["No equivalence margin is registered for SWE-bench or Design2Code.",
                         "Failure to detect a difference does not demonstrate equivalence.",
                         "Binary MDE uses exact McNemar at 80% power and must name the assumed discordance.",
                         "No generic-process control: package contrasts do not establish unique mechanisms."]}
    for family, contrasts in families.items():
        comparisons = [compare(rows, b, t, c, manifest) for b, t, c in contrasts]
        ps = [c["p"] if c["complete"] and c["p"] is not None else 1.0 for c in comparisons]
        for comparison, adjusted in zip(comparisons, holm(ps)):
            comparison.update(family=family, family_size=len(comparisons), p_holm=adjusted,
                              verdict=verdict(comparison, adjusted))
            report["comparisons"].append(comparison)
    report["complete"] = all(c["complete"] for c in report["comparisons"])
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", required=True, help="New cohort scored JSONL rows")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--families", required=True, help="Frozen protocol family mapping JSON")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(args.rows) as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    with open(args.manifest) as handle:
        manifest = json.load(handle)
    with open(args.families) as handle:
        families = json.load(handle)
    result = analyze(rows, manifest, families)
    with open(args.out, "x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
