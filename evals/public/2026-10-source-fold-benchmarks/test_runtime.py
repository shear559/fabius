"""Synthetic runtime tests. No credentials, network, or real provider CLI calls."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import runtime as rt


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="fold-runtime-test-", dir="/private/tmp"))
        self.addCleanup(shutil.rmtree, self.base)
        for arm in ("old", "candidate"):
            source = self.base / arm
            (source / ".claude-plugin").mkdir(parents=True)
            (source / ".claude-plugin/plugin.json").write_text(json.dumps(
                {"name": "fabius", "version": "test"}))
            skill = source / "skills/fabius-disciplina"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("Synthetic " + arm)
            (source / "CORPUS.md").write_text("Synthetic source index")
            (skill / "example.py").write_text("# readable source data")
        self.raw = dict(study_root=str(self.base / "study"), scratch_root=str(self.base / "scratch"),
                        denied_roots=[str(self.base / "existing-study")], cli_path="/usr/bin/false",
                        model="synthetic-model", max_turns=3, timeout_s=1, termination_grace_s=1,
                        hard_call_cap=3, meter_max_age_s=60,
                        meter_ceilings={"five_hour": .8, "seven_day": .8},
                        plugin_sources={a: str(self.base / a) for a in ("old", "candidate")})
        self.manifest = {"study": "synthetic", "tasks": ["one"]}
        self.task = {"id": "bench/one", "prompt": "Read source.txt and answer.", "specialist": "disciplina",
                     "files": {"source.txt": "source content"}}

    def config(self, **changes):
        return rt.RuntimeConfig.from_mapping({**self.raw, **changes})

    def meter(self, now=1000):
        return {"observed_at": now, "info": {"status": "allowed", "unifiedWindows": {
            name: {"utilization": .2, "resetsAt": now + 1000} for name in ("five_hour", "seven_day")}}}

    def stream(self, *events):
        return rt.parse_stream(json.dumps(e) for e in events)

    def init(self, **changes):
        return {"type": "system", "subtype": "init", "model": "synthetic-model", "plugins": [],
                "tools": ["Read", "Skill"], "mcp_servers": [], "skills": [], **changes}

    def result(self, **changes):
        return {"type": "result", "subtype": "success", "is_error": False, "result": "answer",
                "usage": {"output_tokens": 7}, **changes}

    def test_configuration_requires_explicit_budgets(self):
        for key in ("max_turns", "timeout_s", "hard_call_cap", "meter_ceilings"):
            bad = dict(self.raw)
            del bad[key]
            with self.subTest(key=key), self.assertRaises(rt.RuntimeBlocked):
                rt.RuntimeConfig.from_mapping(bad)
        for change in ({"budget_authorized": "yes"}, {"timeout_s": float("nan")},
                       {"max_turns": True}, {"scratch_root": str(self.base / "../elsewhere")}):
            with self.assertRaises(rt.RuntimeBlocked):
                self.config(**change)

    def test_reject_old_or_protected_root_without_writes(self):
        for root in (self.base / "fabius-benchmark", self.base / "existing-study/child", self.base / "old"):
            with self.assertRaises(rt.RuntimeBlocked):
                self.config(study_root=str(root))
        existing = self.base / "already-there"
        existing.mkdir()
        (existing / "original").write_text("keep")
        with self.assertRaises(rt.RuntimeBlocked):
            rt.initialize_study(self.config(study_root=str(existing)), self.manifest)
        self.assertEqual(sorted(p.name for p in existing.iterdir()), ["original"])

    def test_no_authorization_means_no_process_and_no_attempt(self):
        with patch.object(rt.subprocess, "Popen") as process:
            with self.assertRaisesRegex(rt.RuntimeBlocked, "authorization"):
                rt.run_attempt(self.config(), self.manifest, self.task, "baseline")
            process.assert_not_called()
        self.assertFalse((self.base / "study").exists())

    def test_resume_hash_binds_manifest_task_and_plugin(self):
        cfg = self.config()
        binding = rt.initialize_study(cfg, self.manifest)
        self.assertEqual(binding, rt.initialize_study(cfg, self.manifest))
        with self.assertRaisesRegex(rt.RuntimeBlocked, "hash mismatch"):
            rt.initialize_study(cfg, {"changed": True})
        prepared = rt.prepare_attempt(cfg, self.manifest, self.task, "old")
        self.addCleanup(shutil.rmtree, prepared["sandbox"])
        with self.assertRaisesRegex(rt.RuntimeBlocked, "task hash mismatch"):
            rt.prepare_attempt(cfg, self.manifest, {**self.task, "prompt": "different"}, "candidate")
        (self.base / "old/skills/fabius-disciplina/SKILL.md").write_text("changed")
        with self.assertRaisesRegex(rt.RuntimeBlocked, "hash mismatch"):
            rt.initialize_study(cfg, self.manifest)

    def test_attempts_unique_filtered_and_same_task_invocation(self):
        cfg = self.config()
        prepared = []
        for arm in ("baseline", "old", "candidate", "old"):
            p = rt.prepare_attempt(cfg, self.manifest, self.task, arm)
            self.addCleanup(shutil.rmtree, p["sandbox"])
            prepared.append(p)
            cmd = rt.build_cli(cfg, p)
            for flag in ("--restricted", "--strict-mcp-config", "--no-session-persistence"):
                self.assertIn(flag, cmd)
            self.assertNotIn("--bare", cmd)
            self.assertNotIn("--dangerously-skip-permissions", cmd)
            self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project")
            self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Skill")
            self.assertEqual((p["cwd"] / "source.txt").read_text(), "source content")
            self.assertIn("Read(/" + str(cfg.study_root) + "/**)", cmd)
            if arm == "baseline":
                self.assertNotIn("--plugin-dir", cmd)
                self.assertEqual(cmd[2], self.task["prompt"])
            else:
                self.assertEqual(cmd[2], "/fabius:fabius-disciplina " + self.task["prompt"])
                self.assertFalse((p["plugin"] / "evals").exists())
                for name in (".claude-plugin/plugin.json", "CORPUS.md", "skills/fabius-disciplina/example.py"):
                    self.assertEqual((p["plugin"] / name).read_bytes(), (self.base / arm / name).read_bytes())
        self.assertEqual(len(set(p["attempt_dir"] for p in prepared)), 4)
        self.assertEqual(len(set(p["plugin"] for p in prepared if p["plugin"])), 3)
        self.assertEqual(len(set(p["task_sha256"] for p in prepared)), 1)

    def test_frozen_plugin_rejects_hooks_and_extra_paths(self):
        source = self.base / "old"
        (source / "evals").mkdir()
        with self.assertRaisesRegex(rt.RuntimeBlocked, "extra directory"):
            rt.initialize_study(self.config(), self.manifest)
        (source / "evals").rmdir()
        path = source / ".claude-plugin/plugin.json"
        value = json.loads(path.read_text())
        value["hooks"] = {}
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(rt.RuntimeBlocked, "hooks"):
            rt.initialize_study(self.config(), self.manifest)

    def test_unsupported_swe_and_scoring_fields_fail_before_attempt(self):
        for update in ({"profile": "swe"}, {"scorer_data": "secret"}, {"files": {"CLAUDE.md": "bad"}}):
            with self.assertRaises(rt.RuntimeBlocked):
                rt.prepare_attempt(self.config(), self.manifest, {**self.task, **update}, "baseline")

    def test_full_skill_names_and_router_invocations(self):
        for arm in ("old", "candidate"):
            router = self.base / arm / "skills/fabius"
            router.mkdir()
            (router / "SKILL.md").write_text("Synthetic router")
        cfg = self.config()
        for name, prefix in (("fabius", "/fabius "), ("fabius-disciplina", "/fabius:fabius-disciplina ")):
            task = {**self.task, "id": name, "specialist": name}
            p = rt.prepare_attempt(cfg, self.manifest, task, "old")
            self.addCleanup(shutil.rmtree, p["sandbox"])
            self.assertEqual(rt.build_cli(cfg, p)[2], prefix + task["prompt"])

    def test_missing_stale_unknown_and_exhausted_usage(self):
        cfg = self.config(budget_authorized=True)
        binding = rt.initialize_study(cfg, self.manifest)
        meters = [None, {}, self.meter(900), {"observed_at": 1000, "info": {}},
                  {"observed_at": 1000, "info": {"status": "rejected"}}]
        incomplete = self.meter()
        del incomplete["info"]["unifiedWindows"]["five_hour"]["utilization"]
        meters.append(incomplete)
        high = self.meter()
        high["info"]["unifiedWindows"]["seven_day"]["utilization"] = .8
        meters.append(high)
        for meter in meters:
            with self.subTest(meter=meter), self.assertRaises(rt.RuntimeBlocked):
                rt.reserve_call(cfg, binding, meter, now=1000)
        self.assertEqual(json.loads((cfg.study_root / "calls.json").read_text())["reservations"], [])

    def test_hard_cap_atomically_shared_by_controllers(self):
        cfg = self.config(budget_authorized=True, hard_call_cap=2)
        binding = rt.initialize_study(cfg, self.manifest)
        def reserve(_):
            try:
                return rt.reserve_call(cfg, binding, self.meter(), now=1000)
            except rt.RuntimeBlocked:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            reservations = list(pool.map(reserve, range(20)))
        count = sum(r is not None for r in reservations)
        self.assertGreater(count, 0)
        self.assertLessEqual(count, 2)
        for _ in range(2 - count):
            rt.reserve_call(cfg, binding, self.meter(), now=1000)
        with self.assertRaisesRegex(rt.RuntimeBlocked, "cap exhausted"):
            rt.reserve_call(cfg, binding, self.meter(), now=1000)

    def test_probe_requires_explicit_exception_and_is_once_only(self):
        cfg = self.config()
        binding = rt.initialize_study(cfg, self.manifest)
        with self.assertRaisesRegex(rt.RuntimeBlocked, "not authorized"):
            rt.reserve_call(cfg, binding, None, "probe", now=1000)
        authorized = self.config(probe_authorized=True)
        self.assertEqual(binding, rt.initialize_study(authorized, self.manifest))
        rt.reserve_call(authorized, binding, None, "probe", now=1000)
        with self.assertRaisesRegex(rt.RuntimeBlocked, "already consumed"):
            rt.reserve_call(authorized, binding, None, "probe", now=1000)
        with self.assertRaisesRegex(rt.RuntimeBlocked, "not authorized"):
            rt.reserve_call(authorized, binding, self.meter(), now=1000)
        with self.assertRaisesRegex(rt.RuntimeBlocked, "dedicated"):
            rt.run_attempt(authorized, self.manifest, self.task, "baseline", kind="probe")

    def test_missing_init_retained_even_for_timeout(self):
        summary = rt.summarize_attempt(self.stream(self.result()), exit_code=-15, timed_out=True,
                                       expected_model="synthetic-model", arm="baseline")
        self.assertEqual(summary["status"], "invalid")
        self.assertIn("missing_init", summary["issues"])
        self.assertEqual(summary["stop_reason"], "timeout")
        self.assertFalse(summary["outcome_ready"])

    def test_valid_caps_are_terminal_outcomes_without_retry(self):
        text = {"type": "assistant", "message": {"content": [{"type": "text", "text": "partial answer"}]}}
        for events, timed_out, code in (([self.init(), text], True, -15),
                                       ([self.init(), text, self.result(subtype="error_max_turns", is_error=True)], False, 1)):
            summary = rt.summarize_attempt(self.stream(*events), exit_code=code, timed_out=timed_out,
                                           expected_model="synthetic-model", arm="baseline")
            self.assertEqual(summary["status"], "outcome_limit")
            self.assertTrue(summary["outcome_ready"])
            self.assertIsNone(summary["pause_reason"])
        self.assertIsNone(rt.summarize_attempt(self.stream(self.init(), text), exit_code=-15, timed_out=True,
                           expected_model="synthetic-model", arm="baseline")["usage"])

    def test_provider_errors_do_not_become_cap_outcomes(self):
        for message, reason in (("Not logged in", "authentication"), ("Usage limit reached", "rate_limit"),
                                ("API Error overloaded", "provider_error")):
            summary = rt.summarize_attempt(self.stream(self.init()), exit_code=-15, timed_out=True,
                        expected_model="synthetic-model", arm="baseline", stderr_text=message)
            self.assertFalse(summary["outcome_ready"])
            self.assertEqual(summary["pause_reason"], reason)

    def test_wrong_skills_or_missing_tools_fail_init_gate(self):
        for skills in ([], ["unrelated:skill"], ["fabius:fabius-cohors"]):
            init = self.init(plugins=[{"name": "fabius", "path": "/private/tmp/plugin"}], skills=skills)
            summary = rt.summarize_attempt(self.stream(init, self.result()), exit_code=0, timed_out=False,
                        expected_model="synthetic-model", arm="candidate", expected_plugin="/private/tmp/plugin",
                        expected_skills=["fabius-disciplina"], required_skill="fabius-disciplina")
            self.assertFalse(summary["outcome_ready"])
            self.assertIn("unexpected_skill_inventory", summary["issues"])
        summary = rt.summarize_attempt(self.stream(self.init(tools=[]), self.result()), exit_code=0,
                    timed_out=False, expected_model="synthetic-model", arm="baseline")
        self.assertFalse(summary["outcome_ready"])

    def test_init_contamination_and_rate_limit_remain_invalid(self):
        parsed = self.stream(self.init(plugins=[{"name": "other"}], tools=["Bash"], memory_paths=["unexpected"]),
                             self.result(), {"type": "rate_limit_event", "rate_limit_info": {"status": "rejected"}})
        summary = rt.summarize_attempt(parsed, exit_code=0, timed_out=False,
                                       expected_model="synthetic-model", arm="baseline")
        for issue in ("baseline_plugin_contamination", "unexpected_tool_scope", "unexpected_memory_paths", "rate_limit_rejected"):
            self.assertIn(issue, summary["issues"])

    def test_missing_new_meter_invalidates_previous_admission(self):
        cfg = self.config(budget_authorized=True)
        binding = rt.initialize_study(cfg, self.manifest)
        rt.reserve_call(cfg, binding, self.meter(), now=1000)
        with patch.object(rt.time, "time", return_value=1001):
            rt._record_meter(cfg, binding, None)
        with self.assertRaises(rt.RuntimeBlocked):
            rt.reserve_call(cfg, binding, self.meter(), now=1001)

    def test_usage_from_final_result_only_no_fallback_answer(self):
        assistant = {"type": "assistant", "message": {"usage": {"output_tokens": 999, "input_tokens": 42},
                      "content": [{"type": "text", "text": "unfinished"}]}}
        summary = rt.summarize_attempt(self.stream(self.init(), assistant, self.result()), exit_code=0,
                                       timed_out=False, expected_model="synthetic-model", arm="baseline")
        self.assertEqual(summary["usage"], {"output_tokens": 7})
        self.assertEqual(summary["first_turn_prompt_tokens"], 42)
        partial = rt.summarize_attempt(self.stream(self.init(), assistant), exit_code=0, timed_out=False,
                                       expected_model="synthetic-model", arm="baseline")
        self.assertIsNone(partial["usage"])
        self.assertIsNone(partial["final_text"])

    def test_failed_read_is_not_delivered_and_success_is_hashed(self):
        calls = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "id": k, "input": {"file_path": "source.txt", "offset": 3, "limit": 2}}
            for k in ("denied", "good", "unreturned")]}}
        response = {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "denied", "is_error": True, "content": "permission denied"},
            {"type": "tool_result", "tool_use_id": "good", "content": "  3→one\n  4→two\n[output truncated]"}]}}
        denied, good, pending = self.stream(calls, response)["reads"]
        self.assertTrue(denied["returned"])
        self.assertFalse(denied["delivered"])
        self.assertTrue(good["delivered"])
        self.assertEqual(good["returned_line_ranges"], [[3, 4]])
        self.assertTrue(good["truncated"])
        self.assertEqual(good["text_sha256"], rt.hashlib.sha256(good["text"].encode()).hexdigest())
        self.assertFalse(pending["returned"])
        self.assertFalse(pending["delivered"])

    def test_successful_image_read_has_delivered_binary_evidence(self):
        call = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "id": "image", "input": {"file_path": "input/screenshot.png"}}]}}
        result = {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "image", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "synthetic"}}]}]}}
        read = self.stream(call, result)["reads"][0]
        self.assertTrue(read["delivered"])
        self.assertFalse(read["delivered_text"])
        self.assertEqual(read["non_text_blocks"][0]["type"], "image")
        self.assertEqual(len(read["non_text_blocks"][0]["sha256"]), 64)

    def test_generic_tool_requests_and_results_are_bound(self):
        call = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "id": "shell", "input": {"command": '/private/tmp/run "git status"'}},
            {"type": "tool_use", "name": "Write", "id": "denied", "input": {"file_path": "/forbidden", "content": "x"}}]}}
        result = {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "shell", "content": "clean"},
            {"type": "tool_result", "tool_use_id": "denied", "is_error": True, "content": "denied"}]}}
        shell, denied = self.stream(call, result)["tool_events"]
        self.assertEqual(shell["request_event_index"], 0)
        self.assertEqual(shell["result_event_index"], 1)
        self.assertFalse(shell["is_error"])
        self.assertEqual(shell["result_text"], "clean")
        self.assertEqual(shell["result_text_sha256"], rt.hashlib.sha256(b"clean").hexdigest())
        self.assertTrue(denied["is_error"])

    def test_actual_synthetic_process_no_provider(self):
        # /usr/bin/false is a real local executable, never a provider CLI.
        cfg = self.config(probe_authorized=True)
        outcome = rt.run_probe(cfg, self.manifest)
        summary = outcome["summary"]
        self.assertEqual(summary["exit_code"], 1)
        self.assertIn("missing_init", summary["issues"])
        directory = Path(outcome["attempt_dir"])
        self.assertTrue((directory / "stream.jsonl").exists())
        self.assertTrue((directory / "reservation.json").exists())
        command = json.loads((directory / "command.json").read_text())["argv"]
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--max-turns") + 1], "1")
        self.assertEqual(list((self.base / "scratch").iterdir()), [])
        self.assertIsNone(summary["usage"])
        self.assertEqual(rt.verify_receipt(directory)["task_sha256"], summary["task_sha256"])
        self.assertTrue(all(not Path(name).is_absolute() for name in rt.verify_receipt(directory)["files"]))

    def test_actual_synthetic_timeout_is_bounded_no_provider(self):
        binary = self.base / "synthetic-cli"
        binary.write_text("#!/usr/bin/python3\nimport time\ntime.sleep(30)\n")
        binary.chmod(0o755)
        cfg = self.config(cli_path=str(binary), probe_authorized=True, timeout_s=.1, termination_grace_s=1)
        outcome = rt.run_probe(cfg, self.manifest)
        self.assertTrue(outcome["summary"]["timed_out"])
        self.assertIn("missing_init", outcome["summary"]["issues"])
        self.assertLess(outcome["summary"]["elapsed_s"], 3)

    def test_meter_timestamp_is_actual_stream_receipt_not_process_completion(self):
        binary = self.base / "synthetic-meter-cli"
        binary.write_text("""#!/usr/bin/python3
import json, time
print(json.dumps({'type':'system','subtype':'init','model':'synthetic-model','tools':[],
 'plugins':[],'skills':[],'mcp_servers':[]}), flush=True)
print(json.dumps({'type':'rate_limit_event','rate_limit_info':{'status':'allowed','unifiedWindows':{
 n:{'utilization':0.2,'resetsAt':time.time()+1000} for n in ['five_hour','seven_day']}}}), flush=True)
time.sleep(.15)
print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'OK','usage':{'output_tokens':1}}))
""")
        binary.chmod(0o755)
        cfg = self.config(cli_path=str(binary), probe_authorized=True)
        before = time.time()
        outcome = rt.run_probe(cfg, self.manifest)
        after = time.time()
        summary = outcome["summary"]
        self.assertTrue(summary["outcome_ready"])
        self.assertGreaterEqual(summary["meter_observed_at"], before)
        self.assertLess(summary["meter_observed_at"], after - .10)
        ledger = json.loads((cfg.study_root / "calls.json").read_text())
        self.assertEqual(ledger["meter"]["observed_at"], summary["meter_observed_at"])
        self.assertEqual(rt.verify_receipt(outcome["attempt_dir"])["task_sha256"], summary["task_sha256"])

    def swe_config(self, **changes):
        return self.config(swe_max_turns=150, swe_timeout_s=2400,
            swe_config={"study_root": self.raw["study_root"], "scratch_root": self.raw["scratch_root"]}, **changes)

    def swe_row(self):
        return {"image": "synthetic@sha256:" + "a" * 64, "base_commit": "b" * 40,
                "problem_statement": self.task["prompt"]}

    def synthetic_repository(self, config, row, attempt_dir, snapshot_path=None, scratch_root=None):
        root = Path(scratch_root) / "workspace-synthetic"
        repo = root / "repo"
        repo.mkdir(parents=True)
        def git(*args):
            return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout.strip()
        git("init", "-q")
        (repo / "source.py").write_text("value = 1\n")
        git("add", "source.py")
        git("-c", "user.name=Synthetic", "-c", "user.email=demo@example.com", "commit", "-qm", "Synthetic fixture")
        wrapper = root / "run"
        wrapper.write_text("#!/bin/sh\n# synthetic-container\n")
        return {"profile": "swe_repository", "cwd": str(repo), "workspace_root": str(root),
                "scratch_root": str(scratch_root), "wrapper": str(wrapper), "container": "synthetic-container",
                "plugin_snapshot": str(snapshot_path) if snapshot_path else None,
                "prompt": row["problem_statement"] + "\n\n---\nRepository " + str(repo) + "; wrapper " + str(wrapper),
                "tools": rt.SWE_TOOLS, "allowed_tools": rt.SWE_TOOLS[:-1] + [f"Bash({wrapper}:*)"],
                "permission_mode": "dontAsk", "head": git("rev-parse", "HEAD"), "docker_run": []}

    def synthetic_finish(self, config, plan, attempt_dir):
        patch = subprocess.run(["git", "-C", plan["cwd"], "diff", plan["head"]],
                               check=True, capture_output=True, text=True).stdout
        destination = Path(attempt_dir) / "patch.diff"
        destination.write_text(patch)
        unfiltered = Path(attempt_dir) / "patch.unfiltered.diff"
        unfiltered.write_text(patch)
        return {"patch": str(destination), "patch_unfiltered": str(unfiltered), "container_stopped": True}

    def test_swe_real_git_patch_scoped_command_and_cap_cleanup(self):
        import swe_adapter
        binary = self.base / "synthetic-swe-cli"
        binary.write_text("""#!/usr/bin/python3
