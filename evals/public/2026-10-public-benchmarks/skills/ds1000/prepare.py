"""Build items.jsonl and source.json for DS-1000 (skill under test: fabius-doctrina, ML / data-engineering code).

python prepare.py
Downloads the pinned HF file (SHA-256 verified), keeps every non-Pytorch/non-Tensorflow problem,
samples N with the study seed and writes one item per line: {"item", "prompt", "gold"}.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np

from score import image_tag

HERE = Path(__file__).resolve().parent
HF_REPO, HF_REVISION, HF_FILE = "xlangai/DS-1000", "4416080ac5cb80bdf7576aefb8f9a0b4d5426a44", "test.jsonl"
HF_SHA256 = "26a492838b05f9d030b2f08a5715c6bafecafb601c157da912bf417fd8b0d363"
GIT_REPO, GIT_COMMIT = "https://github.com/xlang-ai/DS-1000", "b39aab71da6d23ef8d3cac59a7c5f834516ab334"
GIT_DATA_SHA256 = "e8c6daa9d7223976bce0296644f3933f78d7f47830669ff05cd61da62c6ba9b3"  # data/ds1000.jsonl.gz, same 1000 records
EXCLUDED_LIBRARIES = ("Pytorch", "Tensorflow")
SEED, N = 20261006, 200

# Official chat-model instruction (run_openai.py @ GIT_COMMIT: "Only provide the code completion needed. Don't repeat
# the context code." / "Write a short code following the given format and indentation."), plus the one-code-block format.
INSTRUCTION = (
    "Only provide the code completion needed. Don't repeat the context code. "
    "Follow the given format and indentation, and put the completion in a single ```python code block."
)


def build_prompt(official_prompt: str) -> str:
    return official_prompt + "\n\n" + INSTRUCTION


def solution_indent(official_prompt: str) -> str:
    """Function-body problems end with an indented '### BEGIN SOLUTION': the solution continues at that indent."""
    last = official_prompt.rstrip().split("\n")[-1]
    return last[: len(last) - len(last.lstrip())] if last.strip() == "### BEGIN SOLUTION" else ""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch() -> Path:
    path = HERE / ".cache" / f"hf-{HF_REVISION[:12]}-{HF_FILE}"
    if not path.exists() or sha256(path) != HF_SHA256:
        path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/datasets/{HF_REPO}/resolve/{HF_REVISION}/{HF_FILE}"
        path.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    if sha256(path) != HF_SHA256:
        raise SystemExit(f"SHA-256 mismatch for {path}")
    return path


def main() -> None:
    data_path = fetch()
    problems = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]
    assert len(problems) == 1000
    by_id = {f"ds1000-{p['metadata']['problem_id']:04d}": p for p in problems}
    eligible = sorted(i for i, p in by_id.items() if p["metadata"]["library"] not in EXCLUDED_LIBRARIES)
    order = np.random.default_rng(SEED).permutation(len(eligible))
    sample = [eligible[k] for k in order[:N]]

    with open(HERE / "items.jsonl", "w") as f:
        for item_id in sample:
            p, m = by_id[item_id], by_id[item_id]["metadata"]
            gold = {
                "problem_id": m["problem_id"],
                "library": m["library"],
                "perturbation_type": m["perturbation_type"],
                "perturbation_origin_id": m["perturbation_origin_id"],
                "test_case_cnt": m["test_case_cnt"],
                "solution_indent": solution_indent(p["prompt"]),
                "code_context": p["code_context"],
                "reference_code": p["reference_code"],
            }
            f.write(json.dumps({"item": item_id, "prompt": build_prompt(p["prompt"]), "gold": gold}) + "\n")

    libs = {}
    for item_id in sample:
        lib = by_id[item_id]["metadata"]["library"]
        libs[lib] = libs.get(lib, 0) + 1
    docker = HERE / "docker"
    source = {
        "benchmark": "DS-1000 (Lai et al., 2022), simplified format (04/2024)",
        "dataset": {
            "hf_repo": HF_REPO, "hf_revision": HF_REVISION, "file": HF_FILE, "sha256": HF_SHA256,
            "url": f"https://huggingface.co/datasets/{HF_REPO}/blob/{HF_REVISION}/{HF_FILE}", "license": "CC-BY-SA-4.0",
        },
        "official_repo": {
            "url": GIT_REPO, "commit": GIT_COMMIT, "license": "CC-BY-SA-4.0",
            "data_file": "data/ds1000.jsonl.gz", "data_sha256": GIT_DATA_SHA256,
            "data_note": "all 1000 records identical to the HF file above",
            "execution.py": {"sha256": sha256(docker / "execution.py"), "use": "vendored verbatim, runs every test"},
            "test_ds1000.py": {"sha256": "32ebe279eefa2d3cb1d633a82b43954ea813567e2fca28a9f6d777ce7f04d50c",
                               "use": "test-program assembly, postprocess(), timeout=120 reproduced in score.py"},
            "run_openai.py": {"sha256": "a30c13ac66397eec077dd3996c3cc08f50a19a24b39d3e4fa0ce535b2a63891f",
                              "use": "wording of the chat instruction appended to each prompt"},
            "environment.yml": {"sha256": "61575788abe7cd77d26921ba2043efb652d2e1a9fe569378e9405a8469bb76aa",
                                "use": "library pins of the execution image (docker/requirements.in)"},
        },
        "execution_image": {
            "tag": image_tag(), "build_context": "docker/ (tag = hash of its files; score.py builds it on first use)",
            "base": "python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d",
            "lock_file": "docker/requirements.lock.txt", "lock_sha256": sha256(docker / "requirements.lock.txt"),
            "lock_rule": "official pins + every transitive dependency resolved with uv --exclude-newer 2024-04-27",
            "offline_data": "seaborn-data@71e2436a (tips, planets, penguins, exercise) + sklearn California housing",
        },
        "sampling": {
            "eligible": "metadata.library not in ['Pytorch', 'Tensorflow']", "n_eligible": len(eligible),
            "id_format": "ds1000-{problem_id:04d}", "seed": SEED, "N": len(sample),
            "method": "sorted eligible ids -> numpy.random.default_rng(seed).permutation -> first N",
            "numpy_version": np.__version__, "libraries_in_sample": dict(sorted(libs.items())),
        },
        "prompt_instruction": INSTRUCTION,
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    print(f"{len(sample)} items from {len(eligible)} eligible -> items.jsonl; libraries: {libs}")


if __name__ == "__main__":
    main()
