#!/usr/bin/env python3
"""Self-check of the LongMemEval harness -> selfcheck.json (+ selfcheck/ files). Calls no model.

Offline legs: (1) official/ is the pinned commit; (2) items.jsonl prompts and score.py judge prompts are
byte-identical to the official functions run as ordinary module imports (independent of
official_loader's AST path); (3) verdict -> passed follows evaluate_qa.py and joins by item id;
(4) gold answers pass and clearly wrong answers fail the deterministic secondary string_match.
LLM-judge leg: selfcheck/{gold,wrong}.judge_prompts.jsonl are ready for the study's judge; save its
replies as selfcheck/{gold,wrong}.judgements.jsonl ({"item","judgement"}) and re-run this script.
"""
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import types

import numpy as np
import tiktoken

import official_loader
import prepare
from score import normalize, read_jsonl, write_jsonl
from score_from_judgements import official_label, score as score_judgements, strict_label, summary

HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "selfcheck")
PY = sys.executable
VERDICTS = [  # (judge reply, official label, strict label)
    ("yes", 1, 1), ("Yes", 1, 1), ("Yes.", 1, 1), ("YES", 1, 1), (" yes\n", 1, 1), ("**Yes**", 1, 1),
    ("no", 0, 0), ("No.", 0, 0), ("NO", 0, 0), ("No, the response is incorrect.", 0, 0), ("", 0, None),
    ("No. It never says yes.", 1, 0),  # official substring rule's false positive -> flagged verdict_ambiguous
]


def import_official(filename):
    """Import a vendored official module the ordinary way, with inert stubs for its API-client imports."""
    openai = types.ModuleType("openai")
    openai.RateLimitError = openai.APIError = type("StubError", (Exception,), {})
    openai.OpenAI = object
    backoff = types.ModuleType("backoff")
    backoff.expo = backoff.constant = None
    backoff.on_exception = lambda *a, **k: (lambda f: f)
    tqdm = types.ModuleType("tqdm")
    tqdm.tqdm = lambda x, **k: x
    transformers = types.ModuleType("transformers")
    transformers.AutoTokenizer = None
    stubs = {"openai": openai, "backoff": backoff, "tqdm": tqdm, "transformers": transformers}
    saved = {k: sys.modules.get(k) for k in stubs}
    sys.modules.update(stubs)
    try:
        spec = importlib.util.spec_from_file_location("official_" + filename[:-3],
                                                      os.path.join(official_loader.OFFICIAL_DIR, filename))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return mod


def numbers(text):
    return [int(x) for x in re.findall(r"\d+", normalize(text))]


def clearly_different(candidate, gold):
    a, b = normalize(candidate), normalize(gold)
    if not a or f" {a} " in f" {b} " or f" {b} " in f" {a} ":
        return False
    return not any(abs(x - y) <= 1 for x in numbers(a) for y in numbers(b))  # temporal judge forgives off-by-one


def wrong_answers(items, data):
    """Another question's gold answer of the same type (abstention items get a confident non-abstention answer)."""
    rng = np.random.default_rng(0)
    pool = {}
    for e in sorted(data, key=lambda e: e["question_id"]):
        if "_abs" not in e["question_id"]:
            pool.setdefault(e["question_type"], []).append(e)
    out = {}
    for r in items:
        g = r["gold"]
        cands = [e for e in pool[g["question_type"]] if e["question_id"] != r["item"]]
        out[r["item"]] = next(str(cands[j]["answer"]) for j in rng.permutation(len(cands))
                              if clearly_different(str(cands[j]["answer"]), str(g["answer"])))
    return out


def run(*args):
    return subprocess.run([PY, *args], cwd=HERE, capture_output=True, text=True)


def judged(name, expect):
    """Fold in the LLM-judge calibration replies if the study has produced them."""
    jp, jj = os.path.join(SC, f"{name}.judge_prompts.jsonl"), os.path.join(SC, f"{name}.judgements.jsonl")
    if not os.path.exists(jj):
        return {"status": "pending: needs the study's judge model", "judge_prompts": os.path.relpath(jp, HERE),
                "save_replies_to": os.path.relpath(jj, HERE), "expected": expect}
    rows = score_judgements(read_jsonl(jp), read_jsonl(jj))
    return {"status": "done", "expected": expect, **summary(rows),
            "items_not_as_expected": [r["item"] for r in rows if r["passed"] != (name == "gold")]}


