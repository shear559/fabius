#!/usr/bin/env python3
"""SWE-bench Verified Mini agent runs (PROTOCOL.md v1.1, benchmark 1).

  swe_runner.py --replicate 1 [--workers 2] [--limit N]

Items in schedule.json order (Django and Sphinx alternating), valid instances only. Each
item runs its arms back to back in the item's seeded order: baseline and fabius-loaded on
every valid item, fabius-doc only on the fixed stratified subset (replicate 1 only). Every
attempt gets a fresh workspace and a fresh container; the container is killed before the
patch is taken. The usage gate from runner.py applies before each item starts.
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import claude_run as cr  # noqa: E402
import swe_prepare as sp  # noqa: E402
from classify import classify  # noqa: E402
from runner import gate, log_budget, STATE, LOCK, windows  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
TOOLS = "Read,Edit,Write,Glob,Grep,TodoWrite,Skill,Bash"
ALLOWED = ["Read", "Edit", "Write", "Glob", "Grep", "TodoWrite", "Skill"]


def rows():
    return {r["instance_id"]: r for r in json.load(open(ROOT / "swebench-mini-official-rows.json"))}


def run_arm(item, row, image_ref, arm, rep):
    arm_dir = ROOT / "runs" / "swebench" / f"r{rep}" / item / arm
    res_path = arm_dir / "result.json"
    if res_path.exists():
        return json.loads(res_path.read_text())
    arm_dir.mkdir(parents=True, exist_ok=True)
    discarded, n, retries = [], 0, 0
    while True:
        n += 1
        adir = arm_dir / f"attempt-{n}"
        log = {"image": image_ref}
        root, repo, ok = sp.prepare_workspace(image_ref, row["base_commit"], log)
        if not ok:
            sp.cleanup(root)
            adir.mkdir(parents=True)
            (adir / "workspace.json").write_text(json.dumps(log, indent=1))
            out = {"item": item, "arm": arm, "replicate": rep, "scored_attempt": None,
                   "outcome_reason": "workspace assertion failed", "discarded": discarded}
            res_path.write_text(json.dumps(out, indent=1))
            return out
        cname, docker_args = sp.start_container(image_ref, repo)
        wrapper = sp.write_wrapper(root, cname)
        prompt = sp.render_prompt(row["problem_statement"], repo, wrapper)
        try:
            s = cr.run_attempt(prompt, arm, repo, adir, tools=TOOLS, allowed=ALLOWED + [f"Bash({wrapper}:*)"],
                               max_turns=150, timeout_s=2400, permission_mode="dontAsk")
        finally:
            sp.kill_container(cname)
        filtered, unfiltered = sp.extract_patch(repo, log["workspace_asserts"]["head"])
        (adir / "patch.diff").write_text(filtered)
        (adir / "patch.unfiltered.diff").write_text(unfiltered)
        log.update({"docker_run": docker_args, "wrapper": str(wrapper), "workspace_root": str(root),
                    "normalized_prompt_sha256": __import__("hashlib").sha256(
                        sp.normalized_prompt(prompt, root).encode()).hexdigest(),
                    "patch_size": sp.patch_size(filtered), "unfiltered_patch_size": sp.patch_size(unfiltered)})
        (adir / "workspace.json").write_text(json.dumps(log, indent=1))
        sp.cleanup(root)
        if s.get("meter"):
            with LOCK:
                STATE["meter"] = s["meter"]
        c = classify(s, arm)
        if c["kind"] == "OUTCOME":
            out = {"item": item, "arm": arm, "replicate": rep, "scored_attempt": n, "outcome_reason": c["reason"],
                   "discarded": discarded, "summary": f"attempt-{n}/summary.json", "patch": f"attempt-{n}/patch.diff"}
            res_path.write_text(json.dumps(out, indent=1))
            return out
        discarded.append({"attempt": n, **c})
        if c["kind"] == "LIMIT":
            until = c.get("resets_at") or (time.time() + 900)
            log_budget(f"swebench/{item}/{arm}: usage limit hit — pausing until {time.strftime('%H:%M', time.localtime(until))}")
            time.sleep(max(60, until - time.time() + 60))
            continue
        retries += 1
        if retries > 2:
            out = {"item": item, "arm": arm, "replicate": rep, "scored_attempt": None,
                   "outcome_reason": "INFRA after 2 retries", "discarded": discarded}
            res_path.write_text(json.dumps(out, indent=1))
            return out
        time.sleep(30 * retries)


def run_item(item, row, image_ref, arms, rep):
    if not gate(f"swebench-r{rep}/{item}"):
        return item, None
    return item, [run_arm(item, row, image_ref, a, rep) for a in arms]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicate", type=int, default=1)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--items", default="")
    a = ap.parse_args()
    sched = json.load(open(ROOT / "schedule.json"))["swebench"]
    valid = json.load(open(ROOT / "swebench-validity.json"))
    pins = json.load(open(ROOT / "swebench-image-digests.json"))
    doc_subset = set(json.load(open(ROOT / "swebench-doc-subset.json")))
    R = rows()
    items = [i for i in sched["items"] if valid.get(i, {}).get("valid")]
    if a.items:
        items = [i for i in items if i in set(a.items.split(","))]
    if a.limit:
        items = items[: a.limit]

    def arms_for(i):
        keep = {"baseline", "fabius-loaded"} | ({"fabius-doc"} if a.replicate == 1 and i in doc_subset else set())
        return [x for x in sched["arm_order"][i] if x in keep]

    log_budget(f"swebench r{a.replicate}: start, {len(items)} valid items, {a.workers} workers")
    done = 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_item, i, R[i], pins[i], arms_for(i), a.replicate) for i in items]
        for f in cf.as_completed(futs):
            item, res = f.result()
            done += 1
            five, seven = windows(STATE["meter"])
            print(f"swebench r{a.replicate}: {done}/{len(items)} items ({item}) · 5h {five.get('utilization')} · "
                  f"7d {seven.get('utilization')}", flush=True)
    five, seven = windows(STATE["meter"])
    log_budget(f"swebench r{a.replicate}: end · meters 5h {five.get('utilization')} · 7d {seven.get('utilization')}")


if __name__ == "__main__":
    main()
