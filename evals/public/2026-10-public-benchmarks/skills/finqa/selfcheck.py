#!/usr/bin/env python3
"""Prove score.py right on the sampled items -> selfcheck.json.  Usage: python selfcheck.py"""
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


score = load("finqa_score", HERE / "score.py")
official = load("finqa_official_evaluate", HERE / "code" / "evaluate" / "evaluate.py")  # needs sympy, tqdm

# Manual review of every qa.answer failure in the pinned 200-item sample (checked against table/text).
MANUAL = {
    "L/2009/page_84.pdf-3": "exe_ans wrong: divide(128.16, 100) is the index ratio 1.2816; growth asked is 28.16% (qa.answer right)",
    "LMT/2014/page_77.pdf-1": "exe_ans wrong: program adds const_3 instead of dividing by 3; average is 325.7 (qa.answer right)",
    "SNA/2007/page_69.pdf-3": "exe_ans wrong: last step divides #0 (-4.9) not #1 (-1.2) by 3.7; change is -32.4% (qa.answer right)",
    "ETR/2004/page_212.pdf-2": "sign: revisions are -29.4 so exe_ans is -3.16%; qa.answer gives the magnitude",
    "AES/2001/page_85.pdf-2": "qa.answer wrong: 200 million x 7.375% = 14,750,000 = exe_ans",
    "DRE/2007/page_56.pdf-1": "exe_ans wrong: subtracts const_100 from the ratio 0.50034; change is +50.0% (qa.answer right)",
    "V/2014/page_126.pdf-2": "exe_ans wrong: program stops at the difference 5.08; increase is 5.08/39.03 = 13.0% (qa.answer right)",
    "ETR/2016/page_23.pdf-4": "qa.answer empty; exe_ans 5829 - 100 (net-of-tax gain) answers the question",
    "BLK/2014/page_120.pdf-2": "exe_ans wrong: program stops at 349 due by 2017; 349/1178 = 29.63% (qa.answer right)",
    "AWK/2018/page_146.pdf-4": "qa.answer empty; exe_ans 0.6 + 0.7 = 1.3 million shares answers the question",
    "BLL/2006/page_67.pdf-1": "exe_ans wrong: program stops at current assets 259.7 and omits /802.6 (= 32.4%); qa.answer 32.2% is close",
    "RSG/2018/page_135.pdf-2": "qa.answer empty; exe_ans (17 - 30)/30 = -43.3% answers the question",
    "RSG/2015/page_98.pdf-2": "qa.answer empty; exe_ans 100.3/46.7 = 2.148 answers the question",
    "JKHY/2019/page_18.pdf-1": "exe_ans wrong: 2nd step subtracts 151.16 again instead of dividing; growth is 17.3% (qa.answer right)",
    "SNA/2007/page_49.pdf-4": "exe_ans wrong: adds 1.11 + 1.08 instead of subtracting; change is 2.78% (qa.answer 2.7% truncated)",
    "PNC/2012/page_100.pdf-3": "qa.answer empty; exe_ans 74 + 110 = 184 answers the question",
    "MRK/2013/page_125.pdf-4": "sign: question asks for a decrease; exe_ans is the signed change -44.58%, qa.answer the magnitude",
    "ETR/2017/page_143.pdf-3": "qa.answer wrong by 10x (typo): 760,000 thousand x 7.458% = 56,680,800 = exe_ans",
}


def signed(x, fmt, minus="−"):
    return (minus if x < 0 else "") + format(abs(x), fmt)


def renderings(g):
    """Gold exe_ans written the ways a model plausibly writes it; every one must pass."""
    if isinstance(g, str):
        G = g.capitalize()
        return {"plain": f"Answer: {g}", "styled": f"**Answer:** {G}.", "true_false": f"Answer: {g == 'yes'}",
                "with_reason": f"Answer: {G}, 5.2 > 4.1", "next_line": f"**Answer:**\n\n{G}",
                "buried": f"Answer: <value> comes last.\nThe answer is not 12.\n\nFinal answer: {g.upper()}",
                "weak_only": f"So the answer is {g}.", "boxed_only": f"Result: $\\boxed{{\\text{{{g}}}}}$"}
    styled = (f"**Answer:** {signed(g * 100, '.2f')}%" if abs(g) < 1
              else f"**Answer:** {'−' if g < 0 else ''}${abs(g):,.2f}")
    units = (f"Answer: ${g / 1e6:.2f} million" if abs(g) >= 1e6 else f"Answer: ${g / 1e3:.2f} thousand"
             if abs(g) >= 1e3 else f"Answer: ({abs(g):.4f})" if g < 0 else f"Answer: {g:.4f}")
    return {"plain": f"Answer: {g!r}", "styled": styled, "units_or_accounting": units,
            "equation": f"We compute (a - b) / b.\nAnswer: (a - b) / b = {g!r}",
            "next_line": f"**Answer:**\n\n{g!r}",
            "buried": f"Answer: <value> comes last.\nRows 2019 and 2018; the answer is not 12.\n\nFinal answer: {g!r}",
            "weak_only": f"So the answer is {g!r}.", "boxed_only": f"Result: $\\boxed{{{g!r}}}$"}


