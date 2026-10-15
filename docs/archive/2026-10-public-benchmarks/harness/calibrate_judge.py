#!/usr/bin/env python3
"""Calibrate the substitute LongMemEval judge on controls with known labels, before any arm is judged.

  calibrate_judge.py [--out <dir>]   (reads skills-bench/longmemeval/items.jsonl under FB_ROOT)

Controls, built from the frozen sample's gold field: GOLD = the gold answer as the hypothesis
(abstention items: an explicit abstention); WRONG = the gold answer of another item of the same question
type (abstention items: that confident wrong answer, which should be judged incorrect). Each control set
goes through the official stage-1 prompt builder (score.py), the judge, and stage 2, exactly as an arm's
responses will. Acceptance, fixed before judging: GOLD pass rate >= 0.95 and WRONG pass rate <= 0.05.
The judge is run twice on GOLD to report its own repeatability.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
BENCH = ROOT / "skills-bench" / "longmemeval"
PY = str(ROOT / ".venv/bin/python")
HERE = Path(__file__).resolve().parent
ABSTAIN = "The chat history does not contain this information, so I cannot answer that."


def controls(items):
    by_type = {}
    for r in items:
        by_type.setdefault(r["gold"]["question_type"], []).append(r)
    gold, wrong = [], []
    for r in items:
        g = r["gold"]
        gold.append({"item": r["item"], "response": ABSTAIN if g.get("abstention") else str(g["answer"])})
        others = [o for o in by_type[g["question_type"]] if o["item"] != r["item"] and not o["gold"].get("abstention")]
        donor = others[hash(r["item"]) % len(others)] if others else None
        wrong.append({"item": r["item"], "response": str(donor["gold"]["answer"]) if donor else "42"})
    return gold, wrong


def run_set(name, rows, out, workers):
    rp = out / f"{name}-responses.jsonl"
    rp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    s1 = out / f"{name}-stage1.jsonl"
    jp = out / f"{name}-judge-prompts.jsonl"
    subprocess.run([PY, "score.py", str(rp), str(s1), "--judge-prompts", str(jp)], cwd=BENCH, check=True)
    jd = out / f"{name}-judgements.jsonl"
    subprocess.run([PY, str(HERE / "judge_longmemeval.py"), str(jp), str(jd), "--workers", str(workers)], check=True)
    sc = out / f"{name}-scored.jsonl"
    subprocess.run([PY, "score_from_judgements.py", str(jp), str(jd), str(sc)], cwd=BENCH, check=True)
    scored = [json.loads(l) for l in open(sc)]
    return {"n": len(scored), "pass_rate": sum(r["passed"] for r in scored) / len(scored),
            "ambiguous": sum(1 for r in scored if r.get("verdict_ambiguous")),
            "by_type": {t: round(sum(r["passed"] for r in scored if r["question_type"] == t) /
                                 max(1, sum(1 for r in scored if r["question_type"] == t)), 3)
                        for t in sorted({r["question_type"] for r in scored})}}, scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "longmemeval-judge-calibration"))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(BENCH / "items.jsonl")]
    gold, wrong = controls(items)
    rep = {"acceptance": {"gold_min": 0.95, "wrong_max": 0.05}}
    rep["gold"], g1 = run_set("gold", gold, out, a.workers)
    rep["wrong"], wrong_scored = run_set("wrong", wrong, out, a.workers)
    rep["gold_repeat"], g2 = run_set("gold-repeat", gold, out, a.workers)
    a1, a2 = {r["item"]: r["passed"] for r in g1}, {r["item"]: r["passed"] for r in g2}
    rep["gold_repeatability"] = sum(a1[i] == a2[i] for i in a1) / len(a1)
    # single-session-preference items carry a grading rubric as their gold, not an answer: a rubric fed back as
    # the hypothesis is rightly judged incorrect, so those items cannot be gold-calibrated and the acceptance
    # rule applies to the answer-type items; the preference items are reported separately.
    pref = "single-session-preference"
    def rate(scored):
        s = [r["passed"] for r in scored if r["question_type"] != pref]
        return sum(s) / len(s)
    rep["acceptance"]["applies_to"] = f"question types other than {pref} (a rubric, not an answer, is the gold there)"
    rep["gold"]["pass_rate_answer_types"] = rate(g1)
    rep["wrong"]["pass_rate_answer_types"] = rate(wrong_scored)
    rep["accepted"] = rep["gold"]["pass_rate_answer_types"] >= 0.95 and rep["wrong"]["pass_rate_answer_types"] <= 0.05
    (out / "calibration.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    sys.exit(0 if rep["accepted"] else 1)


if __name__ == "__main__":
    main()
