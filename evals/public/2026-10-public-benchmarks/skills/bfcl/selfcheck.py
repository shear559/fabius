"""Self-check of score.py on the 200 sampled items.  usage: python selfcheck.py  -> selfcheck.json

Gold sets (must pass): the official possible_answer rendered as [func(param=value, ...)]:
  gold_first   every listed parameter, first allowed value
  gold_minimal parameters omitted when possible_answer allows "" and the schema does not require them
  gold_reorder gold_first with the call order reversed (parallel categories are order-free)
  irrelevance gold = a sentence pointing out that no function applies / "[]" / "".
Wrong sets (must fail): wrong_other_item (gold of another item of the same category), wrong_value (one
argument value perturbed); irrelevance rows in both call the offered function with placeholder arguments.
Informative sets: refusal text everywhere; gold wrapped in a ```python fence; gold without outer brackets.
Also: hostile responses (sandbox probes) and gold_first/gold_minimal over all 1,240 non-live entries.
"""
import json
from collections import defaultdict

from prepare import CATEGORIES, PKG_ROOT
from score import HERE, read_jsonl, run_core, score_rows

NO_CALL_TEXT = "None of the provided functions can be used to answer this question."
PLACEHOLDER = {"integer": 1, "float": 1.0, "string": "x", "boolean": True, "array": [], "tuple": [],
               "dict": {}, "any": "x"}

# Every gold failure must be explained here after inspection (item id -> reason); unexplained ones are flagged.
GOLD_FAILURE_EXPLANATIONS = {}
DATA_NOTES = [
    "Official data quirk (5 cases in the full non-live data, 2 sampled: parallel_multiple_87 "
    "kinematics.distance.initial_velocity, parallel_multiple_119 league_stats.get_top_scorer.league_name): "
    "possible_answer marks a parameter omittable (\"\") that the function schema lists as required. The official "
    "checker enforces `required` first, so omitting it fails; gold_minimal therefore keeps schema-required "
    "parameters (an earlier run that dropped them failed exactly these 2 items with "
    "simple_function_checker:missing_required).",
    "Official data quirk outside the sample (full-data check only): parallel_multiple_12 and parallel_multiple_26 "
    "list a parameter in possible_answer that the function schema does not define (permeability for "
    "calculate_voltage_difference; type for bank.calculate_balance), marked omittable. Passing it is rejected by "
    "the official checker (simple_function_checker:unexpected_param), so gold_first fails exactly these 2 of 1,240 "
    "entries while gold_minimal passes all 1,240.",
]
FULL_DATA_EXPLANATIONS = {
    "parallel_multiple_12": "possible_answer lists 'permeability' (omittable) for calculate_voltage_difference, "
                            "whose schema has no such parameter; official checker: unexpected_param",
    "parallel_multiple_26": "possible_answer lists 'type' (omittable) for bank.calculate_balance, whose schema "
                            "has no such top-level parameter; official checker: unexpected_param",
}


def pick(allowed, minimal):
    """Value to emit for a parameter (or dict key) whose allowed values are `allowed`; None = omit."""
    if minimal and "" in allowed:
        return None
    return next(((v,) for v in allowed if v != ""), None)


def render_dict(allowed_dict, minimal):
    out = {}
    for key, allowed in allowed_dict.items():
        chosen = pick(allowed, minimal) if isinstance(allowed, list) else (allowed,)
        if chosen is not None:
            out[key] = chosen[0]
    return out


def render_value(schema, value, minimal):
    ptype = schema.get("type")
    if ptype == "dict" and isinstance(value, dict):
        return render_dict(value, minimal)
    if ptype == "array" and schema.get("items", {}).get("type") == "dict" and isinstance(value, list):
        return [render_dict(v, minimal) if isinstance(v, dict) else v for v in value]
    return value


