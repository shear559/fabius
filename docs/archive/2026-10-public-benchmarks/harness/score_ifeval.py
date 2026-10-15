#!/usr/bin/env python3
"""Score IFEval with the official google-research code (PROTOCOL.md v1.4, benchmark 2).

One process: set langdetect.DetectorFactory.seed = 0 (the declared deviation that makes
language detection deterministic), then for every arm and every response variant run the
official evaluation_main logic unchanged — read_prompt_list, test_instruction_following_strict
and _loose, write_outputs — on the official input data. Variants: "final" (the primary: the
run's final result text) and "concat" (the declared sensitivity: all assistant text blocks).
Writes results/ifeval/items.csv and the official output files per arm and variant.
"""
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.path.expanduser(os.environ.get("FB_ROOT", "~/Documents/fabius-benchmark")))
sys.path.insert(0, str(ROOT / "ifeval"))
sys.path.insert(0, str(ROOT / "harness"))

import langdetect  # noqa: E402

langdetect.DetectorFactory.seed = 0

from instruction_following_eval import evaluation_lib  # noqa: E402
from collect import records  # noqa: E402

import cohort  # noqa: E402

ARMS = cohort.ARM_ORDER if cohort.ACTIVE else ["baseline", "fabius-loaded"]  # fabius-doc dropped on IFEval by the gate
OUT = ROOT / "results" / "ifeval"
INPUT = ROOT / "ifeval/instruction_following_eval/data/input_data.jsonl"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = evaluation_lib.read_prompt_list(str(INPUT))
    key_of = {json.loads(l)["prompt"]: str(json.loads(l)["key"]) for l in open(INPUT)}
    recs = {(r["item"], r["arm"]): r for r in records("ifeval") if r["arm"] in ARMS}
    results = {}
    for arm in ARMS:
        for variant in ("final", "concat"):
            prompt_to_response = {}
            for inp in inputs:
                r = recs.get((key_of[inp.prompt], arm))
                if not r or r.get("scored_attempt") is None:
                    prompt_to_response[inp.prompt] = ""
                elif variant == "final":
                    prompt_to_response[inp.prompt] = r["final_text"]
                else:
                    prompt_to_response[inp.prompt] = "\n\n".join(r.get("all_texts") or []) or r["final_text"]
            for func, name in ((evaluation_lib.test_instruction_following_strict, "strict"),
                               (evaluation_lib.test_instruction_following_loose, "loose")):
                outputs = [func(inp, prompt_to_response) for inp in inputs]
                evaluation_lib.write_outputs(str(OUT / f"eval_results_{name}-{arm}-{variant}.jsonl"), outputs)
                for o in outputs:
                    results[(key_of[o.prompt], arm, variant, name)] = (o.follow_all_instructions,
                                                                      sum(o.follow_instruction_list),
                                                                      len(o.follow_instruction_list),
                                                                      list(o.instruction_id_list))
    fields = ["item", "arm", "replicate", "passed", "loose_passed", "passed_concat", "loose_passed_concat",
              "instr_followed_strict", "instr_followed_loose", "instr_total", "has_repeat_prompt", "excluded",
              "router_injected", "fabius_skills_loaded", "skill_calls", "output_tokens", "total_tokens", "cost_usd",
              "elapsed_s", "num_turns", "outcome_reason", "scored_attempt", "discarded_attempts", "discarded_reasons",
              "assistant_text_messages", "init_model", "first_turn_prompt_tokens", "package_reads_delivered", "package_reads_denied", "package_files_read"]
    missing = {item for (item, arm), r in recs.items() if r.get("scored_attempt") is None}
    with open(OUT / "items.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for (item, arm), r in sorted(recs.items()):
            s, sl, sc, scl = (results[(item, arm, v, n)] for v, n in (("final", "strict"), ("final", "loose"),
                                                                       ("concat", "strict"), ("concat", "loose")))
            ex = "no scored attempt after retries (dropped from both arms)" if item in missing else ""
            w.writerow({"item": item, "arm": arm, "replicate": 1,
                        "passed": "" if ex else int(s[0]), "loose_passed": "" if ex else int(sl[0]),
                        "passed_concat": "" if ex else int(sc[0]), "loose_passed_concat": "" if ex else int(scl[0]),
                        "instr_followed_strict": s[1], "instr_followed_loose": sl[1], "instr_total": s[2],
                        "has_repeat_prompt": int(any(i == "combination:repeat_prompt" for i in s[3])),
                        "excluded": ex, "router_injected": r.get("router_injected"),
                        "fabius_skills_loaded": json.dumps(r.get("fabius_skills_loaded") or []),
                        "skill_calls": json.dumps(r.get("skill_calls") or []),
                        **{k: r.get(k) for k in ("output_tokens", "total_tokens", "cost_usd", "elapsed_s", "num_turns",
                                                 "outcome_reason", "scored_attempt", "discarded_attempts",
                                                 "discarded_reasons", "assistant_text_messages", "init_model",
                                                 "first_turn_prompt_tokens", "package_reads_delivered", "package_reads_denied")},
                        "package_files_read": json.dumps(r.get("package_files_read") or [])})
    for arm in ARMS:
        ok = [results[(k, arm, "final", "strict")][0] for k in {i for i, a in recs if a == arm} if k not in missing]
        print(f"{arm}: prompt-level strict {sum(ok)}/{len(ok)} = {sum(ok)/len(ok):.4f}")
    print("dropped (infra, both arms):", sorted(missing))


if __name__ == "__main__":
    main()
