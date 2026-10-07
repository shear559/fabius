"""Score DS-1000 responses with the official execution test, inside a network-less Docker sandbox.

usage: python score.py responses.jsonl out.jsonl
  responses.jsonl: {"item": ..., "response": "<model text>"} per line (items from items.jsonl)
  out.jsonl:       {"item", "passed": 0|1, "result", "library", "perturbation_type", "extraction",
                    "n_code_blocks", "reindented", "passed_without_reindent", "seconds", "max_rss_mb",
                    "sandbox_error", "code"}; exits non-zero if any sandbox_error remains after 3 attempts
env (optional): DS1000_WORKERS (default 4), DS1000_MEMORY (default 2g), DS1000_CPUS (default 2)

Pipeline per response (official parts marked):
  1. extract the solution: first ```python / ```py block (else first untagged ``` block); if there is none,
     the whole response, minus any prose before a <code> tag
  2. official postprocess() from test_ds1000.py
  3. function-body problems only (prompt ends with an indented '### BEGIN SOLUTION'): if the first code line
     has no indentation, indent every non-blank line by that indent (4 spaces)
  4. official program: code_context + code = repr(solution) + test_execution(code) [+ test_string(code)]
  5. official execution.check_correctness(program, timeout=120) in a fresh container (--network none, read-only)
"""
import concurrent.futures as cf
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCKER_DIR = HERE / "docker"
TIMEOUT = 120  # official test_ds1000.py value
OUTER_TIMEOUT = TIMEOUT + 120  # container start + imports, before the container is killed
PY_LANG = re.compile(r"^(python|py)3?$")
FENCE_OPEN = re.compile(r"^(?P<indent> *)(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^`\n]*)$")


def official_postprocess(code: str) -> str:
    """Verbatim logic of postprocess() in test_ds1000.py @ b39aab71."""
    code = code.split("</code>")[0]
    code = code.replace("```python", "")
    code = code.split("```")[0]
    code = code.split("\nEND SOLUTION")[0]
    code = code.replace("<code>", "")
    return code


