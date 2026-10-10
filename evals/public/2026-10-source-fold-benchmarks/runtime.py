"""Isolated, bounded Claude CLI attempts. Importing this module never calls a provider.

The hard cap counts CLI launches (including failures/probes), not the provider's
internal HTTP retries. max_turns is separately required. Raw receipts stay private.
No credential files are read here; subscription authentication remains the CLI's job.
"""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass


class RuntimeBlocked(ValueError):
    """A configuration, isolation, resume, or admission gate failed closed."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _under(path, parent):
    return path == parent or parent in path.parents


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _absolute(value):
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise RuntimeBlocked("paths must be explicit and absolute")
    path = Path(value)
    if any(part in {"..", ".claude", ".codex"} for part in path.parts):
        raise RuntimeBlocked("unsafe path")
    if path.resolve() != path:
        raise RuntimeBlocked("paths must be canonical, without symlinks")
    return path


@dataclass(frozen=True)
class RuntimeConfig:
    study_root: Path
    scratch_root: Path
    denied_roots: tuple
    cli_path: Path
    model: str
    max_turns: int
    timeout_s: float
    termination_grace_s: float
    hard_call_cap: int
    meter_max_age_s: float
    meter_ceilings: dict
    plugin_sources: dict
    budget_authorized: bool = False
    probe_authorized: bool = False
    swe_max_turns: int = None
    swe_timeout_s: float = None
    swe_config: dict = None

    @classmethod
    def from_mapping(cls, value):
        required = set(cls.__dataclass_fields__) - {"budget_authorized", "probe_authorized", "swe_max_turns", "swe_timeout_s", "swe_config"}
        if not isinstance(value, dict) or required - value.keys() or value.keys() - cls.__dataclass_fields__.keys():
            raise RuntimeBlocked("missing or unknown runtime configuration fields")
        cfg = dict(value)
        for key in ("study_root", "scratch_root", "cli_path"):
            cfg[key] = _absolute(cfg[key])
        if not isinstance(cfg["denied_roots"], list) or not cfg["denied_roots"]:
            raise RuntimeBlocked("explicit denied_roots are required")
        cfg["denied_roots"] = tuple(_absolute(p) for p in cfg["denied_roots"])
        if not isinstance(cfg["plugin_sources"], dict) or set(cfg["plugin_sources"]) != {"old", "candidate"}:
            raise RuntimeBlocked("old and candidate plugin sources required")
        cfg["plugin_sources"] = {k: _absolute(v) for k, v in cfg["plugin_sources"].items()}
        for key in ("max_turns", "hard_call_cap"):
            if type(cfg[key]) is not int or cfg[key] < 1:
                raise RuntimeBlocked(key + " must be an explicit positive integer")
        for key in ("timeout_s", "termination_grace_s", "meter_max_age_s"):
            if not _number(cfg[key]) or cfg[key] <= 0:
                raise RuntimeBlocked(key + " must be an explicit positive number")
        if not isinstance(cfg["model"], str) or not cfg["model"] or cfg["model"].startswith("-"):
            raise RuntimeBlocked("explicit model required")
        limits = cfg["meter_ceilings"]
        if not isinstance(limits, dict) or set(limits) != {"five_hour", "seven_day"} or any(
                not _number(v) or not 0 < v <= 1 for v in limits.values()):
            raise RuntimeBlocked("explicit fractional five_hour and seven_day ceilings required")
        for key in ("budget_authorized", "probe_authorized"):
            if key in cfg and type(cfg[key]) is not bool:
                raise RuntimeBlocked("authorization must be a boolean")
        swe = [cfg.get(k) for k in ("swe_max_turns", "swe_timeout_s", "swe_config")]
        if any(v is not None for v in swe):
            if type(swe[0]) is not int or swe[0] < 1 or not _number(swe[1]) or swe[1] <= 0 or not isinstance(swe[2], dict):
                raise RuntimeBlocked("SWE requires explicit turn/time limits and adapter config")
            if swe[2].get("study_root") != str(cfg["study_root"]) or swe[2].get("scratch_root") != str(cfg["scratch_root"]):
                raise RuntimeBlocked("SWE adapter roots must equal runtime roots")
        root, scratch = cfg["study_root"], cfg["scratch_root"]
        if root == Path(root.anchor) or "fabius-benchmark" in root.parts or any(
                _under(root, p) or _under(p, root) for p in (*cfg["denied_roots"], *cfg["plugin_sources"].values())):
            raise RuntimeBlocked("study root overlaps a protected or existing study/source root")
        if not _under(scratch, Path("/private/tmp")) or _under(root, scratch) or _under(scratch, root):
            raise RuntimeBlocked("scratch root must be isolated under /private/tmp")
        if any(_under(scratch, p) or _under(p, scratch) for p in (*cfg["denied_roots"], *cfg["plugin_sources"].values())):
            raise RuntimeBlocked("scratch root overlaps protected/source data")
        return cls(**cfg)

    def binding(self):
        # Budget authorization may be granted later without changing the experiment.
        return {k: ([str(p) for p in v] if k == "denied_roots" else
                    {a: str(p) for a, p in v.items()} if k == "plugin_sources" else
                    str(v) if isinstance(v, Path) else v)
                for k, v in self.__dict__.items() if k not in {"budget_authorized", "probe_authorized"}}


def _write_new(path, value):
    with open(path, "x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def _replace_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    try:
        _write_new(temporary, value)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _lock(root):
    # Nonblocking: callers retry by policy; this runtime never spins or waits for quota.
    with open(root / ".runtime.lock", "a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeBlocked("another controller holds the runtime lock") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _plugin_files(source):
    if not source.is_dir() or source.is_symlink():
        raise RuntimeBlocked("plugin source missing or symlinked")
    manifest = source / ".claude-plugin" / "plugin.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise RuntimeBlocked("plugin manifest missing")
    metadata = json.loads(manifest.read_text())
    if metadata.get("name") != "fabius":
        raise RuntimeBlocked("expected fabius plugin namespace")
    metadata_keys = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords", "skills"}
    if metadata.keys() - metadata_keys:
        raise RuntimeBlocked("plugin manifest contains hooks, MCP, or unsupported configuration")
    if "skills" in metadata and (not isinstance(metadata["skills"], list) or any(
            not isinstance(p, str) or not re.fullmatch(r"\./skills/fabius(?:-[a-z]+)?", p)
            for p in metadata["skills"])):
        raise RuntimeBlocked("plugin manifest contains external skill paths")
    # Sources must already be frozen packages. Preserve exact whitelist bytes;
    # scripts are readable source data, never executable with this tool profile.
    root_files = {"AGENTS.md", "ARCHITECTURE.md", "CORPUS.md", "LICENSE"}
    result = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or path.resolve() != path:
            raise RuntimeBlocked("symlink in plugin source")
        rel = path.relative_to(source)
        name = rel.as_posix()
        if path.is_dir():
            if rel.parts[0] not in {"skills", ".claude-plugin"} or rel.parts[0] == ".claude-plugin" and len(rel.parts) > 1:
                raise RuntimeBlocked("extra directory in frozen plugin source")
            continue
        if not path.is_file() or not (rel.parts[0] == "skills" or name in root_files or name == ".claude-plugin/plugin.json"):
            raise RuntimeBlocked("extra file in frozen plugin source")
        if any(p.lower() in {"evals", "gold", "raw", "outcomes", "results"} for p in rel.parts):
            raise RuntimeBlocked("evaluation material in plugin skill tree")
        result[name] = path.read_bytes()
    if not any(p.endswith("/SKILL.md") for p in result):
        raise RuntimeBlocked("plugin contains no skills")
    return result


def initialize_study(config, manifest):
    """Create an empty study once, or verify all resume bindings; no provider call."""
    hashes = {arm: digest({p: hashlib.sha256(b).hexdigest() for p, b in _plugin_files(src).items()})
              for arm, src in config.plugin_sources.items()}
    binding = {"manifest_sha256": digest(manifest), "config_sha256": digest(config.binding()),
               "cli_sha256": file_hash(config.cli_path),
               "runtime_sha256": file_hash(Path(__file__).resolve()),
               "plugin_sha256": hashes}
    if config.swe_config is not None:
        binding["swe_adapter_code"] = {name: file_hash(Path(__file__).resolve().with_name(name))
                                       for name in ("swe_adapter.py", "scoring.py")}
    root = config.study_root
    if root.exists():
        marker = root / "runtime-binding.json"
        if not marker.is_file() or marker.is_symlink():
            raise RuntimeBlocked("refusing to write an existing unbound study directory")
        if json.loads(marker.read_text()) != binding:
            raise RuntimeBlocked("resume manifest, config or plugin hash mismatch")
        if file_hash(root / "manifest.json") != file_hash_bytes_json(manifest):
            raise RuntimeBlocked("persisted manifest changed")
    else:
        root.mkdir(parents=True, exist_ok=False)
        _write_new(root / "manifest.json", manifest)
        _write_new(root / "runtime-binding.json", binding)
        _write_new(root / "calls.json", {"binding": binding, "reservations": [], "meter": None})
    return binding


def file_hash_bytes_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False).encode()).hexdigest()


def validate_meter(config, meter, now=None):
    """Require complete fresh provider windows; absence never means zero usage."""
    now = time.time() if now is None else now
    if not isinstance(meter, dict) or not _number(meter.get("observed_at")):
        raise RuntimeBlocked("current usage is unknown")
    age = now - meter["observed_at"]
    if age < 0 or age > config.meter_max_age_s:
        raise RuntimeBlocked("usage observation is stale or future-dated")
    info = meter.get("info")
    if not isinstance(info, dict) or info.get("status") not in {"allowed", "allowed_warning"}:
        raise RuntimeBlocked("usage status is missing, unknown, or rejected")
    windows = info.get("unifiedWindows")
    if not isinstance(windows, dict):
        raise RuntimeBlocked("usage windows missing")
    for name, ceiling in config.meter_ceilings.items():
        w = windows.get(name)
        if not isinstance(w, dict) or not _number(w.get("utilization")) or not 0 <= w["utilization"] <= 1:
            raise RuntimeBlocked("usage window is incomplete or unknown: " + name)
        if not _number(w.get("resetsAt")) or w["resetsAt"] <= now:
            raise RuntimeBlocked("usage window reset passed; refresh required: " + name)
        if w["utilization"] >= ceiling:
            raise RuntimeBlocked("usage ceiling reached: " + name)
    return meter


def reserve_call(config, binding, meter, kind="scheduled", now=None):
    """Atomically consume one launch slot. A slot is never refunded, even on failure."""
    if kind not in {"scheduled", "probe"}:
        raise RuntimeBlocked("unknown call kind")
    if kind == "scheduled" and not config.budget_authorized:
        raise RuntimeBlocked("scheduled provider calls are not authorized")
    if kind == "probe" and not config.probe_authorized:
        raise RuntimeBlocked("one-call quota probe is not authorized")
    now = time.time() if now is None else now
    with _lock(config.study_root):
        ledger_path = config.study_root / "calls.json"
        state = json.loads(ledger_path.read_text())
        if state.get("binding") != binding:
            raise RuntimeBlocked("call-ledger binding mismatch")
        reservations = state["reservations"]
        if len(reservations) >= config.hard_call_cap:
            raise RuntimeBlocked("hard CLI-launch cap exhausted")
        if kind == "probe" and any(x["kind"] == "probe" for x in reservations):
            raise RuntimeBlocked("one-call quota probe already consumed")
        latest = state.get("meter")
        if latest and (not meter or latest["observed_at"] >= meter.get("observed_at", -1)):
            meter = latest
        if kind == "scheduled":
            validate_meter(config, meter, now)
        reservation = {"id": uuid.uuid4().hex, "kind": kind, "reserved_at": now,
                       "ordinal": len(reservations) + 1}
        reservations.append(reservation)
        if meter:
            state["meter"] = meter
        _replace_json(ledger_path, state)
        return reservation


def _record_meter(config, binding, info, observed_at=None):
    with _lock(config.study_root):
        path = config.study_root / "calls.json"
        state = json.loads(path.read_text())
        if state.get("binding") != binding:
            raise RuntimeBlocked("call-ledger binding mismatch")
        # An attempt without a meter invalidates previous evidence. Never fall back.
        state["meter"] = {"observed_at": time.time() if info is None or observed_at is None else observed_at, "info": info}
        _replace_json(path, state)


def _task_name(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name or any(
            p.startswith(".") or p.lower() in {"claude.md", "agents.md", "gold", "evals", "outcomes", "raw"}
            for p in path.parts):
        raise RuntimeBlocked("unsafe task filename")
    return path


def _skill_name(name):
    if name == "fabius":
        return name
    if not isinstance(name, str) or not re.fullmatch(r"(?:fabius-)?[a-z]+", name):
        raise RuntimeBlocked("task-specific specialist name required")
    return name if name.startswith("fabius-") else "fabius-" + name


def _swe_row(config, task, row):
    if config.swe_config is None or config.swe_max_turns is None or config.swe_timeout_s is None:
        raise RuntimeBlocked("SWE repository profile requires explicit adapter configuration")
    if not isinstance(row, dict) or set(row) != {"image", "base_commit", "problem_statement"}:
        raise RuntimeBlocked("SWE row must contain only image, base_commit and problem_statement")
    if row["problem_statement"] != task["prompt"]:
        raise RuntimeBlocked("SWE issue differs from the frozen task prompt")
    if not isinstance(row["image"], str) or not re.fullmatch(r"[^\s]+@sha256:[a-f0-9]{64}", row["image"]):
        raise RuntimeBlocked("SWE image digest is not pinned")
    if not isinstance(row["base_commit"], str) or not re.fullmatch(r"[a-f0-9]{40}", row["base_commit"]):
        raise RuntimeBlocked("SWE base commit is not pinned")
    if task.get("files") or task.get("assets"):
        raise RuntimeBlocked("SWE inputs come only from the pinned repository adapter")
    return row


def prepare_attempt(config, manifest, task, arm, *, swe_row=None):
    """Make immutable receipt directory and isolated input/plugin snapshots."""
    if arm not in {"baseline", "old", "candidate"}:
        raise RuntimeBlocked("unknown arm")
    profile = task.get("profile", "read_only")
    if profile not in {"read_only", "swe", "swe_repository"}:
        raise RuntimeBlocked("unsupported execution profile; an actual execution adapter is required")
    if not isinstance(task.get("id"), str) or not isinstance(task.get("prompt"), str) or not task["prompt"]:
        raise RuntimeBlocked("task id and prompt required")
    specialist = _skill_name(task.get("specialist", ""))
    allowed = {"id", "prompt", "specialist", "files", "assets", "profile"}
    if task.keys() - allowed:
        raise RuntimeBlocked("task contains unrecognized fields (possibly scoring data)")
    if profile != "read_only":
        swe_row = _swe_row(config, task, swe_row)
    elif swe_row is not None:
        raise RuntimeBlocked("SWE metadata supplied to a non-SWE task")
    files = {}
    for name, content in task.get("files", {}).items():
        _task_name(name)
        if not isinstance(content, str):
            raise RuntimeBlocked("inline task files must contain text")
        files[name] = content.encode()
    for asset in task.get("assets", []):
        name = asset["path"]
        _task_name(name)
        source = _absolute(asset["source"])
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != asset["sha256"] or name in files:
            raise RuntimeBlocked("asset hash mismatch or duplicated task filename")
        files[name] = data
    task_binding = {k: v for k, v in task.items() if k not in {"files", "assets"}}
    task_binding["file_sha256"] = {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}
    if swe_row is not None:
        task_binding["swe_row_sha256"] = digest(swe_row)
    binding = initialize_study(config, manifest)
    plugin_data = _plugin_files(config.plugin_sources[arm]) if arm != "baseline" else {}
    plugin_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in plugin_data.items()}
    if arm != "baseline":
        if digest(plugin_hashes) != binding["plugin_sha256"][arm]:
            raise RuntimeBlocked("plugin changed after study binding")
        if "skills/" + specialist + "/SKILL.md" not in plugin_data:
            raise RuntimeBlocked("task specialist missing in filtered plugin")
    item_root = config.study_root / "attempts" / digest(task["id"])
    item_dir = item_root / arm
    with _lock(config.study_root):
        item_dir.mkdir(parents=True, exist_ok=True)
        item_binding = item_root / "task-binding.json"
        if item_binding.exists():
            if json.loads(item_binding.read_text()) != task_binding:
                raise RuntimeBlocked("resume task hash mismatch")
        else:
            _write_new(item_binding, task_binding)
        attempt_dir = item_dir / ("attempt-" + uuid.uuid4().hex)
        attempt_dir.mkdir(exist_ok=False)
    config.scratch_root.mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="fold-attempt-", dir=config.scratch_root))
    cwd = sandbox / "task"
    cwd.mkdir()
    for name, data in files.items():
        destination = cwd / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        destination.chmod(0o444)
    plugin = None
    if arm != "baseline":
        plugin = sandbox / ("plugin-" + arm)
        for name, data in plugin_data.items():
            destination = plugin / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod(0o444)
    prepared = {"attempt_dir": attempt_dir, "sandbox": sandbox, "cwd": cwd, "plugin": plugin,
                "binding": binding, "task_sha256": digest(task_binding), "arm": arm,
                "prompt": task["prompt"], "specialist": specialist, "profile": profile,
                "swe_row": swe_row, "expected_skills": sorted(p.split("/")[1] for p in plugin_data
                    if re.fullmatch(r"skills/[^/]+/SKILL.md", p))}
    _write_new(attempt_dir / "binding.json", {"study": binding, "task": task_binding,
               "arm": arm, "plugin_files": plugin_hashes, "task_sha256": prepared["task_sha256"]})
    return prepared


SWE_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "TodoWrite", "Skill", "Bash"]


def _bind_swe_plan(config, prepared, plan):
    """Accept only the frozen adapter's repository/wrapper boundary and prompt."""
    sandbox = prepared["sandbox"]
    repo, workspace, wrapper = (_absolute(plan[k]) for k in ("cwd", "workspace_root", "wrapper"))
    if (not _under(repo, workspace) or repo == workspace or not _under(workspace, sandbox) or
            workspace == sandbox or not _under(wrapper, workspace) or _under(wrapper, repo) or
            not repo.is_dir() or not wrapper.is_file() or wrapper.name != "run"):
        raise RuntimeBlocked("SWE adapter escaped the fresh repository/wrapper scope")
    plugin = prepared["plugin"]
    if plugin and (_under(plugin, repo) or _under(repo, plugin)):
        raise RuntimeBlocked("plugin snapshot must remain outside the editable repository")
    allowed = SWE_TOOLS[:-1] + ["Bash(" + str(wrapper) + ":*)"]
    if plan.get("profile") != "swe_repository" or plan.get("tools") != SWE_TOOLS or plan.get("allowed_tools") != allowed or plan.get("permission_mode") != "dontAsk":
        raise RuntimeBlocked("SWE adapter tool plan differs from the frozen profile")
    if plan.get("plugin_snapshot") != (str(plugin) if plugin else None) or plan.get("scratch_root") != str(sandbox):
        raise RuntimeBlocked("SWE adapter snapshot/scratch binding mismatch")
    if not isinstance(plan.get("prompt"), str) or not plan["prompt"].startswith(prepared["prompt"] + "\n\n---\n"):
        raise RuntimeBlocked("SWE adapter did not preserve the issue prompt")
    execution = {"normalized_prompt": plan["prompt"].replace(str(workspace), "<workspace>"),
                 "tools": plan["tools"], "allowed_tools": [p.replace(str(workspace), "<workspace>") for p in allowed],
                 "permission_mode": plan["permission_mode"], "head": plan["head"],
                 "wrapper_sha256": file_hash(wrapper)}
    # Wrapper contains a unique container id, so compare its normalized content.
    execution["wrapper_sha256"] = digest(wrapper.read_text().replace(plan["container"], "<container>"))
    common = prepared["attempt_dir"].parents[1] / "execution-binding.json"
    with _lock(config.study_root):
        if common.exists():
            if json.loads(common.read_text()) != execution:
                raise RuntimeBlocked("SWE normalized invocation changed across arms or resume")
        else:
            _write_new(common, execution)
    _write_new(prepared["attempt_dir"] / "execution-plan.json", plan)
    prepared.update(cwd=repo, prompt=plan["prompt"], swe_plan=plan)