def decimals(s):
    m = re.search(r"\d+(?:\.(\d+))?", s.replace(",", ""))
    return len(m.group(1) or "") if m else 0


def human_reason(ans, g):
    """Why the dataset's own answer string fails against exe_ans (deterministic categories)."""
    parsed = score.parse(score.extract("Answer: " + ans))
    if not ans.strip():
        return "empty: qa.answer is blank in the dataset"
    if parsed is None:
        return "unparseable: qa.answer has no number or yes/no"
    if (parsed[0] == "yesno") != isinstance(g, str):
        return "type: qa.answer is yes/no but exe_ans is a number, or the reverse (dataset inconsistency)"
    if parsed[0] == "number" and score.match(("number", -parsed[1], parsed[2]), g):
        return "sign: qa.answer gives the magnitude with the opposite sign of exe_ans"
    if parsed[0] == "number":
        p = decimals(ans)
        if any(round(f, p) == parsed[1] for f in (g, g * 100, g / 100)):
            return f"rounding: qa.answer is exe_ans rounded to {p} decimals, coarser than the tolerance"
    if len(re.findall(r"[a-z]{2,}", ans.lower())) >= 3:
        return "text: qa.answer is a sentence whose first number is not the answer"
    return "label noise: qa.answer disagrees with exe_ans beyond rounding (exe_ans is the official program result)"


