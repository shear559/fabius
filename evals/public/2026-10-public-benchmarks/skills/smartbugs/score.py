#!/usr/bin/env python3
"""Score SmartBugs-curated responses.

usage: python score.py responses.jsonl out.jsonl
  responses.jsonl: {"item": ..., "response": "<model text>"} per line
  out.jsonl:       {"item", "passed", ...secondary} per line (same order)

Rule (deterministic):
  * The LAST line starting with "Category:" (markdown decoration allowed) is the answer;
    if none starts that way, the last "...category:" anywhere in a line. Same for "Lines:".
  * Its value must name exactly ONE of the 10 labels, by snake_case label, DASP name or
    SmartBugs marker spelling (case/punctuation-insensitive; bracketed asides and text after
    a spaced dash are ignored). Two different labels = hedge = fail; no label = fail.
  * passed       = that label is one of the contract's annotated categories.
  * line_hit     = any predicted line (ranges like 12-14 expanded) is an annotated line.
  * cat_line_hit = passed AND a predicted line is annotated for that category
                   (the SmartBugs/ICSE-2020 tool criterion: right category at the right line).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# normalised spelling -> canonical SmartBugs-curated label
SPELLINGS = {
    "reentrancy": "reentrancy", "re entrancy": "reentrancy",
    "access control": "access_control",
    "arithmetic": "arithmetic", "arithmetic issues": "arithmetic", "arithmetic issue": "arithmetic",
    "unchecked low level calls": "unchecked_low_level_calls",
    "unchecked low level call": "unchecked_low_level_calls",
    "unchecked return values for low level calls": "unchecked_low_level_calls",
    "unchecked ll calls": "unchecked_low_level_calls",  # SmartBugs marker UNCHECKED_LL_CALLS
    "denial of service": "denial_of_service",
    "bad randomness": "bad_randomness",
    "front running": "front_running", "frontrunning": "front_running",
    "time manipulation": "time_manipulation",
    "short addresses": "short_addresses", "short address": "short_addresses",
    "short address attack": "short_addresses",
    "other": "other", "unknown unknowns": "other",
}
DECOR = r"[\s>*_`#|•\-\d.)]*"  # bullets, quotes, bold, headings, "1." before the field name
CAT_START = re.compile(rf"^{DECOR}category[\s*_`]*[:：](.*)$", re.I)
CAT_ANY = re.compile(r"\bcategory\b[\s*_`]*[:：](.*)$", re.I)
LINES_START = re.compile(rf"^{DECOR}lines?(?:\(s\))?[\s*_`]*[:：](.*)$", re.I)
LINES_ANY = re.compile(r"\blines?(?:\(s\))?[\s*_`]*[:：](.*)$", re.I)
NUM = re.compile(r"(?<![A-Za-z0-9_.])[L#]?(\d+)(?:\s*(?:-|–|—|\.\.|to)\s*[L#]?(\d+))?(?![A-Za-z0-9_])")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def last_value(text: str, start: re.Pattern, anywhere: re.Pattern):
    lines = text.splitlines()
    for pat in (start, anywhere):
        for line in reversed(lines):
            m = pat.search(line)
            if m:
                return m.group(1)
    return None


def labels_in(n: str) -> set:
    if n in SPELLINGS:
        return {SPELLINGS[n]}
    return {lab for sp, lab in SPELLINGS.items() if re.search(rf"(?<![a-z0-9]){re.escape(sp)}(?![a-z0-9])", n)}


def resolve_category(value):
    """-> (label or None, status). Bracketed asides and text after a spaced dash are
    explanation: "reentrancy (not access_control)" -> reentrancy; "a or b" -> ambiguous."""
    if value is None:
        return None, "no_category_line"
    value = re.split(r"\blines?(?:\(s\))?[\s*_`]*[:：]", value, flags=re.I)[0]
    main = re.split(r"\s[-–—]\s", re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", value))[0]
    found = labels_in(norm(main)) or labels_in(norm(value))
    if len(found) == 1:
        return found.pop(), "ok"
    if not norm(value):
        return None, "empty_label"
    return None, "ambiguous_label" if found else "unknown_label"


def parse_lines(value):
    if value is None:
        return []
    out = set()
    for m in NUM.finditer(value):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        out.update(range(a, b + 1) if a <= b <= a + 10000 else (a, b))
    return sorted(out)


def score_one(response, gold):
    text = response if isinstance(response, str) else ""
    cat, status = resolve_category(last_value(text, CAT_START, CAT_ANY))
    pred = parse_lines(last_value(text, LINES_START, LINES_ANY))
    all_gold = {x for ls in gold["lines"].values() for x in ls}
    passed = int(cat in gold["categories"])
    return {
        "passed": passed,
        "category_pred": cat,
        "category_status": status,
        "gold_categories": gold["categories"],
        "line_hit": int(bool(all_gold.intersection(pred))),
        "cat_line_hit": int(passed and bool(set(gold["lines"][cat]).intersection(pred))),
        "n_lines_pred": len(pred),
        "lines_pred": pred[:50],
    }


def main(resp_path, out_path):
    gold = {}
    with open(HERE / "items.jsonl", encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            gold[it["item"]] = it["gold"]
    rows = []
    with open(resp_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r["item"] not in gold:
                    sys.exit(f"unknown item id: {r['item']!r}")
                rows.append({"item": r["item"], **score_one(r.get("response"), gold[r["item"]])})
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    n = len(rows) or 1
    print(f"n={len(rows)} passed={sum(r['passed'] for r in rows) / n:.3f} "
          f"line_hit={sum(r['line_hit'] for r in rows) / n:.3f} "
          f"cat_line_hit={sum(r['cat_line_hit'] for r in rows) / n:.3f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python score.py responses.jsonl out.jsonl")
    main(sys.argv[1], sys.argv[2])