def build_cli(config, prepared, kind="scheduled"):
    """Read+Skill only. Restricted mode confines file tools to cwd and selected plugin."""
    if kind not in {"scheduled", "probe"} or kind == "probe" and prepared["arm"] != "baseline":
        raise RuntimeBlocked("probe must be a no-plugin baseline call")
    invocation = "/fabius" if prepared["specialist"] == "fabius" else "/fabius:" + prepared["specialist"]
    prefix = "" if prepared["arm"] == "baseline" else invocation + " "
    swe = prepared.get("profile", "read_only") != "read_only"
    if swe and (kind != "scheduled" or "swe_plan" not in prepared):
        raise RuntimeBlocked("SWE command requires a prepared real repository plan")
    deny = ["WebFetch", "WebSearch", "Agent", "Read(//Users/**)",
            "Read(//private/var/folders/**)"]
    if not swe:
        deny += ["Bash", "Edit", "Write"]
    else:
        deny += ["Edit(//Users/**)", "Write(//Users/**)", "Edit(//private/var/folders/**)", "Write(//private/var/folders/**)"]
    for path in (config.study_root, *config.denied_roots, *config.plugin_sources.values()):
        deny += [tool + "(/" + str(path) + "/**)" for tool in ("Read", "Edit", "Write")]
    if prepared["plugin"]:
        deny += [tool + "(/" + str(prepared["plugin"]) + "/**)" for tool in ("Edit", "Write")]
    tools = "" if kind == "probe" else ",".join(SWE_TOOLS) if swe else "Read,Skill"
    turns = "1" if kind == "probe" else str(config.swe_max_turns if swe else config.max_turns)
    cmd = [str(config.cli_path), "-p", prefix + prepared["prompt"], "--model", config.model,
           "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
           "--no-session-persistence", "--restricted", "--no-chrome", "--output-format", "stream-json",
           "--verbose", "--tools", tools, "--permission-mode", "dontAsk",
           "--permission-prompts", "none", "--max-turns", turns,
           "--settings", '{"autoMemoryEnabled":false,"disableAllHooks":true}',
           "--disallowedTools", *deny]
    allowed = ["Read(/" + str(prepared["cwd"]) + "/**)", "Skill"]
    if swe:
        allowed += [tool + "(/" + str(prepared["cwd"]) + "/**)" for tool in ("Edit", "Write")]
        allowed += ["Glob", "Grep", "TodoWrite", "Bash(" + prepared["swe_plan"]["wrapper"] + ":*)"]
    if prepared["plugin"]:
        cmd += ["--add-dir", str(prepared["plugin"]), "--plugin-dir", str(prepared["plugin"])]
        allowed.append("Read(/" + str(prepared["plugin"]) + "/**)")
    if kind != "probe":
        cmd += ["--allowedTools", *allowed]
    return cmd


