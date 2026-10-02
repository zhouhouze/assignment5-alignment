"""Evaluation boundary cases beyond the unchanged official metric tests."""

import pytest

from cs336_alignment.supplement_metrics import parse_gsm8k_response, parse_mmlu_response
from tests.adapters import run_parse_mmlu_response


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("", None),
        (" B.\n", "B"),
        ("The correct answer is c.", "C"),
        ("The correct answer is Bacteria.", None),
        ("A is tempting, but the correct answer is D.", "D"),
        ("The correct answer is A. The correct answer is B.", None),
        ("The correct answer is B. The correct answer is B.", "B"),
    ],
)
def test_mmlu_extraction_boundaries(response, expected):
    assert parse_mmlu_response(response) == expected


def test_mmlu_does_not_use_gold_answer():
    for gold in ("A", "B", "C", "D"):
        example = {"subject": "test", "question": "?", "options": ["a", "b", "c", "d"], "answer": gold}
        assert run_parse_mmlu_response(example, "The correct answer is B.") == "B"
        assert run_parse_mmlu_response(example, "No answer.") is None


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("", None),
        ("seventy-two", None),
        ("48 / 2 = 24; 48 + 24 = 72.", "72"),
        ("The amount is $1,234.50.", "1234.50"),
        ("The temperature is -12.5 degrees.", "-12.5"),
        ("The balance is −3.", "-3"),
        ("Probability: .5", ".5"),
        ("First 72, correction 73.", "73"),
    ],
)
def test_gsm8k_extraction_boundaries(response, expected):
    assert parse_gsm8k_response(response) == expected
