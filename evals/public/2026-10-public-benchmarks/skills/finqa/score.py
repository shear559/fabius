#!/usr/bin/env python3
"""Score free-text answers to FinQA items.  Usage: python score.py responses.jsonl out.jsonl

FinQA's official metric executes a predicted DSL program, so free text needs a defined rule:
1. Answer text: rest of the line after the LAST line-initial "Answer:" (or "Final answer:" anywhere,
   or an "Answer" heading line); the next non-empty line if that is blank. Only without one: the last
   mid-line "answer:", then the last "answer is ...", then the last \\boxed{...}. No marker -> fail.
2. yes/no (true/false) if the answer text starts with it. Otherwise the first number in it, read
   after the last "=" or "≈" (parenthesised "(= ...)" notes are dropped first). Markdown, LaTeX, $,
   thousands commas and % are ignored; a - (any dash) touching the number or its currency sign, or
   accounting parentheses, make it negative ("- 5" is a bullet); a scale word after the number
   (thousand/k, million/m/mm/mn, billion/b/bn, trillion/t/tn) is tried both ignored and applied.
3. Gold is qa.exe_ans. A number v passes if any of v, v/100, v*100 is within
   max(1% of |gold|, 0.01) of gold (FinQA stores percentages as ratios); yes/no must equal it.
"""
import json
import math
import re
import sys
from pathlib import Path

REL_TOL, ABS_TOL = 0.01, 0.01
HERE = Path(__file__).resolve().parent

_TRANS = str.maketrans({"\u2212": "-", "\u2012": "-", "\u2013": "-", "\ufe63": "-", "\uff0d": "-",
                        "\u00a0": " ", "\u2009": " ", "\u202f": " ", "\uff1a": ":"})
_NOTE = r"(?:[ \t]*\([^)\n]{0,40}\))?[ \t]*"
MARKERS = (  # tried in order; the LAST hit of the first family that has any hit wins
    re.compile(rf"(?:^[ \t>#+•-]*(?:final\s+)?answer|\bfinal\s+answer)\b{_NOTE}(?:[:=]|$)", re.I | re.M),
    re.compile(rf"\banswer\b{_NOTE}[:=]", re.I),
    re.compile(r"\b(?:final\s+)?answer\s+(?:is|would\s+be)\b[ \t]*:?", re.I),
)
BOXED = re.compile(r"\\boxed\s*\{((?:[^{}]|\{[^{}]*\})*)\}")
YESNO = re.compile(r"^[\s\"'(\[]*(yes|no|true|false)\b", re.I)
_SC = r"trillions?|billions?|millions?|thousands?|tn|bn|mn|mm|k|m|b|t"
NUM = re.compile(rf"""(?<![\w.])
    (?P<open>\()?[ \t]*(?:(?P<s1>-)(?=[$€£¥.\d]|us))?(?:us\$|usd|[$€£¥])?[ \t]*(?P<s2>-)?
    (?P<num>\d{{1,3}}(?:,\d{{3}})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)(?:e(?P<exp>[-+]?\d+))?
    [ \t]*(?:%|percent(?:age)?\b)?
    (?:[ \t]*(?P<scale>{_SC})(?![a-z]))?
    [ \t]*(?P<close>\))?
    (?:[ \t]*(?P<scale2>{_SC})(?![a-z]))?""", re.I | re.X)
SCALE = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "mm": 1e6, "mn": 1e6,
         "billion": 1e9, "b": 1e9, "bn": 1e9, "trillion": 1e12, "t": 1e12, "tn": 1e12}


def clean(s):
    s = s.translate(_TRANS)
    s = re.sub(r"\\(?:boxed|text|textbf|mathrm|mathbf)\s*\{", "", s)
    s = s.replace("\\%", "%").replace("\\$", "$").replace("{,}", ",").replace("\\,", "")
    return re.sub(r"\\[()\[\]]|[*_`{}]", "", s)


def _after(text, end):
    """Rest of the line after a marker; the next non-empty line if that is blank."""
    rest = text[end:].split("\n")
    for line in rest[:4]:
        if line.strip():
            return line.strip()
    return ""


def extract(response):
    """Return the answer text chosen by rule 1, or None."""
    text = clean(response or "")
    for rx in MARKERS:
        hits = list(rx.finditer(text))
        if hits:
            return _after(text, hits[-1].end())
    boxed = BOXED.findall((response or "").translate(_TRANS))
    return clean(boxed[-1]).strip() if boxed else None


def parse(ans):
    """('yesno', 'yes'|'no') or ('number', value, scale) or None."""
    if ans is None:
        return None
    m = YESNO.match(ans)
    if m:
        return ("yesno", "yes" if m.group(1).lower() in ("yes", "true") else "no")
    s = re.sub(r"\([^()]*[=≈][^()]*\)", " ", ans)
    s = re.split(r"[=≈]", s)[-1]
    m = NUM.search(s)
    if not m:
        return None
    v = float(m.group("num").replace(",", "") + ("e" + m.group("exp") if m.group("exp") else ""))
    if not math.isfinite(v):
        return None
    if m.group("s1") or m.group("s2") or (m.group("open") and m.group("close")):
        v = -v
    scale = m.group("scale") or m.group("scale2")
    return ("number", v, SCALE[scale.lower().rstrip("s")] if scale else None)


def match(parsed, gold, rel=REL_TOL, absol=ABS_TOL):
    """Return the matching form name, or None."""
    if parsed is None:
        return None
    if isinstance(gold, str):
        return "yes/no" if parsed[0] == "yesno" and parsed[1] == gold.strip().lower() else None
    if parsed[0] != "number":
        return None
    _, v, scale = parsed
    tol = max(rel * abs(gold), absol) + 1e-9 * max(1.0, abs(gold))
    for name, base in [("v", v)] + ([("v*scale", v * scale)] if scale else []):
        for suffix, cand in (("", base), ("/100", base / 100), ("*100", base * 100)):
            if abs(cand - gold) <= tol:
                return name + suffix
    return None


def score_one(response, gold):
    ans = extract(response)
    parsed = parse(ans)
    form = match(parsed, gold)
    flipped = None if parsed is None or parsed[0] != "number" else ("number", -parsed[1], parsed[2])
    return {
        "passed": int(form is not None),
        "format_ok": int(parsed is not None),
        "extracted": None if ans is None else ans[:200],
        "pred": None if parsed is None else parsed[1],
        "gold": gold,
        "form": form,
        "passed_rel1pct": int(match(parsed, gold, absol=0.0) is not None),
        "sign_flip_match": int(form is None and match(flipped, gold) is not None),
    }


def load_gold(path=HERE / "items.jsonl"):
    with open(path) as f:
        return {it["item"]: it["gold"]["exe_ans"] for it in map(json.loads, f)}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python score.py responses.jsonl out.jsonl")
    gold = load_gold()
    rows, seen = [], set()
    with open(argv[1]) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("item") not in gold:
                raise SystemExit(f"{argv[1]}:{n}: unknown item {rec.get('item')!r}")
            resp = rec.get("response")
            rows.append({"item": rec["item"], **score_one(resp if isinstance(resp, str) else "", gold[rec["item"]])})
            seen.add(rec["item"])
    with open(argv[2], "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    n = len(rows)
    summary = {"n_scored": n, "passed": sum(r["passed"] for r in rows),
               "accuracy": round(sum(r["passed"] for r in rows) / n, 4) if n else None,
               "format_ok": sum(r["format_ok"] for r in rows), "items_without_response": len(gold) - len(seen)}
    print(json.dumps(summary), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