def fenced_blocks(text: str):
    """CommonMark-style fenced blocks -> [(language, content)]; an unclosed fence runs to the end."""
    lines, blocks, i = text.split("\n"), [], 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        indent, fence = len(m.group("indent")), m.group("fence")
        info = m.group("info").strip()
        close = re.compile(r"^ *" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*$")
        body, j = [], i + 1
        while j < len(lines) and not close.match(lines[j]):
            line = lines[j]
            strip = len(line) - len(line.lstrip(" "))
            body.append(line[min(indent, strip):])
            j += 1
        blocks.append((info.split()[0].lower() if info else "", "\n".join(body) + "\n"))
        i = j + 1
    return blocks


def extract(response: str):
    """-> (code before postprocess, extraction method, number of fenced blocks)."""
    response = response or ""
    blocks = fenced_blocks(response)
    for wanted in (lambda lang: bool(PY_LANG.match(lang)), lambda lang: lang == ""):
        for lang, content in blocks:
            if wanted(lang):
                return content, "fenced", len(blocks)
    if "<code>" in response:
        return response.split("<code>", 1)[1], "code_tag", len(blocks)
    return response, "whole", len(blocks)


def reindent_if_needed(code: str, indent: str):
    """Function-body problems (gold solution_indent, from the official prompt): if the first code line is not
    indented, indent every non-blank line by solution_indent. Formatting only; strict official = no re-indent."""
    if not indent:
        return code, False
    first = next((line for line in code.split("\n") if line.strip() and not line.lstrip().startswith("#")), None)
    if first is None or first[:1] in (" ", "\t"):
        return code, False
    return "\n".join(indent + line if line.strip() else line for line in code.split("\n")), True


def solution_from_response(response: str, gold: dict) -> dict:
    raw, method, n_blocks = extract(response)
    code = official_postprocess(raw)
    code, reindented = reindent_if_needed(code, gold["solution_indent"])
    return {"code": code, "extraction": method, "n_code_blocks": n_blocks, "reindented": reindented}


def official_program(code_context: str, code: str) -> str:
    """Test-program assembly of eval_ds1000() in test_ds1000.py @ b39aab71."""
    return (
        code_context + "\n"
        + f"code = {repr(code)}\n"
        + "test_execution(code)\n"
        + ("test_string(code)\n" if "test_string(" in code_context else "\n")
    )


IMAGE_FILES = ("Dockerfile", "execution.py", "fetch_data.py", "requirements.lock.txt", "run_one.py")


def image_tag() -> str:
    h = hashlib.sha256()
    for name in IMAGE_FILES:
        h.update(name.encode() + b"\0" + (DOCKER_DIR / name).read_bytes() + b"\0")
    return f"fabius-ds1000:{h.hexdigest()[:12]}"


def ensure_image() -> str:
    tag = image_tag()
    if subprocess.run(["docker", "image", "inspect", tag], capture_output=True).returncode != 0:
        print(f"building {tag} (first run only) ...", file=sys.stderr)
        subprocess.run(["docker", "build", "-q", "-t", tag, str(DOCKER_DIR)], check=True, stdout=sys.stderr)
    return tag


def run_program(image: str, item: str, program: str, attempts: int = 3) -> dict:
    """Official result dict; a sandbox failure (no result line at all) is retried, then flagged sandbox_error."""
    for _ in range(attempts):
        res = run_container(image, item, program)
        if not res.get("sandbox_error"):
            break
    return res


def run_container(image: str, item: str, program: str) -> dict:
    name = f"ds1000-{uuid.uuid4().hex[:12]}"
    mem = os.environ.get("DS1000_MEMORY", "2g")
    cmd = [
        "docker", "run", "--rm", "-i", "--name", name, "--network", "none", "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,size=1g", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "512", "--memory", mem, "--memory-swap", mem,
        "--cpus", os.environ.get("DS1000_CPUS", "2"), image,
    ]
    payload = json.dumps({"id": item, "program": program, "timeout": TIMEOUT})
    try:
        proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=OUTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return {"passed": False, "result": "timed out (container)", "seconds": None}
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    try:
        res = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        tail = proc.stderr.strip().splitlines()[-3:]
        return {"passed": False, "result": f"sandbox error (exit {proc.returncode}): {' | '.join(tail)}",
                "seconds": None, "sandbox_error": True}
    return res


def score_rows(rows, items, workers=None):
    """rows: [{"item", "response"}]; items: {item: gold}. Returns output rows in input order."""
    image = ensure_image()
    workers = workers or int(os.environ.get("DS1000_WORKERS", "4"))

    def one(row):
        gold = items[row["item"]]
        sol = solution_from_response(row.get("response"), gold)
        res = run_program(image, row["item"], official_program(gold["code_context"], sol["code"]))
        passed = 1 if res.get("passed") else 0
        return {
            "item": row["item"], "passed": passed, "result": str(res.get("result"))[:500],
            "library": gold["library"], "perturbation_type": gold["perturbation_type"],
            "extraction": sol["extraction"], "n_code_blocks": sol["n_code_blocks"],
            "reindented": sol["reindented"], "passed_without_reindent": 0 if sol["reindented"] else passed,
            "seconds": res.get("seconds"), "max_rss_mb": res.get("max_rss_mb"),
            "sandbox_error": bool(res.get("sandbox_error")), "code": sol["code"],
        }

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, rows))


def load_items(path=HERE / "items.jsonl"):
    return {d["item"]: d["gold"] for d in map(json.loads, Path(path).read_text().splitlines())}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    items = load_items()
    rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
    ids = [r["item"] for r in rows]
    unknown = sorted(set(ids) - set(items))
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if unknown or dupes:
        raise SystemExit(f"unknown items: {unknown[:10]} duplicate items: {dupes[:10]}")
    missing = set(items) - set(ids)
    if missing:
        print(f"warning: {len(missing)} items have no response and are not scored", file=sys.stderr)
    out = score_rows(rows, items)
    with open(sys.argv[2], "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    n = len(out)
    print(f"passed {sum(r['passed'] for r in out)}/{n} = {sum(r['passed'] for r in out) / max(n, 1):.3f}", file=sys.stderr)
    broken = [r["item"] for r in out if r["sandbox_error"]]
    if broken:
        raise SystemExit(f"ERROR: sandbox failed for {len(broken)} items (scored 0, re-run them): {broken[:10]}")


if __name__ == "__main__":
    main()
