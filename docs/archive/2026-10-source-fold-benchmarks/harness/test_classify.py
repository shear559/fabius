#!/usr/bin/env python3
"""Unit tests for classify(): real canary records plus synthetic failure records."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from classify import classify  # noqa: E402

ROOT = os.path.expanduser("~/Documents/fabius-benchmark/canaries")
F15 = [f"fabius:x{i}" for i in range(15)]
OK = {"result_subtype": "success", "init_model": "claude-sonnet-5-5", "init_skills": [], "is_error": False,
      "api_error_status": None, "meter": {"status": "allowed"}, "result_text": "fine", "final_text": "fine"}
cases = [
    ("real max-turns canary is an outcome", json.load(open(f"{ROOT}/maxturns/summary.json")), "baseline", "OUTCOME"),
    ("real success canary is an outcome", json.load(open(f"{ROOT}/deny-baseline/summary.json")), "baseline", "OUTCOME"),
    ("real fabius-loaded canary is an outcome", json.load(open(f"{ROOT}/skill-load-loaded/summary.json")), "fabius-loaded", "OUTCOME"),
    ("no result record is INFRA", {**OK, "result_subtype": None}, "baseline", "INFRA"),
    ("usage-limit error is LIMIT", {**OK, "is_error": True, "result_text": "You've hit your session limit · resets 22:30"}, "baseline", "LIMIT"),
    ("rejected meter is LIMIT", {**OK, "meter": {"status": "rejected", "resetsAt": 1}}, "baseline", "LIMIT"),
    ("api error status is INFRA", {**OK, "api_error_status": 529}, "baseline", "INFRA"),
    ("overload error text is INFRA", {**OK, "is_error": True, "result_text": "API Error: 529 overloaded"}, "baseline", "INFRA"),
    ("unknown subtype is INFRA", {**OK, "result_subtype": "error_during_execution"}, "baseline", "INFRA"),
    ("wrong model is INFRA", {**OK, "init_model": "claude-opus-5-5"}, "baseline", "INFRA"),
    ("baseline with fabius skills is INFRA", {**OK, "init_skills": F15}, "baseline", "INFRA"),
    ("fabius arm without the plugin is INFRA", {**OK}, "fabius-loaded", "INFRA"),
    ("fabius arm with 15 skills is an outcome", {**OK, "init_skills": F15}, "fabius-doc", "OUTCOME"),
    ("timeout after a real start is an outcome", {**OK, "timed_out": True, "result_subtype": None}, "baseline", "OUTCOME"),
]
fails = 0
for name, summary, arm, want in cases:
    got = classify(summary, arm)["kind"]
    ok = got == want
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" — got {got}, want {want}"))
print(f"{len(cases) - fails}/{len(cases)} passed")
sys.exit(1 if fails else 0)
