#!/usr/bin/env python3
"""Build items.jsonl + source.json for SmartBugs-curated (pinned commit).

Run from anywhere:  python prepare.py
Reads the dataset straight from the git object store at COMMIT (this directory is
the upstream clone), so working-tree edits can never change the items.
"""
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_URL = "https://github.com/smartbugs/smartbugs-curated"
COMMIT = "230e649123477eff332742a59a1c7cc6dc286cab"
SEED, N = 20261006, 143

# The 10 DASP Top-10 (2018) categories, in DASP order, as SmartBugs-curated labels them.
CATEGORIES = [
    ("reentrancy", "Reentrancy"),
    ("access_control", "Access Control"),
    ("arithmetic", "Arithmetic Issues"),
    ("unchecked_low_level_calls", "Unchecked Return Values For Low Level Calls"),
    ("denial_of_service", "Denial of Service"),
    ("bad_randomness", "Bad Randomness"),
    ("front_running", "Front-Running"),
    ("time_manipulation", "Time Manipulation"),
    ("short_addresses", "Short Address Attack"),
    ("other", "Unknown Unknowns: any vulnerability not covered by the labels above"),
]

TEMPLATE = (
    "Below is a Solidity smart contract. Each line is prefixed with its line number.\n\n"
    "```solidity\n{source}\n```\n\n"
    "Identify the most important vulnerability in this contract and classify it with "
    "exactly one of these 10 DASP category labels:\n"
    + "".join(f"- {label} ({name})\n" for label, name in CATEGORIES)
    + "\nEnd your answer with exactly these two lines:\n"
    "Category: <one label from the list above>\n"
    "Lines: <comma-separated line numbers of the vulnerable code>"
)

# SmartBugs-curated markup = the answer key; it must not reach the model.
MARKER = re.compile(r"^\s*//\s*<yes>\s*<report>\s*(.*?)\s*$")  # line before each vulnerable line


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(HERE), *args], check=True, capture_output=True).stdout


def strip_markup(text: str):
    """Drop the leading SmartBugs header comment (@source/@author/@vulnerable_at_lines ...),
    every `// <yes> <report> X` marker line, and leading/trailing blank lines.
    Returns (kept_lines, orig_to_new line map, [(marker_orig_line, label)])."""
    lines = text.split("\n")
    n, drop = len(lines), set()
    i = 0
    while i < n and not lines[i].strip():
        i += 1
    j = i
    while j < n and "*/" not in lines[j]:
        j += 1
    header = lines[i:j + 1]
    assert lines[i].lstrip().startswith("/*") and lines[j].strip() == "*/", "header block expected"
    assert any("@vulnerable_at_lines" in h for h in header), "SmartBugs header expected"
    drop.update(range(j + 1))
    k = j + 1
    while k < n and not lines[k].strip():
        drop.add(k)
        k += 1
    markers = []
    for idx, line in enumerate(lines):
        m = MARKER.match(line)
        if m:
            drop.add(idx)
            markers.append((idx + 1, m.group(1)))
    k = n - 1
    while k >= 0 and (k in drop or not lines[k].strip()):
        drop.add(k)
        k -= 1
    kept = [(idx + 1, line) for idx, line in enumerate(lines) if idx not in drop]
    orig_to_new = {orig: new for new, (orig, _) in enumerate(kept, 1)}
    return [line for _, line in kept], orig_to_new, markers


def number(lines):
    w = len(str(len(lines)))
    return "\n".join(f"{i:>{w}} | {line}".rstrip() for i, line in enumerate(lines, 1))


def load_records():
    """One record per annotated contract file in vulnerabilities.json at COMMIT."""
    assert git_bytes("rev-parse", f"{COMMIT}^{{commit}}").decode().strip() == COMMIT
    vulns_raw = git_bytes("show", f"{COMMIT}:vulnerabilities.json")
    records = []
    for entry in json.loads(vulns_raw):
        raw = git_bytes("show", f"{COMMIT}:{entry['path']}")
        kept, o2n, markers = strip_markup(raw.decode("utf-8"))
        assert "```" not in "\n".join(kept)
        by_cat = defaultdict(set)
        for v in entry["vulnerabilities"]:
            by_cat[v["category"]].update(v["lines"])
        assert by_cat and set(by_cat) <= {c for c, _ in CATEGORIES}, entry["path"]
        for orig in set().union(*by_cat.values()):
            assert orig in o2n and kept[o2n[orig] - 1].strip(), (entry["path"], orig)
        records.append({
            "path": entry["path"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "source": number(kept),
            "annotations": [{"path": entry["path"], "category": c, "orig_lines": sorted(ls),
                             "lines": sorted(o2n[x] for x in ls)} for c, ls in sorted(by_cat.items())],
            "markers": [{"label": label, "line": o2n[orig + 1]} for orig, label in markers],
        })
    # Identical code under two paths (0x627fa62c... in reentrancy/ and unchecked_low_level_calls/):
    # the model cannot tell the copies apart, so each copy accepts the union of their annotations.
    groups = defaultdict(list)
    for r in records:
        groups[r["source"]].append(r)
    for r in records:
        anns = [a for g in groups[r["source"]] for a in g["annotations"]]
        lines = defaultdict(set)
        for a in anns:
            lines[a["category"]].update(a["lines"])
        r["gold"] = {"categories": sorted(lines), "lines": {c: sorted(v) for c, v in sorted(lines.items())},
                     "annotations": anns}
    return records, vulns_raw


def main():
    records, vulns_raw = load_records()
    ids = sorted(r["path"] for r in records)
    perm = np.random.default_rng(SEED).permutation(len(ids))
    chosen = [ids[i] for i in perm[:N]]
    by_id = {r["path"]: r for r in records}
    with open(HERE / "items.jsonl", "w", encoding="utf-8") as f:
        for item in chosen:
            r = by_id[item]
            f.write(json.dumps({"item": item, "prompt": TEMPLATE.replace("{source}", r["source"]),
                                "gold": r["gold"]}, ensure_ascii=False) + "\n")
    dup = sorted(r["path"] for r in records if len(r["gold"]["annotations"]) > len(r["annotations"]))
    source = {
        "dataset": "SmartBugs-curated",
        "repo": REPO_URL,
        "commit": COMMIT,
        "license": "Apache-2.0 (repository); contracts keep their original licences (public sources / Etherscan)",
        "vulnerabilities_json_sha256": hashlib.sha256(vulns_raw).hexdigest(),
        "contract_sha256": {r["path"]: r["sha256"] for r in sorted(records, key=lambda r: r["path"])},
        "n_eligible": len(ids),
        "n_sampled": len(chosen),
        "sampling": f"sorted paths -> numpy.random.default_rng({SEED}).permutation -> first {N}",
        "union_gold_for_identical_code": dup,
        "items_jsonl_sha256": hashlib.sha256((HERE / "items.jsonl").read_bytes()).hexdigest(),
    }
    (HERE / "source.json").write_text(json.dumps(source, indent=1) + "\n")
    print(f"wrote {len(chosen)} items; union-gold items: {dup}")


if __name__ == "__main__":
    main()
