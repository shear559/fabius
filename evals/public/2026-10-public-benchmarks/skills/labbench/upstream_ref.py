"""Run the UPSTREAM LAB-Bench code straight from the pinned vendored sources (not official.py).

Only import-time I/O dependencies are stubbed: datasets/dotenv (data loading, never called),
PIL (figures, absent for ProtocolQA/SeqQA) and loguru (chembench disables its logger).
Every executed definition (zero_shot.py and evaluator.py in full; the needed nodes of
labbench/utils.py, chembench utils.py/prompter.py; all of chembench constant.py and
ProtocolQA/SeqQA task.py) is compiled from the pinned files. Used by selfcheck.py.
"""

from __future__ import annotations

import ast
import glob
import json
import logging
import os
import pathlib
import random
import re
import string
import sys
import types
import typing
import uuid
from pathlib import Path

import pydantic

VENDOR = Path(__file__).resolve().parent / "vendor"
LB = VENDOR / "LAB-Bench-998a8e0"
CB = VENDOR / "chembench-0.3.0" / "chembench"


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    return None


def _exec(path: Path, module: types.ModuleType, keep: set[str] | None = None) -> None:
    tree = ast.parse(path.read_text())
    if keep is not None:
        tree.body = [n for n in tree.body if _node_name(n) in keep]
        missing = keep - {_node_name(n) for n in tree.body}
        if missing:
            raise RuntimeError(f"{path}: missing {missing}")
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)


def _module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod


class _DisabledLogger:
    def warning(self, *a, **k):
        pass

    def debug(self, *a, **k):
        pass


def load() -> types.SimpleNamespace:
    os.environ.setdefault("TQDM_DISABLE", "1")
    # --- chembench 0.3.0 (pinned wheel) ---
    _module("chembench", __path__=[])
    const = _module("chembench.constant")
    _exec(CB / "constant.py", const)
    cutils = _module("chembench.utils", re=re, Union=typing.Union, Optional=typing.Optional,
                     LATEX_ENV_REGEX=const.LATEX_ENV_REGEX)
    _exec(CB / "utils.py", cutils, {"run_regex", "create_multiple_choice_regex", "remove_ce", "remove_math",
                                    "remove_smiles", "remove_rxnsmiles", "remove_pu", "passthrough",
                                    "post_process_prompts"})
    prompter = _module("chembench.prompter", re=re, Union=typing.Union, Optional=typing.Optional,
                       MCQ_REGEX_TEMPLATE_1=const.MCQ_REGEX_TEMPLATE_1, logger=_DisabledLogger(),
                       ChemBenchModel=object, prompt2messages=None)
    _exec(CB / "prompter.py", prompter, {"prepare_mcq_answer"})
    # --- PIL stub (figures unused by text-only subsets) ---
    pil_image = _module("PIL.Image", Image=type("Image", (), {}))
    _module("PIL", __path__=[], Image=pil_image)
    # --- LAB-Bench @ 998a8e0 ---
    lb_pkg = _module("labbench", __path__=[])
    lutils = _module("labbench.utils", base64=None, json=json, os=os, pathlib=pathlib, random=random,
                     string=string, uuid=uuid, glob=glob.glob, Generic=typing.Generic, Literal=typing.Literal,
                     TypeVar=typing.TypeVar, BaseModel=pydantic.BaseModel, ConfigDict=pydantic.ConfigDict,
                     Field=pydantic.Field, SkipValidation=pydantic.SkipValidation, Image=pil_image,
                     logger=logging.getLogger("labbench"), PUBLIC_RELEASE=True)
    _exec(LB / "labbench" / "utils.py", lutils,
          {"ALPHABET", "FIG_KEY", "REFUSE_CHOICE", "REPO_ROOT", "BaseModelWithID", "AgentInput",
           "BaseEvalInstance", "TEvalInstance", "EvalSet", "randomize_choices", "get_data_sources"})
    zero_shot = _module("labbench.zero_shot")
    _exec(LB / "labbench" / "zero_shot.py", zero_shot)
    evaluator = _module("labbench.evaluator")
    _exec(LB / "labbench" / "evaluator.py", evaluator)
    for name in ("AgentInput", "BaseEvalInstance", "get_data_sources", "randomize_choices", "ALPHABET"):
        setattr(lb_pkg, name, getattr(lutils, name))
    lb_pkg.BaseZeroShotAgent = zero_shot.BaseZeroShotAgent
    lb_pkg.Evaluator, lb_pkg.Eval = evaluator.Evaluator, evaluator.Eval
    tasks = {}
    for subset in ("ProtocolQA", "SeqQA"):
        task = types.ModuleType(f"{subset}.task")
        _exec(LB / subset / "task.py", task)
        tasks[subset] = task
    return types.SimpleNamespace(utils=lutils, zero_shot=zero_shot, evaluator=evaluator, tasks=tasks,
                                 const=const, prompter=prompter, cutils=cutils)
