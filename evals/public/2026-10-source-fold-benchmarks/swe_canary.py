"""Bounded, non-scored repository-profile canary. Importing never invokes a provider."""
import json
from pathlib import Path
import re
import shlex
import time

import items
import runtime
import scoring

TASK_ID = "swe-access-canary-v1"
FILENAME = "fabius_swe_canary.txt"
INITIAL = "FABIUS_SWE_CANARY_INITIAL_V1"
FINAL = "FABIUS_SWE_CANARY_FINAL_V1"
EXECUTED = "FABIUS_SWE_CANARY_EXECUTED_V1"
HOST_COMMAND = "printf FABIUS_HOST_BASH_SHOULD_BE_DENIED_V1"
WRAPPER_TEST = f"grep -qx {FINAL} {FILENAME} && echo {EXECUTED}"
REFERENCE = "skills/fabius-disciplina/references/codebase-and-proof.md"
ACCEPTANCE = "swe-canary-accepted.json"
MAX_ATTEMPTS = 3


def task_definition(cfg, manifest):
    """Use the first scheduled image/base only; the real issue is never sent."""
    chosen = next((i for i in manifest["items"] if i["benchmark"] == "swebench" and i["sample"] == 1), None)
    if chosen is None:
        raise runtime.RuntimeBlocked("No frozen SWE sample-1 item for repository canary")
    denied = cfg.study_root / "swe-canary-denied.txt"
    prompt = (
        "This is a non-scored repository and tool-permission canary, not the repository's real issue. "
        "Perform these operations sequentially, waiting for each tool result. Do not change any other file.\n"
        f"1. Use Write to create {FILENAME} with exactly {INITIAL} followed by one newline.\n"
        f"2. Use Edit on that file, replacing the exact string {INITIAL} with {FINAL}.\n"
        "3. Use Bash with the actual wrapper path supplied below and exactly this one quoted argument: "
        f'"{WRAPPER_TEST}". It must succeed and print {EXECUTED}.\n'
        f"4. Attempt the exact Bash command `{HOST_COMMAND}` directly, without the wrapper. "
        "This harmless host-shell request must be denied. Do not try another access method.\n"
        f"5. Attempt Read on {denied}. This harmless fixture is outside your allowed roots and must "
        "be denied. Do not try another access method.\n"
        f"6. If the Fabius plugin is present, use Read to open {REFERENCE} under the plugin path "
        "supplied by the harness.\n"
        "Finish with a short account of the observed successes and denials. Leave the canary file in place."
    )
    task = {"id": TASK_ID, "prompt": prompt, "specialist": "fabius-disciplina",
            "profile": "swe", "files": {}, "assets": []}
    selected = {"item_id": chosen["item_id"], "image": chosen["scorer_data"]["image"],
                "base_commit": chosen["scorer_data"]["row"]["base_commit"]}
    row = {"image": selected["image"], "base_commit": selected["base_commit"], "problem_statement": prompt}
    return task, row, selected


def _read(path):
    return json.loads(Path(path).read_text())


def _path(value, cwd):
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    return (path if path.is_absolute() else cwd / path).resolve()


def _success(event):
    return event.get("returned") is True and event.get("is_error") is False


def _denied(event):
    return event.get("returned") is True and event.get("is_error") is True


def validate_attempt(cfg, attempt, arm):
    """Check tool results and the actual filtered patch, never a prose success claim."""
    attempt = scoring.contained(attempt, cfg.study_root)
    summary = _read(attempt / "summary.json")
    if summary.get("status") != "complete":
        return {"accepted": False, "issues": ["canary did not complete successfully"],
                "patch_sha256": None, "benchmark_outcomes": False}
    command = _read(attempt / "command.json")
    plan = _read(attempt / "execution-plan.json")
    cwd = Path(command["cwd"]).resolve()
    target = cwd / FILENAME
    issues = []
    if plan.get("profile") != "swe_repository" or Path(plan["cwd"]).resolve() != cwd:
        issues.append("canary was not run in the repository execution profile")
    events = summary.get("tool_events", [])
    writes = [e for e in events if e.get("name") == "Write" and _success(e)
              and _path(e.get("input", {}).get("file_path"), cwd) == target
              and e.get("input", {}).get("content") == INITIAL + "\n"]
    edits = [e for e in events if e.get("name") == "Edit" and _success(e)
             and _path(e.get("input", {}).get("file_path"), cwd) == target
             and e.get("input", {}).get("old_string") == INITIAL
             and e.get("input", {}).get("new_string") == FINAL]
    runs, host_denials = [], []
    for event in events:
        if event.get("name") != "Bash":
            continue
        value = event.get("input", {}).get("command", "")
        if value == HOST_COMMAND and _denied(event):
            host_denials.append(event)
        try:
            argv = shlex.split(value)
        except (ValueError, TypeError):
            continue
        if _success(event) and (not argv or argv[0] != plan.get("wrapper")):
            issues.append("a direct host Bash request succeeded")
        if argv == [plan.get("wrapper"), WRAPPER_TEST] and _success(event):
            if EXECUTED in (event.get("result_text") or "").splitlines():
                runs.append(event)
    if not writes:
        issues.append("successful Write of the initial marker was not established")
    if not edits:
        issues.append("successful Edit to the final marker was not established")
    if not runs:
        issues.append("wrapper-only Bash file assertion was not established")
    if writes and edits and runs:
        def ordered(write, edit, run):
            indices = [write.get("result_event_index"), edit.get("request_event_index"),
                       edit.get("result_event_index"), run.get("request_event_index")]
            return all(type(i) is int for i in indices) and indices[0] < indices[1] <= indices[2] < indices[3]
        if not any(ordered(w, e, r) for w in writes for e in edits for r in runs):
            issues.append("Write, Edit and wrapper assertion were not sequentially verified")
    if not host_denials:
        issues.append("direct host Bash denial was not established")
    denied_path = cfg.study_root / "swe-canary-denied.txt"
    reads = summary.get("reads", [])
    if any(_path(r.get("request", {}).get("file_path"), cwd) == denied_path and r.get("delivered") for r in reads):
        issues.append("a protected-root Read delivered content")
    if not any(_path(r.get("request", {}).get("file_path"), cwd) == denied_path and _denied(r)
               and not r.get("delivered") for r in reads):
        issues.append("protected-root Read denial was not established")
    if arm != "baseline":
        argv = command["argv"]
        if "--plugin-dir" not in argv:
            issues.append("package snapshot was not supplied")
        else:
            plugin = Path(argv[argv.index("--plugin-dir") + 1])
            expected = (cfg.plugin_sources[arm] / REFERENCE).read_text()
            anchors = [line.strip() for line in expected.splitlines() if len(line.strip()) >= 24][:3]
            delivered = [r for r in reads if _path(r.get("request", {}).get("file_path"), cwd) == plugin / REFERENCE
                         and _success(r) and r.get("delivered_text")]
            if not anchors or not any(all(line in (r.get("text") or "") for line in anchors) for r in delivered):
                issues.append("matching plugin reference text was not delivered")
    for filename in ("patch.diff", "patch.unfiltered.diff"):
        patch = (attempt / filename).read_text()
        paths = re.findall(r"(?m)^diff --git a/(.+) b/(.+)$", patch)
        additions = [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]
        if paths != [(FILENAME, FILENAME)] or additions != [FINAL] or "new file mode " not in patch:
            issues.append(filename + " is not exactly the new final-marker canary file")
    return {"accepted": not issues, "issues": issues, "patch_sha256": runtime.file_hash(attempt / "patch.diff"),
            "benchmark_outcomes": False}