def parse_stream(lines):
    """Keep requested reads separate from actually returned content; never infer delivery."""
    out = {"init": None, "init_count": 0, "result": None, "meters": [], "errors": [], "tools": {}, "skills": [], "tool_events": [],
           "reads": [], "texts": [], "malformed_lines": 0, "first_turn_prompt_tokens": None}
    reads, tool_events = {}, {}
    for event_index, raw in enumerate(lines):
        try:
            event = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            if str(raw).strip():
                out["malformed_lines"] += 1
            continue
        if not isinstance(event, dict):
            out["malformed_lines"] += 1
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            out["init"] = event
            out["init_count"] += 1
        elif kind == "result":
            out["result"] = event
        elif kind == "rate_limit_event":
            out["meters"].append(event.get("rate_limit_info"))
        elif kind == "error":
            out["errors"].append(event)
        if kind not in {"assistant", "user"}:
            continue
        message = event.get("message") or {}
        if kind == "assistant" and out["first_turn_prompt_tokens"] is None and message.get("usage"):
            usage = message["usage"]
            values = [usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
            if all(_number(v) for v in values):
                out["first_turn_prompt_tokens"] = sum(values)
        for block in message.get("content", []) if isinstance(message.get("content", []), list) else []:
            if not isinstance(block, dict):
                continue
            if kind == "user" and block.get("type") == "tool_result" and block.get("tool_use_id") in tool_events:
                record = tool_events[block["tool_use_id"]]
                content = block.get("content")
                parts = [content] if isinstance(content, str) else [b["text"] for b in (content or [])
                         if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
                text = "\n".join(parts)
                record.update(returned=True, result_event_index=event_index, is_error=block.get("is_error", False) is not False,
                              result_text=text, result_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                              result_sha256=digest(content))
            if kind == "assistant" and block.get("type") == "tool_use":
                name, inp = block.get("name"), block.get("input") or {}
                out["tools"][name] = out["tools"].get(name, 0) + 1
                record = {"tool_use_id": block.get("id"), "name": name, "input": inp,
                          "request_event_index": event_index, "returned": False, "is_error": None,
                          "result_text": None, "result_text_sha256": None, "result_sha256": None}
                out["tool_events"].append(record)
                tool_events[block.get("id")] = record
                if name == "Skill":
                    out["skills"].append(inp)
                if name == "Read":
                    record = {"tool_use_id": block.get("id"), "request": inp, "returned": False,
                              "is_error": None, "delivered": False, "text": None, "text_sha256": None,
                              "returned_line_ranges": [], "truncated": None}
                    out["reads"].append(record)
                    reads[block.get("id")] = record
            elif kind == "assistant" and block.get("type") == "text":
                out["texts"].append(block.get("text", ""))
            elif kind == "user" and block.get("type") == "tool_result" and block.get("tool_use_id") in reads:
                record = reads[block["tool_use_id"]]
                content = block.get("content")
                texts = [content] if isinstance(content, str) else [b["text"] for b in (content or [])
                         if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
                text = "\n".join(texts)
                other = [b for b in content if isinstance(b, dict) and b.get("type") != "text"] if isinstance(content, list) else []
                is_error = block.get("is_error", False) is not False
                record.update(returned=True, is_error=is_error, delivered=bool(text or other) and not is_error,
                              delivered_text=bool(text) and not is_error,
                              text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest())
                nums = [int(n) for n in re.findall(r"(?m)^\s*(\d+)\s*(?:→|\t)", text)]
                ranges = []
                for n in nums:
                    if ranges and n == ranges[-1][1] + 1:
                        ranges[-1][1] = n
                    else:
                        ranges.append([n, n])
                record["returned_line_ranges"] = ranges
                # None means the stream cannot establish whether the host clipped it.
                record["truncated"] = True if re.search(r"\[(?:output|content) truncated[^\]]*\]|<persisted-output>", text, re.I) else None
                if isinstance(content, list):
                    record["non_text_blocks"] = [{"type": b.get("type"), "sha256": digest(b)} for b in other]
                metadata = event.get("tool_use_result")
                if isinstance(metadata, dict):
                    record["host_metadata"] = metadata
                    file = metadata.get("file")
                    if isinstance(file, dict) and type(file.get("startLine")) is int and type(file.get("numLines")) is int:
                        record["host_returned_range"] = [file["startLine"], file["startLine"] + file["numLines"] - 1]
                    if type(metadata.get("truncated")) is bool:
                        record["truncated"] = metadata["truncated"]
    return out


def summarize_attempt(parsed, *, exit_code, timed_out, expected_model, arm, launch_error=None,
                      expected_plugin=None, expected_tools=None, expected_skills=None,
                      required_skill=None, stderr_text=""):
    init, result = parsed["init"], parsed["result"]
    issues = []
    if init is None:
        issues.append("missing_init")
    elif init.get("model") != expected_model:
        issues.append("model_mismatch")
    if parsed.get("init_count", int(init is not None)) != 1:
        issues.append("init_count_mismatch")
    if init:
        plugins = init.get("plugins")
        if arm == "baseline" and plugins:
            issues.append("baseline_plugin_contamination")
        if arm != "baseline" and not plugins:
            issues.append("missing_plugin_init")
        if arm != "baseline" and plugins:
            if any(not isinstance(p, dict) or p.get("name") != "fabius" for p in plugins) or len(plugins) != 1:
                issues.append("unexpected_plugin_init")
            elif expected_plugin and plugins[0].get("path") != str(expected_plugin):
                issues.append("plugin_path_mismatch")
        expected_tools = {"Read", "Skill"} if expected_tools is None else set(expected_tools)
        if not isinstance(init.get("tools"), list) or set(init["tools"]) != expected_tools:
            issues.append("unexpected_tool_scope")
        skills = init.get("skills")
        if not isinstance(skills, list) or any(not isinstance(s, str) for s in skills):
            issues.append("missing_skill_inventory")
        else:
            namespaced = [s for s in skills if ":" in s or s == "fabius" or s.startswith("fabius-")]
            package_skills = [s.removeprefix("fabius:") for s in namespaced if s.startswith("fabius:") or s == "fabius" or s.startswith("fabius-")]
            if arm == "baseline" and namespaced:
                issues.append("baseline_skill_contamination")
            if arm != "baseline":
                if expected_skills is None or sorted(package_skills) != sorted(expected_skills) or len(namespaced) != len(package_skills):
                    issues.append("unexpected_skill_inventory")
                if required_skill and required_skill not in package_skills:
                    issues.append("missing_owner_skill")
        if init.get("mcp_servers"):
            issues.append("unexpected_mcp_servers")
        if init.get("memory_paths"):
            issues.append("unexpected_memory_paths")
    trusted_init = not issues
    cap = "timeout" if timed_out else "max_turns" if result and result.get("subtype") == "error_max_turns" else None
    if launch_error:
        issues.append("launch_error")
    if exit_code != 0 and not cap:
        issues.append("nonzero_exit")
    if result is None and not cap:
        issues.append("missing_result")
    elif result and result.get("subtype") not in {"success", "error_max_turns"}:
        issues.append("result_error")
    elif result and result.get("is_error") and not cap:
        issues.append("result_error")
    meter = parsed["meters"][-1] if parsed["meters"] else None
    if isinstance(meter, dict) and meter.get("status") == "rejected":
        issues.append("rate_limit_rejected")
    pause_reason = "rate_limit" if "rate_limit_rejected" in issues else None
    error_text = stderr_text + " " + json.dumps(parsed["errors"])
    if result and (result.get("is_error") or result.get("api_error_status")):
        error_text += " " + json.dumps(result)
    if re.search(r"not logged in|authentication failed|unauthorized|invalid api key|oauth.{0,30}expired", error_text, re.I):
        pause_reason = "authentication"
        issues.append("authentication_error")
    elif re.search(r"usage limit|hit your limit|weekly limit|rate.?limit|limit reached", error_text, re.I):
        pause_reason = "rate_limit"
        issues.append("provider_limit")
    elif (result and result.get("api_error_status")) or re.search(r"overloaded|API Error|internal server error|connection error", error_text, re.I):
        pause_reason = "provider_error"
        issues.append("provider_error")
    if parsed["errors"]:
        issues.append("stream_error")
    if parsed["malformed_lines"]:
        issues.append("malformed_stream")
    outcome = trusted_init and not issues
    final_text = result.get("result") if result else None
    text_source = "result" if final_text is not None else None
    if outcome and cap and final_text is None:
        final_text = parsed["texts"][-1] if parsed["texts"] else ""
        text_source = "last_assistant_on_limit" if parsed["texts"] else "blank_on_limit"
    return {**parsed, "status": "outcome_limit" if outcome and cap else "complete" if outcome else "invalid", "issues": issues,
            "outcome_ready": outcome, "stop_reason": cap, "pause_reason": pause_reason,
            "exit_code": exit_code, "timed_out": timed_out, "launch_error": launch_error,
            "usage": result.get("usage") if result else None,
            "model_usage": result.get("modelUsage") if result else None,
            "final_text": final_text, "final_text_source": text_source, "meter": meter}


def _capture_stdout(pipe, output, observation):
    """Drain continuously so receipt time, including during a long SWE run, is real."""
    try:
        for raw in iter(pipe.readline, b""):
            received_at = time.time()
            output.write(raw)
            output.flush()
            try:
                event = json.loads(raw)
            except (ValueError, UnicodeError):
                continue
            if isinstance(event, dict) and event.get("type") == "rate_limit_event":
                observation["meter"] = {"observed_at": received_at, "info": event.get("rate_limit_info")}
    except (OSError, ValueError) as exc:
        observation["error"] = type(exc).__name__


RECEIPT_REQUIRED = {"binding.json", "command.json", "reservation.json", "summary.json", "stream.jsonl", "stderr.txt"}
RECEIPT_OPTIONAL = {"patch.diff", "patch.unfiltered.diff", "patch-receipt.json", "execution-plan.json",
                    "workspace.json", "container-termination.json", "repository-finish-error.json"}


def seal_attempt(directory, summary):
    """Seal actual attempt bytes once; controller checkpoints can pin the receipt itself."""
    directory = Path(directory)
    required = set(RECEIPT_REQUIRED)
    if summary.get("repository_patch") is not None:
        required |= {"patch.diff", "patch.unfiltered.diff", "patch-receipt.json"}
    if any(not (directory / name).is_file() for name in required):
        raise RuntimeBlocked("cannot seal an incomplete attempt")
    names = required | {name for name in RECEIPT_OPTIONAL if (directory / name).is_file()}
    receipt = {"schema_version": 1, "task_sha256": summary["task_sha256"],
               "manifest_sha256": summary["manifest_sha256"],
               "files": {name: file_hash(directory / name) for name in sorted(names)}}
    _write_new(directory / "receipt.json", receipt)
    for name in names | {"receipt.json"}:
        (directory / name).chmod(0o444)
    return receipt


def verify_receipt(directory):
    """Fail closed on edited bytes, missing required files, or unsafe receipt entries."""
    directory = Path(directory).resolve()
    receipt = json.loads((directory / "receipt.json").read_text())
    files = receipt.get("files")
    if receipt.get("schema_version") != 1 or not isinstance(files, dict) or not RECEIPT_REQUIRED <= files.keys():
        raise RuntimeBlocked("incomplete attempt receipt")
    for name, expected in files.items():
        if name not in RECEIPT_REQUIRED | RECEIPT_OPTIONAL:
            raise RuntimeBlocked("unsafe or unexpected receipt path")
        path = directory / name
        if path.is_symlink() or not path.is_file() or file_hash(path) != expected:
            raise RuntimeBlocked("attempt receipt hash mismatch: " + name)
    summary = json.loads((directory / "summary.json").read_text())
    binding = json.loads((directory / "binding.json").read_text())
    if (receipt["task_sha256"] != summary["task_sha256"] or receipt["task_sha256"] != binding["task_sha256"] or
            receipt["manifest_sha256"] != summary["manifest_sha256"] or
            receipt["manifest_sha256"] != binding["study"]["manifest_sha256"]):
        raise RuntimeBlocked("attempt receipt study/task binding mismatch")
    if summary.get("repository_patch") is not None and not {"patch.diff", "patch.unfiltered.diff", "patch-receipt.json"} <= files.keys():
        raise RuntimeBlocked("SWE patch missing from attempt receipt")
    return receipt


def run_attempt(config, manifest, task, arm, meter=None, kind="scheduled", *, swe_row=None):
    """Exactly one bounded CLI attempt; no retry loop and no automatic quota probe."""
    if not (config.budget_authorized if kind == "scheduled" else kind == "probe" and config.probe_authorized):
        raise RuntimeBlocked("provider-call authorization pending")
    if kind == "probe" and (arm != "baseline" or task != quota_probe_task()):
        raise RuntimeBlocked("probe exception only permits the dedicated no-tools quota probe")
    prepared = prepare_attempt(config, manifest, task, arm, swe_row=swe_row)
    directory = prepared["attempt_dir"]
    plan, summary, patch_receipt, finish_error = None, None, None, None
    swe = prepared["profile"] != "read_only"
    try:
        try:
            if swe:
                import swe_adapter
                plan = swe_adapter.prepare_repository(config.swe_config, prepared["swe_row"], directory,
                                                       prepared["plugin"], scratch_root=prepared["sandbox"])
                _bind_swe_plan(config, prepared, plan)
            # Admission follows potentially slow repository preparation, immediately before launch.
            reservation = reserve_call(config, prepared["binding"], meter, kind)
            _write_new(directory / "reservation.json", reservation)
            command = build_cli(config, prepared, kind)
            _write_new(directory / "command.json", {"argv": command, "cwd": str(prepared["cwd"])})
            # Subscription authentication belongs to the CLI; no API credentials are copied.
            env = {k: os.environ[k] for k in ("HOME", "PATH", "TMPDIR", "SHELL", "LANG", "LC_ALL", "TERM")
                   if k in os.environ}
            env.update(CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
            started = time.monotonic()
            timed_out, code, error = False, None, None
            observation = {}
            with open(directory / "stream.jsonl", "xb") as stdout, open(directory / "stderr.txt", "x") as stderr:
                process = None
                collector = None
                try:
                    process = subprocess.Popen(command, cwd=prepared["cwd"], env=env, stdin=subprocess.DEVNULL,
                                               stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
                    collector = threading.Thread(target=_capture_stdout, args=(process.stdout, stdout, observation), daemon=True)
                    collector.start()
                    try:
                        code = process.wait(timeout=config.swe_timeout_s if swe else config.timeout_s)
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            code = process.wait(timeout=config.termination_grace_s)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            code = process.wait(timeout=config.termination_grace_s)
                except OSError as exc:
                    error = type(exc).__name__
                finally:
                    if process is not None and process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=config.termination_grace_s)
                    if collector is not None:
                        collector.join(timeout=config.termination_grace_s)
                        if collector.is_alive():
                            observation["error"] = "stdout did not close after process shutdown"
                            os.close(process.stdout.fileno())
                        else:
                            process.stdout.close()
            with open(directory / "stream.jsonl") as stream:
                parsed = parse_stream(stream)
            summary = summarize_attempt(parsed, exit_code=code, timed_out=timed_out, expected_model=config.model,
                                        arm=arm, launch_error=error, expected_plugin=prepared["plugin"],
                                        expected_tools=[] if kind == "probe" else SWE_TOOLS if swe else ["Read", "Skill"],
                                        expected_skills=prepared["expected_skills"], required_skill=prepared["specialist"],
                                        stderr_text=(directory / "stderr.txt").read_text())
            summary.update(elapsed_s=time.monotonic() - started, reservation_id=reservation["id"],
                           task_sha256=prepared["task_sha256"], manifest_sha256=prepared["binding"]["manifest_sha256"],
                           meter_observed_at=(observation.get("meter") or {}).get("observed_at"),
                           meter_time_basis="actual stream event receipt time")
            if parsed["meters"] and (observation.get("meter") or {}).get("info") != summary["meter"]:
                observation["error"] = "stream meter observation did not match archived bytes"
            if observation.get("error"):
                summary.update(status="invalid", outcome_ready=False, stream_capture_error=observation["error"])
                summary["issues"].append("stream_capture_error")
        finally:
            if plan is not None:
                try:
                    patch_receipt = swe_adapter.finish_repository(config.swe_config, plan, directory)
                    _write_new(directory / "patch-receipt.json", patch_receipt)
                except Exception as exc:
                    finish_error = {"kind": type(exc).__name__, "message": str(exc),
                                    "preserved_scratch": str(prepared["sandbox"])}
                    _write_new(directory / "repository-finish-error.json", finish_error)
            if finish_error is None:
                shutil.rmtree(prepared["sandbox"])
        if swe:
            summary["repository_patch"] = patch_receipt
            if finish_error:
                summary.update(status="invalid", outcome_ready=False, repository_error=finish_error)
                summary["issues"].append("repository_finish_failed")
        _write_new(directory / "summary.json", summary)
        _record_meter(config, prepared["binding"], None if summary.get("stream_capture_error") else summary["meter"], summary["meter_observed_at"])
        seal_attempt(directory, summary)
        return {"attempt_dir": str(directory), "summary": summary}
    except RuntimeBlocked as exc:
        _write_new(directory / "blocked.json", {"reason": str(exc)})
        raise


def quota_probe_task():
    """This control call is not a benchmark outcome and cannot read local files."""
    return {"id": "quota-probe", "prompt": "Reply with exactly OK.", "specialist": "disciplina", "files": {}}


def run_probe(config, manifest):
    return run_attempt(config, manifest, quota_probe_task(), "baseline", kind="probe")
