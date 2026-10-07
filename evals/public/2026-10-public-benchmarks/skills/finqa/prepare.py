#!/usr/bin/env python3
"""Build items.jsonl + source.json from the pinned FinQA public test split.

Usage: python prepare.py
Source: github.com/czyssrs/FinQA @ 0f16e28 (this directory is that clone), dataset/test.json.
"""
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "dataset" / "test.json"
COMMIT = "0f16e2867befa6840783e58be38c9efb9229d742"
DATA_SHA256 = "831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc"
SEED, N = 20261006, 200

INTRO = "Read the following text and table, and then answer a question."
INSTRUCTION = ('Give your final answer on the last line in the form "Answer: <value>", '
               "where <value> is a single number, or yes or no if the question asks for a yes/no answer.")


def render_table(rows):
    """Markdown pipe table; row 0 is the header, as in FinQA's own table_row_to_text."""
    line = lambda cells: "| " + " | ".join(cells) + " |"
    return "\n".join([line(rows[0]), "|" + " --- |" * len(rows[0])] + [line(r) for r in rows[1:]])


def build_prompt(ex):
    parts = [INTRO, " ".join(ex["pre_text"]).strip(), render_table(ex["table"]),
             " ".join(ex["post_text"]).strip(), "Question: " + ex["qa"]["question"].strip(), INSTRUCTION]
    return "\n\n".join(p for p in parts if p)


def eligible(ex):
    g = ex["qa"].get("exe_ans")
    ok_gold = g in ("yes", "no") or (isinstance(g, (int, float)) and math.isfinite(g))
    return ok_gold and bool(ex["qa"].get("question", "").strip()) and bool(ex["table"])


def main():
    head = subprocess.run(["git", "-C", str(HERE), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"FinQA clone is at {head}, expected {COMMIT}")
    raw = DATA.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != DATA_SHA256:
        raise SystemExit(f"dataset/test.json sha256 {sha} != pinned {DATA_SHA256}")
    data = json.loads(raw)
    by_id = {ex["id"]: ex for ex in data}
    if len(by_id) != len(data):
        raise SystemExit("duplicate ids in dataset/test.json")

    ids = sorted(i for i, ex in by_id.items() if eligible(ex))
    perm = np.random.default_rng(SEED).permutation(len(ids))
    chosen = [ids[k] for k in perm[:N]]

    lines = []
    for i in chosen:
        qa = by_id[i]["qa"]
        gold = {"exe_ans": qa["exe_ans"], "answer": qa["answer"], "program": qa["program"]}
        lines.append(json.dumps({"item": i, "prompt": build_prompt(by_id[i]), "gold": gold}))
    body = ("\n".join(lines) + "\n").encode()
    (HERE / "items.jsonl").write_bytes(body)

    source = {
        "benchmark": "FinQA (Chen et al., EMNLP 2021, arXiv:2109.00122)",
        "repo": "https://github.com/czyssrs/FinQA",
        "commit": COMMIT,
        "file": "dataset/test.json",
        "file_sha256": sha,
        "split": "public test (with references)",
        "licence": "MIT (repository LICENSE, covers code and data)",
        "n_total": len(data),
        "n_eligible": len(ids),
        "eligibility": "every test example whose qa.exe_ans is a finite number or yes/no, with a question and a table",
        "n_sampled": len(chosen),
        "sampling": f"sorted(eligible ids); numpy.random.default_rng({SEED}).permutation(len(ids)); first {N}",
        "numpy_version": np.__version__,
        "gold_numeric": sum(not isinstance(by_id[i]["qa"]["exe_ans"], str) for i in chosen),
        "gold_yes_no": sum(isinstance(by_id[i]["qa"]["exe_ans"], str) for i in chosen),
        "items_sha256": hashlib.sha256(body).hexdigest(),
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    print(json.dumps(source, indent=2))


if __name__ == "__main__":
    main()
