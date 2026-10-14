#!/usr/bin/env python3
"""Every results table of the public-benchmark report, generated from the analysis files only.

  make_report.py > results/tables.md

Reads results/analysis.json (Part A) and results/skills-analysis.json (Part B). No number in the
report is typed by hand: the prose cites these tables.
"""
import json
import os
from pathlib import Path

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
BENCH = {"swebench": "SWE-bench Verified Mini", "ifeval": "IFEval", "humaneval": "HumanEval+",
         "cyberseceval": "CyberSecEval instruct (Python)", "labbench": "LAB-Bench ProtocolQA + SeqQA",
         "finqa": "FinQA", "ds1000": "DS-1000 (no PyTorch/TensorFlow)", "smartbugs": "SmartBugs-curated",
         "bfcl": "BFCL non-live AST"}
ENDPOINT = {"swebench": "resolved", "ifeval": "prompt-level strict", "humaneval": "plus tests pass",
            "cyberseceval": "not flagged insecure", "labbench": "correct option", "finqa": "answer matches",
            "ds1000": "tests pass", "smartbugs": "category matches", "bfcl": "official AST check"}


def pct(x):
    return f"{x * 100:.1f}%"


def pts(x):
    return f"{x * 100:+.1f}"


def ci(c, key="ci95"):
    lo, hi = c[key]
    return f"{lo * 100:+.1f} to {hi * 100:+.1f}"


def row(name, bench, c):
    k = c.get("k", 1)
    disc = f"{c['b']} / {c['c']}" if k == 1 and "b" in c else "—"
    return (f"| {name} | {BENCH.get(bench, bench)} ({ENDPOINT.get(bench, '')}) | {c['n']}{' × 2' if k == 2 else ''} | "
            f"{pct(c['rate_treated'])} | {pct(c['rate_baseline'])} | {pts(c['delta'])} | {ci(c)} | {disc} | "
            f"{c['p']:.3f} | {c.get('p_holm', float('nan')):.3f} | **{c.get('verdict', '—')}** |")


def main():
    a = json.load(open(ROOT / "results/analysis.json"))
    b = json.load(open(ROOT / "results/skills-analysis.json")) if (ROOT / "results/skills-analysis.json").exists() else {"comparisons": {}}
    head = ("| Arm | Benchmark (endpoint) | n | Fabius | Baseline | Difference (points) | 95% CI | only Fabius / only baseline "
            "| p | p (Holm) | Verdict |\n|---|---|---|---|---|---|---|---|---|---|---|")
    print("### Part A — the router, `/fabius` (Family 1) and the README's `fabius:` prefix (Family 2)\n")
    print(head)
    for key, c in a["comparisons"].items():
        if "descriptive" in key:
            continue
        arm, bench = key.split(" vs baseline · ")
        name = "`/fabius`" if arm == "fabius-loaded" else "`fabius:` prefix"
        print(row(name, bench.split(" ")[0], c))
    d = a["comparisons"].get("fabius-doc vs baseline · swebench (subset, descriptive)")
    if d:
        print(f"\nThe `fabius:` prefix on the fixed 10-task SWE-bench subset (descriptive, outside the test families): "
              f"{pct(d['rate_treated'])} vs {pct(d['rate_baseline'])}, n = {d['n']}.")
    print("\n### Part B — each skill by its own command, `/fabius:fabius-<skill>` (Family B)\n")
    print(head)
    for key, c in b["comparisons"].items():
        arm, bench = key.split(" vs baseline · ")
        print(row(f"`/fabius:{arm}`", bench, c))
    print("\n### Did the rules actually load?\n")
    print("| Arm · benchmark | Runs | Contract in context at the first turn | Specialists loaded with the Skill tool |\n|---|---|---|---|")
    for key, v in a.get("load", {}).items():
        sk = ", ".join(f"{s} ×{x['runs']}" for s, x in v.get("skill_loads", {}).items()) or "none"
        print(f"| {key} | {v['n']} | {v['router_injected']} / {v['n']} (router) | {sk} |")
    for key, v in b.get("load", {}).items():
        sk = ", ".join(f"{s} ×{x['runs']}" for s, x in (v.get("skill_tool_loads") or {}).items()) or "none"
        print(f"| {key} | {v['n']} | {v['skill_injected']} / {v['n']} (the skill) | {sk} |")
    print("\n### Cost and behaviour (Fabius ÷ baseline, per item, BCa 95% interval; descriptive)\n")
    print("| Arm · benchmark · measure | Ratio | 95% CI | n |\n|---|---|---|---|")
    for src in (a, b):
        for key, v in src.get("efficiency", {}).items():
            if key.endswith("cost_usd") or "cost_usd ·" in key:
                continue  # the pre-registered +1 smoothing is meaningless in dollars; the micro-dollar ratio is shown
            print(f"| {key.replace('cost_microusd', 'cost')} | ×{v['ratio']:.2f} | {v['ci95'][0]:.2f}–{v['ci95'][1]:.2f} | {v['n']} |")
    if a.get("sensitivities"):
        print("\n### Declared sensitivity analyses\n")
        print("| Analysis | Result |\n|---|---|")
        for key, v in a["sensitivities"].items():
            if isinstance(v, dict) and "delta" in v:
                print(f"| {key} | {pts(v['delta'])} points, 95% CI {ci(v)}, n = {v['n']}, p = {v['p']:.3f} |")
            elif isinstance(v, dict):
                print(f"| {key} | {', '.join(f'{k} {x:.2f}' if isinstance(x, float) else f'{k} {x}' for k, x in v.items())} |")
            else:
                print(f"| {key} | {', '.join(v) if isinstance(v, list) else v} |")
    dp = ROOT / "results/descriptives.json"
    if dp.exists():
        d = json.load(open(dp))
        print("\n### Run outcomes per arm (descriptives.py)\n")
        print("| Benchmark · arm | Scored runs | Items with no scored attempt | INFRA attempts retried | Turn-cap hits "
              "| Timeouts | Final text ends on a question |\n|---|---|---|---|---|---|---|")
        for key, v in d.items():
            print(f"| {key} | {v['runs']} | {v['no_scored_attempt']} | {v['infra_retries']} | {v['turn_cap']} | "
                  f"{v['timeouts']} | {v['ended_on_question']} |")
        print("\n### Exploratory, SWE-bench (not pre-registered)\n")
        print("| Replicate · arm | Runs that attempted a command in the test container | Runs where one executed | "
              "Runs with at least one permission denial |\n|---|---|---|---|")
        for key, v in d.items():
            if "container_executed" in v:
                print(f"| {key.replace('swebench ', '')} | {v['container_attempted']} / {v['runs']} | "
                      f"{v['container_executed']} / {v['runs']} ({pct(v['container_executed'] / v['runs'])}) | "
                      f"{v['runs_with_permission_denial']} / {v['runs']} |")


if __name__ == "__main__":
    main()
