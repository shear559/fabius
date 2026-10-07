#!/usr/bin/env python3
"""LongMemEval scorer, stage 1 of 2: write the OFFICIAL judge prompt for every response.

usage: python score.py responses.jsonl out.jsonl [--judge-prompts PATH]

LongMemEval's official metric is an LLM judge (evaluate_qa.py). This script calls no model:
  * PATH (default: out.jsonl with ".jsonl" -> ".judge_prompts.jsonl") gets one line per response
    {"item", "judge_prompt", "official_judge", ...}; judge_prompt is built by the authors' own
    get_anscheck_prompt (per question type, abstention template for *_abs ids), byte for byte.
  * out.jsonl gets {"item", "passed": null, "status": "awaiting_judge", ...} placeholders.
Send each judge_prompt as ONE user message to the judge (official: gpt-4o-2024-08-06,
temperature 0, max_tokens 10), save {"item", "judgement": "<judge text>"} lines, then run
  python score_from_judgements.py PATH judgements.jsonl out.jsonl
which writes the final passed (0/1) with the official rule  'yes' in judgement.lower().
"""
import argparse
import json
import os
import re
import string
import sys
import unicodedata

import official_loader

HERE = os.path.dirname(os.path.abspath(__file__))
OFFICIAL_JUDGE = {"model": "gpt-4o-2024-08-06", "temperature": 0, "max_tokens": 10, "n": 1,
                  "input": "judge_prompt as the only (user) message"}
NUMWORDS = dict(zip("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                    "sixteen seventeen eighteen nineteen twenty".split(), map(str, range(21))))
NUMWORDS.update(dict(zip("thirty forty fifty sixty seventy eighty ninety".split(), map(str, range(30, 100, 10)))))


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def normalize(text):
    """SQuAD normalize_answer (lower, drop punctuation, drop a/an/the, squeeze spaces) + number words 0-20, 30-90."""
    s = unicodedata.normalize("NFKC", str(text)).lower()
    s = "".join(ch for ch in s if ch not in string.punctuation and not unicodedata.category(ch).startswith("P"))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(NUMWORDS.get(t, t) for t in s.split())


def string_match(answer, response):
    """SECONDARY, not official: the whole normalized gold answer occurs in the normalized response."""
    g = normalize(answer)
    return int(bool(g) and f" {g} " in f" {normalize(response)} ")


def judge_rows(items, responses):
    anscheck = official_loader.get_anscheck_prompt()
    rows, seen = [], set()
    for r in responses:
        iid = r["item"]
        if iid not in items:
            raise SystemExit(f"unknown item {iid!r} (not in items.jsonl)")
        if iid in seen:
            raise SystemExit(f"duplicate response for item {iid!r}")
        seen.add(iid)
        g = items[iid]["gold"]
        hyp = "" if r.get("response") is None else str(r["response"]).strip()  # official hypothesis = reply .strip()
        abstention = "_abs" in iid  # evaluate_qa.py: abstention='_abs' in question_id
        rows.append({
            "item": iid,
            "judge_prompt": anscheck(g["question_type"], g["question"], g["answer"], hyp, abstention=abstention),
            "official_judge": OFFICIAL_JUDGE,
            "question_type": g["question_type"],
            "abstention": abstention,
            "string_match": None if abstention or g["question_type"] == "single-session-preference"
            else string_match(g["answer"], hyp),
            "empty_response": hyp == "",
        })
    return rows, set(items) - seen


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("responses")
    ap.add_argument("out")
    ap.add_argument("--judge-prompts", default=None)
    a = ap.parse_args()
    jp_path = a.judge_prompts or (a.out[:-6] if a.out.endswith(".jsonl") else a.out) + ".judge_prompts.jsonl"
    if os.path.abspath(jp_path) == os.path.abspath(a.out):
        raise SystemExit("--judge-prompts must differ from out")

    items = {r["item"]: r for r in read_jsonl(os.path.join(HERE, "items.jsonl"))}
    rows, missing = judge_rows(items, read_jsonl(a.responses))
    write_jsonl(jp_path, rows)
    keep = ("question_type", "abstention", "string_match", "empty_response")
    write_jsonl(a.out, [{"item": r["item"], "passed": None, "status": "awaiting_judge", **{k: r[k] for k in keep}}
                        for r in rows])
    if missing:
        print(f"note: {len(missing)} of {len(items)} items have no response: {sorted(missing)[:10]}", file=sys.stderr)
    print(f"wrote {len(rows)} official judge prompts -> {jp_path}\n"
          f"next: judge each prompt (official: gpt-4o-2024-08-06, temperature 0, max_tokens 10), save "
          f'{{"item", "judgement"}} lines, then: python score_from_judgements.py {jp_path} judgements.jsonl {a.out}')


if __name__ == "__main__":
    main()
