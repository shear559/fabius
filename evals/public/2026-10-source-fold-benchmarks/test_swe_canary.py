"""Synthetic tool/patch receipts only. No Docker, CLI, or provider calls."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import controller
import runtime
import swe_canary as canary


class SWECanaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.cfg = SimpleNamespace(study_root=self.root, budget_authorized=True,
                                   plugin_sources={a: self.root / "sources" / a for a in ("old", "candidate")})
        self.reference = "A first distinctive reference heading.\nA second distinctive rule for this canary.\nA third distinctive reference paragraph.\n"
        for source in self.cfg.plugin_sources.values():
            p = source / canary.REFERENCE
            p.parent.mkdir(parents=True)
            p.write_text(self.reference)
        self.manifest = {"items": [{"benchmark": "swebench", "sample": 1, "item_id": "example__repo-1",
                                    "scorer_data": {"image": "image@sha256:" + "a"*64,
                                                    "row": {"base_commit": "b"*40, "problem_statement": "REAL_ISSUE_MUST_NOT_BE_SENT"}}}]}

    def receipt(self, arm, suffix="1"):
        directory = self.root / "attempts" / arm / suffix
        directory.mkdir(parents=True)
        cwd = directory / "discarded-workspace" / "repo"
        wrapper = cwd.parent / "run"
        plugin = directory / "discarded-plugin"
        target = str(cwd / canary.FILENAME)
        def event(name, inp, request, result, text="", error=False):
            return {"name": name, "input": inp, "returned": True, "is_error": error,
                    "request_event_index": request, "result_event_index": result, "result_text": text}
        tools = [event("Write", {"file_path": target, "content": canary.INITIAL + "\n"}, 1, 2),
                 event("Edit", {"file_path": target, "old_string": canary.INITIAL, "new_string": canary.FINAL}, 3, 4),
                 event("Bash", {"command": f'{wrapper} "{canary.WRAPPER_TEST}"'}, 5, 6, canary.EXECUTED),
                 event("Bash", {"command": canary.HOST_COMMAND}, 7, 8, "Denied", True)]
        reads = [{"request": {"file_path": str(self.root / "swe-canary-denied.txt")},
                  "returned": True, "is_error": True, "delivered": False}]
        argv = []
        if arm != "baseline":
            argv = ["--plugin-dir", str(plugin)]
            reads.append({"request": {"file_path": str(plugin / canary.REFERENCE)}, "returned": True,
                          "is_error": False, "delivered_text": True, "text": self.reference})
        documents = {"summary.json": {"status": "complete", "tool_events": tools, "reads": reads},
                     "command.json": {"cwd": str(cwd), "argv": argv},
                     "execution-plan.json": {"profile": "swe_repository", "cwd": str(cwd), "wrapper": str(wrapper)}}
        for name, value in documents.items():
            (directory / name).write_text(json.dumps(value))
        (directory / "patch.diff").write_text(
            f"diff --git a/{canary.FILENAME} b/{canary.FILENAME}\nnew file mode 100644\n"
            f"--- /dev/null\n+++ b/{canary.FILENAME}\n@@ -0,0 +1 @@\n+{canary.FINAL}\n")
        (directory / "patch.unfiltered.diff").write_bytes((directory / "patch.diff").read_bytes())
        return directory

    def alter_summary(self, directory, change):
        path = directory / "summary.json"
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def test_uses_frozen_image_and_base_but_never_real_issue(self):
        task, row, selected = canary.task_definition(self.cfg, self.manifest)
        self.assertEqual(task["profile"], "swe")
        self.assertEqual(row["problem_statement"], task["prompt"])
        self.assertEqual(row["base_commit"], "b"*40)
        self.assertEqual(selected["image"], "image@sha256:" + "a"*64)
        self.assertNotIn("REAL_ISSUE_MUST_NOT_BE_SENT", json.dumps(task))

    def test_all_arms_require_genuine_tool_and_patch_evidence(self):
        for arm in ("baseline", "old", "candidate"):
            self.assertTrue(canary.validate_attempt(self.cfg, self.receipt(arm), arm)["accepted"])

    def test_prose_success_is_not_evidence(self):
        directory = self.receipt("baseline")
        self.alter_summary(directory, lambda s: s.update(tool_events=[], final_text="All checks succeeded"))
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_final_patch_and_operation_order_are_required(self):
        directory = self.receipt("baseline")
        self.alter_summary(directory, lambda s: s["tool_events"][1].update(request_event_index=1))
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])
        (directory / "patch.diff").write_text("+" + canary.FINAL)
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_successful_host_bash_is_a_failure(self):
        directory = self.receipt("baseline")
        self.alter_summary(directory, lambda s: s["tool_events"][3].update(is_error=False))
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_a_denial_does_not_hide_another_successful_host_call(self):
        directory = self.receipt("baseline")
        def append_success(summary):
            event = dict(summary["tool_events"][3], is_error=False)
            summary["tool_events"].append(event)
        self.alter_summary(directory, append_success)
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_filtered_patch_cannot_hide_extra_test_edits(self):
        directory = self.receipt("baseline")
        with (directory / "patch.unfiltered.diff").open("a") as handle:
            handle.write("diff --git a/tests/test_extra.py b/tests/test_extra.py\n+pass\n")
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_reference_claim_without_matching_content_is_a_failure(self):
        directory = self.receipt("old")
        self.alter_summary(directory, lambda s: s["reads"][1].update(text="I read the reference."))
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "old")["accepted"])

    def test_invalid_attempt_without_execution_plan_can_be_retried(self):
        directory = self.root / "incomplete"
        directory.mkdir()
        (directory / "summary.json").write_text(json.dumps({"status": "invalid"}))
        self.assertFalse(canary.validate_attempt(self.cfg, directory, "baseline")["accepted"])

    def test_no_budget_never_calls_provider(self):
        self.cfg.budget_authorized = False
        with patch.object(runtime, "run_attempt") as run:
            with self.assertRaisesRegex(runtime.RuntimeBlocked, "authorization"):
                canary.run_canary({}, self.cfg, self.manifest)
            run.assert_not_called()

    def test_accepted_run_is_reused_and_changed_receipt_is_rejected(self):
        directories = {arm: self.receipt(arm) for arm in ("baseline", "old", "candidate")}
        def history(cfg, item, arm, **kwargs):
            return [{"path": directories[arm]}], None
        with patch.object(controller, "verify_freeze"), patch.object(controller, "history", side_effect=history), \
                patch.object(runtime, "initialize_study", return_value={"frozen": "binding"}), \
                patch.object(runtime, "run_attempt") as run:
            result = canary.run_canary({}, self.cfg, self.manifest)
            self.assertEqual(result["swe_canary"], "accepted")
            self.assertEqual(canary.run_canary({}, self.cfg, self.manifest)["swe_canary"], "already accepted")
            run.assert_not_called()
            (directories["old"] / "patch.diff").write_text("changed")
            with self.assertRaisesRegex(runtime.RuntimeBlocked, "receipt changed"):
                canary.verify_acceptance(self.cfg, self.manifest)

    def test_three_semantic_failures_exhaust_lifetime_allowance(self):
        attempts = []
        for number in range(3):
            directory = self.receipt("baseline", str(number))
            self.alter_summary(directory, lambda s: s.update(tool_events=[]))
            attempts.append({"path": directory})
        with patch.object(controller, "verify_freeze"), patch.object(controller, "history", return_value=(attempts, None)), \
                patch.object(runtime, "initialize_study", return_value={"frozen": "binding"}), \
                patch.object(runtime, "run_attempt") as run:
            with self.assertRaisesRegex(runtime.RuntimeBlocked, "retry allowance exhausted"):
                canary.run_canary({}, self.cfg, self.manifest)
            run.assert_not_called()

    def test_completed_failed_evidence_canary_gets_one_bounded_retry(self):
        previous = self.receipt("baseline", "previous")
        self.alter_summary(previous, lambda s: s.update(tool_events=[]))
        replacement = self.receipt("baseline", "replacement")
        others = {arm: self.receipt(arm) for arm in ("old", "candidate")}
        def history(cfg, item, arm, **kwargs):
            return [{"path": previous if arm == "baseline" else others[arm]}], None
        with patch.object(controller, "verify_freeze"), patch.object(controller, "history", side_effect=history), \
                patch.object(runtime, "initialize_study", return_value={"frozen": "binding"}), \
                patch.object(runtime, "run_attempt", return_value={"attempt_dir": str(replacement)}) as run:
            self.assertEqual(canary.run_canary({}, self.cfg, self.manifest)["swe_canary"], "accepted")
            self.assertEqual(run.call_count, 1)
            args, kwargs = run.call_args
            self.assertEqual(args[3], "baseline")
            self.assertEqual(args[2]["profile"], "swe")
            self.assertEqual(kwargs["swe_row"]["problem_statement"], args[2]["prompt"])


if __name__ == "__main__":
    unittest.main()