def main():
    os.makedirs(SC, exist_ok=True)
    official_loader.verify()
    rg, ev = import_official("run_generation.py"), import_official("evaluate_qa.py")
    data = prepare.fetch()
    by_id = {e["question_id"]: e for e in data}
    items = read_jsonl(os.path.join(HERE, "items.jsonl"))
    enc = tiktoken.get_encoding("o200k_base")
    rep = {"official_code_pinned": {"repo": official_loader.REPO, "commit": official_loader.COMMIT,
                                    "git_blobs_match": True, "files": sorted(official_loader.PATHS)}}

    # (2a) sampling and reader prompts
    same = sum(rg.prepare_prompt(copy.deepcopy(by_id[r["item"]]), tokenizer=enc, tokenizer_backend="openai",
                                 max_retrieval_length=prepare.MAX_RETRIEVAL_LENGTH, **prepare.READER) == r["prompt"]
               for r in items)
    chrono = tail = 0
    for e in data:  # all 500: builds, no truncation, no has_answer leak (asserted inside build_prompt)
        p = prepare.build_prompt(rg.prepare_prompt, e, enc)
        dates = re.findall(r"\n### Session \d+:\nSession Date: (.*)\n", p)
        chrono += dates == sorted(e["haystack_dates"])
        tail += p.endswith(f"\n\nCurrent Date: {e['question_date']}\nQuestion: {e['question']}\nAnswer (step by step):")
    rep["reader_prompts"] = {
        "sample_reproduced": prepare.sample_ids(by_id) == [r["item"] for r in items],
        "items_byte_identical_to_official_prepare_prompt": f"{same}/{len(items)}",
        "all_500_built_untruncated_without_has_answer": True,
        "all_500_sessions_in_date_order": f"{chrono}/500",
        "all_500_end_with_date_question_answer_cue": f"{tail}/500",
    }

    # (2b) judge prompts from score.py vs the official function, gold / wrong / mixed response sets
    wrong = wrong_answers(items, data)
    sets = {
        "gold": {r["item"]: str(r["gold"]["answer"]) for r in items},
        "wrong": wrong,
        "mixed": {r["item"]: (str(r["gold"]["answer"]) if i % 2 == 0 else wrong[r["item"]]) for i, r in enumerate(items)},
    }
    jrows = {}
    for name, resp in sets.items():
        write_jsonl(os.path.join(SC, f"{name}.responses.jsonl"), [{"item": k, "response": v} for k, v in resp.items()])
        res = run("score.py", f"selfcheck/{name}.responses.jsonl", f"selfcheck/{name}.out.jsonl",
                  "--judge-prompts", f"selfcheck/{name}.judge_prompts.jsonl")
        assert res.returncode == 0, res.stderr
        jrows[name] = read_jsonl(os.path.join(SC, f"{name}.judge_prompts.jsonl"))
    gold_by = {r["item"]: r["gold"] for r in items}
    ident = sum(j["judge_prompt"] == ev.get_anscheck_prompt(gold_by[j["item"]]["question_type"],
                                                            gold_by[j["item"]]["question"], gold_by[j["item"]]["answer"],
                                                            sets[name][j["item"]].strip(), abstention="_abs" in j["item"])
                for name in sets for j in jrows[name])
    abs_tpl = sum(j["judge_prompt"].startswith("I will give you an unanswerable question") for j in jrows["gold"])
    rep["judge_prompts"] = {
        "byte_identical_to_official_get_anscheck_prompt": f"{ident}/{sum(map(len, jrows.values()))}",
        "abstention_template_used": f"{abs_tpl} (= *_abs items in sample: {sum('_abs' in r['item'] for r in items)})",
    }

    # (3) verdict -> passed, join by item id (verdicts written in reverse order)
    vec_ok = all(official_label(t) == o and strict_label(t) == s for t, o, s in VERDICTS)
    mixed_j = [{"item": r["item"], "judgement": "Yes" if i % 2 == 0 else "No"} for i, r in enumerate(items)][::-1]
    write_jsonl(os.path.join(SC, "mixed.judgements.jsonl"), mixed_j)
    res = run("score_from_judgements.py", "selfcheck/mixed.judge_prompts.jsonl", "selfcheck/mixed.judgements.jsonl",
              "selfcheck/mixed.final.jsonl")
    final = {r["item"]: r["passed"] for r in read_jsonl(os.path.join(SC, "mixed.final.jsonl"))}
    write_jsonl(os.path.join(SC, "bad.responses.jsonl"), [{"item": "not-an-item", "response": "x"}])
    write_jsonl(os.path.join(SC, "bad.judgements.jsonl"), mixed_j[1:])
    rep["verdict_to_passed"] = {
        "rule": "passed = int('yes' in judgement.strip().lower())  (evaluate_qa.py lines 112-113)",
        "verdict_vectors": {"ok": vec_ok, "cases": len(VERDICTS),
                            "note": "incl. 'No. It never says yes.' -> 1 by the official rule, flagged verdict_ambiguous"},
        "mixed_set_exact": res.returncode == 0 and all(final[r["item"]] == int(i % 2 == 0) for i, r in enumerate(items)),
        "unknown_item_rejected": run("score.py", "selfcheck/bad.responses.jsonl", "selfcheck/bad.out.jsonl").returncode != 0,
        "missing_judgement_rejected": run("score_from_judgements.py", "selfcheck/mixed.judge_prompts.jsonl",
                                          "selfcheck/bad.judgements.jsonl", "selfcheck/bad.final.jsonl").returncode != 0,
    }

    # (4) deterministic secondary string_match on gold vs clearly wrong answers
    def sm(name):
        vals = [j["string_match"] for j in jrows[name] if j["string_match"] is not None]
        return {"pass_rate": round(sum(vals) / len(vals), 4), "n": len(vals),
                "passed_items": [j["item"] for j in jrows[name] if j["string_match"] == 1]}
    g, w = sm("gold"), sm("wrong")
    rep["string_match_secondary"] = {
        "gold": {k: v for k, v in g.items() if k != "passed_items"},
        "gold_failures": [j["item"] for j in jrows["gold"] if j["string_match"] == 0],
        "wrong": {k: v for k, v in w.items() if k != "passed_items"}, "wrong_passes": w["passed_items"],
        "not_applicable": "abstention and single-session-preference items (judge-only)",
        "wrong_set": "per item, another question's gold answer of the same type (abstention items: a confident answer), "
                     "chosen with numpy default_rng(0), never overlapping the gold and no number within +-1 of it",
    }

    # (5) LLM-judge calibration leg
    rep["llm_judge_leg"] = {
        "gold": judged("gold", "nearly all passed"),
        "wrong": judged("wrong", "nearly all failed"),
    }
    keep = {f"{n}.{k}.jsonl" for n in ("gold", "wrong") for k in ("responses", "judge_prompts", "judgements")}
    for f in set(os.listdir(SC)) - keep:  # by-products of the offline legs
        os.remove(os.path.join(SC, f))
    with open(os.path.join(HERE, "selfcheck.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(rep, indent=1)[:4000])


if __name__ == "__main__":
    main()
