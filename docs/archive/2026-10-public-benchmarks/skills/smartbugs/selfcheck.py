#!/usr/bin/env python3
"""Prove prepare.py + score.py right; writes selfcheck.json.  usage: python selfcheck.py"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import prepare

HERE = Path(__file__).resolve().parent
LABELS = [c for c, _ in prepare.CATEGORIES]
DASP = {"reentrancy": "Reentrancy", "access_control": "Access Control", "arithmetic": "Arithmetic Issues",
        "unchecked_low_level_calls": "Unchecked Return Values For Low Level Calls",
        "denial_of_service": "Denial of Service", "bad_randomness": "Bad Randomness",
        "front_running": "Front-Running", "time_manipulation": "Time Manipulation",
        "short_addresses": "Short Address Attack", "other": "Unknown Unknowns"}

items = [json.loads(line) for line in open(HERE / "items.jsonl", encoding="utf-8")]
records, _ = prepare.load_records()
rec = {r["path"]: r for r in records}


def wrong_label(gold_cats):
    i = LABELS.index(gold_cats[0])
    return next(LABELS[(i + k) % 10] for k in range(1, 10) if LABELS[(i + k) % 10] not in gold_cats)


def non_gold_line(gold):
    used = {x for ls in gold["lines"].values() for x in ls}
    return next(n for n in range(1, 10**6) if n not in used)


def own(it):  # the item's own vulnerabilities.json annotation (not the duplicate's)
    return rec[it["item"]]["annotations"][0]


def csv(xs):
    return ", ".join(map(str, xs))


SETS = {  # name -> (expected passed, expected line_hit or None, response builder)
    "gold_vulnerabilities_json": (1, 1, lambda it: (
        f"Category: {own(it)['category']}\nLines: {csv(own(it)['lines'])}")),
    "gold_inline_markers_verbatim": (1, 1, lambda it: (
        f"Category: {rec[it['item']]['markers'][0]['label']}\n"
        f"Lines: {csv(m['line'] for m in rec[it['item']]['markers'])}")),
    "gold_dasp_names_markdown_range": (1, 1, lambda it: (
        "## Finding\nThe flaw sits in the function shown.\n\n"
        f"**Category:** {DASP[own(it)['category']]}\n"
        f"**Lines:** {own(it)['lines'][0]}–{own(it)['lines'][0] + 2}\n\nHappy to suggest a fix.")),
    "every_wrong_label_after_gold_in_prose": (0, 0, lambda it: [
        f"One could suspect {DASP[it['gold']['categories'][0]]} here, but the main issue differs.\n"
        f"Category: {w}\nLines: {non_gold_line(it['gold'])}" for w in LABELS if w not in it["gold"]["categories"]]),
    "hedged_two_labels": (0, 1, lambda it: (
        f"Category: {it['gold']['categories'][0]} or {wrong_label(it['gold']['categories'])}\n"
        f"Lines: {csv(it['gold']['lines'][it['gold']['categories'][0]])}")),
    "gold_in_prose_no_answer_lines": (0, 0, lambda it: (
        f"The most important vulnerability is {it['gold']['categories'][0]} "
        f"({DASP[it['gold']['categories'][0]]}) at line {it['gold']['lines'][it['gold']['categories'][0]][0]}.")),
    "empty_response": (0, 0, lambda it: ""),
}


def run_set(build, tmp, name):
    resp, out = Path(tmp) / f"{name}.jsonl", Path(tmp) / f"{name}.out.jsonl"
    resp.write_text("".join(json.dumps({"item": it["item"], "response": r}) + "\n" for it in items
                            for r in (lambda x: x if isinstance(x, list) else [x])(build(it))))
    subprocess.run([sys.executable, str(HERE / "score.py"), str(resp), str(out)], check=True, capture_output=True)
    return [json.loads(line) for line in out.read_text().splitlines()]


def prompt_checks():
    leaks = [it["item"] for it in items
             if re.search(r"<yes>|<report>|@vulnerable_at_lines|@source|smartbugs", it["prompt"], re.I)]
    mismatches, checked = [], 0
    for it in items:
        code = it["prompt"].split("```solidity\n", 1)[1].rsplit("\n```", 1)[0].split("\n")
        shown = {int(m.group(1)): m.group(2) for m in (re.match(r"^\s*(\d+) \|(?: (.*))?$", c) for c in code)}
        for a in it["gold"]["annotations"]:
            raw = subprocess.run(["git", "-C", str(HERE), "show", f"{prepare.COMMIT}:{a['path']}"],
                                 check=True, capture_output=True).stdout.decode().split("\n")
            for orig, new in zip(a["orig_lines"], a["lines"]):
                checked += 1
                if (shown.get(new) or "").rstrip() != raw[orig - 1].rstrip():
                    mismatches.append([it["item"], orig, new])
    fresh = {r["path"]: prepare.TEMPLATE.replace("{source}", r["source"]) for r in records}
    ids = sorted(fresh)
    order = [ids[i] for i in np.random.default_rng(prepare.SEED).permutation(len(ids))[:prepare.N]]
    src = json.loads((HERE / "source.json").read_text())
    return {
        "sampling_order_reproduces": [it["item"] for it in items] == order,
        "items_jsonl_sha256_matches_source_json":
            hashlib.sha256((HERE / "items.jsonl").read_bytes()).hexdigest() == src["items_jsonl_sha256"],
        "prompts_with_markup_or_dataset_name": leaks,
        "gold_lines_checked": checked,
        "gold_line_text_mismatches_vs_annotated_file": mismatches,
        "items_match_fresh_prepare_run": all(fresh[it["item"]] == it["prompt"] and
                                             rec[it["item"]]["gold"] == it["gold"] for it in items),
        "readme_contains_exact_template": json.dumps(prepare.TEMPLATE) in (HERE / "README.md").read_text(),
    }


def main():
    report = {"n_items": len(items), "prompt_integrity": prompt_checks(), "sets": {}}
    pi = report["prompt_integrity"]
    ok = (not pi["prompts_with_markup_or_dataset_name"] and not pi["gold_line_text_mismatches_vs_annotated_file"]
          and pi["items_match_fresh_prepare_run"] and pi["readme_contains_exact_template"]
          and pi["sampling_order_reproduces"] and pi["items_jsonl_sha256_matches_source_json"])
    with tempfile.TemporaryDirectory() as tmp:
        for name, (exp_pass, exp_line, build) in SETS.items():
            rows = run_set(build, tmp, name)
            off = [{"item": r["item"], "passed": r["passed"], "line_hit": r["line_hit"],
                    "category_pred": r["category_pred"], "status": r["category_status"]}
                   for r in rows if r["passed"] != exp_pass or (exp_line is not None and r["line_hit"] != exp_line)]
            report["sets"][name] = {
                "expect_passed": exp_pass, "expect_line_hit": exp_line, "n": len(rows),
                "passed": sum(r["passed"] for r in rows), "line_hit": sum(r["line_hit"] for r in rows),
                "cat_line_hit": sum(r["cat_line_hit"] for r in rows), "unexpected": off,
            }
            ok &= not off
    report["all_expectations_met"] = ok
    (HERE / "selfcheck.json").write_text(json.dumps(report, indent=1) + "\n")
    for name, s in report["sets"].items():
        print(f"{name:38s} passed {s['passed']:4d}/{s['n']:<4d} line_hit {s['line_hit']:4d}  "
              f"cat_line_hit {s['cat_line_hit']:4d}  unexpected {len(s['unexpected'])}")
    print(json.dumps(report["prompt_integrity"]), "\nALL OK" if ok else "\nFAILURES")


if __name__ == "__main__":
    main()
