#!/usr/bin/env python3
"""OUTCOME or INFRA for one attempt, decided from its record before any scoring (PROTOCOL.md v1.1).

An attempt is INFRA if: there is no result record; the result carries an API error status;
the result subtype is not success or error_max_turns; it is an error naming a usage limit,
a rate limit, an overload or an API error; the last usage event says rejected; the init
model is wrong; or the init skills do not match the arm. A usage-limit INFRA is LIMIT (the
pool pauses until the reset, without spending a retry). Everything else is an OUTCOME and
is never rerun, including turn-cap hits and timeouts.
"""
import re

LIMIT_RE = re.compile(r"usage limit|hit your limit|session limit|weekly limit|limit reached", re.I)
INFRA_RE = re.compile(r"rate.?limit|overloaded|API Error|internal server error|connection error", re.I)
FABIUS_SKILLS = 15


def fabius_skill_count(init_skills):
    return sum(1 for s in (init_skills or []) if str(s).startswith("fabius:"))


def classify(summary, arm, expected_model="claude-sonnet-5-5"):
    s = summary or {}
    meter = s.get("meter") or {}
    text = " ".join(str(x) for x in (s.get("result_text"), s.get("final_text")) if x)
    if s.get("timed_out"):
        # a timeout is an outcome, but only if the run had really started with the right setup
        if s.get("init_model") and s.get("init_model") != expected_model:
            return {"kind": "INFRA", "reason": f"wrong model {s.get('init_model')}"}
        return {"kind": "OUTCOME", "reason": "timeout"}
    if s.get("result_subtype") is None:
        if LIMIT_RE.search(text):
            return {"kind": "LIMIT", "reason": "usage limit (no result record)", "resets_at": meter.get("resetsAt")}
        return {"kind": "INFRA", "reason": "no result record"}
    if meter.get("status") == "rejected" or (s.get("is_error") and LIMIT_RE.search(text)):
        return {"kind": "LIMIT", "reason": "usage limit", "resets_at": meter.get("resetsAt")}
    if s.get("api_error_status") not in (None, "", 0):
        return {"kind": "INFRA", "reason": f"api error status {s.get('api_error_status')}"}
    if s.get("result_subtype") not in ("success", "error_max_turns"):
        return {"kind": "INFRA", "reason": f"result subtype {s.get('result_subtype')}"}
    if s.get("is_error") and INFRA_RE.search(text):
        return {"kind": "INFRA", "reason": "api/rate-limit/overload error text"}
    if s.get("init_model") != expected_model:
        return {"kind": "INFRA", "reason": f"wrong model {s.get('init_model')}"}
    n = fabius_skill_count(s.get("init_skills"))
    want = 0 if arm == "baseline" else FABIUS_SKILLS
    if n != want:
        return {"kind": "INFRA", "reason": f"init lists {n} fabius skills, arm {arm} needs {want}"}
    if s.get("result_subtype") == "error_max_turns":
        return {"kind": "OUTCOME", "reason": "max turns"}
    return {"kind": "OUTCOME", "reason": "success"}
