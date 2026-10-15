"""Build items.jsonl + source.json for BFCL (non-live AST: simple_python, multiple, parallel,
parallel_multiple, irrelevance).  usage: python prepare.py [--offline]

Sampling, per category (stratified, 200 / 5 = 40 each): sorted(ids) -> numpy.random.default_rng(20261006)
.permutation (a fresh generator per category) -> first 40.  Prompts are built inside the scoring container
by the official bfcl-eval functions (see bfcl_core.py: cmd_prompts).
"""
import base64
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

from score import IMAGE, run_core

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
WHEEL = VENDOR / "bfcl_eval-2026.3.23-py3-none-any.whl"
WHEEL_SHA256 = "3bb6dfa5f0c68ad403c9ec50b00db2bb3b4cc9b38ab1ff33f48fe30d853d3a0a"  # PyPI bfcl-eval 2026.3.23
PKG_ROOT = VENDOR / "bfcl_eval_2026.3.23"
GIT_REPO, GIT_COMMIT = "ShishirPatil/gorilla", "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"  # release commit
GIT_SUBDIR = "berkeley-function-call-leaderboard"
CATEGORIES = ["simple_python", "multiple", "parallel", "parallel_multiple", "irrelevance"]
N, SEED = 200, 20261006
DATA_FILES = [f"bfcl_eval/data/BFCL_v4_{c}.json" for c in CATEGORIES] + [
    f"bfcl_eval/data/possible_answer/BFCL_v4_{c}.json" for c in CATEGORIES if c != "irrelevance"]
CODE_FILES = [
    "bfcl_eval/eval_checker/ast_eval/ast_checker.py", "bfcl_eval/eval_checker/eval_runner.py",
    "bfcl_eval/model_handler/utils.py", "bfcl_eval/utils.py", "bfcl_eval/constants/default_prompts.py",
    "bfcl_eval/constants/model_config.py", "bfcl_eval/model_handler/api_inference/claude.py"]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify_vendor():
    """The vendored package must be the pinned PyPI wheel, unmodified (checked against its RECORD)."""
    wheel_bytes = WHEEL.read_bytes()
    assert sha256(wheel_bytes) == WHEEL_SHA256, "wheel hash mismatch"
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as zf:
        record_name = next(n for n in zf.namelist() if n.endswith(".dist-info/RECORD"))
        record = list(csv.reader(io.StringIO(zf.read(record_name).decode())))
    checked = 0
    for path, digest, _size in record:
        if not digest:
            continue
        algo, expected = digest.split("=", 1)
        got = base64.urlsafe_b64encode(hashlib.new(algo, (PKG_ROOT / path).read_bytes()).digest()).rstrip(b"=")
        assert got.decode() == expected, f"vendored file differs from wheel: {path}"
        checked += 1
    return checked


def verify_git(paths):
    """Byte-compare vendored files with the gorilla repo at the release commit."""
    for path in paths:
        url = f"https://raw.githubusercontent.com/{GIT_REPO}/{GIT_COMMIT}/{GIT_SUBDIR}/{path}"
        with urllib.request.urlopen(url, timeout=60) as resp:
            assert resp.read() == (PKG_ROOT / path).read_bytes(), f"differs from git: {path}"
    return paths


def sample():
    chosen, eligible = [], {}
    per_cat = N // len(CATEGORIES)
    for cat in CATEGORIES:
        with open(PKG_ROOT / f"bfcl_eval/data/BFCL_v4_{cat}.json", encoding="utf-8") as fh:
            ids = sorted(json.loads(line)["id"] for line in fh if line.strip())
        eligible[cat] = len(ids)
        perm = np.random.default_rng(SEED).permutation(len(ids))
        chosen += [ids[i] for i in perm[:per_cat]]
    return chosen, eligible


def main(argv):
    record_files = verify_vendor()
    git_checked = [] if "--offline" in argv else verify_git(DATA_FILES + CODE_FILES)
    ids, eligible = sample()
    rows = run_core("prompts", json.dumps({"ids": ids}))
    assert [r["item"] for r in rows] == ids
    with open(HERE / "items.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            gold = {"category": r["category"], "function": r["function"], "ground_truth": r["ground_truth"]}
            fh.write(json.dumps({"item": r["item"], "prompt": r["prompt"], "gold": gold}, ensure_ascii=False) + "\n")
    env = run_core("env", "")[0]
    source = {
        "benchmark": "Berkeley Function Calling Leaderboard (BFCL v4), non-live AST categories",
        "categories": CATEGORIES,
        "upstream": {"repo": f"https://github.com/{GIT_REPO}", "subdir": GIT_SUBDIR, "commit": GIT_COMMIT,
                     "pypi": "bfcl-eval==2026.3.23", "wheel": WHEEL.name, "wheel_sha256": WHEEL_SHA256,
                     "wheel_files_verified_against_RECORD": record_files,
                     "files_byte_identical_to_git_commit": git_checked or "not checked (--offline)"},
        "licence": "Apache-2.0 (gorilla repo licence; bfcl_eval/data/README.md front matter: license: apache-2.0)",
        "data_files_sha256": {p: sha256((PKG_ROOT / p).read_bytes()) for p in DATA_FILES},
        "code_files_sha256": {p: sha256((PKG_ROOT / p).read_bytes()) for p in CODE_FILES},
        "sampling": {"N": len(ids), "per_category": N // len(CATEGORIES), "seed": SEED, "eligible": eligible,
                     "method": "per category: sorted(ids) (string order) -> numpy.random.default_rng(seed)"
                               ".permutation(len) with a fresh generator per category -> first 40",
                     "numpy": np.__version__},
        "container": {"image": IMAGE, "tag_when_pinned": "python:3.11-slim", **env},
        "deps_lock_sha256": sha256((VENDOR / "requirements-container.lock").read_bytes()),
        "items_jsonl_sha256": sha256((HERE / "items.jsonl").read_bytes()),
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(ids)} items; per category {N // len(CATEGORIES)}; RECORD-verified {record_files} files; "
          f"git-verified {len(git_checked)} files")


if __name__ == "__main__":
    main(sys.argv[1:])
