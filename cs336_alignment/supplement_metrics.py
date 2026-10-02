"""Answer extraction for the optional instruction-tuning/RLHF supplement."""

import re


def parse_mmlu_response(model_output: str) -> str | None:
    """Extract the requested answer letter; conflicting declarations are invalid.

    Accept the official 'The correct answer is X' sentence or a standalone
    letter. Do not infer a choice from option text or the gold answer.
    """
    answers = {
        answer.upper()
        for answer in re.findall(
            r"\bthe\s+correct\s+answer\s+is\s+([A-D])\b",
            model_output,
            flags=re.IGNORECASE,
        )
    }
    if answers:
        return next(iter(answers)) if len(answers) == 1 else None
    standalone = re.fullmatch(r"\s*([A-D])[.)]?\s*", model_output, re.IGNORECASE)
    return standalone.group(1).upper() if standalone else None


def parse_gsm8k_response(model_output: str) -> str | None:
    """Return the last signed decimal numeral, removing thousands separators.

    This implements final-number extraction, not mathematical expression
    evaluation: written-out numbers and fractions are not evaluated.
    """
    numbers = re.findall(
        r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|[-+]?\.\d+",
        model_output.replace("−", "-"),
    )
    return numbers[-1].replace(",", "") if numbers else None
