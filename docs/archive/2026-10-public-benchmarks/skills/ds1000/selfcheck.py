"""Prove score.py right on the sampled items -> selfcheck.json.   usage: python selfcheck.py

Every set goes through score.py's full pipeline (extraction -> official postprocess -> official test, Docker):
  gold_fenced   reference_code in a chat-style ```python block with prose around it   expect pass
  gold_raw      reference_code as the bare response (no block: whole-response path)   expect pass
  gold_dedented function-body items: reference with 4 leading spaces removed          expect pass (re-indent rule)
  empty         empty response                                                         expect fail
  wrong         reference_code of the next sampled item (cyclic shift)                 expect fail
"""
import collections
import datetime
import json
import os
import re
import time
from pathlib import Path

import score

HERE = Path(__file__).resolve().parent

# Filled in after inspecting each unexpected outcome (item -> reason); anything not listed is reported UNEXPLAINED.
EXPLANATIONS = {}

UNIT_CASES = [  # (response, expected extraction method, expected solution after postprocess)
    ("Here:\n```python\nresult = 1\n```\nDone.", "fenced", "result = 1\n"),
    ("```python\nA = 1\n```\nthen\n```python\nB = 2\n```", "fenced", "A = 1\n"),
    ("```\nout\n```\n```py\nX = 1\n```", "fenced", "X = 1\n"),
    ("1. Do this:\n   ```Python\n   result = 4\n   ```\n", "fenced", "result = 4\n"),
    ("```python\nresult = 5\n", "fenced", "result = 5\n\n"),
    ("```python\nresult = 7\nEND SOLUTION\n```", "fenced", "result = 7"),
    ("Sure!\n<code>\nresult = 2\n</code>\nEND SOLUTION", "code_tag", "\nresult = 2\n"),
    ("result = 3\n", "whole", "result = 3\n"),
    ("", "whole", ""),
]


def unit_checks():
    failures = []
    for response, method, expected in UNIT_CASES:
        raw, got_method, _ = score.extract(response)
        got = score.official_postprocess(raw)
        if (got_method, got) != (method, expected):
            failures.append({"response": response, "got": [got_method, got], "expected": [method, expected]})
    reindent = [
        (score.reindent_if_needed("result = df\nreturn result\n", "    "), ("    result = df\n    return result\n", True)),
        (score.reindent_if_needed("# note\n    return df\n", "    "), ("# note\n    return df\n", False)),
        (score.reindent_if_needed("result = df\n", ""), ("result = df\n", False)),
    ]
    failures += [{"reindent_got": got, "expected": exp} for got, exp in reindent if got != exp]
    return {"n": len(UNIT_CASES) + len(reindent), "failures": failures}


def dedent4(code: str) -> str:
    return "\n".join(line[4:] if line.startswith("    ") else line for line in code.split("\n"))


def main() -> None:
    items = score.load_items()
    ids = list(items)
    sets = {  # name: (expect, description, rows)
        "gold_fenced": ("pass", "reference_code inside a chat-style ```python block with prose around it",
                        [{"item": i, "response": "Here is the completion:\n```python\n" + items[i]["reference_code"]
                          + "\n```\nIt fills in the solution."} for i in ids]),
        "gold_raw": ("pass", "reference_code as the bare response (no block: whole-response path)",
                     [{"item": i, "response": items[i]["reference_code"]} for i in ids]),
        "gold_dedented": ("pass", "function-body items: reference with 4 leading spaces removed (re-indent rule)",
                          [{"item": i, "response": "```python\n" + dedent4(items[i]["reference_code"]) + "\n```"}
                           for i in ids if items[i]["solution_indent"]]),
        "empty": ("fail", "empty response", [{"item": i, "response": ""} for i in ids]),
        "wrong": ("fail", "reference_code of the next sampled item (cyclic shift), in a ```python block",
                  [{"item": i, "response": "```python\n" + items[ids[(k + 1) % len(ids)]]["reference_code"] + "\n```"}
                   for k, i in enumerate(ids)]),
    }
    report = {
        "created": datetime.date.today().isoformat(), "image": score.image_tag(), "n_items": len(ids),
        "workers": int(os.environ.get("DS1000_WORKERS", "4")), "extraction_unit_checks": unit_checks(), "sets": {},
    }
    results = {}
    for name, (expect, description, rows) in sets.items():
        t0 = time.time()
        out = score.score_rows(rows, items)
        results[name] = {r["item"]: r for r in out}
        unexpected = [r for r in out if r["passed"] != (expect == "pass")]
        kinds = collections.Counter(re.sub(r"\d+", "#", r["result"])[:70] for r in out)
        report["sets"][name] = {
            "expect": expect, "description": description, "n": len(out), "passed": sum(r["passed"] for r in out),
            "pass_rate": round(sum(r["passed"] for r in out) / len(out), 4),
            "reindented": sum(r["reindented"] for r in out), "sandbox_errors": sum(r["sandbox_error"] for r in out),
            "seconds": round(time.time() - t0), "top_results": kinds.most_common(6),
            "unexpected": [{"item": r["item"], "library": r["library"], "result": r["result"][:300],
                            "explanation": EXPLANATIONS.get((name, r["item"]), EXPLANATIONS.get(r["item"], "UNEXPLAINED"))}
                           for r in unexpected],
        }
        print(f"{name}: {report['sets'][name]['passed']}/{len(out)} passed (expect {expect})")
    flips = [i for i in ids if results["gold_fenced"][i]["passed"] != results["gold_raw"][i]["passed"]]
    report["gold_fenced_vs_gold_raw_disagreements"] = flips
    (HERE / "selfcheck.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
