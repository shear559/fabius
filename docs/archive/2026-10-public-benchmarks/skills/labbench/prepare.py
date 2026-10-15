#!/usr/bin/env python3
"""Build items.jsonl + source.json for LAB-Bench ProtocolQA (all) + SeqQA (seeded fill to N).

Prompt = the official LAB-Bench zero-shot MCQ prompt (labbench/zero_shot.py, use_cot=True),
options = official randomize_choices (ideal + "Insufficient information..." + distractors)
shuffled under a fixed per-item seed. Usage: python prepare.py
"""

from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official  # noqa: E402

N = 220
SAMPLE_SEED = 20261006  # numpy default_rng permutation of sorted eligible ids
CHOICE_SEED = 20261006  # random.seed(f"{CHOICE_SEED}:{uuid}") before official randomize_choices
HF_REPO = "futurehouse/lab-bench"
HF_REVISION = "5c77cec648430f30611808808861eb86f81d5eaa"
GH_REPO = "https://github.com/Future-House/LAB-Bench"
GH_COMMIT = "998a8e0a40cf116c80e1b0e7a805ebb5fb9fa838"
CHEMBENCH_WHEEL_SHA256 = "bf8bb8ec91c12e8b10ba2db26b88d0228ac464d425ac6729a6e12b7dae2d71ee"
FILES = {  # HF config -> (file at HF_REVISION, sha256 == HF LFS oid)
    "ProtocolQA": ("ProtocolQA/train-00000-of-00001.parquet",
                   "d48d455638ff49b0c02ae96135703f239ea865a5936233045ee010a5d819239a"),
    "SeqQA": ("SeqQA/train-00000-of-00001.parquet",
              "5864776d3d85774f91d82432e30ac31e9222f1670621e8ea141414173c5e9b46"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(subset: str) -> tuple[list[dict], Path]:
    rel, want = FILES[subset]
    path = Path(hf_hub_download(HF_REPO, rel, repo_type="dataset", revision=HF_REVISION,
                                local_dir=HERE / "data" / "hf"))
    got = sha256(path)
    if got != want:
        raise SystemExit(f"{rel}: sha256 {got} != pinned {want}")
    return pq.read_table(path).to_pylist(), path


def seeded_take(ids: list[str], k: int) -> list[str]:
    ids = sorted(ids)
    perm = np.random.default_rng(SAMPLE_SEED).permutation(len(ids))
    return [ids[i] for i in perm[:k]]


def main() -> None:
    records: dict[str, dict] = {}
    eligible: dict[str, list[str]] = {}
    excluded: list[dict] = []
    files_meta = {}
    for subset in FILES:
        rows, path = load_rows(subset)
        files_meta[subset] = {"hf_path": FILES[subset][0], "sha256": FILES[subset][1], "rows": len(rows)}
        eligible[subset] = []
        for row in rows:
            uid = row["id"]
            item_id = f"{subset}/{uid}"
            ideal, distractors = row["ideal"], list(row["distractors"])
            if ideal in distractors:
                excluded.append({"item": item_id, "subtask": row["subtask"],
                                 "reason": "ideal answer text also appears as a distractor option "
                                           "(two identical options, only one scored correct)"})
                continue
            # ProtocolQA/task.py: input.question = self.protocol + input.question (no separator)
            question = (row["protocol"] + row["question"]) if subset == "ProtocolQA" else row["question"]
            choices, answer, unsure = official.shuffled_choices(uid, ideal, distractors, CHOICE_SEED)
            records[item_id] = {
                "item": item_id,
                "prompt": official.build_prompt(question, choices),
                "gold": {"answer": answer, "insufficient": unsure, "n_choices": len(choices),
                         "choices": choices, "ideal": ideal, "subset": subset, "subtask": row["subtask"]},
            }
            eligible[subset].append(item_id)

    proto = seeded_take(eligible["ProtocolQA"], len(eligible["ProtocolQA"]))  # all ProtocolQA
    seq = seeded_take(eligible["SeqQA"], max(0, N - len(proto)))  # fill to N
    chosen = (proto + seq)[:N]
    with open(HERE / "items.jsonl", "w") as f:
        for item_id in chosen:
            # ASCII-escaped: one ProtocolQA text holds U+2028, which str.splitlines() would split on
            f.write(json.dumps(records[item_id]) + "\n")

    prompts = [records[i]["prompt"] for i in chosen]
    source = {
        "benchmark": "LAB-Bench (Laurent et al. 2024, arXiv:2407.10362), subsets ProtocolQA + SeqQA, multiple choice",
        "dataset": {"hf_repo": HF_REPO, "hf_revision": HF_REVISION, "split": "train (= public MC release)",
                    "files": files_meta, "licence": "CC-BY-SA-4.0"},
        "official_harness": {"repo": GH_REPO, "commit": GH_COMMIT,
                             "files": "labbench/utils.py, labbench/zero_shot.py, labbench/evaluator.py, "
                                      "ProtocolQA/task.py, SeqQA/task.py",
                             "parser": "chembench==0.3.0 (pinned in LAB-Bench uv.lock)",
                             "chembench_wheel_sha256": CHEMBENCH_WHEEL_SHA256,
                             "github_jsonl_identical_to_hf": True},
        "eligible": {k: len(v) for k, v in eligible.items()},
        "excluded": excluded,
        "sampling": (f"ProtocolQA: all eligible ids. SeqQA: sorted eligible ids, "
                     f"numpy.random.default_rng({SAMPLE_SEED}).permutation, first N-{len(proto)}. "
                     f"Each list keeps its permuted order; ProtocolQA first. N={N}."),
        "choice_shuffle": (f"official randomize_choices after random.seed('{CHOICE_SEED}:<uuid>') per item "
                           f"(Python {sys.version.split()[0]})"),
        "n_items": len(chosen),
        "per_subset": dict(collections.Counter(records[i]["gold"]["subset"] for i in chosen)),
        "per_subtask": dict(sorted(collections.Counter(records[i]["gold"]["subtask"] for i in chosen).items())),
        "n_choices": dict(sorted(collections.Counter(records[i]["gold"]["n_choices"] for i in chosen).items())),
        "answer_letter": dict(sorted(collections.Counter(records[i]["gold"]["answer"] for i in chosen).items())),
        "insufficient_letter": dict(sorted(collections.Counter(records[i]["gold"]["insufficient"] for i in chosen).items())),
        "avg_prompt_chars": round(sum(map(len, prompts)) / len(prompts)),
        "max_prompt_chars": max(map(len, prompts)),
        "items_jsonl_sha256": sha256(HERE / "items.jsonl"),
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(chosen)} items ({source['per_subset']}), avg prompt {source['avg_prompt_chars']} chars, "
          f"excluded {len(excluded)}")


if __name__ == "__main__":
    main()
