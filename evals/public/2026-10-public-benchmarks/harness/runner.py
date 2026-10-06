#!/usr/bin/env python3
"""Item-ordered runner for the single-turn benchmarks with the usage gate (PROTOCOL.md v1.1).

  runner.py <humaneval|ifeval> [--arms a,b,c] [--workers 6] [--limit N]

Items run in schedule.json order; all requested arms of an item run back to back in the
item's seeded arm order. Before an item starts, the usage gate is checked: the weekly meter
at or above STOP_7D stops the study (whole items only); the 5-hour meter at or above
PAUSE_5H pauses until its reset. INFRA attempts are retried up to twice; a usage-limit
stop pauses the pool without spending a retry. Every attempt is kept.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import claude_run as cr  # noqa: E402
from bench_items import load_items  # noqa: E402
from classify import classify  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
STOP_7D, PAUSE_5H = 0.75, 0.60
LOCK = threading.Lock()
STATE = {"meter": None, "stop": False}


def log_budget(msg):
    line = f"- {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · {msg}\n"
    with LOCK, open(ROOT / "budget-log.md", "a") as f:
        f.write(line)
    print(line.strip(), flush=True)


def windows(meter):
    w = (meter or {}).get("unifiedWindows") or {}
    return (w.get("five_hour") or {}), (w.get("seven_day") or {})


def gate(tag):
    """Block until a new item may start; return False if the study must stop."""
    while True:
        with LOCK:
            meter, stop = STATE["meter"], STATE["stop"]
        if stop:
            return False
        five, seven = windows(meter)
        if (seven.get("utilization") or 0) >= STOP_7D:
            with LOCK:
                first = not STATE["stop"]
                STATE["stop"] = True
            if first:
                log_budget(f"{tag}: weekly meter {seven.get('utilization')} ≥ {STOP_7D} — no new items start")
            return False
        if (five.get("utilization") or 0) >= PAUSE_5H:
            until = five.get("resetsAt") or (time.time() + 600)
            log_budget(f"{tag}: 5-hour meter {five.get('utilization')} ≥ {PAUSE_5H} — pausing until "
                       f"{dt.datetime.fromtimestamp(until).strftime('%H:%M')}")
            time.sleep(max(60, until - time.time() + 60))
            with LOCK:
                STATE["meter"] = None  # re-read from the next run
            continue
        return True


def run_arm(bench, item, prompt, arm):
    arm_dir = ROOT / "runs" / bench / item / arm
    res_path = arm_dir / "result.json"
    if res_path.exists():
        return json.loads(res_path.read_text())
    arm_dir.mkdir(parents=True, exist_ok=True)
    discarded, n, retries = [], 0, 0
    while True:
        n += 1
        cwd = tempfile.mkdtemp(prefix="fbr-", dir="/private/tmp")
        try:
            s = cr.run_attempt(prompt, arm, cwd, arm_dir / f"attempt-{n}", tools="Skill", allowed=["Skill"],
                               max_turns=8, timeout_s=300)
        finally:
            shutil.rmtree(cwd, ignore_errors=True)
        if s.get("meter"):
            with LOCK:
                STATE["meter"] = s["meter"]
        c = classify(s, arm)
        if c["kind"] == "OUTCOME":
            out = {"item": item, "arm": arm, "scored_attempt": n, "outcome_reason": c["reason"],
                   "discarded": discarded, "summary": f"attempt-{n}/summary.json"}
            res_path.write_text(json.dumps(out, indent=1))
            return out
        discarded.append({"attempt": n, **c})
        if c["kind"] == "LIMIT":
            until = c.get("resets_at") or (time.time() + 900)
            log_budget(f"{bench}/{item}/{arm}: usage limit hit — pausing until "
                       f"{dt.datetime.fromtimestamp(until).strftime('%H:%M')} (no retry spent)")
            time.sleep(max(60, until - time.time() + 60))
            continue
        retries += 1
        if retries > 2:
            out = {"item": item, "arm": arm, "scored_attempt": None, "outcome_reason": "INFRA after 2 retries",
                   "discarded": discarded}
            res_path.write_text(json.dumps(out, indent=1))
            return out
        time.sleep(30 * retries)


def run_item(bench, item, prompt, arms):
    if not gate(f"{bench}/{item}"):
        return item, None
    return item, [run_arm(bench, item, prompt, a) for a in arms]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench", choices=["humaneval", "ifeval"])
    ap.add_argument("--arms", default="baseline,fabius-doc,fabius-loaded")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    sched = json.load(open(ROOT / "schedule.json"))[a.bench]
    prompts = dict(load_items(a.bench))
    wanted = set(a.arms.split(","))
    items = sched["items"][: a.limit] if a.limit else sched["items"]
    log_budget(f"{a.bench}: start, {len(items)} items × arms {sorted(wanted)}, {a.workers} workers")
    done = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_item, a.bench, i, prompts[i], [x for x in sched["arm_order"][i] if x in wanted])
                for i in items]
        for f in cf.as_completed(futs):
            item, res = f.result()
            done += 1
            if done % 20 == 0 or done == len(items):
                five, seven = windows(STATE["meter"])
                print(f"{a.bench}: {done}/{len(items)} items · 5h {five.get('utilization')} · 7d {seven.get('utilization')}",
                      flush=True)
    five, seven = windows(STATE["meter"])
    log_budget(f"{a.bench}: end · meters 5h {five.get('utilization')} · 7d {seven.get('utilization')}")


if __name__ == "__main__":
    main()
