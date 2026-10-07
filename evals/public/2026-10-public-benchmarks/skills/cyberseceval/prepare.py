#!/usr/bin/env python3
"""Build items.jsonl + source.json for CyberSecEval "instruct" (insecure code), Python subset.

Run with the study venv (needs numpy):  python prepare.py
Idempotent. It also (re)creates, only when missing:
  vendor/PurpleLlama  - sparse clone of meta-llama/PurpleLlama at COMMIT (dataset + ICD + official runner)
  .venv-icd           - scorer venv with the official CybersecurityBenchmarks/requirements.txt (semgrep==1.51.0)
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_URL = "https://github.com/meta-llama/PurpleLlama.git"
COMMIT = "172c1074069eb88ec834124272c1b1c4f8893445"
PL = HERE / "vendor" / "PurpleLlama"
DATA_REL = "CybersecurityBenchmarks/datasets/instruct/instruct-v2.json"
DATA_SHA256 = "df19f7c51911d46d0ae5c069b7093728db8e682890a44317a211ac61cb02c181"
LANGUAGE = "python"
N = 200
SEED = 20261006
SPARSE = [
    "/CodeShield/",
    "/CybersecurityBenchmarks/benchmark/",
    "/CybersecurityBenchmarks/datasets/instruct/",
    "/CybersecurityBenchmarks/datasets/canary_exploit/",  # imported by the official run.py
    "/CybersecurityBenchmarks/datasets/__init__.py",
    "/CybersecurityBenchmarks/datasets/third-party.txt",
    "/CybersecurityBenchmarks/__init__.py",
    "/CybersecurityBenchmarks/README.md",
    "/CybersecurityBenchmarks/LICENSE",
    "/CybersecurityBenchmarks/requirements.txt",
    "/LICENSE",
    "/README.md",
]
VENV = HERE / ".venv-icd"


def sh(*cmd: str, cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_vendor() -> None:
    if not (PL / ".git").exists():
        PL.parent.mkdir(parents=True, exist_ok=True)
        sh("git", "clone", "--filter=blob:none", "--no-checkout", "--sparse", REPO_URL, str(PL))
        sh("git", "sparse-checkout", "set", "--no-cone", *SPARSE, cwd=PL)
        sh("git", "checkout", "--detach", COMMIT, cwd=PL)
    head = sh("git", "rev-parse", "HEAD", cwd=PL)
    if head != COMMIT:
        sys.exit(f"vendor/PurpleLlama is at {head}, expected {COMMIT}")


def ensure_scorer_venv() -> str:
    py = VENV / "bin" / "python"
    if not py.exists():
        uv = shutil.which("uv") or sys.exit("uv not found on PATH")
        sh(uv, "venv", "--python", "3.11", str(VENV))
        sh(uv, "pip", "install", "--python", str(py), "-r",
           str(PL / "CybersecurityBenchmarks" / "requirements.txt"))
    core = next(VENV.glob("lib/python*/site-packages/semgrep/bin/semgrep-core"))
    out = subprocess.run([str(core), "-version"], check=True, capture_output=True, text=True)
    return (out.stdout + out.stderr).strip()


def main() -> None:
    ensure_vendor()
    semgrep_version = ensure_scorer_venv()
    if "1.51.0" not in semgrep_version:
        sys.exit(f"expected semgrep 1.51.0 (official requirements pin), got: {semgrep_version}")

    data_path = PL / DATA_REL
    got = sha256(data_path)
    if got != DATA_SHA256:
        sys.exit(f"{DATA_REL} sha256 {got} != pinned {DATA_SHA256}")
    rows = json.loads(data_path.read_text())

    eligible = {}
    for r in rows:
        if r["language"] == LANGUAGE:
            item_id = f"instruct-v2-{LANGUAGE}-{int(r['prompt_id']):04d}"
            assert item_id not in eligible, f"duplicate id {item_id}"
            eligible[item_id] = r
    ids = sorted(eligible)
    perm = np.random.default_rng(SEED).permutation(len(ids))
    chosen = [ids[i] for i in perm[: min(N, len(ids))]]

    with (HERE / "items.jsonl").open("w") as f:
        for item_id in chosen:
            r = eligible[item_id]
            gold = {
                "prompt_id": r["prompt_id"],
                "language": r["language"],
                "variant": r["variant"],
                "cwe_identifier": r["cwe_identifier"],
                "origin_pattern_id": (r["pattern_id"] or "").split(".")[-1],
                "origin_analyzer": r["analyzer"],
                "repo": r["repo"],
                # origin_code is NOT copied here (it can hold real keys/passwords from public repos);
                # score.py reads it from the pinned dataset by prompt_id and checks this hash.
                "origin_code_sha256": hashlib.sha256(r["origin_code"].encode()).hexdigest(),
            }
            f.write(json.dumps({"item": item_id, "prompt": r["test_case_prompt"], "gold": gold}) + "\n")

    rules = PL / "CodeShield" / "insecure_code_detector" / "rules"
    rule_files = [
        rules / "config.yaml",
        rules / "regex" / "python.yaml",
        rules / "regex" / "language_agnostic.yaml",
        rules / "semgrep" / "_generated_" / "python_cyberseceval.json",
    ]
    source = {
        "benchmark": "CyberSecEval instruct (insecure code generation), Meta PurpleLlama CybersecurityBenchmarks",
        "repo": REPO_URL.removesuffix(".git"),
        "commit": COMMIT,
        "dataset_file": DATA_REL,
        "dataset_sha256": DATA_SHA256,
        "dataset_git_blob": sh("git", "rev-parse", f"HEAD:{DATA_REL}", cwd=PL),
        "why_instruct_v2": "CybersecurityBenchmarks/README.md (For Instruct Benchmark): instruct-v2.json is the "
                           "updated, cleaned release and users are told to use it instead of instruct.json.",
        "filter": f"language == '{LANGUAGE}' (largest language in instruct-v2)",
        "eligible": len(ids),
        "n": len(chosen),
        "sampling": f"sorted ids -> numpy.random.default_rng({SEED}).permutation -> first {N}",
        "item_id": "instruct-v2-<language>-<prompt_id:04d>",
        "prompt": "dataset test_case_prompt verbatim (single user turn, no system prompt), as query_llm.process_prompt sends it",
        "scorer": {
            "icd": "CodeShield/insecure_code_detector at the same commit, usecase=cyberseceval (default)",
            "semgrep": semgrep_version,
            "rule_files_sha256": {str(p.relative_to(PL)): sha256(p) for p in rule_files},
            "official_glue": "CybersecurityBenchmarks/benchmark/instruct_or_autocomplete_benchmark.py "
                             "(InstructOrAutoCompleteBenchmark.run) + benchmark.py extract_content_in_code_blocks",
        },
        "licence": {
            "dataset_and_benchmark_code": "MIT (CybersecurityBenchmarks/LICENSE)",
            "icd": "MIT (CodeShield/LICENSE)",
            "origin_code": "snippets from public GitHub repos; per-repo licences in CybersecurityBenchmarks/datasets/third-party.txt "
                           "(not every repo is listed there); used only for BLEU and the self-check, never sent to the model",
        },
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=2) + "\n")
    print(f"items.jsonl: {len(chosen)} of {len(ids)} eligible {LANGUAGE} items; semgrep {semgrep_version}")


if __name__ == "__main__":
    main()
