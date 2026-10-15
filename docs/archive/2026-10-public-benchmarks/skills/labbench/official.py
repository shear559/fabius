"""Official LAB-Bench zero-shot MCQ prompt + answer-parsing code, copied verbatim.

Every definition between the BEGIN/END VERBATIM markers is a byte-identical copy of the
pinned upstream source (selfcheck.py re-extracts each one from the pinned files and
compares the text; it also runs the upstream code itself and diffs the outputs):

  github.com/Future-House/LAB-Bench @ 998a8e0a40cf116c80e1b0e7a805ebb5fb9fa838
    labbench/utils.py      -> ALPHABET, REFUSE_CHOICE, randomize_choices
    labbench/zero_shot.py  -> MCQ_INSTRUCT_TEMPLATE
  chembench 0.3.0 wheel (sha256 bf8bb8ec91c12e8b10ba2db26b88d0228ac464d425ac6729a6e12b7dae2d71ee,
  the version + hash pinned in LAB-Bench uv.lock)
    chembench/constant.py  -> COT_PROMPT, MCQ_REGEX_TEMPLATE_1, LATEX_ENV_REGEX
    chembench/utils.py     -> run_regex, create_multiple_choice_regex, remove_*, passthrough,
                              post_process_prompts
    chembench/prompter.py  -> prepare_mcq_answer

build_prompt / parse_answer / is_correct / is_sure restate, step for step, what
BaseZeroShotAgent.run_task (zero_shot.py), EvalInstance.get_input_output
(ProtocolQA/task.py) and Evaluator.score_agent (evaluator.py) do.
"""

from __future__ import annotations  # keeps upstream annotations (ChemBenchModel) unevaluated

import random
import re
import string
from typing import Optional, Union


