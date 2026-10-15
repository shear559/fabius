"""Official BFCL code path. Runs INSIDE the pinned, network-less container (launched by score.py).

All prompt construction, decoding and checking below is done by unmodified bfcl-eval 2026.3.23
functions (vendor/bfcl_eval_2026.3.23 = the PyPI wheel, byte-identical to gorilla@6ea5797).
The one substitution: `bfcl_eval.constants.model_config` imports every vendor SDK just to build a
model registry; it is replaced by the official registry entry for the Claude prompting model,
parsed from the pinned source. Inside the checker that entry only feeds `underscore_to_dot`.

Subcommands (stdin -> stdout, JSON lines):
  env      versions of the container environment
  prompts  {"ids": [...]}             -> {"item","category","prompt","function","ground_truth"}
  score    {"item","response"} lines  -> one verdict line per input line
"""
import ast
import copy
import json
import os
import re
import select
import signal
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BFCL_ROOT = HERE / "vendor" / "bfcl_eval_2026.3.23"
SITE = HERE / "vendor" / "site-linux"
REGISTRY_NAME = "claude-sonnet-4-5-20250929"  # newest Claude Sonnet "(Prompt)" entry in the pinned registry
CATEGORIES = ["simple_python", "multiple", "parallel", "parallel_multiple", "irrelevance"]
ITEM_TIMEOUT_S = 10
FENCE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)


