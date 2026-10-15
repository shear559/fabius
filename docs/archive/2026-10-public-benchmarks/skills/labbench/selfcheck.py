#!/usr/bin/env python3
"""Prove the LAB-Bench harness is right -> selfcheck.json. Usage: python selfcheck.py

1. provenance: pinned parquet sha256, chembench wheel sha256 + unpacked files == wheel bytes,
   vendored LAB-Bench files == git blobs of commit 998a8e0.
2. verbatim: every definition in official.py's verbatim block == the pinned upstream text.
3. differential: the UPSTREAM code (upstream_ref.py: zero_shot.py, evaluator.py, task.py, chembench,
   all executed from the pinned files) is run on all 707 eligible items and on 18 response variants
   x 220 sampled items; our prompts, options, letters, parsed answers, correct and sure must match.
4. outcomes: gold variants must pass, wrong variants must fail; score.py CLI run end to end.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
import zipfile
from pathlib import Path

os.environ.setdefault("TQDM_DISABLE", "1")  # upstream Evaluator.score_agent draws a tqdm bar per run

import pyarrow.parquet as pq  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import official  # noqa: E402
import prepare  # noqa: E402
import score  # noqa: E402
import upstream_ref  # noqa: E402

VENDOR = HERE / "vendor"
PINNED_GIT_BLOBS = {  # `git ls-tree -r 998a8e0a40cf116c80e1b0e7a805ebb5fb9fa838`
    "labbench/utils.py": "31fa14694ccea2fb7279a7905ad59fc90e91ee00",
    "labbench/zero_shot.py": "f6ec75100dbd5883a9a85bcd8aeac216b83a8db7",
    "labbench/evaluator.py": "1a9ffc47d86a8db6bc1a25e47e4958e7cc10536c",
    "ProtocolQA/task.py": "00d2a3c883a005851bed51566146a01764eb50f4",
    "SeqQA/task.py": "a9ef67d7894b931da4ae8f046bd2b41087c806e7",
    "ProtocolQA/protocolqa-v1-public.jsonl": "108c3cce20b9a19953ae13cb049fb9fb86b37112",
    "LICENSE": "7d4f96c54aa155a17387e64501c50b6a0469932c",
}

# name -> (builder(t, u, w, ideal), kind). t=correct letter, u=insufficient-info letter, w=a wrong letter
VARIANTS = {
    "gold_tag": (lambda t, u, w, x: f"[ANSWER]{t}[/ANSWER]", "gold"),
    "gold_cot": (lambda t, u, w, x: (
        f"Let me think step by step.\nOption ({w}) does not fit the protocol/sequence.\n"
        f"Option ({u}) is not needed: the question gives enough information.\n"
        f"Option ({t}) is consistent with every step: {x}\n\nTherefore:\n[ANSWER]{t}[/ANSWER]"), "gold"),
    "gold_bold_line": (lambda t, u, w, x: f"Reasoning...\n\n**Final answer:** [ANSWER]{t}[/ANSWER]", "gold"),
    "gold_tag_spaces": (lambda t, u, w, x: f"[ANSWER] {t} [/ANSWER]", "gold"),
    "gold_tag_with_text": (lambda t, u, w, x: f"[ANSWER]{t}. {x}[/ANSWER]", "gold"),
    "gold_bare_letter": (lambda t, u, w, x: t, "gold"),
    "wrong_tag": (lambda t, u, w, x: f"[ANSWER]{w}[/ANSWER]", "wrong"),
    "wrong_cot_praises_gold": (lambda t, u, w, x: (
        f"Option ({t}) looks tempting: {x}\nBut on balance I pick ({w}).\n[ANSWER]{w}[/ANSWER]"), "wrong"),
    "insufficient_tag": (lambda t, u, w, x: f"[ANSWER]{u}[/ANSWER]", "wrong"),
    "out_of_range_letter": (lambda t, u, w, x: "[ANSWER]Z[/ANSWER]", "wrong"),
    "untagged_prose": (lambda t, u, w, x: f"The correct answer is ({t}).", "unparsed"),
    "empty": (lambda t, u, w, x: "", "unparsed"),
    "bold_inside_tag": (lambda t, u, w, x: f"[ANSWER]**{t}**[/ANSWER]", "format"),
    "paren_inside_tag": (lambda t, u, w, x: f"[ANSWER]({t})[/ANSWER]", "format"),
    "lowercase_tags": (lambda t, u, w, x: f"[answer]{t}[/answer]", "format"),
    "lowercase_letter": (lambda t, u, w, x: f"[ANSWER]{t.lower()}[/ANSWER]", "format"),
    "option_word_inside_tag": (lambda t, u, w, x: f"[ANSWER]Option {t}[/ANSWER]", "format"),
    "two_tags_wrong_then_gold": (lambda t, u, w, x: (
        f"First guess: [ANSWER]{w}[/ANSWER]. On reflection the answer is [ANSWER]{t}[/ANSWER]."), "quirk"),
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def segment(path: Path, name: str) -> str:
    src = path.read_text()
    for node in ast.parse(src).body:
        if upstream_ref._node_name(node) == name:
            return ast.get_source_segment(src, node)
    raise KeyError(f"{name} not in {path}")


def letters_for(gold: dict) -> tuple[str, str, str, str]:
    t, u = gold["answer"], gold["insufficient"]
    w = next(c for c in official.ALPHABET[: gold["n_choices"]] if c not in (t, u))
    return t, u, w, gold["ideal"]


def provenance() -> dict:
    out = {}
    for subset, (rel, want) in prepare.FILES.items():
        out[f"parquet_{subset}_sha256_ok"] = sha256((HERE / "data" / "hf" / rel).read_bytes()) == want
    wheel = VENDOR / "chembench-0.3.0-py3-none-any.whl"
    out["chembench_wheel_sha256_ok"] = sha256(wheel.read_bytes()) == prepare.CHEMBENCH_WHEEL_SHA256
    with zipfile.ZipFile(wheel) as zf:
        out["chembench_unpacked_equals_wheel"] = all(
            zf.read(f"chembench/{f}") == (VENDOR / "chembench-0.3.0" / "chembench" / f).read_bytes()
            for f in ("constant.py", "utils.py", "prompter.py", "__init__.py"))
    out["labbench_files_equal_pinned_git_blobs"] = {
        rel: git_blob((upstream_ref.LB / rel).read_bytes()) == blob for rel, blob in PINNED_GIT_BLOBS.items()}
    return out


def verbatim() -> dict:
    mismatches = [name for name, (rel, upstream_name) in official.VERBATIM_SOURCES.items()
                  if segment(VENDOR / rel, upstream_name) != segment(HERE / "official.py", name)]
    return {"definitions": len(official.VERBATIM_SOURCES), "identical": len(official.VERBATIM_SOURCES) - len(mismatches),
            "mismatches": mismatches}


def run_upstream(up, rows: dict[str, tuple[str, dict]], responses: dict[str, str]) -> dict[str, dict]:
    """Upstream Evaluator.score_agent + BaseZeroShotAgent.run_task; the only addition is the per-item seed."""
    results, crashes = {}, set()
    for subset in ("ProtocolQA", "SeqQA"):
        class Seeded(up.tasks[subset].EvalInstance):
            def get_input_output(self):
                random.seed(f"{prepare.CHOICE_SEED}:{self.id}")
                return super().get_input_output()

        class CannedAgent(up.zero_shot.BaseZeroShotAgent):
            async def get_completion(self, text_prompt, figs):
                return responses[str(self.task_buffer[-1]["id"])]

        agent = CannedAgent(use_cot=True, open_answer=False)

        async def agent_fn(inp, agent=agent):
            try:
                return await agent.run_task(inp)
            except TypeError as e:  # upstream run_regex(pattern, None): would abort the whole upstream run
                if "expected string" not in str(e):
                    raise
                crashes.add(str(inp.id))
                return None

        ev = object.__new__(up.evaluator.Evaluator)
        ev.eval = up.evaluator.Eval(subset)
        ev.eval_set = [(row["subtask"], Seeded(**row)) for uid, (sub, row) in rows.items() if sub == subset]
        if not ev.eval_set:
            continue
        out = asyncio.run(ev.score_agent(agent_fn, n_threads=1))
        prompts = {str(t["id"]): t["text_prompt"] for t in agent.task_buffer}
        for iid, r in out["results"].items():
            uid = str(iid)
            results[uid] = {"prompt": prompts[uid], "choices": r["input"].choices, "target": r["target_choice"],
                            "unsure": r["unsure_choice"], "answer": r["agent_output"], "correct": bool(r["correct"]),
                            "sure": bool(r["sure"]), "crashed": uid in crashes}
    return results


def main() -> None:
    up = upstream_ref.load()
    items = [json.loads(line) for line in (HERE / "items.jsonl").read_text().split("\n") if line.strip()]
    source = json.loads((HERE / "source.json").read_text())
    rows = {}
    for subset, (rel, _) in prepare.FILES.items():
        for row in pq.read_table(HERE / "data" / "hf" / rel).to_pylist():
            rows[row["id"]] = (subset, row)
    excluded = {e["item"].split("/", 1)[1] for e in source["excluded"]}
    eligible = {uid: v for uid, v in rows.items() if uid not in excluded}

    # 3a. every eligible item: upstream prompt / options / letters == ours; items.jsonl == upstream
    up_all = run_upstream(up, eligible, dict.fromkeys(eligible, "[ANSWER]A[/ANSWER]"))
    mism = {"prompt": 0, "choices": 0, "letters": 0}
    for uid, (subset, row) in eligible.items():
        question = row["protocol"] + row["question"] if subset == "ProtocolQA" else row["question"]
        choices, t, u = official.shuffled_choices(uid, row["ideal"], row["distractors"], prepare.CHOICE_SEED)
        r = up_all[uid]
        mism["prompt"] += r["prompt"] != official.build_prompt(question, choices)
        mism["choices"] += r["choices"] != choices
        mism["letters"] += (r["target"], r["unsure"]) != (t, u)
    items_mism = sum(
        (up_all[it["item"].split("/", 1)[1]]["prompt"], up_all[it["item"].split("/", 1)[1]]["choices"],
         up_all[it["item"].split("/", 1)[1]]["target"], up_all[it["item"].split("/", 1)[1]]["unsure"])
        != (it["prompt"], it["gold"]["choices"], it["gold"]["answer"], it["gold"]["insufficient"]) for it in items)

    # 3b + 4. response variants on the sampled items: ours vs upstream, and outcome expectations
    uids = [it["item"].split("/", 1)[1] for it in items]
    sampled = {uid: rows[uid] for uid in uids}
    diff = {"answer": 0, "correct": 0, "sure": 0}
    diff_examples, report, problems = [], {}, []
    quirk_expected = sum(letters_for(it["gold"])[0] < letters_for(it["gold"])[2] for it in items)
    for name, (build, kind) in VARIANTS.items():
        responses = {uid: build(*letters_for(it["gold"])) for uid, it in zip(uids, items)}
        upr = run_upstream(up, sampled, responses)
        agg = {"passed": 0, "passed_lenient": 0, "chose_insufficient": 0, "parsed": 0, "upstream_would_crash": 0}
        for uid, it in zip(uids, items):
            ours, r = score.score_one(responses[uid], it["gold"]), upr[uid]
            for key, a, b in (("answer", ours["answer"], r["answer"]), ("correct", bool(ours["passed"]), r["correct"]),
                              ("sure", bool(ours["sure"]), r["sure"])):
                if a != b:
                    diff[key] += 1
                    diff_examples.append({"variant": name, "item": it["item"], "field": key, "ours": a, "upstream": b})
            for key in ("passed", "passed_lenient", "chose_insufficient", "parsed"):
                agg[key] += ours[key]
            agg["upstream_would_crash"] += r["crashed"]
        n = len(items)
        expect = {"gold": (n, n), "wrong": (0, 0), "unparsed": (0, 0), "format": (0, n),
                  "quirk": (quirk_expected, n)}[kind]
        ok = (agg["passed"], agg["passed_lenient"]) == expect
        if not ok:
            problems.append(f"{name}: passed/passed_lenient {agg['passed']}/{agg['passed_lenient']} != expected {expect}")
        report[name] = {"kind": kind, "example (t=C,u=B,w=A)": build("C", "B", "A", "<ideal option text>")[:120],
                        "n": n, **agg, "expected_passed/passed_lenient": list(expect), "ok": ok}

    # chance level: seeded uniformly random letters
    rng = random.Random(prepare.SAMPLE_SEED)
    rand = [score.score_one(f"[ANSWER]{rng.choice(official.ALPHABET[: it['gold']['n_choices']])}[/ANSWER]", it["gold"])
            for it in items]
    chance = {"observed_accuracy": round(sum(r["passed"] for r in rand) / len(rand), 4),
              "expected_accuracy_mean_1_over_k": round(sum(1 / it["gold"]["n_choices"] for it in items) / len(items), 4)}

    # score.py CLI end to end
    run_dir = HERE / "selfcheck_data"
    run_dir.mkdir(exist_ok=True)
    cli = {}
    for label, variant, want in (("gold", "gold_cot", 1), ("wrong", "wrong_cot_praises_gold", 0)):
        resp = run_dir / f"responses_{label}.jsonl"
        out = run_dir / f"scored_{label}.jsonl"
        build = VARIANTS[variant][0]
        resp.write_text("".join(json.dumps({"item": it["item"], "response": build(*letters_for(it["gold"]))}) + "\n"
                                for it in items))
        proc = subprocess.run([sys.executable, str(HERE / "score.py"), str(resp), str(out)], capture_output=True, text=True)
        scored = [json.loads(line) for line in out.read_text().split("\n") if line.strip()] if proc.returncode == 0 else []
        cli[label] = {"exit_code": proc.returncode, "rows": len(scored), "passed": sum(r["passed"] for r in scored),
                      "ok": proc.returncode == 0 and len(scored) == len(items)
                      and all(r["passed"] == want for r in scored)}

    prov, verb = provenance(), verbatim()
    prov_ok = all(v if isinstance(v, bool) else all(v.values()) for v in prov.values())
    differential_ok = not any(mism.values()) and items_mism == 0 and not any(diff.values())
    ok = (prov_ok and not verb["mismatches"] and differential_ok and not problems
          and all(c["ok"] for c in cli.values()) and sha256((HERE / "items.jsonl").read_bytes()) == source["items_jsonl_sha256"])
    gold = [v for v in report.values() if v["kind"] == "gold"]
    wrong = [v for v in report.values() if v["kind"] in ("wrong", "unparsed")]
    result = {
        "ok": ok,
        "summary": {
            "gold_pass_rate": round(sum(v["passed"] for v in gold) / sum(v["n"] for v in gold), 4),
            "wrong_pass_rate": round(sum(v["passed"] for v in wrong) / sum(v["n"] for v in wrong), 4),
            "gold_variants": len(gold), "wrong_variants": len(wrong), "items": len(items),
            "differential_mismatches_vs_upstream": sum(mism.values()) + items_mism + sum(diff.values()),
        },
        "provenance": prov,
        "verbatim_identity": verb,
        "differential_vs_upstream": {
            "eligible_items_checked": len(eligible), "mismatches_on_eligible": mism,
            "items_jsonl_rows_differing_from_upstream": items_mism,
            "variant_x_item_checks": len(VARIANTS) * len(items), "mismatches_on_variants": diff,
            "examples": diff_examples[:10],
        },
        "variants": report,
        "chance_level": chance,
        "score_py_cli": cli,
        "problems": problems,
        "explained_failures": [
            "No gold-answer failures: every gold variant passes on all items.",
            "format variants (bold/parenthesised/lowercase letter, lowercase tags, 'Option X' inside the tag) FAIL the "
            "official parser by design: chembench MCQ_REGEX_TEMPLATE_1 needs an uppercase letter directly inside "
            "[ANSWER]...[/ANSWER]; passed_lenient (secondary, not official) accepts them.",
            "upstream_would_crash counts outputs for which upstream prepare_mcq_answer returns None (untagged, no comma, "
            "no space, not one capital letter) and run_regex then raises TypeError, aborting the upstream run; "
            "score.py scores them as unparsed (answer null, passed 0, sure 1), the same way upstream scores every "
            "other unparsed output.",
            f"two_tags_wrong_then_gold passes officially only when the correct letter sorts first ({quirk_expected}/"
            f"{len(items)}): upstream sorts the set of tagged letters and keeps the first; multi_tag_conflict flags it.",
        ],
    }
    (HERE / "selfcheck.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["summary"]), "ok" if ok else "NOT OK", problems)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
