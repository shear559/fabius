#!/usr/bin/env python3
"""LongMemEval judge: the official judge prompts, sent one at a time to a tool-less headless Claude Code
session, as the continuation's declared substitute for the unavailable official judge (gpt-4o-2024-08-06).

  judge_longmemeval.py <judge_prompts.jsonl> <judgements.jsonl> [--workers 6] [--model claude-sonnet-5-5]

Each judge_prompt is the only user message; no tools, one turn, the same clean-context flags as every
run of the study, a fresh working directory, no package loaded, and no knowledge of which arm produced
the answer. The reply text is the judgement; score_from_judgements.py applies the official rule
('yes' in reply.lower()). Every call's init model, usage and cost are kept beside the reply. A call with
no result or an API error is retried up to twice; an item still missing is written with judgement null
so stage 2 refuses to score it.
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import claude_run as cr  # noqa: E402

FLAGS = ["--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
         "--output-format", "stream-json", "--verbose", "--tools", "", "--max-turns", "1"]


def judge_one(prompt, model):
    import subprocess
    cwd = tempfile.mkdtemp(prefix="fbj-", dir="/private/tmp")
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    try:
        for attempt in range(3):
            proc = subprocess.run([cr.CLAUDE, "-p", prompt, "--model", model, *FLAGS], cwd=cwd, env=env,
                                  stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
            p = cr.parse_stream(proc.stdout.splitlines())
            res, init = p["result"] or {}, p["init"] or {}
            ok = res.get("subtype") == "success" and not res.get("api_error_status") and init.get("model") == model
            if ok:
                return {"judgement": res.get("result"), "init_model": init.get("model"), "num_turns": res.get("num_turns"),
                        "cost_usd": res.get("total_cost_usd"), "usage": res.get("usage"), "attempts": attempt + 1,
                        "meter": p["meters"][-1] if p["meters"] else None}
            time.sleep(20 * (attempt + 1))
        return {"judgement": None, "init_model": init.get("model"), "error": res.get("subtype") or "no result",
                "attempts": 3}
    finally:
        mem = cr.memory_dir_for(cwd)
        if mem.exists():
            shutil.rmtree(mem, ignore_errors=True)
        shutil.rmtree(cwd, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompts")
    ap.add_argument("out")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default=cr.MODEL)
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.prompts)]
    done = {}
    if Path(a.out).exists():  # resume: keep finished judgements
        for l in open(a.out):
            r = json.loads(l)
            if r.get("judgement") is not None:
                done[r["item"]] = r
    todo = [r for r in rows if r["item"] not in done]
    print(f"judging {len(todo)} of {len(rows)} prompts with {a.model}", flush=True)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(judge_one, r["judge_prompt"], a.model): r for r in todo}
        for i, f in enumerate(cf.as_completed(futs), 1):
            r = futs[f]
            done[r["item"]] = {"item": r["item"], **f.result()}
            if i % 20 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}", flush=True)
    with open(a.out, "w") as fo:
        for r in rows:
            fo.write(json.dumps(done.get(r["item"], {"item": r["item"], "judgement": None, "error": "not judged"})) + "\n")
    missing = [r["item"] for r in rows if done.get(r["item"], {}).get("judgement") is None]
    print(f"judged {len(rows) - len(missing)}/{len(rows)}; missing: {missing[:10]}")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
