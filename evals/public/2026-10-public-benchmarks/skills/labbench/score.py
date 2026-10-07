#!/usr/bin/env python3
"""Score LAB-Bench (ProtocolQA + SeqQA) responses with the official LAB-Bench parser.

Usage: python score.py responses.jsonl out.jsonl [--items items.jsonl]

passed = official rule: chembench 0.3.0 prepare_mcq_answer + run_regex over the
[ANSWER]X[/ANSWER] tag exactly as labbench/zero_shot.py runs it, then
evaluator.py `agent_output == target`. Secondary fields:
  answer / target / insufficient   parsed letter (null if none), correct letter, refuse-option letter
  chose_insufficient               1 if the parsed letter is "Insufficient information to answer the question"
  sure                             official coverage flag: answer != insufficient letter (unparsed counts as sure)
  parsed                           1 if the official parser produced an option letter
  multi_tag_conflict               1 if the tags hold >1 distinct letters (upstream then keeps the alphabetically first)
  answer_lenient / passed_lenient / chose_insufficient_lenient
                                   robustness view, NOT the official metric: letter of the LAST answer-tag pair after
                                   tolerating tag case, markdown/quote wrappers, "(B)", "B)", "B:", "Option B";
                                   no tagged letter -> the official answer
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official  # noqa: E402

_TAG_PAIR = re.compile(
    r"(?:\[ANSWER\]|\[ANS\]|<ANS>|<ANSWER>)(.*?)(?:\[/?ANSWER\]|\[/ANS\]|</ANS>|</ANSWER>)",
    re.IGNORECASE | re.DOTALL,
)
_WRAP = " \t\r\n*_`'\"“”‘’"
_PREFIX = re.compile(r"^(?:option|answer|choice)\s*[:\-]?\s*", re.IGNORECASE)
_LETTER_FORMS = (
    re.compile(r"\(([A-Za-z])\)(?:\s.*)?", re.DOTALL),  # (B) / (B) text
    re.compile(r"\[([A-Za-z])\](?:\s.*)?", re.DOTALL),  # [B] / [B] text
    re.compile(r"([A-Za-z])[.:)](?:\s.*)?", re.DOTALL),  # B. / B: / B) / B) text
    re.compile(r"([A-Za-z])"),  # B
)


def lenient_answer(text: str, n_choices: int, official_answer: str | None) -> str | None:
    allowed = official.ALPHABET[:n_choices]
    letters = []
    for inner in _TAG_PAIR.findall(text):
        s = _PREFIX.sub("", inner.strip(_WRAP)).strip(_WRAP)
        for form in _LETTER_FORMS:
            m = form.fullmatch(s)
            if m and m.group(1).upper() in allowed:
                letters.append(m.group(1).upper())
                break
    return letters[-1] if letters else official_answer


def score_one(response: str | None, gold: dict) -> dict:
    text = response if isinstance(response, str) else ""
    n = gold["n_choices"]
    answer, _ = official.parse_answer(text, n)
    tagged = {x.strip() for m in re.findall(official.MCQ_REGEX_TEMPLATE_1, text, re.DOTALL) for x in m.split(",")}
    lenient = lenient_answer(text, n, answer)
    return {
        "passed": int(official.is_correct(answer, gold["answer"])),
        "answer": answer,
        "target": gold["answer"],
        "insufficient": gold["insufficient"],
        "chose_insufficient": int(answer == gold["insufficient"]),
        "sure": int(official.is_sure(answer, gold["insufficient"])),
        "parsed": int(answer is not None),
        "multi_tag_conflict": int(len(tagged) > 1),
        "answer_lenient": lenient,
        "passed_lenient": int(lenient == gold["answer"]),
        "chose_insufficient_lenient": int(lenient == gold["insufficient"]),
        "subset": gold["subset"],
        "subtask": gold["subtask"],
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(r["passed"] for r in rows)
    sure = sum(r["sure"] for r in rows)
    return {
        "n": n,
        "accuracy": round(correct / n, 4) if n else 0.0,
        "precision": round(correct / sure, 4) if sure else 0.0,  # official: correct / sure
        "coverage": round(sure / n, 4) if n else 0.0,  # official: sure / total
        "parsed": round(sum(r["parsed"] for r in rows) / n, 4) if n else 0.0,
        "chose_insufficient": round(sum(r["chose_insufficient"] for r in rows) / n, 4) if n else 0.0,
        "accuracy_lenient": round(sum(r["passed_lenient"] for r in rows) / n, 4) if n else 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("responses")
    ap.add_argument("out")
    ap.add_argument("--items", default=str(HERE / "items.jsonl"))
    args = ap.parse_args()

    gold = {}
    with open(args.items, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                gold[rec["item"]] = rec["gold"]

    responses = []
    with open(args.responses, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if line.strip():
                rec = json.loads(line)
                if rec.get("item") not in gold:
                    sys.exit(f"{args.responses}:{lineno}: unknown item {rec.get('item')!r} (wrong items file?)")
                responses.append(rec)

    rows = [{"item": rec["item"], **score_one(rec.get("response"), gold[rec["item"]])} for rec in responses]
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    counts = collections.Counter(r["item"] for r in rows)
    dupes = sorted(k for k, v in counts.items() if v > 1)
    missing = len(set(gold) - set(counts))
    if dupes:
        print(f"WARNING: {len(dupes)} items scored more than once, e.g. {dupes[0]}", file=sys.stderr)
    if missing:
        print(f"WARNING: {missing} of {len(gold)} items have no response (not written)", file=sys.stderr)
    summary = {"all": summarize(rows)}
    for subset in sorted({r["subset"] for r in rows}):
        summary[subset] = summarize([r for r in rows if r["subset"] == subset])
    print(json.dumps(summary), file=sys.stderr)


if __name__ == "__main__":
    main()
