#!/usr/bin/env python3
"""Collect the scored attempt of every (item, arm, replicate) into one record list (PROTOCOL.md v1.1, Receipts)."""
import json
import os
from pathlib import Path

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
ROUTER_DELTA = 4500


def _usage(s):
    u = s.get("usage") or {}
    return {"input_tokens": u.get("input_tokens") or 0, "cache_creation_tokens": u.get("cache_creation_input_tokens") or 0,
            "cache_read_tokens": u.get("cache_read_input_tokens") or 0, "output_tokens": u.get("output_tokens") or 0}


def records(bench, rep=None):
    """[{item, arm, replicate, status, scored_attempt, outcome_reason, ...summary fields}]"""
    base = ROOT / "runs" / bench / (f"r{rep}" if rep else "")
    out = []
    if not base.exists():
        return out
    for item_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for arm_dir in sorted(p for p in item_dir.iterdir() if p.is_dir()):
            res = arm_dir / "result.json"
            if not res.exists():
                continue
            r = json.loads(res.read_text())
            rec = {"item": item_dir.name, "arm": arm_dir.name, "replicate": rep or 1,
                   "scored_attempt": r.get("scored_attempt"), "outcome_reason": r.get("outcome_reason"),
                   "discarded_attempts": len(r.get("discarded") or []),
                   "discarded_reasons": ";".join(d.get("reason", "") for d in (r.get("discarded") or []))}
            if r.get("scored_attempt"):
                adir = arm_dir / f"attempt-{r['scored_attempt']}"
                s = json.loads((adir / "summary.json").read_text())
                tu = _usage(s)
                rec.update({
                    "final_text": s.get("final_text") or "", "all_texts": s.get("all_texts") or [],
                    "init_model": s.get("init_model"), "skill_calls": s.get("skill_calls") or [],
                    "fabius_skills_loaded": s.get("fabius_skills_loaded") or [],
                    "first_turn_prompt_tokens": s.get("first_turn_prompt_tokens"),
                    "assistant_text_messages": s.get("assistant_text_messages"),
                    "num_turns": s.get("num_turns"), "elapsed_s": s.get("elapsed_s"),
                    "cost_usd": s.get("total_cost_usd"), **tu,
                    "total_tokens": sum(tu.values()), "timed_out": s.get("timed_out"),
                    "result_subtype": s.get("result_subtype"),
                    "permission_denials": len(s.get("permission_denials") or []),
                })
                ws = adir / "workspace.json"
                if ws.exists():
                    w = json.loads(ws.read_text())
                    rec["patch_lines"] = (w.get("patch_size") or {}).get("added", 0) + (w.get("patch_size") or {}).get("removed", 0)
                    rec["patch_files"] = (w.get("patch_size") or {}).get("files", 0)
                    rec["prompt_sha256"] = w.get("normalized_prompt_sha256")
                    rec["patch_path"] = str(adir / "patch.diff")
                    rec["patch_unfiltered_path"] = str(adir / "patch.unfiltered.diff")
            out.append(rec)
    # router_injected: first-turn prompt tokens exceed the same item's baseline by >= ROUTER_DELTA
    base_tok = {(r["item"], r["replicate"]): r.get("first_turn_prompt_tokens") for r in out if r["arm"] == "baseline"}
    for r in out:
        b = base_tok.get((r["item"], r["replicate"]))
        t = r.get("first_turn_prompt_tokens")
        r["router_injected"] = None if (b is None or t is None) else (t - b >= ROUTER_DELTA)
    return out