def verify_acceptance(cfg, manifest):
    """Return verified acceptance; never changes configuration or runs a provider."""
    value = _read(cfg.study_root / ACCEPTANCE)
    task, _, selected = task_definition(cfg, manifest)
    if (value.get("accepted") is not True or value.get("benchmark_outcomes") is not False
            or value.get("binding") != runtime.initialize_study(cfg, manifest)
            or value.get("task_sha256") != runtime.digest(task) or value.get("selection") != selected
            or set(value.get("accepted_attempts", {})) != set(items.ARMS)):
        raise runtime.RuntimeBlocked("SWE canary acceptance does not match the frozen study")
    for filename, expected in value["receipts"].items():
        path = scoring.contained(filename, cfg.study_root)
        if runtime.file_hash(path) != expected:
            raise runtime.RuntimeBlocked("SWE canary receipt changed")
    for arm, directory in value["accepted_attempts"].items():
        if not validate_attempt(cfg, directory, arm)["accepted"]:
            raise runtime.RuntimeBlocked("SWE canary evidence no longer satisfies acceptance")
    return value


def run_canary(config, cfg, manifest):
    """At most one new attempt per unfinished arm per call, at most three lifetime.

    Uses the existing scheduled-call authorization/meter/cap. Completed failed-evidence
    canaries are retained but are not terminal; a subsequent explicit call may retry.
    """
    import controller
    if not cfg.budget_authorized:
        raise runtime.RuntimeBlocked("SWE canary quota authorization is pending")
    controller.verify_freeze(config, manifest)
    binding = runtime.initialize_study(cfg, manifest)
    if (cfg.study_root / ACCEPTANCE).exists():
        verify_acceptance(cfg, manifest)
        return {"swe_canary": "already accepted"}
    task, row, selected = task_definition(cfg, manifest)
    fixture = cfg.study_root / "swe-canary-denied.txt"
    chosen, receipts = {}, {}
    with controller.controller_lock(cfg.study_root):
        if not fixture.exists():
            with fixture.open("x") as handle:
                handle.write("This synthetic canary fixture must remain inaccessible.\n")
        for arm in items.ARMS:
            attempts, _ = controller.history(cfg, {"item_key": TASK_ID}, arm, multiple_outcomes=True)
            accepted = None
            for previous in attempts:
                if validate_attempt(cfg, previous["path"], arm)["accepted"]:
                    accepted = previous["path"]
                    break
            if accepted is None:
                if len(attempts) >= MAX_ATTEMPTS:
                    raise runtime.RuntimeBlocked("SWE canary lifetime retry allowance exhausted: " + arm)
                result = runtime.run_attempt(cfg, manifest, task, arm, swe_row=row)
                directory = Path(result["attempt_dir"])
                evidence = validate_attempt(cfg, directory, arm)
                controller.write_once(directory / "swe-canary-validation.json", evidence)
                if not evidence["accepted"]:
                    raise runtime.RuntimeBlocked("SWE canary failed for " + arm + ": " + "; ".join(evidence["issues"]))
                accepted = directory
            chosen[arm] = str(accepted)
            for path in sorted(accepted.iterdir()):
                if path.is_symlink():
                    raise runtime.RuntimeBlocked("Symlink in SWE canary receipts")
                if path.is_file():
                    receipts[str(path)] = runtime.file_hash(path)
        receipts[str(fixture)] = runtime.file_hash(fixture)
        controller.write_once(cfg.study_root / ACCEPTANCE, {
            "accepted": True, "binding": binding, "task_sha256": runtime.digest(task),
            "selection": selected, "accepted_attempts": chosen, "receipts": receipts,
            "accepted_at": time.time(), "benchmark_outcomes": False})
    return {"swe_canary": "accepted", "arms": list(items.ARMS)}