def official_registry_entry(name):
    tree = ast.parse((BFCL_ROOT / "bfcl_eval/constants/model_config.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == name and isinstance(value, ast.Call):
                    kw = {k.arg: ast.literal_eval(k.value) for k in value.keywords
                          if k.arg in ("model_name", "is_fc_model", "underscore_to_dot")}
                    if kw.get("is_fc_model") is not False or "underscore_to_dot" not in kw:
                        raise SystemExit(f"unexpected registry entry for {name}: {kw}")
                    return kw
    raise SystemExit(f"registry entry {name} not found")


def bootstrap():
    os.environ.setdefault("BFCL_PROJECT_ROOT", "/tmp/bfcl_project")  # eval_config mkdirs here
    sys.path[:0] = [str(SITE), str(BFCL_ROOT)]
    stub = types.ModuleType("bfcl_eval.constants.model_config")
    stub.MODEL_CONFIG_MAPPING = {REGISTRY_NAME: types.SimpleNamespace(**official_registry_entry(REGISTRY_NAME))}
    sys.modules["bfcl_eval.constants.model_config"] = stub


bootstrap()

from bfcl_eval.constants.enums import Language, ReturnFormat  # noqa: E402
from bfcl_eval.eval_checker import eval_runner  # noqa: E402
from bfcl_eval.model_handler.utils import (  # noqa: E402
    combine_consecutive_user_prompts,
    convert_system_prompt_into_user_prompt,
    default_decode_ast_prompting,
    system_prompt_pre_processing_chat_model,
)
from bfcl_eval.utils import load_dataset_entry, load_ground_truth_entry, make_json_serializable  # noqa: E402


class PromptingHandler:
    """decode_ast of the official ClaudeHandler with is_fc_model=False (api_inference/claude.py:38-40)."""

    def decode_ast(self, result, language, has_tool_call_tag):
        return default_decode_ast_prompting(result, language, has_tool_call_tag)


HANDLER = PromptingHandler()


def category_of(item_id):
    return item_id.rsplit("_", 1)[0]  # == bfcl_eval.utils.extract_test_category_from_id for these ids


def load_entries(include_hint):
    """include_hint=True: entries as the official generation step loads them (prompt side).
    include_hint=False: entries as the official evaluate_task loads them (checker side)."""
    out = {}
    for cat in CATEGORIES:
        if include_hint:
            entries = load_dataset_entry(cat)
        else:
            entries = load_dataset_entry(cat, include_prereq=False, include_language_specific_hint=False)
        for e in entries:
            assert category_of(e["id"]) == cat and e["id"] not in out
            out[e["id"]] = e
    return out


def load_ground_truth():
    out = {}
    for cat in CATEGORIES:
        if cat == "irrelevance":  # no possible_answer file; scored by relevance_file_runner logic
            continue
        prompts = [e["id"] for e in load_dataset_entry(cat, include_prereq=False, include_language_specific_hint=False)]
        truth = load_ground_truth_entry(cat)
        assert prompts == [t["id"] for t in truth], f"{cat}: prompt/ground-truth id order differs"
        out.update({t["id"]: t["ground_truth"] for t in truth})
    return out


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def cmd_env():
    import importlib.metadata as md
    import platform
    pkgs = ["numpy", "pandas", "tree-sitter", "tree-sitter-java", "tree-sitter-javascript",
            "filelock", "tenacity", "python-dotenv", "overrides", "tqdm"]
    emit({"python": sys.version.split()[0], "machine": platform.machine(),
          "packages": {p: md.version(p) for p in pkgs},
          "registry_entry": {REGISTRY_NAME: official_registry_entry(REGISTRY_NAME)}})


def cmd_prompts(request):
    prompt_side = load_entries(include_hint=True)
    checker_side = load_entries(include_hint=False)
    truth = load_ground_truth()
    for item_id in request["ids"]:
        entry = copy.deepcopy(prompt_side[item_id])
        assert len(entry["question"]) == 1, "non-live single-turn only"
        # Official prompting path for a model that takes everything in one user message
        # (identical to the DeepSeek-R1 prompting handler): system prompt, then fold it into the user turn.
        msgs = system_prompt_pre_processing_chat_model(entry["question"][0], entry["function"], entry["id"])
        msgs = combine_consecutive_user_prompts(convert_system_prompt_into_user_prompt(msgs))
        assert len(msgs) == 1 and msgs[0]["role"] == "user"
        emit({"item": item_id, "category": category_of(item_id), "prompt": msgs[0]["content"],
              "function": checker_side[item_id]["function"], "ground_truth": truth.get(item_id)})


def official_verdict(item_id, text, entries, truth):
    """Exactly what the official evaluate_task does for one entry of this category."""
    cat = category_of(item_id)
    entry = copy.deepcopy(entries[item_id])
    if cat == "irrelevance":
        return eval_runner._evaluate_single_relevance_entry(HANDLER, item_id, text, entry, REGISTRY_NAME, cat)
    return eval_runner._evaluate_single_ast_entry(
        HANDLER, item_id, text, copy.deepcopy(truth[item_id]), entry, REGISTRY_NAME, cat,
        language=Language.PYTHON, return_format=ReturnFormat.PYTHON, has_tool_call_tag=False)


def judge(item_id, response, entries, truth):
    official = official_verdict(item_id, response, entries, truth)
    try:
        decoded = make_json_serializable(default_decode_ast_prompting(response, ReturnFormat.PYTHON, False))
    except Exception:
        decoded = None
    # Secondary, NOT official: judge the first ``` fenced block if the response has one.
    fenced = FENCE.search(response)
    lenient = official_verdict(item_id, fenced.group(1), entries, truth)["valid"] if fenced else official["valid"]
    decoded_json = json.dumps(decoded, ensure_ascii=False)
    return {
        "passed": int(bool(official["valid"])),
        "passed_lenient": int(bool(lenient)),
        "error_type": official.get("error_type"),
        "error": json.dumps(make_json_serializable(official["error"]), ensure_ascii=False)[:1000] if "error" in official else None,
        "decoded": decoded if len(decoded_json) <= 20000 else decoded_json[:20000],
    }


def run_isolated(fn, timeout):
    """Run fn() in a forked child; kill it after `timeout` s (the official decoder eval()s BinOp nodes)."""
    rfd, wfd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(rfd)
        try:
            payload = json.dumps(fn(), ensure_ascii=False)
        except BaseException as exc:  # noqa: BLE001 - any child failure becomes a verdict
            payload = json.dumps({"__crash__": f"{type(exc).__name__}: {exc}"[:1000]})
        with os.fdopen(wfd, "wb") as fh:
            fh.write(payload.encode())
        os._exit(0)
    os.close(wfd)
    chunks, finished, deadline = [], False, time.monotonic() + timeout
    while True:
        left = deadline - time.monotonic()
        if left <= 0 or not select.select([rfd], [], [], left)[0]:
            break
        chunk = os.read(rfd, 1 << 16)
        if not chunk:
            finished = True
            break
        chunks.append(chunk)
    os.close(rfd)
    if not finished:
        os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    if not finished:
        return {"__timeout__": True}
    try:
        return json.loads(b"".join(chunks) or b'{"__crash__": "child produced no output"}')
    except ValueError:
        return {"__crash__": "child output not JSON"}


def cmd_score(lines):
    entries = load_entries(include_hint=False)
    truth = load_ground_truth()
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        item_id, response = row["item"], row["response"]
        if item_id not in entries or not isinstance(response, str):
            raise SystemExit(f"bad scoring row for item {item_id!r}")
        out = run_isolated(lambda: judge(item_id, response, entries, truth), ITEM_TIMEOUT_S)
        if "__timeout__" in out or "__crash__" in out:
            kind = "timeout" if "__timeout__" in out else "crash"
            out = {"passed": 0, "passed_lenient": 0, "error_type": f"harness:{kind}",
                   "error": out.get("__crash__", f"exceeded {ITEM_TIMEOUT_S}s"), "decoded": None}
        emit({"item": item_id, "category": category_of(item_id), **out})


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "env":
        cmd_env()
    elif command == "prompts":
        cmd_prompts(json.loads(sys.stdin.read()))
    elif command == "score":
        cmd_score(sys.stdin)
    else:
        raise SystemExit(__doc__)