import json, sys
from pathlib import Path
args = sys.argv
plugin = args[args.index('--plugin-dir') + 1]
print(json.dumps({'type':'system','subtype':'init','model':'synthetic-model',
 'tools':args[args.index('--tools') + 1].split(','), 'plugins':[{'name':'fabius','path':plugin}],
 'skills':['fabius:fabius-disciplina'], 'mcp_servers':[]}))
Path('source.py').write_text('value = 2\\n')
print(json.dumps({'type':'result','subtype':'error_max_turns','is_error':True,
 'result':'implemented partial patch','usage':{'output_tokens':9}}))
""")
        binary.chmod(0o755)
        cfg = self.swe_config(cli_path=str(binary), budget_authorized=True)
        task = {**self.task, "files": {}, "profile": "swe"}
        with patch.object(swe_adapter, "prepare_repository", side_effect=self.synthetic_repository), \
             patch.object(swe_adapter, "finish_repository", side_effect=self.synthetic_finish) as finish:
            outcome = rt.run_attempt(cfg, self.manifest, task, "old", self.meter(time.time()), swe_row=self.swe_row())
        finish.assert_called_once()
        summary = outcome["summary"]
        self.assertEqual(summary["status"], "outcome_limit")
        self.assertTrue(summary["outcome_ready"])
        self.assertIn("+value = 2", Path(summary["repository_patch"]["patch"]).read_text())
        directory = Path(outcome["attempt_dir"])
        command = json.loads((directory / "command.json").read_text())
        args = command["argv"]
        plan = json.loads((directory / "execution-plan.json").read_text())
        self.assertEqual(command["cwd"], plan["cwd"])
        self.assertEqual(args[args.index("--max-turns") + 1], "150")
        self.assertIn("Bash(" + plan["wrapper"] + ":*)", args)
        self.assertIn("Edit(/" + plan["plugin_snapshot"] + "/**)", args)
        self.assertNotIn("--dangerously-skip-permissions", args)
        self.assertFalse(Path(plan["scratch_root"]).exists())
        receipt = rt.verify_receipt(directory)
        self.assertIn("patch.diff", receipt["files"])
        patch_path = directory / "patch.diff"
        patch_path.chmod(0o644)
        patch_path.write_text("corrupt patch")
        with self.assertRaisesRegex(rt.RuntimeBlocked, "hash mismatch: patch.diff"):
            rt.verify_receipt(directory)

    def test_swe_container_finishes_even_when_admission_fails(self):
        import swe_adapter
        cfg = self.swe_config(budget_authorized=True)
        task = {**self.task, "files": {}, "profile": "swe"}
        with patch.object(swe_adapter, "prepare_repository", side_effect=self.synthetic_repository), \
             patch.object(swe_adapter, "finish_repository", side_effect=self.synthetic_finish) as finish, \
             patch.object(rt.subprocess, "Popen", wraps=rt.subprocess.Popen) as process:
            with self.assertRaisesRegex(rt.RuntimeBlocked, "unknown"):
                rt.run_attempt(cfg, self.manifest, task, "baseline", None, swe_row=self.swe_row())
        finish.assert_called_once()
        # Synthetic Git setup uses subprocess; no CLI binary can have launched.
        self.assertFalse(any(call.args[0][0] == str(cfg.cli_path) for call in process.call_args_list))
        self.assertEqual(list((self.base / "scratch").iterdir()), [])

    def test_swe_metadata_and_config_fail_closed(self):
        with self.assertRaisesRegex(rt.RuntimeBlocked, "roots"):
            self.config(swe_max_turns=150, swe_timeout_s=2400, swe_config={"study_root": "/private/tmp/wrong"})
        task = {**self.task, "files": {}, "profile": "swe"}
        cfg = self.swe_config()
        for row in ({**self.swe_row(), "gold": "never"}, {**self.swe_row(), "problem_statement": "wrong"},
                    {**self.swe_row(), "image": "mutable:latest"}):
            with self.assertRaises(rt.RuntimeBlocked):
                rt.prepare_attempt(cfg, self.manifest, task, "baseline", swe_row=row)


if __name__ == "__main__":
    unittest.main()
