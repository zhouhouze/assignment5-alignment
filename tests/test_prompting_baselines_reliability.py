import importlib
import sys
import types
from types import SimpleNamespace

import pytest


def load_prompting_baselines(monkeypatch):
    fake_vllm = types.ModuleType("vllm")
    fake_vllm.LLM = object

    class FakeSamplingParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_vllm.SamplingParams = FakeSamplingParams
    monkeypatch.setitem(sys.modules, "vllm", fake_vllm)
    module = importlib.import_module("scripts.prompting_baselines")
    monkeypatch.setattr(module, "git_commit", lambda: "test-commit")
    return module


def gsm_example(question: str, answer: str) -> dict:
    return {"question": question, "answer": f"scratch #### {answer}"}


def output(text: str, *, finish_reason: str = "stop", token_ids: list[int] | None = None):
    return SimpleNamespace(
        outputs=[SimpleNamespace(text=text, finish_reason=finish_reason, token_ids=token_ids)]
    )


class FakeModel:
    def __init__(self, batches):
        self.batches = list(batches)

    def generate(self, prompts, sampling_params):
        assert sampling_params.kwargs["temperature"] == 1.0
        assert sampling_params.kwargs["top_p"] == 1.0
        assert sampling_params.kwargs["max_tokens"] == 512
        return self.batches.pop(0)


def test_empty_completion_is_persisted_and_graded(monkeypatch, tmp_path):
    pb = load_prompting_baselines(monkeypatch)
    examples = [gsm_example("What is 2+2?", "4"), gsm_example("What is 1+1?", "2")]
    model = FakeModel([[output("\\boxed{4}", token_ids=[1, 2]), output("", token_ids=[])]])

    records = pb.run_prompt(
        model=model,
        examples=examples,
        prompt_name="question_only",
        model_id="test-model",
        seed=0,
        batch_size=2,
        output_dir=tmp_path,
        dry_run=False,
    )

    prompt_dir = tmp_path / "question_only"
    assert len(records) == 2
    assert not (prompt_dir / "predictions.partial.jsonl").exists()
    assert (prompt_dir / "predictions.jsonl").exists()
    disk_records = pb.read_jsonl(prompt_dir / "predictions.jsonl")
    assert disk_records[1]["response"] == ""
    assert disk_records[1]["empty_response"] is True
    assert disk_records[1]["generation_status"] == "completed_empty"
    assert disk_records[1]["error_type"] == "empty_response"
    assert disk_records[1]["response_token_count"] == 0
    assert disk_records[1]["category"] == "category_3"
    assert disk_records[1]["format_reward"] == 0.0
    assert disk_records[1]["answer_reward"] == 0.0
    summary = pb.json.loads((prompt_dir / "summary.json").read_text())
    assert summary["total_examples"] == 2
    assert summary["category_3_count"] == 1
    progress = pb.json.loads((prompt_dir / "progress.json").read_text())
    assert progress["status"] == "completed"
    assert progress["completed_count"] == 2


def test_short_generation_batch_hard_fails_and_keeps_partial(monkeypatch, tmp_path):
    pb = load_prompting_baselines(monkeypatch)
    examples = [
        gsm_example("q0", "0"),
        gsm_example("q1", "1"),
        gsm_example("q2", "2"),
        gsm_example("q3", "3"),
    ]
    model = FakeModel(
        [
            [output("\\boxed{0}"), output("\\boxed{1}")],
            [output("\\boxed{2}")],
        ]
    )

    with pytest.raises(RuntimeError, match="Expected 2 outputs"):
        pb.run_prompt(
            model=model,
            examples=examples,
            prompt_name="question_only",
            model_id="test-model",
            seed=0,
            batch_size=2,
            output_dir=tmp_path,
            dry_run=False,
        )

    prompt_dir = tmp_path / "question_only"
    partial = prompt_dir / "predictions.partial.jsonl"
    assert partial.exists()
    assert len(pb.read_jsonl(partial)) == 2
    assert not (prompt_dir / "predictions.jsonl").exists()
    progress = pb.json.loads((prompt_dir / "progress.json").read_text())
    assert progress["status"] == "failed"
    assert progress["completed_count"] == 2
    assert progress["failure_type"] == "RuntimeError"


def test_missing_completion_hard_fails(monkeypatch, tmp_path):
    pb = load_prompting_baselines(monkeypatch)
    examples = [gsm_example("q0", "0")]
    model = FakeModel([[SimpleNamespace(outputs=[])]])

    with pytest.raises(RuntimeError, match="Missing completion"):
        pb.run_prompt(
            model=model,
            examples=examples,
            prompt_name="question_only",
            model_id="test-model",
            seed=0,
            batch_size=1,
            output_dir=tmp_path,
            dry_run=False,
        )

    prompt_dir = tmp_path / "question_only"
    assert not (prompt_dir / "predictions.jsonl").exists()
    progress = pb.json.loads((prompt_dir / "progress.json").read_text())
    assert progress["status"] == "failed"
    assert progress["completed_count"] == 0


def test_stop_and_grader_routes_unchanged(monkeypatch):
    pb = load_prompting_baselines(monkeypatch)
    q_params = pb.build_sampling_params("question_only", 0).kwargs
    r1_params = pb.build_sampling_params("r1_zero", 0).kwargs

    assert q_params["top_p"] == 1.0
    assert "stop" not in q_params
    assert r1_params["top_p"] == 1.0
    assert r1_params["stop"] == ["</answer>"]
    assert r1_params["include_stop_str_in_output"] is True
    assert pb.prompt_config("question_only")["reward_fn"].__name__ == "question_only_reward_fn"
    assert pb.prompt_config("r1_zero")["reward_fn"].__name__ == "r1_zero_reward_fn"


def test_modes_do_not_auto_advance(monkeypatch, tmp_path):
    pb = load_prompting_baselines(monkeypatch)
    dataset = tmp_path / "data.jsonl"
    dataset.write_text(
        "\n".join(
            [
                pb.json.dumps(gsm_example("q0", "0")),
                pb.json.dumps(gsm_example("q1", "1")),
            ]
        )
        + "\n"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prompting_baselines.py",
            "--mode",
            "smoke",
            "--prompt-name",
            "question_only",
            "--dataset-path",
            str(dataset),
            "--output-dir",
            str(tmp_path / "smoke"),
            "--dry-run",
        ],
    )
    pb.main()
    assert len(pb.read_jsonl(tmp_path / "smoke" / "question_only" / "predictions.jsonl")) == 1

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prompting_baselines.py",
            "--mode",
            "full",
            "--prompt-name",
            "question_only",
            "--dataset-path",
            str(dataset),
            "--output-dir",
            str(tmp_path / "full"),
            "--dry-run",
        ],
    )
    with pytest.raises(ValueError, match="--limit is required"):
        pb.main()