def render_calls(gold, minimal=False, reverse=False):
    schemas = {f["name"]: f for f in gold["function"]}
    calls = []
    for call in gold["ground_truth"]:
        (name, params), = call.items()
        props = schemas[name]["parameters"]["properties"]
        required = set(schemas[name]["parameters"].get("required", []))
        args = []
        for pname, allowed in params.items():
            chosen = pick(allowed, minimal and pname not in required)  # see DATA_NOTES
            if chosen is not None:
                args.append((pname, render_value(props.get(pname, {}), chosen[0], minimal)))
        calls.append((name, args))
    return calls[::-1] if reverse else calls


def fmt(calls, brackets=True):
    body = ", ".join(f"{name}({', '.join(f'{k}={v!r}' for k, v in args)})" for name, args in calls)
    return f"[{body}]" if brackets else body


def placeholder_call(gold):
    fn = gold["function"][0]
    props, required = fn["parameters"]["properties"], fn["parameters"].get("required", [])
    return fmt([(fn["name"], [(p, PLACEHOLDER.get(props[p]["type"], "x")) for p in required])])


def perturb(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1000003
    if isinstance(value, float):
        return value * 2 + 1.5
    if isinstance(value, str):
        return value + "_qq"
    if isinstance(value, list):
        return value + [value[0]] if value else ["qq"]
    if isinstance(value, dict):
        return {**value, "zz_extra": 1}
    return 1


def wrong_value(gold):
    calls = render_calls(gold)
    name, args = calls[0]
    if args:
        args = [(args[0][0], perturb(args[0][1]))] + args[1:]
    else:
        args = [("zz_unexpected", 1)]
    return fmt([(name, args)] + calls[1:])


EXPECT = {
    "gold_first": "pass all",
    "gold_minimal": "pass all",
    "gold_reorder": "pass all",
    "wrong_other_item": "fail all",
    "wrong_value": "fail all",
    "info_refusal": "AST categories fail; irrelevance passes (no call is the right answer there)",
    "info_fenced": "official: AST categories fail (decoder does not strip a ```python fence), irrelevance "
                   "passes; passed_lenient: pass all",
    "info_no_brackets": "pass all (the official decoder adds the missing outer brackets)",
}


def build_sets(items):
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it["gold"]["category"]].append(it)
    other = {its[i]["item"]: its[(i + 1) % len(its)] for its in by_cat.values() for i in range(len(its))}
    sets = {name: [] for name in EXPECT}
    for it in items:
        gold, irr = it["gold"], it["gold"]["category"] == "irrelevance"
        first = None if irr else fmt(render_calls(gold))
        responses = {
            "gold_first": NO_CALL_TEXT if irr else first,
            "gold_minimal": "[]" if irr else fmt(render_calls(gold, minimal=True)),
            "gold_reorder": "" if irr else fmt(render_calls(gold, reverse=True)),
            "wrong_other_item": placeholder_call(gold) if irr else fmt(render_calls(other[it["item"]]["gold"])),
            "wrong_value": placeholder_call(gold) if irr else wrong_value(gold),
            "info_refusal": "I cannot help with that.",
            "info_fenced": "```python\n" + (NO_CALL_TEXT if irr else first) + "\n```",
            "info_no_brackets": NO_CALL_TEXT if irr else fmt(render_calls(gold), brackets=False),
        }
        for name, text in responses.items():
            sets[name].append({"item": it["item"], "response": text})
    return sets


def sandbox_rows(items):
    """Hostile responses: the official decoder eval()s BinOp arguments, so these run inside the container."""
    first = next(it for it in items if it["gold"]["category"] == "simple_python")
    name = first["gold"]["function"][0]["name"]
    probe = HERE / "SANDBOX_ESCAPE_PROBE"
    return probe, [
        ("write_to_harness_dir", f"[{name}(base=__import__('pathlib').Path('/harness/{probe.name}').write_text('x') + 1)]"),
        ("open_network_socket", f"[{name}(base=__import__('socket').create_connection(('1.1.1.1', 80), 3) + 1)]"),
        ("runaway_arithmetic", f"[{name}(base=9**9**9**9 + 1, height=5)]"),
    ], first["item"]


