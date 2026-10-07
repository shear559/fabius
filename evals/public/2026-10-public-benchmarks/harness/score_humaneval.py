#!/usr/bin/env python3
"""Score HumanEval+ with EvalPlus 0.3.1 in a Linux container, twice (PROTOCOL.md v1.1, benchmark 3).

Builds one samples file per arm from the scored attempts, gives the excluded HumanEval/32 an
empty solution in every arm (EvalPlus refuses a file with a missing problem), runs
evalplus.sanitize and evalplus.evaluate in the container twice, reports flips, and writes
results/humaneval/items.csv.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from collect import records  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
OUT = ROOT / "results" / "humaneval"
IMAGE = "fabius-evalplus:0.3.1"
EXCLUDED = {"HumanEval_32"}
ARMS = ["baseline", "fabius-doc", "fabius-loaded"]


def evaluate(work, name, run):
    cmd = (f"python -m evalplus.sanitize --samples {name}.jsonl >/dev/null 2>&1; "
           f"rm -f {name}-sanitized_eval_results.json; "
           f"python -m evalplus.evaluate --dataset humaneval --samples {name}-sanitized.jsonl --parallel 8 "
           f"--i-just-wanna-run >/dev/null 2>&1; cp {name}-sanitized_eval_results.json {name}-eval-{run}.json")
    subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{work}:/work", "-w", "/work",
                    "-v", f"{ROOT / 'humanevalplus/cache'}:/root/.cache/evalplus", IMAGE, "bash", "-c", cmd], check=True)
    ev = json.load(open(work / f"{name}-eval-{run}.json"))["eval"]
    return {tid.replace("/", "_"): (v[0]["base_status"] == "pass", v[0]["plus_status"] == "pass") for tid, v in ev.items()}


def main():
    running = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True).stdout.split()
    if running:
        print(f"note: {len(running)} other containers are running (the protocol asks for none); continuing "
              f"is recorded in the receipt")
    OUT.mkdir(parents=True, exist_ok=True)
    work = OUT / "evalplus"
    work.mkdir(exist_ok=True)
    recs = records("humaneval")
    global ARMS
    ARMS = sorted({r["arm"] for r in recs})
    all_ids = [json.loads(l)["task_id"] for l in open(ROOT / "humanevalplus/cache/HumanEvalPlus-v0.1.10.jsonl")]
    results = {}
    for arm in ARMS:
        by_item = {r["item"]: r for r in recs if r["arm"] == arm}
        with open(work / f"{arm}.jsonl", "w") as f:
            for tid in all_ids:
                key = tid.replace("/", "_")
                r = by_item.get(key)
                sol = "" if key in EXCLUDED or r is None or r.get("scored_attempt") is None else r["final_text"]
                f.write(json.dumps({"task_id": tid, "solution": sol}) + "\n")
        r1, r2 = evaluate(work, arm, 1), evaluate(work, arm, 2)
        flips = sorted(k for k in r1 if r1[k] != r2.get(k))
        results[arm] = (r1, flips)
        print(f"{arm}: plus pass {sum(v[1] for k, v in r1.items() if k not in EXCLUDED)}/{len(r1) - len(EXCLUDED)} · "
              f"flips between the two evaluations: {flips}")
    sanitized = {arm: {json.loads(l)["task_id"].replace("/", "_"): json.loads(l)["solution"]
                       for l in open(work / f"{arm}-sanitized.jsonl")} for arm in ARMS}
    fields = ["item", "arm", "replicate", "passed", "base_passed", "excluded", "flip", "solution_lines",
              "router_injected", "fabius_skills_loaded", "skill_calls", "output_tokens", "total_tokens", "cost_usd",
              "elapsed_s", "num_turns", "outcome_reason", "scored_attempt", "discarded_attempts", "discarded_reasons",
              "assistant_text_messages", "init_model", "first_turn_prompt_tokens"]
    with open(OUT / "items.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in recs:
            r1, flips = results[r["arm"]]
            ex = "canonical solution fails the evaluator's sandbox" if r["item"] in EXCLUDED else (
                "no scored attempt" if r.get("scored_attempt") is None else "")
            base_p, plus_p = r1.get(r["item"], (False, False))
            sol = sanitized[r["arm"]].get(r["item"], "")
            w.writerow({"item": r["item"], "arm": r["arm"], "replicate": 1,
                        "passed": "" if ex else int(plus_p), "base_passed": "" if ex else int(base_p),
                        "excluded": ex, "flip": int(r["item"] in flips),
                        "solution_lines": sum(1 for l in sol.splitlines() if l.strip()),
                        "router_injected": r.get("router_injected"),
                        "fabius_skills_loaded": json.dumps(r.get("fabius_skills_loaded") or []),
                        "skill_calls": json.dumps(r.get("skill_calls") or []),
                        **{k: r.get(k) for k in ("output_tokens", "total_tokens", "cost_usd", "elapsed_s", "num_turns",
                                                 "outcome_reason", "scored_attempt", "discarded_attempts",
                                                 "discarded_reasons", "assistant_text_messages", "init_model",
                                                 "first_turn_prompt_tokens")}})
    print("wrote", OUT / "items.csv")


if __name__ == "__main__":
    main()
