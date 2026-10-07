#!/usr/bin/env python3
"""Score one Part B benchmark with its own scorer (PROTOCOL-SKILLS.md) and write results/skills/<bench>/items.csv.

  score_skill.py <bench>

Collects the scored attempt of every (item, arm), writes responses-<arm>.jsonl, runs
skills-bench/<bench>/score.py on each, and merges its per-item output with the run record.
"""
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


def main():
    bench = sys.argv[1]
    out = ROOT / "results" / "skills" / bench
    out.mkdir(parents=True, exist_ok=True)
    recs = records(bench)
    arms = sorted({r["arm"] for r in recs})
    scored = {}
    for arm in arms:
        rp = out / f"responses-{arm}.jsonl"
        rp.write_text("".join(json.dumps({"item": r["item"], "response": r.get("final_text") or ""}) + "\n"
                              for r in recs if r["arm"] == arm and r.get("scored_attempt")))
        sp = out / f"scored-{arm}.jsonl"
        subprocess.run([PY, "score.py", str(rp), str(sp)], cwd=ROOT / "skills-bench" / bench, check=True)
        for line in open(sp):
            row = json.loads(line)
            scored[(str(row["item"]), arm)] = row
    extra = sorted({k for v in scored.values() for k in v if k not in ("item", "passed")})
    fields = ["item", "arm", "replicate", "passed", "excluded", "first_turn_prompt_tokens", "skill_injected",
              "fabius_skills_loaded", "skill_calls", "output_tokens", "total_tokens", "cost_usd", "cost_microusd",
              "elapsed_s", "num_turns", "outcome_reason", "scored_attempt", "discarded_attempts", "discarded_reasons",
              "init_model"] + [f"score_{k}" for k in extra]
    base_tok = {r["item"]: r.get("first_turn_prompt_tokens") for r in recs if r["arm"] == "baseline"}
    with open(out / "items.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in recs:
            s = scored.get((r["item"], r["arm"]))
            ex = "" if (s is not None and r.get("scored_attempt")) else "no scored attempt"
            b, t = base_tok.get(r["item"]), r.get("first_turn_prompt_tokens")
            w.writerow({"item": r["item"], "arm": r["arm"], "replicate": 1,
                        "passed": "" if ex else int(s["passed"]), "excluded": ex,
                        "first_turn_prompt_tokens": t,
                        "skill_injected": "" if (b is None or t is None) else (t - b >= 2500),
                        "fabius_skills_loaded": json.dumps(r.get("fabius_skills_loaded") or []),
                        "skill_calls": json.dumps(r.get("skill_calls") or []),
                        "cost_microusd": "" if r.get("cost_usd") is None else round(r["cost_usd"] * 1e6),
                        **{k: r.get(k) for k in ("output_tokens", "total_tokens", "cost_usd", "elapsed_s", "num_turns",
                                                 "outcome_reason", "scored_attempt", "discarded_attempts",
                                                 "discarded_reasons", "init_model")},
                        **{f"score_{k}": (s or {}).get(k) for k in extra}})
    for arm in arms:
        ps = [int(scored[(r["item"], arm)]["passed"]) for r in recs if r["arm"] == arm and (r["item"], arm) in scored]
        print(f"{bench} · {arm}: {sum(ps)}/{len(ps)}")


if __name__ == "__main__":
    main()