def full_data_gold():
    """Same gold renderings over ALL 1,240 non-live entries (not only the sample), same container scorer."""
    ids = []
    for cat in CATEGORIES:
        with open(PKG_ROOT / f"bfcl_eval/data/BFCL_v4_{cat}.json", encoding="utf-8") as fh:
            ids += [json.loads(line)["id"] for line in fh if line.strip()]
    golds = run_core("prompts", json.dumps({"ids": ids}))
    out = {}
    for name, minimal in (("gold_first", False), ("gold_minimal", True)):
        rows = [{"item": g["item"], "response": NO_CALL_TEXT if g["category"] == "irrelevance"
                 else fmt(render_calls(g, minimal=minimal))} for g in golds]
        verdicts = run_core("score", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        fails = [{"item": v["item"], "error_type": v["error_type"], "error": v["error"],
                  "explanation": FULL_DATA_EXPLANATIONS.get(v["item"], "UNEXPLAINED")}
                 for v in verdicts if not v["passed"]]
        out[name] = {"n": len(verdicts), "passed": len(verdicts) - len(fails), "failures": fails}
    return out


def main():
    items = read_jsonl(HERE / "items.jsonl")
    by_id = {it["item"]: it for it in items}
    report = {"items": len(items), "scorer": "score.py (official bfcl-eval 2026.3.23 eval_runner path, in container)",
              "sets": {}, "gold_failures": [], "wrong_passes": [], "sandbox_checks": [], "data_notes": DATA_NOTES}
    for name, rows in build_sets(items).items():
        verdicts = score_rows(rows, by_id)
        per_cat = defaultdict(lambda: {"n": 0, "passed": 0, "passed_lenient": 0})
        for v in verdicts:
            for c in (v["category"], "ALL"):
                per_cat[c]["n"] += 1
                per_cat[c]["passed"] += v["passed"]
                per_cat[c]["passed_lenient"] += v["passed_lenient"]
        report["sets"][name] = {"expectation": EXPECT[name], **per_cat.pop("ALL"), "per_category": dict(per_cat)}
        for v, row in zip(verdicts, rows):
            if name.startswith("gold_") and not v["passed"]:
                report["gold_failures"].append({
                    "set": name, "item": v["item"], "error_type": v["error_type"], "error": v["error"],
                    "response": row["response"][:600],
                    "explanation": GOLD_FAILURE_EXPLANATIONS.get(v["item"], "UNEXPLAINED")})
            if name.startswith("wrong_") and v["passed"]:
                report["wrong_passes"].append({"set": name, "item": v["item"], "response": row["response"][:600]})
    probe, hostile, item_id = sandbox_rows(items)
    probe.unlink(missing_ok=True)
    for label, text in hostile:
        (v,) = score_rows([{"item": item_id, "response": text}], by_id)
        report["sandbox_checks"].append({"check": label, "passed": v["passed"], "error_type": v["error_type"],
                                         "error": (v["error"] or "")[:300]})
    report["sandbox_checks"].append({"check": "probe_file_absent_on_host", "ok": not probe.exists()})
    report["full_data_gold"] = full_data_gold()
    report["unexplained_gold_failures"] = sum(f["explanation"] == "UNEXPLAINED" for f in report["gold_failures"]) + sum(
        f["explanation"] == "UNEXPLAINED" for s in report["full_data_gold"].values() for f in s["failures"])
    (HERE / "selfcheck.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, s in report["sets"].items():
        print(f"{name:18s} passed {s['passed']:3d}/{s['n']}  lenient {s['passed_lenient']:3d}/{s['n']}  ({s['expectation']})")
    print(f"gold failures: {len(report['gold_failures'])} (unexplained {report['unexplained_gold_failures']}); "
          f"wrong passes: {len(report['wrong_passes'])}")
    for check in report["sandbox_checks"]:
        print("sandbox:", check)
    for name, s in report["full_data_gold"].items():
        print(f"full data {name}: {s['passed']}/{s['n']}", [f["item"] for f in s["failures"]])


if __name__ == "__main__":
    main()
