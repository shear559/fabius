#!/usr/bin/env python3
"""LongMemEval scorer, stage 2 of 2: judge verdicts -> passed.

usage: python score_from_judgements.py judge_prompts.jsonl judgements.jsonl out.jsonl

judgements.jsonl: one line per item {"item": ..., "judgement": "<the judge's reply text>"}
("judgment", "verdict" or "response" are accepted as the key too). Every item of
judge_prompts.jsonl needs exactly one judgement, or nothing is written.
passed = official rule of evaluate_qa.py:  label = 'yes' in reply.strip().lower()
Secondary: verdict_strict (first word yes/no, else null) and verdict_ambiguous (strict != official),
for spotting replies such as "No ... yes" that the official substring rule counts as yes.
Prints accuracy the way print_qa_metrics.py does (per type, task-averaged, overall, abstention).
"""
import json
import re
import statistics
import sys

from score import read_jsonl, write_jsonl

KEYS = ("judgement", "judgment", "verdict", "response")
TYPES = ["single-session-user", "single-session-preference", "single-session-assistant",
         "multi-session", "temporal-reasoning", "knowledge-update"]  # print_qa_metrics.py order


def official_label(text):
    return int("yes" in str(text).strip().lower())


def strict_label(text):
    m = re.match(r"[^a-z]*([a-z]+)", str(text).strip().lower())
    word = m.group(1) if m else ""
    return {"yes": 1, "no": 0}.get(word)


def judgement_text(row):
    for k in KEYS:
        if k in row:
            return "" if row[k] is None else str(row[k])
    raise SystemExit(f"judgement line without any of {KEYS}: {row}")


def score(prompt_rows, judgement_rows):
    verdicts = {}
    for r in judgement_rows:
        if r["item"] in verdicts:
            raise SystemExit(f"duplicate judgement for item {r['item']!r}")
        verdicts[r["item"]] = judgement_text(r)
    items = [p["item"] for p in prompt_rows]
    missing = [i for i in items if i not in verdicts]
    extra = sorted(set(verdicts) - set(items))
    if missing or extra:
        raise SystemExit(f"judgements do not match judge prompts: missing {missing[:10]} ({len(missing)}), "
                         f"unknown {extra[:10]} ({len(extra)})")
    out = []
    for p in prompt_rows:
        text = verdicts[p["item"]]
        passed, strict = official_label(text), strict_label(text)
        out.append({"item": p["item"], "passed": passed, "judgement": text[:300], "verdict_strict": strict,
                    "verdict_ambiguous": strict != passed, "question_type": p["question_type"],
                    "abstention": p["abstention"], "string_match": p["string_match"],
                    "empty_response": p["empty_response"]})
    return out


def summary(rows):
    def acc(xs):
        return round(statistics.mean(xs), 4) if xs else None

    by_type = {t: [r["passed"] for r in rows if r["question_type"] == t] for t in TYPES}
    present = [v for v in by_type.values() if v]
    return {
        "n": len(rows),
        "overall_accuracy": acc([r["passed"] for r in rows]),
        "task_averaged_accuracy": acc([statistics.mean(v) for v in present]),
        "abstention_accuracy": acc([r["passed"] for r in rows if r["abstention"]]),
        "by_type": {t: {"accuracy": acc(v), "n": len(v)} for t, v in by_type.items()},
        "ambiguous_verdicts": sum(r["verdict_ambiguous"] for r in rows),
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: python score_from_judgements.py judge_prompts.jsonl judgements.jsonl out.jsonl")
    rows = score(read_jsonl(sys.argv[1]), read_jsonl(sys.argv[2]))
    write_jsonl(sys.argv[3], rows)
    print(json.dumps(summary(rows), indent=1))


if __name__ == "__main__":
    main()
