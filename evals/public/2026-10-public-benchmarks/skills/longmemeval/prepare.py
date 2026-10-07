#!/usr/bin/env python3
"""Build items.jsonl + source.json for LongMemEval (oracle setting).

Prompt = LongMemEval's official reader prompt, produced by the authors' own
run_generation.prepare_prompt (official/run_generation.py) with the README-recommended
long-context settings: run_generation.sh <oracle> gpt-4o full-history-session 1000 json false con
-> retriever_type=orig-session, topk_context=1000, history_format=json, useronly=false, cot=true.
"""
import copy
import hashlib
import json
import os
import statistics
import urllib.request
from collections import Counter

import numpy as np
import tiktoken

import official_loader

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("TIKTOKEN_CACHE_DIR", os.path.join(HERE, "data", "tiktoken"))  # keep downloads in this folder
HF_REPO = "xiaowu0162/longmemeval"
HF_REVISION = "2ec2a557f339b6c0369619b1ed5793734cc87533"
HF_FILE = "longmemeval_oracle"
SHA256 = "821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c"
URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/{HF_REVISION}/{HF_FILE}"
DATA = os.path.join(HERE, "data", "longmemeval_oracle.json")
SEED, N = 20261006, 120

READER = {  # run_generation.sh: full-history-session -> orig-session; reading method "con" -> cot=true
    "retriever_type": "orig-session",
    "topk_context": 1000,
    "useronly": False,
    "history_format": "json",
    "cot": True,
    "merge_key_expansion_into_value": "none",
}
MAX_RETRIEVAL_LENGTH = 128000 - 800 - 1000  # official gpt-4o setting (o200k_base); never reached here, asserted below


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def fetch():
    if not os.path.exists(DATA):
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        urllib.request.urlretrieve(URL, DATA + ".part")
        os.replace(DATA + ".part", DATA)
    if sha256(DATA) != SHA256:
        raise SystemExit(f"{DATA}: SHA-256 mismatch, expected {SHA256}")
    return json.load(open(DATA, encoding="utf-8"))


def sample_ids(all_ids):
    ids = sorted(all_ids)
    perm = np.random.default_rng(SEED).permutation(len(ids))
    return [ids[i] for i in perm[:N]]


def build_prompt(prepare_prompt, entry, enc):
    prompt = prepare_prompt(copy.deepcopy(entry), tokenizer=enc, tokenizer_backend="openai",
                            max_retrieval_length=MAX_RETRIEVAL_LENGTH, **READER)
    for sess in entry["haystack_sessions"]:  # every evidence session present in full => no truncation, no leak
        clean = [{k: v for k, v in t.items() if k != "has_answer"} for t in sess]
        assert json.dumps(clean) in prompt, entry["question_id"]
    assert "has_answer" not in prompt, entry["question_id"]
    return prompt


def main():
    data = fetch()
    by_id = {e["question_id"]: e for e in data}
    assert len(by_id) == len(data) == 500
    chosen = sample_ids(by_id)
    prepare_prompt = official_loader.prepare_prompt()
    o200k, cl100k = tiktoken.get_encoding("o200k_base"), tiktoken.get_encoding("cl100k_base")

    rows, chars, tok_o, tok_c = [], [], [], []
    for qid in chosen:
        e = by_id[qid]
        prompt = build_prompt(prepare_prompt, e, o200k)
        gold = {
            "question_type": e["question_type"],
            "abstention": "_abs" in qid,  # official rule (evaluate_qa.py)
            "question": e["question"],
            "answer": e["answer"],  # original type kept (32 answers are ints), as the judge template formats it
            "question_date": e["question_date"],
        }
        rows.append({"item": qid, "prompt": prompt, "gold": gold})
        chars.append(len(prompt))
        tok_o.append(len(o200k.encode(prompt)))
        tok_c.append(len(cl100k.encode(prompt)))

    with open(os.path.join(HERE, "items.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def stats(xs):
        return {"mean": round(statistics.mean(xs), 1), "median": statistics.median(xs), "min": min(xs),
                "max": max(xs), "total": sum(xs)}

    source = {
        "benchmark": "LongMemEval (Wu et al., ICLR 2025), oracle setting: only the evidence sessions are in the history",
        "dataset": {
            "hf_repo": HF_REPO, "revision": HF_REVISION, "file": HF_FILE, "url": URL,
            "sha256": SHA256, "bytes": os.path.getsize(DATA), "licence": "MIT (dataset card and code repo)",
            "byte_identical_copy": {"hf_repo": "xiaowu0162/longmemeval-cleaned",
                                    "revision": "98d7416c24c778c2fee6e6f3006e7a073259d48f",
                                    "file": "longmemeval_oracle.json", "sha256": SHA256,
                                    "note": "the 2025-09 cleaning changed only the _s/_m haystacks; the oracle file is the same bytes"},
        },
        "official_code": {
            "repo": official_loader.REPO, "commit": official_loader.COMMIT, "licence": "MIT",
            "vendored": {name: {"repo_path": p, "git_blob_sha1": b,
                                "sha256": sha256(os.path.join(official_loader.OFFICIAL_DIR, name))}
                         for name, (p, b) in official_loader.PATHS.items()},
        },
        "sampling": {
            "eligible": "all 500 question_ids of the oracle file (6 question types, incl. the 30 *_abs abstention items)",
            "method": "ids sorted; numpy.random.default_rng(20261006).permutation(len(ids)); first 120, in that order",
            "seed": SEED, "n": len(rows), "ids": chosen,
            "composition": dict(Counter(r["gold"]["question_type"] for r in rows).most_common()),
            "abstention_items": sum(r["gold"]["abstention"] for r in rows),
        },
        "reader_prompt": {
            "function": "official/run_generation.py::prepare_prompt",
            "settings": READER, "max_retrieval_length": MAX_RETRIEVAL_LENGTH, "truncated_items": 0,
            "equivalent_command": "bash run_generation.sh longmemeval_oracle.json gpt-4o full-history-session 1000 json false con",
            "official_generation_params": {"temperature": 0, "max_tokens": 800, "messages": "one user message = prompt"},
        },
        "prompt_length": {
            "chars": stats(chars),
            "tokens_o200k_base": stats(tok_o),
            "tokens_cl100k_base": stats(tok_c),
            "note": "OpenAI tokenizers as a proxy; Claude's tokenizer is not available offline, use the runs' usage for cost",
        },
    }
    with open(os.path.join(HERE, "source.json"), "w", encoding="utf-8") as f:
        json.dump(source, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {len(rows)} items; prompt chars mean {source['prompt_length']['chars']['mean']}, "
          f"o200k tokens mean {source['prompt_length']['tokens_o200k_base']['mean']}")


if __name__ == "__main__":
    main()
