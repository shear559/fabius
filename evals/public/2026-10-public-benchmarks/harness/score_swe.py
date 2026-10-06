#!/usr/bin/env python3
"""Score SWE-bench Verified Mini runs with the official harness (PROTOCOL.md v1.2, benchmark 1).

  score_swe.py --replicate 1 [--unfiltered]

One predictions file per (arm, replicate) from the scored attempts' patches; empty patches
are recorded as unresolved without being run (as the official harness does); the official
run_evaluation scores the rest against the pinned rows file; a harness error not caused by
the patch is re-scored up to twice with one worker. Writes results/swebench/items.csv.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from collect import records  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
PY = str(ROOT / ".venv/bin/python")
OUT = ROOT / "results" / "swebench"


def report_for(run_id, model, iid):
    p = ROOT / "eval/logs/run_evaluation" / run_id / model / iid / "report.json"
    if p.exists():
        return json.loads(p.read_text()).get(iid, {})
    return None


def run_eval(preds, run_id, workers):
    if not preds:
        return
    pp = OUT / f"predictions-{run_id}.jsonl"
    pp.write_text("".join(json.dumps(p) + "\n" for p in preds))
    subprocess.run([PY, "-m", "swebench.harness.run_evaluation", "-d", str(ROOT / "swebench-mini-rows-pinned.json"),
                    "-p", str(pp), "-id", run_id, "--max_workers", str(workers), "-t", "1800",
                    "-i", *[p["instance_id"] for p in preds]], cwd=ROOT / "eval", check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicate", type=int, default=1)
    ap.add_argument("--unfiltered", action="store_true", help="score the declared secondary (unfiltered patches)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    valid = json.load(open(ROOT / "swebench-validity.json"))
    recs = [r for r in records("swebench", a.replicate)]
    kind = "unfiltered" if a.unfiltered else "filtered"
    status = {}
    for arm in sorted({r["arm"] for r in recs}):
        model = f"{arm}-r{a.replicate}-{kind}"
        run_id = f"fabius-{model}"
        preds, empty = [], set()
        for r in recs:
            if r["arm"] != arm or r.get("scored_attempt") is None:
                continue
            patch = Path(r["patch_unfiltered_path" if a.unfiltered else "patch_path"]).read_text()
            if not patch.strip():
                empty.add(r["item"])
                continue
            preds.append({"instance_id": r["item"], "model_name_or_path": model, "model_patch": patch})
        run_eval(preds, run_id, 2)
        for attempt in range(2):  # re-score harness errors (no report) with one worker
            missing = [p for p in preds if report_for(run_id, model, p["instance_id"]) is None]
            if not missing:
                break
            run_eval(missing, run_id, 1)
        for r in recs:
            if r["arm"] != arm:
                continue
            rep = report_for(run_id, model, r["item"]) if r["item"] not in empty else {}
            status[(r["item"], arm)] = {
                "resolved": bool(rep and rep.get("resolved")) if rep is not None else None,
                "empty_patch": r["item"] in empty, "patch_applied": bool(rep and rep.get("patch_successfully_applied")),
                "harness_error": rep is None}
    fields = ["item", "arm", "replicate", "repo", "passed", "excluded", "empty_patch", "patch_applied", "harness_error",
              "patch_lines", "patch_files", "router_injected", "fabius_skills_loaded", "skill_calls", "output_tokens",
              "total_tokens", "cost_usd", "elapsed_s", "num_turns", "outcome_reason", "timed_out", "result_subtype",
              "scored_attempt", "discarded_attempts", "discarded_reasons", "permission_denials", "init_model",
              "first_turn_prompt_tokens", "prompt_sha256"]
    path = OUT / (f"items{'-unfiltered' if a.unfiltered else ''}-r{a.replicate}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in recs:
            st = status.get((r["item"], r["arm"]), {})
            ex = "" if valid.get(r["item"], {}).get("valid") else "invalid instance"
            if not ex and r.get("scored_attempt") is None:
                ex = "no scored attempt after retries"
            if not ex and st.get("harness_error"):
                ex = "harness error after re-scoring"
            w.writerow({"item": r["item"], "arm": r["arm"], "replicate": a.replicate,
                        "repo": r["item"].split("__")[0], "passed": "" if ex else int(bool(st.get("resolved"))),
                        "excluded": ex, "empty_patch": int(bool(st.get("empty_patch"))),
                        "patch_applied": int(bool(st.get("patch_applied"))), "harness_error": int(bool(st.get("harness_error"))),
                        "router_injected": r.get("router_injected"),
                        "fabius_skills_loaded": json.dumps(r.get("fabius_skills_loaded") or []),
                        "skill_calls": json.dumps(r.get("skill_calls") or []),
                        **{k: r.get(k) for k in ("patch_lines", "patch_files", "output_tokens", "total_tokens", "cost_usd",
                                                 "elapsed_s", "num_turns", "outcome_reason", "timed_out", "result_subtype",
                                                 "scored_attempt", "discarded_attempts", "discarded_reasons",
                                                 "permission_denials", "init_model", "first_turn_prompt_tokens",
                                                 "prompt_sha256")}})
    print("wrote", path)


if __name__ == "__main__":
    main()
