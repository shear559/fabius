"""Offline synthetic tests; no provider, old results, or benchmark gold required."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import analysis
import items


class ItemTests(unittest.TestCase):
    def fixture(self, root):
        def write(name, value, jsonl=False):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(json.dumps(r)+"\n" for r in value) if jsonl else json.dumps(value))

        swe_ids = ["django__example-1", "sphinx-doc__example-2"]
        write("schedule.json", {
            "swebench": {"items": swe_ids}, "ifeval": {"items": ["143", "144"]},
            "humaneval": {"items": ["HumanEval_0", "HumanEval_1"]}})
        write("swebench-mini-official-rows.json", [
            {"instance_id": i, "problem_statement": "Fix example.", "patch": "PRIVATE_GOLD"} for i in swe_ids])
        write("swebench-validity.json", {i: {"valid": True} for i in swe_ids})
        write("swebench-image-digests.json", {i: "image@sha256:test" for i in swe_ids})
        write("ifeval/instruction_following_eval/data/input_data.jsonl", [
            {"key": i, "prompt": "Answer only yes.", "kwargs": ["PRIVATE_GOLD"]} for i in (143, 144)], True)
        write("humanevalplus/cache/HumanEvalPlus-v0.1.10.jsonl", [
            {"task_id": f"HumanEval/{i}", "prompt": "def f(): ...", "canonical_solution": "PRIVATE_GOLD"}
            for i in (0, 1, 32)], True)
        part_b = {}
        for benchmark in list(items.SKILLS)[3:]:
            ids = ["nested/1", "nested_1"]
            rows = []
            for ident in ids:
                prompt, gold = "Solve the example.", {"answer": "PRIVATE_GOLD"}
                if benchmark == "design2code":
                    png = f"screenshots/{ident}.png"
                    ref = f"refs/{ident}.html"
                    for name, data in ((png, b"test png"), (ref, b"PRIVATE_GOLD"), ("refs/rick.jpg", b"placeholder")):
                        path = root / "skills-bench" / benchmark / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                    prompt = "the PNG image file at /isolated/legacy/image.png (view it with your file-reading tool)"
                    gold = {"screenshot": png, "screenshot_sha256": items.digest(b"test png"),
                            "ref_html": ref, "ref_html_sha256": items.digest(b"PRIVATE_GOLD")}
                rows.append({"item": ident, "prompt": prompt, "gold": gold})
            write(f"skills-bench/{benchmark}/items.jsonl", rows, True)
            write(f"skills-bench/{benchmark}/source.json", {"sampling": {"ids": ids}})
            if benchmark not in ("longmemeval", "design2code"):
                part_b[benchmark] = {"items": ids}
        write("schedule-skills.json", part_b)

    def build(self, root):
        self.fixture(root)
        with patch.dict(items.COUNTS, {b: 2 for b in items.SKILLS}):
            return items.build_manifest(root)

    def test_manifest_selection_arms_and_privacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.build(root)
            with patch.dict(items.COUNTS, {b: 2 for b in items.SKILLS}):
                second = items.build_manifest(root)
            self.assertEqual(manifest, second)
            self.assertEqual(len(manifest["schedule"]), 24)
            self.assertEqual(set(i["benchmark"] for i in manifest["items"]), set(items.SKILLS))
            self.assertTrue(any(i["benchmark"] == "ifeval" and i["item_id"] == "143" for i in manifest["items"]))
            self.assertFalse(any(i["item_id"] == "HumanEval_32" for i in manifest["items"]))
            for item, block in zip(manifest["items"], manifest["schedule"]):
                self.assertEqual(set(block["arms"]), set(items.ARMS))
                tasks = [items.runtime_task(item) for _ in block["arms"]]
                self.assertEqual(tasks[0], tasks[1])
                self.assertEqual(tasks[1], tasks[2])
                self.assertNotIn("PRIVATE_GOLD", json.dumps(tasks))
                self.assertNotIn("scorer_data", tasks[0])
            self.assertTrue(items.verify_manifest(manifest))

    def test_nested_ids_are_not_flattened(self):
        self.assertNotEqual(items.item_key("x", "nested/1"), items.item_key("x", "nested_1"))
        self.assertNotEqual(items.item_key("x", "1", 1), items.item_key("x", "1", 2))

    def test_input_changes_break_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.build(root)
            target = root / "skills-bench/design2code/screenshots/nested/1.png"
            target.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Frozen source changed"):
                items.verify_manifest(manifest)

    def test_manifest_tampering_breaks_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.build(Path(directory))
            manifest["items"][0]["prompt"] = "different"
            with self.assertRaisesRegex(ValueError, "Manifest content hash"):
                items.verify_manifest(manifest)

    def test_freeze_refuses_input_root_and_overwrite(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as out:
            manifest = self.build(Path(data))
            with self.assertRaises(ValueError):
                items.write_manifest(manifest, Path(data)/"manifest.json")
            target = Path(out)/"manifest.json"
            items.write_manifest(manifest, target)
            items.write_manifest(manifest, target)
            altered = copy.deepcopy(manifest)
            altered["seed"] += 1
            with self.assertRaises(FileExistsError):
                items.write_manifest(altered, target)


def row(benchmark, ident, arm, value, sample=1):
    return {"benchmark": benchmark, "item_id": ident, "arm": arm, "sample": sample,
            "score" if benchmark == "design2code" else "passed": value}


class AnalysisTests(unittest.TestCase):
    def test_continuous_scores_do_not_become_ints(self):
        rows = [row("design2code", "a", "baseline", .10), row("design2code", "a", "candidate", .20),
                row("design2code", "b", "baseline", .90), row("design2code", "b", "candidate", .95)]
        result = analysis.compare(rows, "design2code", "candidate", "baseline")
        self.assertAlmostEqual(result["delta"], .075)
        self.assertAlmostEqual(result["mean_control"], .50)
        self.assertEqual(result["test"], "paired sign-flip")

    def test_missing_pair_is_not_zero(self):
        rows = [row("ifeval", "a", "baseline", 1), row("ifeval", "a", "candidate", 1),
                row("ifeval", "b", "baseline", 1)]
        result = analysis.compare(rows, "ifeval", "candidate", "baseline")
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["delta"], 0)
        self.assertEqual(result["missing_pair_count"], 1)
        self.assertEqual(analysis.verdict(result, 0), "INCOMPLETE")

    def test_swe_replicates_must_all_match(self):
        rows = [row("swebench", "a", "baseline", 1, 1), row("swebench", "a", "candidate", 1, 1),
                row("swebench", "a", "baseline", 0, 2)]
        result = analysis.compare(rows, "swebench", "candidate", "baseline")
        self.assertEqual(result["n"], 0)
        self.assertIsNone(result["delta"])

    def test_binary_fraction_is_rejected(self):
        with self.assertRaises(ValueError):
            analysis.compare([row("ifeval", "a", "candidate", .7)], "ifeval", "candidate", "baseline")

    def test_duplicate_outcomes_are_rejected(self):
        rows = [row("ifeval", "a", "candidate", 1)] * 2
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            analysis.compare(rows, "ifeval", "candidate", "baseline")

    def test_equivalence_never_applies_to_continuous(self):
        rows = [row("design2code", i, a, .8) for i in ("a", "b") for a in ("candidate", "baseline")]
        result = analysis.compare(rows, "design2code", "candidate", "baseline")
        self.assertEqual(analysis.verdict(result, 1), "INCONCLUSIVE")

    def test_binary_equivalence_needs_registered_interval(self):
        rows = [row("ifeval", str(i), a, 1) for i in range(500) for a in ("candidate", "baseline")]
        result = analysis.compare(rows, "ifeval", "candidate", "baseline")
        self.assertEqual(analysis.verdict(result, 1), "TIE")

    def test_family_keeps_all_planned_tests_even_when_empty(self):
        manifest = {"manifest_sha256": "fixture", "items": [
            {"benchmark": b, "item_id": "a", "sample": 1} for b in items.SKILLS]}
        result = analysis.analyze([], manifest)
        self.assertEqual(len(result["comparisons"]), 33)
        self.assertTrue(all(c["family_size"] == 33 and c["verdict"] == "INCOMPLETE" for c in result["comparisons"]))
        self.assertFalse(result["complete"])
        with self.assertRaises(ValueError):
            analysis.analyze([], manifest, {"partial": [["ifeval", "candidate", "baseline"]]})

    def test_exact_test_and_holm(self):
        self.assertEqual(analysis.mcnemar_exact(0, 0), 1)
        self.assertEqual(analysis.mcnemar_exact(4, 0), .125)
        self.assertEqual(analysis.holm([.01, .04, .03]), [.03, .06, .06])


if __name__ == "__main__":
    unittest.main()
