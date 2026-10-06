#!/usr/bin/env python3
"""Item lists and prompts for the single-turn benchmarks, exactly as PROTOCOL.md v1.1 fixes them."""
import json
import os
from pathlib import Path

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
EVALPLUS_INSTRUCTION = ("Please provide a self-contained Python script that solves the following "
                        "problem in a markdown code block:")


def load_items(bench):
    """[(item_id, prompt)] in the benchmark's own order."""
    if bench == "ifeval":
        rows = [json.loads(l) for l in open(ROOT / "ifeval/instruction_following_eval/data/input_data.jsonl")]
        return [(str(r["key"]), r["prompt"]) for r in rows]
    if bench == "humaneval":
        rows = [json.loads(l) for l in open(ROOT / "humanevalplus/cache/HumanEvalPlus-v0.1.10.jsonl")]
        rows.sort(key=lambda r: int(r["task_id"].split("/")[1]))
        return [(r["task_id"].replace("/", "_"), EVALPLUS_INSTRUCTION + f"\n```python\n{r['prompt'].strip()}\n```\n")
                for r in rows]
    raise ValueError(bench)
