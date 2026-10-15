#!/usr/bin/env python3
"""Per-arm run outcomes the protocol requires (PROTOCOL.md v1.4, Runs, failures, and integrity), plus two
exploratory SWE-bench measures. Writes results/descriptives.json; make_report.py prints it.

Per benchmark, arm and replicate: scored runs, turn-cap hits (result subtype error_max_turns), timeouts,
runs whose final text ends on a question, INFRA attempts discarded and retried, and items with no scored
attempt. Exploratory (not pre-registered): SWE-bench runs that attempted a command in the test container and runs
where at least one such command executed (a refused call, such as a host-side edit chained to the wrapper,
is counted as attempted only), and runs with at least one permission denial.
"""
import json
import os
from pathlib import Path

from collect import records

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
BENCHES = [("swebench", 1), ("swebench", 2), ("ifeval", None), ("humaneval", None), ("cyberseceval", None),
           ("labbench", None), ("finqa", None), ("ds1000", None), ("smartbugs", None), ("bfcl", None)]
if os.environ.get("FB_COHORT") == "fold":
    BENCHES += [("longmemeval", None), ("design2code", None)]


def ends_on_question(text):
    lines = [l.strip() for l in (text or "").strip().splitlines() if l.strip()]
    return bool(lines) and lines[-1].rstrip("*_`) ").endswith("?")


def container_calls(adir):
    """(attempted, executed): Bash tool calls naming the run's container wrapper, and those whose tool result
    was not an error (a refused permission, e.g. a host-side edit chained to the wrapper, is an error)."""
    root = str(Path(json.loads((adir / "cmd.json").read_text())["cwd"]).parent)
    wrapper = root + "/run"
    uses, ok = set(), set()
    for line in open(adir / "stream.jsonl"):
        d = json.loads(line)
        msg = d.get("message") if isinstance(d.get("message"), dict) else {}
        for b in msg.get("content", []) or []:
            if d.get("type") == "assistant" and b.get("type") == "tool_use" and b.get("name") == "Bash" \
                    and wrapper in ((b.get("input") or {}).get("command") or ""):
                uses.add(b["id"])
            elif d.get("type") == "user" and b.get("type") == "tool_result" and b.get("tool_use_id") in uses \
                    and not b.get("is_error", False):
                ok.add(b["tool_use_id"])
    return len(uses), len(ok)


def main():
    out = {}
    for bench, rep in BENCHES:
        by_arm = {}
        for r in records(bench, rep):
            by_arm.setdefault(r["arm"], []).append(r)
        for arm, rs in sorted(by_arm.items()):
            scored = [r for r in rs if r.get("scored_attempt")]
            row = {"runs": len(scored), "no_scored_attempt": len(rs) - len(scored),
                   "infra_retries": sum(r["discarded_attempts"] for r in rs),
                   "turn_cap": sum(r.get("result_subtype") == "error_max_turns" for r in scored),
                   "timeouts": sum(bool(r.get("timed_out")) for r in scored),
                   "ended_on_question": sum(ends_on_question(r.get("final_text")) for r in scored)}
            if bench == "swebench":
                base = ROOT / "runs" / "swebench" / f"r{rep}"
                calls = [container_calls(base / r["item"] / arm / f"attempt-{r['scored_attempt']}") for r in scored]
                row["container_attempted"] = sum(1 for a, _ in calls if a)
                row["container_executed"] = sum(1 for _, e in calls if e)
                row["runs_with_permission_denial"] = sum(r.get("permission_denials", 0) > 0 for r in scored)
            out[f"{bench}{f' r{rep}' if rep else ''} · {arm}"] = row
    (ROOT / "results" / "descriptives.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main()
