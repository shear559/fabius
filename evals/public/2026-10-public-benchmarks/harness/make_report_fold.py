#!/usr/bin/env python3
"""Every table of the continuation report, generated from results/fold-analysis.json and results/descriptives.json.

  FB_ROOT=<root> make_report_fold.py > results/fold-tables.md
"""
import json
import os
from pathlib import Path

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
BENCH = {"swebench": "SWE-bench Verified Mini", "ifeval": "IFEval", "humaneval": "HumanEval+",
         "cyberseceval": "CyberSecEval instruct (Python)", "labbench": "LAB-Bench ProtocolQA + SeqQA", "finqa": "FinQA",
         "ds1000": "DS-1000 (no PyTorch/TensorFlow)", "smartbugs": "SmartBugs-curated", "bfcl": "BFCL non-live AST",
         "longmemeval": "LongMemEval oracle", "design2code": "Design2Code"}
ENDPOINT = {"swebench": "resolved", "ifeval": "prompt-level strict", "humaneval": "plus tests pass",
            "cyberseceval": "not flagged insecure", "labbench": "correct option", "finqa": "answer matches",
            "ds1000": "tests pass", "smartbugs": "category matches", "bfcl": "official AST check",
            "longmemeval": "judged correct", "design2code": "visual score, 0–1"}
OWNER = {"swebench": "disciplina", "ifeval": None, "humaneval": "parcus", "cyberseceval": "praesidium",
         "labbench": "scientia", "finqa": "fortuna", "ds1000": "doctrina", "smartbugs": "catena", "bfcl": "cohors",
         "longmemeval": "archivum", "design2code": "decor"}
ARM = {"baseline": "baseline", "old": "old (3.3.0)", "candidate": "candidate (fold)"}


def pct(x):
    return f"{x * 100:.1f}%"


def pts(x):
    return f"{x * 100:+.1f}"


def ci(c, key="ci95"):
    lo, hi = c[key]
    return f"{lo * 100:+.1f} to {hi * 100:+.1f}"


def main():
    a = json.load(open(ROOT / "results/fold-analysis.json"))
    d = json.load(open(ROOT / "results/descriptives.json")) if (ROOT / "results/descriptives.json").exists() else {}
    print("### The 33 contrasts (one family, Holm-corrected together)\n")
    print("| Contrast | Benchmark (endpoint) | n | Treated | Control | Difference (points) | 95% CI | only treated / only control | p | p (Holm) | Verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for key, c in a["comparisons"].items():
        pair, bench = key.split(" · ")
        arm, control = pair.split(" vs ")
        inv = "`/fabius`" if OWNER[bench] is None else f"`/fabius:fabius-{OWNER[bench]}`"
        name = f"{ARM[arm]} − {ARM[control]}"
        if not c.get("n"):
            print(f"| {name} | {BENCH[bench]} ({ENDPOINT[bench]}) | 0 | — | — | — | — | — | — | — | **INCOMPLETE** |")
            continue
        cont = "endpoint" in c
        tr = f"{c['mean_treated']:.3f}" if cont else pct(c["rate_treated"])
        co = f"{c['mean_control']:.3f}" if cont else pct(c["rate_control"])
        delta = f"{c['delta']:+.3f}" if cont else pts(c["delta"])
        cis = f"{c['ci95'][0]:+.3f} to {c['ci95'][1]:+.3f}" if cont else ci(c)
        disc = f"{c['b']} / {c['c']}" if c.get("k", 1) == 1 and "b" in c else "—"
        print(f"| {name} | {BENCH[bench]} ({ENDPOINT[bench]}), {inv} | {c['n']}{' × 2' if c.get('k') == 2 else ''} | {tr} | {co} | "
              f"{delta} | {cis} | {disc} | {c['p']:.3f} | {c['p_holm']:.3f} | **{c['verdict']}** |")
    print("\n### Did the package reach the model?\n")
    print("| Arm · benchmark | Runs | Contract in context at the first turn | Median first-turn growth (tokens) | Runs with a delivered package read | Package reads delivered / refused |")
    print("|---|---|---|---|---|---|")
    for key, v in a["exposure"].items():
        g = v["first_turn_growth_median"]
        print(f"| {key} | {v['n']} | {v['contract_injected']} / {v['n']} | {g:,.0f} | {v['runs_with_a_delivered_package_read']} | "
              f"{v['package_reads_delivered']} / {v['package_reads_denied']} |" if g is not None else f"| {key} | {v['n']} | — | — | — | — |")
    print("\n### Cost and behaviour (treated ÷ control, per item, geometric mean, BCa 95% interval; descriptive)\n")
    print("| Contrast · benchmark · measure | Ratio | 95% CI | n |\n|---|---|---|---|")
    for key, v in a["efficiency"].items():
        if "cost_microusd" in key:
            key = key.replace("cost_microusd", "cost")
        print(f"| {key} | ×{v['ratio']:.2f} | {v['ci95'][0]:.2f}–{v['ci95'][1]:.2f} | {v['n']} |")
    if a.get("mde"):
        print("\n### Minimum detectable effect at 80% power (exact McNemar, α = 0.05/33), points\n")
        print("| Benchmark | n | ψ = 0.1 | ψ = 0.2 | ψ = 0.3 |\n|---|---|---|---|---|")
        for b, v in a["mde"].items():
            n = max(c["n"] for k, c in a["comparisons"].items() if k.endswith(f"· {b}"))
            cells = [("—" if v[f"psi={p}"] is None else f"{v[f'psi={p}'] * 100:.1f}") for p in (0.1, 0.2, 0.3)]
            print(f"| {BENCH[b]} | {n} | {' | '.join(cells)} |")
    if d:
        print("\n### Run outcomes per arm\n")
        print("| Benchmark · arm | Scored runs | Items with no scored attempt | INFRA attempts retried | Turn-cap hits | Timeouts | Final text ends on a question |")
        print("|---|---|---|---|---|---|---|")
        for key, v in d.items():
            print(f"| {key} | {v['runs']} | {v['no_scored_attempt']} | {v['infra_retries']} | {v['turn_cap']} | {v['timeouts']} | {v['ended_on_question']} |")
        rows = [(k, v) for k, v in d.items() if "container_executed" in v]
        if rows:
            print("\n### SWE-bench behaviour (exploratory)\n")
            print("| Replicate · arm | Runs that attempted a command in the test container | Runs where one executed | Runs with at least one permission denial |\n|---|---|---|---|")
            for k, v in rows:
                print(f"| {k.replace('swebench ', '')} | {v['container_attempted']} / {v['runs']} | {v['container_executed']} / {v['runs']} ({pct(v['container_executed'] / v['runs'])}) | {v['runs_with_permission_denial']} / {v['runs']} |")


if __name__ == "__main__":
    main()
