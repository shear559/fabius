#!/usr/bin/env python3
"""Re-score IFEval from the public archive and compare with the published outcomes.

  check_ifeval_public.py <archive_root> <path to google-research instruction_following_eval parent>

Uses the official scorer unchanged (langdetect seeded as in score_ifeval.py) on the masked
final texts in <archive_root>/runs/ifeval and compares prompt-level strict and loose outcomes
with <archive_root>/results/ifeval/items.csv. Expected: every outcome reproduces except
possibly items 1122 and 1129, whose instruction names a non-letter ("#", "!") as the letter to
count; the official code then counts a random letter, so those two outcomes vary between
scorings whatever the text.
"""
import csv
import json
import sys
from pathlib import Path

ARCHIVE, IFEVAL = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(IFEVAL))
sys.path.insert(0, str(ARCHIVE / "harness"))

import langdetect  # noqa: E402

langdetect.DetectorFactory.seed = 0

from instruction_following_eval import evaluation_lib  # noqa: E402
import collect  # noqa: E402

RANDOM_LETTER_ITEMS = {"1122", "1129"}


def main():
    collect.ROOT = ARCHIVE
    data = IFEVAL / "instruction_following_eval/data/input_data.jsonl"
    inputs = evaluation_lib.read_prompt_list(str(data))
    key_of = {json.loads(l)["prompt"]: str(json.loads(l)["key"]) for l in open(data)}
    published = {(r["item"], r["arm"]): r for r in csv.DictReader(open(ARCHIVE / "results/ifeval/items.csv"))}
    recs = {(r["item"], r["arm"]): r for r in collect.records("ifeval")}
    same = differ = 0
    for arm in ("baseline", "fabius-loaded"):
        responses = {inp.prompt: (recs.get((key_of[inp.prompt], arm)) or {}).get("final_text") or "" for inp in inputs}
        for func, col in ((evaluation_lib.test_instruction_following_strict, "passed"),
                          (evaluation_lib.test_instruction_following_loose, "loose_passed")):
            for inp in inputs:
                key = key_of[inp.prompt]
                was = published[(key, arm)][col]
                if was == "":
                    continue  # excluded: no scored attempt in either arm
                if func(inp, responses).follow_all_instructions == (was == "1"):
                    same += 1
                else:
                    differ += 1
                    note = " (random letter in the official scorer)" if key in RANDOM_LETTER_ITEMS else ""
                    print(f"differs: item {key} · {arm} · {col}{note}")
    print(f"reproduced {same} of {same + differ} published IFEval outcomes")


if __name__ == "__main__":
    main()