def main():
    items = [json.loads(l) for l in open(HERE / "items.jsonl")]
    data = {ex["id"]: ex for ex in json.load(open(HERE / "dataset" / "test.json"))}
    golds = [it["gold"]["exe_ans"] for it in items]
    n = len(items)
    out = {"n_items": n, "rule": "pass if any of v, v/100, v*100 is within max(1% of |gold|, 0.01) of qa.exe_ans; yes/no exact"}

    replay = sum(official.eval_program(official.program_tokenization(it["gold"]["program"]), data[it["item"]]["table"])
                 == (0, it["gold"]["exe_ans"]) for it in items)
    out["official_program_replay"] = {"reproduces_exe_ans": replay, "of": n,
                                      "note": "gold program executed with FinQA code/evaluate/evaluate.py eval_program"}

    styles, fails = Counter(), []
    for it, g in zip(items, golds):
        for style, resp in renderings(g).items():
            r = score.score_one(resp, g)
            styles[style] += r["passed"]
            if not r["passed"]:
                fails.append({"item": it["item"], "style": style, "response": resp, "gold": g})
    out["gold_renderings"] = {"passed": sum(styles.values()), "of": n * 8, "by_style": dict(styles), "failures": fails}

    hum_fail = []
    for it, g in zip(items, golds):
        ans = it["gold"]["answer"]
        if not score.score_one("Answer: " + ans, g)["passed"]:
            hum_fail.append({"item": it["item"], "question": data[it["item"]]["qa"]["question"], "qa.answer": ans,
                             "exe_ans": g, "program": it["gold"]["program"], "reason": human_reason(ans, g),
                             "manual_review": MANUAL.get(it["item"], "NOT REVIEWED")})
    full = [ex for ex in data.values() if not score.score_one("Answer: " + ex["qa"]["answer"], ex["qa"]["exe_ans"])["passed"]]
    out["human_reference"] = {
        "what": "the dataset's human-written qa.answer string scored as 'Answer: <qa.answer>'",
        "passed": n - len(hum_fail), "of": n,
        "failure_reasons": dict(Counter(f["reason"].split(":")[0] for f in hum_fail)),
        "failures": hum_fail,
        "full_test_set": {"passed": len(data) - len(full), "of": len(data),
                          "failure_reasons": dict(Counter(human_reason(ex["qa"]["answer"], ex["qa"]["exe_ans"]).split(":")[0] for ex in full))}}

    def run(make):
        rs = [score.score_one(make(it, g, k), g) for k, (it, g) in enumerate(zip(items, golds))]
        return rs, sum(r["passed"] for r in rs), sum(r["passed_rel1pct"] for r in rs)

    wrong = {
        "other_item_gold": lambda it, g, k: f"Answer: {golds[(k + 1) % n]!r}",
        "no_answer_line": lambda it, g, k: "I cannot determine this from the information provided.",
        "unparseable_answer": lambda it, g, k: "Answer: cannot be determined",
        "type_or_polarity_swap": lambda it, g, k: "Answer: " + ({"yes": "no", "no": "yes"}[g] if isinstance(g, str) else "yes"),
    }
    out["wrong_sets"] = {}
    for name, make in wrong.items():
        rs, p, _ = run(make)
        hits = [{"item": it["item"], "gold": g, "response": make(it, g, k),
                 "why": "numeric coincidence within 1% relative" if r["passed_rel1pct"]
                 else "admitted only by the 0.01 absolute floor (|gold| < 1)"}
                for k, (it, g, r) in enumerate(zip(items, golds, rs)) if r["passed"]]
        out["wrong_sets"][name] = {"passed": p, "of": n, "coincidental_passes": hits}

    num = lambda f: (lambda it, g, k: f"Answer: {f(g)!r}" if not isinstance(g, str) else "Answer: maybe")
    near = {"sign_flipped": num(lambda g: -g), "times_1.10": num(lambda g: g * 1.10),
            "times_1.05": num(lambda g: g * 1.05), "times_1000": num(lambda g: g * 1000)}
    out["near_miss_diagnostics"] = {"note": "informational: shows what the 0.01 absolute floor admits; passed_rel1pct drops it"}
    for name, make in near.items():
        _, p, ps = run(make)
        out["near_miss_diagnostics"][name] = {"passed": p, "passed_rel1pct": ps, "of": n}

    cases = [("**Answer:** $(1,234.5) million", ("number", -1234.5, 1e6)), ("Answer:\n\n14.5%", ("number", 14.5, None)),
             ("The answer is 14.5%.", ("number", 14.5, None)), ("$\\boxed{14.5\\%}$", ("number", 14.5, None)),
             ("Answer: 5,829 − 5,735 = 94", ("number", 94.0, None)), ("Answer: 1.64% (= 94/5735)", ("number", 1.64, None)),
             ("Answer: Yes.", ("yesno", "yes")), ("Answer: No, it fell", ("yesno", "no")), ("Answer: N/A", None),
             ("Answer: 1e-05", ("number", 1e-05, None)), ("Answer: −0.5", ("number", -0.5, None)),
             ("Answer: 2.5x", ("number", 2.5, None)), ("Answer: 94 (in millions)", ("number", 94.0, None)),
             ("Answer: $56.7M", ("number", 56.7, 1e6)), ("Answer: 3 months", ("number", 3.0, None)),
             ("Answer: Q4 total 94", ("number", 94.0, None)), ("Answer: -32 ( 32 )", ("number", -32.0, None)),
             ("Answer: 12 then later\nAnswer: 13", ("number", 13.0, None)), ("no marker 14.5", None),
             ("## Answer\n\n14.46%", ("number", 14.46, None)), ("Answer (rounded): 14.5%", ("number", 14.5, None)),
             ("Answer: 12%\nAfter re-checking, the final answer: 14.46%", ("number", 14.46, None)),
             ("Answer: 14.46%\nNote: the question's answer: depends on rounding", ("number", 14.46, None)),
             ("Answer: (11.8)%", ("number", -11.8, None)), ("Answer: 0.44583 (a 44.58% decrease)", ("number", 0.44583, None)),
             ("**Answer:**\n- 14.5%", ("number", 14.5, None)), ("Answer: $ -94", ("number", -94.0, None)),
             ("Answer: -$ 32 million", ("number", -32.0, 1e6)), ("Answer: 1e999", None)]
    bad = [{"response": r, "expected": e, "got": score.parse(score.extract(r))} for r, e in cases
           if score.parse(score.extract(r)) != e]
    out["parser_unit_cases"] = {"passed": len(cases) - len(bad), "of": len(cases), "failures": bad}

    out["summary"] = {
        "official_program_replay": f"{replay}/{n}",
        "gold_renderings_pass": f"{out['gold_renderings']['passed']}/{n * 8}",
        "human_reference_pass": f"{out['human_reference']['passed']}/{n}",
        "wrong_sets_pass": {k: f"{v['passed']}/{n}" for k, v in out["wrong_sets"].items()},
        "parser_unit_cases": f"{len(cases) - len(bad)}/{len(cases)}",
    }
    (HERE / "selfcheck.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary"], indent=1))
    print(json.dumps(out["near_miss_diagnostics"], indent=1))


if __name__ == "__main__":
    main()