class _DisabledLogger:
    """chembench/__init__.py calls logger.disable("chembench"): its log calls print nothing."""

    def warning(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


logger = _DisabledLogger()
ChemBenchModel = object  # only named in a type annotation below


def prompt2messages(*args, **kwargs):  # reached only via llm_extractor, which upstream never sets
    raise NotImplementedError("LAB-Bench zero-shot parsing runs without an LLM extractor")

# ----------------------------------------------------------------- BEGIN VERBATIM
# LAB-Bench labbench/utils.py
ALPHABET = string.ascii_uppercase

REFUSE_CHOICE = "Insufficient information to answer the question"


def randomize_choices(ideal: str, distractors: list[str]) -> tuple[list[str], str, str]:
    choices = [ideal, REFUSE_CHOICE, *distractors]
    n_choices = len(choices)
    if n_choices > len(ALPHABET):
        raise ValueError("Too many choices")

    perm = list(range(n_choices))
    random.shuffle(perm)
    shuffled_choices = [
        f"({letter}) {choices[sigma_i]}"
        for letter, sigma_i in zip(ALPHABET, perm, strict=False)
    ]

    answer = ALPHABET[perm.index(0)]
    unsure = ALPHABET[perm.index(1)]

    return shuffled_choices, answer, unsure


# LAB-Bench labbench/zero_shot.py
MCQ_INSTRUCT_TEMPLATE = """The following is a multiple choice question about biology.
Please answer by responding with the letter of the correct answer.{cot}

Question: {question}

Options:
{answers}

You MUST include the letter of the correct answer within the following tags: [ANSWER] and [/ANSWER].
For example, '[ANSWER]<answer>[/ANSWER]', where <answer> is the correct letter.
Always answer in exactly this format of a single letter between the two tags, even if you are unsure.
We require this because we use automatic parsing."""

# chembench 0.3.0 chembench/constant.py
COT_PROMPT = "Think step by step."

MCQ_REGEX_TEMPLATE_1 = r"(?:\[ANSWER\]|\[ANS\]|<ANS>|<ANSWER>|<ans>)\s*([A-Z](?:,\s*[A-Z])*)\s*(?:\..*?|,.*?)?(?:\[/?ANSWER\]|\[/ANS\]|</ANS>|</ANSWER>|</ans>)"

LATEX_ENV_REGEX = {
    "ce_pattern": r"\\ce\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    "math_pattern": r"\$([^$]+)\$",
    "smiles_pattern": r"\[START_SMILES\](.*?)\[END_SMILES\]",
    "pu_pattern": r"\\pu\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    "rxnsmiles_pattern": r"\[START_RXNSMILES\](.*?)\[END_RXNSMILES\]",
}


# chembench 0.3.0 chembench/utils.py
def run_regex(pattern: str, string: str, return_first: bool = True) -> Union[str, list[str], None]:
    """
    Run a regex pattern on a string and return the matches.

    Args:
        pattern (str): The regex pattern to match.
        string (str): The string to search for matches.
        return_first (bool, optional): If True, return only the first match.
            If False, return a list of all matches.
            Defaults to True.

    Returns:
        Union[str, list[str], None]: The first match if return_first is True,
            a list of all matches if return_first is False,
            or None if no matches are found.
    """
    matches = re.findall(pattern, string, re.IGNORECASE)
    if not matches:
        return None

    if return_first:
        return matches[0]

    return matches


def create_multiple_choice_regex(allowed_letters: list[str]) -> str:
    """
    Create a regex to match the multiple choice answer pattern.

    The pattern is <letter>, where <letter> is one of the allowed letters.
    The pattern can be run with `run_regex` to return the matching letter
        as it uses a capture group.

    Args:
        allowed_letters (list[str]): list of allowed letters.

    Returns:
        str: Regex pattern.
    """
    pattern = "|".join(map(re.escape, allowed_letters))
    pattern = f"(?:{pattern})"

    return pattern


def remove_ce(prompt: str) -> str:
    ce_pattern = LATEX_ENV_REGEX["ce_pattern"]
    prompt = re.sub(ce_pattern, lambda x: x.group(1), prompt)
    return prompt


def remove_math(prompt: str) -> str:
    math_pattern = LATEX_ENV_REGEX["math_pattern"]
    prompt = re.sub(math_pattern, lambda x: x.group(1), prompt)
    return prompt


def remove_smiles(prompt: str) -> str:
    smiles_pattern = LATEX_ENV_REGEX["smiles_pattern"]
    prompt = re.sub(smiles_pattern, lambda x: x.group(1), prompt)
    return prompt


def remove_rxnsmiles(prompt: str) -> str:
    rxnsmiles_pattern = LATEX_ENV_REGEX["rxnsmiles_pattern"]
    prompt = re.sub(rxnsmiles_pattern, lambda x: x.group(1), prompt)
    return prompt


def remove_pu(prompt: str) -> str:
    pu_pattern = LATEX_ENV_REGEX["pu_pattern"]
    prompt = re.sub(pu_pattern, lambda x: x.group(1), prompt)
    return prompt


def passthrough(prompt: str) -> str:
    return prompt


def post_process_prompts(
    prompt: str,
    post_process_ce: callable = remove_ce,
    post_process_math: callable = remove_math,
    post_process_smiles: callable = remove_smiles,
    post_process_rxnsmiles: callable = remove_rxnsmiles,
    post_process_pu: callable = remove_pu,
    other: callable = None,
) -> str:
    if other is None:
        other = [passthrough]
    else:
        other = [other]
    processing_functions = [
        post_process_ce,
        post_process_math,
        post_process_smiles,
        post_process_rxnsmiles,
        post_process_pu,
    ] + other

    for processing_function in processing_functions:
        prompt = processing_function(prompt)

    return prompt


# chembench 0.3.0 chembench/prompter.py
def prepare_mcq_answer(
    text: str,
    pattern: str = MCQ_REGEX_TEMPLATE_1,
    alphabet: Optional[list[str]] = None,
    llm_extractor: Optional[Union[str, ChemBenchModel]] = None,
    example: str = "",
) -> str:
    """Parse string within the identifiers defined in the mcq regex
    for eg: [ANSWER]A,B[ANSWER] -> A,B

    Args:
        text (str): Output from the model in string format.
        pattern (str): Regex pattern to match the identifier.
            Defaults to MCQ_REGEX_TEMPLATE_1.
        alphabet (Optional[list[str]]): list of allowed letters.
            Defaults to None, in which case it uses A-Z.
        llm_extractor (Optional[Union[str, ChemBenchModel]]): LLM extractor to use
            if no pattern matches. Defaults to None.
        example (Optional[dict[str, Any]]): Example dict with keys "input" and "target_scores"
            if llm_fallback is True. Defaults to None.

    Returns:
        str: Text within the identifier for regex matching,
            or the original text if no matches are found.
    """
    if alphabet is None:
        alphabet = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    try:
        matches = sorted(list(set(re.findall(pattern, text, re.DOTALL))))
    except IndexError:
        matches = None
    if matches:
        return str(matches)
    else:
        logger.warning(f"No pattern matched in the model output: {text}")
        if llm_extractor:
            logger.warning("Unable to convert words to number. Now trying LLM")
            response = llm_extractor.extract(prompt2messages([text]), mcq=True, example=example)
            extracted = response["content"]
            return ", ".join(extracted)
        else:
            if text in alphabet:
                logger.debug(f"Returning {text} as it is a single letter")
                return text
            elif "," in text:
                split_text = text.split(",")
                all_letters = [letter for letter in split_text if letter.strip() in alphabet]
                if len(all_letters) == len(split_text):
                    return ",".join(all_letters)
                else:
                    return ""
            elif " " in text:
                split_text = text.split(" ")
                all_letters = [letter for letter in split_text if letter.strip() in alphabet]
                if len(all_letters) == len(split_text):
                    return ",".join(all_letters)
                else:
                    return ""
# ------------------------------------------------------------------- END VERBATIM

VERBATIM_SOURCES = {
    # name -> (pinned file relative to vendor/, top-level definition name)
    "ALPHABET": ("LAB-Bench-998a8e0/labbench/utils.py", "ALPHABET"),
    "REFUSE_CHOICE": ("LAB-Bench-998a8e0/labbench/utils.py", "REFUSE_CHOICE"),
    "randomize_choices": ("LAB-Bench-998a8e0/labbench/utils.py", "randomize_choices"),
    "MCQ_INSTRUCT_TEMPLATE": ("LAB-Bench-998a8e0/labbench/zero_shot.py", "MCQ_INSTRUCT_TEMPLATE"),
    "COT_PROMPT": ("chembench-0.3.0/chembench/constant.py", "COT_PROMPT"),
    "MCQ_REGEX_TEMPLATE_1": ("chembench-0.3.0/chembench/constant.py", "MCQ_REGEX_TEMPLATE_1"),
    "LATEX_ENV_REGEX": ("chembench-0.3.0/chembench/constant.py", "LATEX_ENV_REGEX"),
    "run_regex": ("chembench-0.3.0/chembench/utils.py", "run_regex"),
    "create_multiple_choice_regex": ("chembench-0.3.0/chembench/utils.py", "create_multiple_choice_regex"),
    "remove_ce": ("chembench-0.3.0/chembench/utils.py", "remove_ce"),
    "remove_math": ("chembench-0.3.0/chembench/utils.py", "remove_math"),
    "remove_smiles": ("chembench-0.3.0/chembench/utils.py", "remove_smiles"),
    "remove_rxnsmiles": ("chembench-0.3.0/chembench/utils.py", "remove_rxnsmiles"),
    "remove_pu": ("chembench-0.3.0/chembench/utils.py", "remove_pu"),
    "passthrough": ("chembench-0.3.0/chembench/utils.py", "passthrough"),
    "post_process_prompts": ("chembench-0.3.0/chembench/utils.py", "post_process_prompts"),
    "prepare_mcq_answer": ("chembench-0.3.0/chembench/prompter.py", "prepare_mcq_answer"),
}


def shuffled_choices(item_uuid: str, ideal: str, distractors: list[str], seed: int) -> tuple[list[str], str, str]:
    """Official randomize_choices under a fixed per-item seed (upstream leaves `random` unseeded)."""
    random.seed(f"{seed}:{item_uuid}")
    return randomize_choices(ideal, list(distractors))


def build_prompt(question: str, choices: list[str]) -> str:
    """BaseZeroShotAgent.run_task prompt assembly with use_cot=True (score_baseline.py default)."""
    prompt_kwargs = {"question": question, "cot": "\n" + COT_PROMPT}
    prompt_kwargs["answers"] = "\n".join(choices)
    text_prompt = MCQ_INSTRUCT_TEMPLATE.format(**prompt_kwargs)
    return post_process_prompts(text_prompt)


def parse_answer(agent_output: str | None, n_choices: int) -> tuple[str | None, str | None]:
    """BaseZeroShotAgent.run_task answer extraction (no LLM extractor, as upstream).

    Returns (answer letter or None, chembench prepared_output). Upstream would raise a
    TypeError (aborting the whole run) when prepare_mcq_answer returns None, i.e. for an
    untagged output with no comma and no space that is not one bare capital letter; that
    case and a missing/None output are scored here as "no answer".
    """
    text = agent_output if isinstance(agent_output, str) else ""
    # upstream also passes example=..., which only the (disabled) LLM extractor reads
    prepared_output = prepare_mcq_answer(text, MCQ_REGEX_TEMPLATE_1)
    if prepared_output is None:
        return None, None
    answer = run_regex(
        create_multiple_choice_regex(list(ALPHABET[:n_choices])),
        prepared_output,
        return_first=True,
    )
    return answer, prepared_output


def is_correct(answer: str | None, target: str) -> bool:
    """Evaluator.score_agent: correct = agent_output == target_output."""
    return answer == target


def is_sure(answer: str | None, unsure: str) -> bool:
    """Evaluator.score_agent: sure = agent_output != unsure (an unparsed answer counts as sure)."""
    return answer != unsure
