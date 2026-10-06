#!/usr/bin/env python3
"""One headless Claude Code attempt in a clean context, recorded in full (PROTOCOL.md v1.1).

Clean context in every arm: --setting-sources project (no user settings, enabled plugins,
hooks or user skills), --strict-mcp-config (no MCP servers), a fresh working directory,
--no-session-persistence, and identical file-access denies outside /private/tmp.

Arms (ARMS): baseline = the task verbatim, no plugin; fabius-doc = the README's documented
invocation, "fabius: " + task, plugin loaded; fabius-loaded = "/fabius " + task, plugin
loaded (the slash command puts the router contract in context).
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

CLAUDE = os.path.expanduser(
    "~/.antigravity-ide/extensions/anthropic.claude-code-2.1.289-darwin-x64/resources/native-binary/claude")
PLUGIN_DIR = "/private/tmp/fbplugin/fabius"
MODEL = "claude-sonnet-5-5"
ARMS = {
    "baseline": ("", False),
    "fabius-doc": ("fabius: ", True),
    "fabius-loaded": ("/fabius ", True),
}
DENY = ["Read(//Users/**)", "Edit(//Users/**)", "Write(//Users/**)", "Read(//private/var/folders/**)"]


def claude_sha256():
    return hashlib.sha256(open(CLAUDE, "rb").read()).hexdigest()


def build_cmd(prompt, arm, tools, allowed=None, max_turns=None, permission_mode=None, model=MODEL):
    prefix, with_plugin = ARMS[arm]
    cmd = [CLAUDE, "-p", prefix + prompt, "--model", model,
           "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
           "--output-format", "stream-json", "--verbose",
           "--tools", tools, "--disallowedTools", *DENY]
    if allowed:
        cmd += ["--allowedTools", *allowed]
    if max_turns:
        cmd += ["--max-turns", str(max_turns)]
    if permission_mode:
        cmd += ["--permission-mode", permission_mode]
    if with_plugin:
        cmd += ["--plugin-dir", PLUGIN_DIR]
    return cmd


def parse_stream(lines):
    """init, result, Skill calls, tool counts, all assistant text blocks, usage-meter events,
    and the prompt size of the first assistant turn."""
    out = {"init": None, "result": None, "skills": [], "tools": {}, "texts": [], "meters": [],
           "first_turn_prompt_tokens": None, "assistant_text_messages": 0}
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            out["init"] = ev
        elif kind == "assistant":
            msg = ev.get("message", {}) or {}
            if out["first_turn_prompt_tokens"] is None and msg.get("usage"):
                u = msg["usage"]
                out["first_turn_prompt_tokens"] = (u.get("input_tokens") or 0) + \
                    (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
            had_text = False
            for block in msg.get("content", []) or []:
                if block.get("type") == "tool_use":
                    out["tools"][block["name"]] = out["tools"].get(block["name"], 0) + 1
                    if block["name"] == "Skill":
                        inp = block.get("input", {}) or {}
                        out["skills"].append(inp.get("skill") or inp.get("command") or json.dumps(inp))
                elif block.get("type") == "text" and (block.get("text") or "").strip():
                    out["texts"].append(block["text"])
                    had_text = True
            out["assistant_text_messages"] += had_text
        elif kind == "result":
            out["result"] = ev
        elif kind == "rate_limit_event":
            out["meters"].append(ev.get("rate_limit_info"))
    return out


def memory_dir_for(cwd):
    slug = str(Path(cwd).resolve()).replace("/", "-")
    return Path(os.path.expanduser("~/.claude/projects")) / slug


def run_attempt(prompt, arm, cwd, attempt_dir, tools, allowed=None, max_turns=None, timeout_s=300,
                permission_mode=None, env_extra=None, model=MODEL):
    attempt_dir = Path(attempt_dir)
    attempt_dir.mkdir(parents=True, exist_ok=False)  # attempts are never overwritten
    mem = memory_dir_for(cwd)
    mem_existed = mem.exists()
    if mem_existed:
        raise RuntimeError(f"a project directory already exists for this working directory: {mem}")
    cmd = build_cmd(prompt, arm, tools, allowed, max_turns, permission_mode, model)
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
    if env_extra:
        env.update(env_extra)
    (attempt_dir / "cmd.json").write_text(json.dumps({"cmd": cmd, "cwd": str(cwd)}, indent=1))
    (attempt_dir / "prompt.txt").write_text(ARMS[arm][0] + prompt)
    started = time.time()
    timed_out = False
    with open(attempt_dir / "stream.jsonl", "w") as so, open(attempt_dir / "stderr.txt", "w") as se:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=so, stderr=se,
                                start_new_session=True)
        try:
            code = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, 15)
            try:
                code = proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, 9)
                code = proc.wait()
    elapsed = time.time() - started
    created_memory = mem.exists()
    if created_memory:
        shutil.rmtree(mem, ignore_errors=True)
    p = parse_stream(open(attempt_dir / "stream.jsonl"))
    init, result = p["init"] or {}, p["result"] or {}
    final = result.get("result")
    if not (final or "").strip():
        final = p["texts"][-1] if p["texts"] else ""
    summary = {
        "arm": arm, "prefix": ARMS[arm][0], "model_requested": model, "exit_code": code, "timed_out": timed_out,
        "elapsed_s": round(elapsed, 1),
        "init_model": init.get("model"), "init_tools": init.get("tools"), "init_skills": init.get("skills"),
        "init_plugins": init.get("plugins"),
        "skill_calls": p["skills"], "fabius_skills_loaded": sorted({s for s in p["skills"] if s and "fabius" in s}),
        "tool_calls": p["tools"],
        "first_turn_prompt_tokens": p["first_turn_prompt_tokens"],
        "assistant_text_messages": p["assistant_text_messages"],
        "result_subtype": result.get("subtype"), "is_error": result.get("is_error"),
        "api_error_status": result.get("api_error_status"), "terminal_reason": result.get("terminal_reason"),
        "permission_denials": result.get("permission_denials"),
        "num_turns": result.get("num_turns"), "duration_ms": result.get("duration_ms"),
        "total_cost_usd": result.get("total_cost_usd"), "usage": result.get("usage"),
        "model_usage": result.get("modelUsage"),
        "final_text": final, "result_text": result.get("result"), "all_texts": p["texts"],
        "meter": p["meters"][-1] if p["meters"] else None,
        "memory_dir_created_and_removed": created_memory,
    }
    (attempt_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary
