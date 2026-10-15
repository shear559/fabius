"""Run LongMemEval's own functions verbatim from the vendored files in official/.

official/ holds unmodified copies of four files of github.com/xiaowu0162/LongMemEval at COMMIT.
Each is checked against its git blob hash before use; a single top-level function is then
compiled from the official source text, so the prompt templates are the authors' own bytes and
the official module-level client imports (openai, backoff, transformers) are not needed.
"""
import ast
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OFFICIAL_DIR = os.path.join(HERE, "official")
REPO = "https://github.com/xiaowu0162/LongMemEval"
COMMIT = "9e0b455f4ef0e2ab8f2e582289761153549043fc"
PATHS = {  # vendored name -> (path in the repo, git blob SHA-1 at COMMIT)
    "run_generation.py": ("src/generation/run_generation.py", "8e9e0f25b804d3d0afbadc9619264b0c7a275dc0"),
    "evaluate_qa.py": ("src/evaluation/evaluate_qa.py", "4732f3772b04a2b9069121ade304e6320494abc2"),
    "print_qa_metrics.py": ("src/evaluation/print_qa_metrics.py", "f1f68505865960188f239d0f8ccd0a10f8d7b906"),
    "LICENSE": ("LICENSE", "2e2c8491038bf0383c324a478b66a4663833efea"),
}


def git_blob_sha1(path):
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def verify():
    for name, (_, blob) in PATHS.items():
        got = git_blob_sha1(os.path.join(OFFICIAL_DIR, name))
        if got != blob:
            raise SystemExit(f"official/{name} is not LongMemEval@{COMMIT[:7]} (git blob {got}, expected {blob})")


def load_function(filename, name, namespace=None):
    verify()
    src = open(os.path.join(OFFICIAL_DIR, filename), encoding="utf-8").read()
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name)
    ns = dict(namespace or {})
    exec(compile(ast.Module(body=[node], type_ignores=[]), os.path.join(OFFICIAL_DIR, filename), "exec"), ns)
    return ns[name]


def get_anscheck_prompt():
    """evaluate_qa.get_anscheck_prompt(task, question, answer, response, abstention=False)."""
    return load_function("evaluate_qa.py", "get_anscheck_prompt")


def prepare_prompt():
    """run_generation.prepare_prompt(entry, retriever_type, topk_context, useronly, history_format, cot, ...)."""
    return load_function("run_generation.py", "prepare_prompt", {"json": json})
