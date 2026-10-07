"""BFCL scorer.  usage: python score.py responses.jsonl out.jsonl

responses.jsonl lines: {"item": "<BFCL id>", "response": "<model text>"}
out.jsonl lines:       {"item", "category", "passed", "passed_lenient", "error_type", "error", "decoded"}

passed          OFFICIAL BFCL verdict: bfcl-eval 2026.3.23 eval_runner._evaluate_single_ast_entry
                (default_decode_ast_prompting + is_function_calling_format_output + ast_checker) for
                simple_python/multiple/parallel/parallel_multiple, _evaluate_single_relevance_entry for
                irrelevance (passed = no function call decoded).
passed_lenient  secondary, NOT official: same official verdict applied to the first ``` fenced block when
                the response has one (formatting-only leniency); otherwise equal to passed.
The official decoder eval()s arithmetic in model output, so scoring runs in a pinned python:3.11-slim
container with no network, read-only filesystem, dropped capabilities, one forked child per response
(10 s limit; a timeout or crash scores 0).  Needs Docker; uses only the stdlib on the host.
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "python@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce"  # python:3.11-slim, linux/amd64
DOCKER = [
    "docker", "run", "--rm", "-i", "--network", "none", "--read-only",
    "--tmpfs", "/tmp:rw,size=256m", "--memory", "2g", "--cpus", "2", "--pids-limit", "256",
    "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
    "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "HOME=/tmp", "-e", "OPENBLAS_NUM_THREADS=1",
    "-v", f"{HERE}:/harness:ro", IMAGE, "python", "/harness/bfcl_core.py",
]


def run_core(command, stdin_text):
    try:
        proc = subprocess.run(DOCKER + [command], input=stdin_text, capture_output=True, text=True, timeout=3600)
    except FileNotFoundError:
        raise SystemExit("docker not found: the BFCL scorer runs the official code in a container") from None
    if proc.returncode != 0:
        raise SystemExit(f"bfcl_core {command} failed (exit {proc.returncode}):\n{proc.stderr[-4000:]}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def score_rows(rows, items):
    """rows: [{"item", "response"}]; returns one verdict per row, in order."""
    seen, sendable, verdicts = set(), [], {}
    for row in rows:
        item_id = row.get("item")
        if item_id not in items:
            raise SystemExit(f"unknown item id: {item_id!r}")
        if item_id in seen:
            raise SystemExit(f"duplicate item id: {item_id!r}")
        seen.add(item_id)
        if isinstance(row.get("response"), str):
            sendable.append({"item": item_id, "response": row["response"]})
        else:  # runner failure (null / missing text): not a model abstention, so never a pass
            verdicts[item_id] = {"item": item_id, "category": items[item_id]["gold"]["category"], "passed": 0,
                                 "passed_lenient": 0, "error_type": "harness:invalid_response",
                                 "error": "response is not a string", "decoded": None}
    if sendable:
        payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sendable)
        for verdict in run_core("score", payload):
            verdicts[verdict["item"]] = verdict
    missing = [r["item"] for r in sendable if r["item"] not in verdicts]
    if missing:
        raise SystemExit(f"container returned no verdict for {len(missing)} items, e.g. {missing[:3]}")
    return [verdicts[row["item"]] for row in rows]


def summary(verdicts):
    by_cat = defaultdict(list)
    for v in verdicts:
        by_cat[v["category"]].append(v)
    lines = []
    for cat, vs in [("ALL", verdicts)] + sorted(by_cat.items()):
        lines.append(f"{cat:18s} n={len(vs):4d} passed={sum(v['passed'] for v in vs):4d} "
                     f"lenient={sum(v['passed_lenient'] for v in vs):4d}")
    return "\n".join(lines)


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: python score.py responses.jsonl out.jsonl")
    items = {it["item"]: it for it in read_jsonl(HERE / "items.jsonl")}
    rows = read_jsonl(argv[1])
    verdicts = score_rows(rows, items)
    with open(argv[2], "w", encoding="utf-8") as fh:
        for v in verdicts:
            try:
                line = json.dumps(v, ensure_ascii=False, allow_nan=False)
            except ValueError:  # inf/nan produced by eval()'d arithmetic in the decoded arguments
                line = json.dumps({**v, "decoded": repr(v["decoded"])}, ensure_ascii=False)
            fh.write(line + "\n")
    not_answered = len(items) - len(rows)
    print(summary(verdicts) + (f"\nWARNING: {not_answered} items have no response" if not_answered else ""),
          file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
