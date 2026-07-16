import argparse
import json
import time
from pathlib import Path
from statistics import mean
from typing import Any

from vllm import LLM, SamplingParams

from cs336_alignment.drgrpo_grader import question_only_reward_fn, r1_zero_reward_fn


PROMPT_NAMES = ("question_only", "r1_zero", "r1_zero_three_shot_gsm8k")
PROMPT_DIR = Path(__file__).resolve().parents[1] / "cs336_alignment" / "prompts"


def load_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    examples = []
    with path.open() as f:
        for line in f:
            examples.append(json.loads(line))
            if limit is not None and len(examples) >= limit:
                break
    return examples


def load_prompt(prompt_name: str) -> str:
    return (PROMPT_DIR / f"{prompt_name}.prompt").read_text()


def ground_truth_from_answer(answer: str) -> str:
    return answer.split("####")[-1].strip()


def prompt_config(prompt_name: str) -> dict:
    if prompt_name == "question_only":
        return {
            "stop": None,
            "include_stop_str_in_output": False,
            "reward_fn": question_only_reward_fn,
        }
    if prompt_name in {"r1_zero", "r1_zero_three_shot_gsm8k"}:
        return {
            "stop": ["</answer>"],
            "include_stop_str_in_output": True,
            "reward_fn": r1_zero_reward_fn,
        }
    raise ValueError(f"Unknown prompt name: {prompt_name}")


def category_from_rewards(format_reward: float, answer_reward: float) -> str:
    if format_reward == 1.0 and answer_reward == 1.0:
        return "category_1"
    if format_reward == 1.0 and answer_reward == 0.0:
        return "category_2"
    if format_reward == 0.0 and answer_reward == 0.0:
        return "category_3"
    return "unexpected"


def git_commit() -> str:
    import subprocess

    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def selected_prompt_names(prompt_name: str) -> list[str]:
    if prompt_name == "all":
        return list(PROMPT_NAMES)
    if prompt_name not in PROMPT_NAMES:
        raise ValueError(f"--prompt-name must be all or one of {', '.join(PROMPT_NAMES)}")
    return [prompt_name]


def build_sampling_params(prompt_name: str, seed: int) -> SamplingParams:
    cfg = prompt_config(prompt_name)
    kwargs = {
        "temperature": 1.0,
        "top_p": 1.0,
        "max_tokens": 512,
        "seed": seed,
    }
    if cfg["stop"] is not None:
        kwargs["stop"] = cfg["stop"]
        kwargs["include_stop_str_in_output"] = cfg["include_stop_str_in_output"]
    return SamplingParams(**kwargs)


def generation_parameters(prompt_name: str, seed: int) -> dict:
    cfg = prompt_config(prompt_name)
    return {
        "temperature": 1.0,
        "top_p": 1.0,
        "max_tokens": 512,
        "seed": seed,
        "stop": cfg["stop"],
        "include_stop_str_in_output": cfg["include_stop_str_in_output"],
    }


def summarize(records: list[dict], *, model_id: str, prompt_name: str, seed: int, runtime_seconds: float) -> dict:
    total = len(records)
    counts = {
        "category_1_count": sum(record["category"] == "category_1" for record in records),
        "category_2_count": sum(record["category"] == "category_2" for record in records),
        "category_3_count": sum(record["category"] == "category_3" for record in records),
        "unexpected_count": sum(record["category"] == "unexpected" for record in records),
    }
    return {
        "total_examples": total,
        **counts,
        "answer_accuracy": mean(record["answer_reward"] for record in records) if records else 0.0,
        "format_rate": mean(record["format_reward"] for record in records) if records else 0.0,
        "average_response_tokens": mean(record["response_token_count"] for record in records) if records else 0.0,
        "runtime_seconds": runtime_seconds,
        "throughput": total / runtime_seconds if runtime_seconds > 0 else 0.0,
        "model_id": model_id,
        "prompt_name": prompt_name,
        "seed": seed,
        "generation_parameters": generation_parameters(prompt_name, seed),
        "git_commit": git_commit(),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open() as f:
        for line in f:
            records.append(json.loads(line))
    return records


def append_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("a") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def write_progress(
    prompt_dir: Path,
    *,
    prompt_name: str,
    examples: list[dict],
    model_id: str,
    seed: int,
    status: str,
    completed_count: int,
    failure_type: str | None = None,
    failure_message: str | None = None,
) -> None:
    payload = {
        "prompt_name": prompt_name,
        "completed_count": completed_count,
        "last_completed_example_id": completed_count - 1 if completed_count else None,
        "selected_example_ids": list(range(len(examples))),
        "git_commit": git_commit(),
        "model_id": model_id,
        "generation_parameters": generation_parameters(prompt_name, seed),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": status,
    }
    if failure_type is not None:
        payload["failure_type"] = failure_type
    if failure_message is not None:
        payload["failure_message"] = failure_message
    write_json(prompt_dir / "progress.json", payload)


def completion_from_output(output: Any, *, prompt_name: str, example_id: int) -> Any:
    completions = getattr(output, "outputs", None)
    if not completions:
        raise RuntimeError(f"Missing completion for prompt {prompt_name}, example {example_id}")
    return completions[0]


def build_record(
    *,
    example: dict,
    formatted_prompt: str,
    prompt_name: str,
    model_id: str,
    seed: int,
    example_id: int,
    completion: Any | None,
    latency: float,
    dry_run: bool,
) -> dict:
    cfg = prompt_config(prompt_name)
    ground_truth = ground_truth_from_answer(example["answer"])
    if dry_run:
        response = ""
        finish_reason = "dry_run"
        token_ids = []
        generation_status = "dry_run"
        error_type = None
    else:
        response = completion.text
        finish_reason = completion.finish_reason
        token_ids = completion.token_ids or []
        if response == "":
            generation_status = "completed_empty"
            error_type = "empty_response"
        else:
            generation_status = "completed"
            error_type = None

    rewards = cfg["reward_fn"](response, ground_truth)
    return {
        "example_id": example_id,
        "question": example["question"],
        "ground_truth": ground_truth,
        "prompt_name": prompt_name,
        "formatted_prompt": formatted_prompt,
        "response": response,
        "empty_response": response == "",
        "generation_status": generation_status,
        "error_type": error_type,
        "finish_reason": finish_reason,
        "reward": rewards["reward"],
        "format_reward": rewards["format_reward"],
        "answer_reward": rewards["answer_reward"],
        "category": category_from_rewards(rewards["format_reward"], rewards["answer_reward"]),
        "response_token_count": len(token_ids),
        "latency_seconds": latency,
        "generation_parameters": generation_parameters(prompt_name, seed),
        "git_commit": git_commit(),
    }


def validate_records(records: list[dict], *, expected_count: int) -> None:
    ids = [record["example_id"] for record in records]
    expected_ids = list(range(expected_count))
    if ids != expected_ids:
        raise RuntimeError(f"Expected example IDs {expected_ids}, got {ids}")


def run_prompt(
    *,
    model: LLM | None,
    examples: list[dict],
    prompt_name: str,
    model_id: str,
    seed: int,
    batch_size: int,
    output_dir: Path,
    dry_run: bool,
) -> list[dict]:
    prompt_template = load_prompt(prompt_name)
    records = []
    prompts = [prompt_template.format(question=example["question"]) for example in examples]
    prompt_dir = output_dir / prompt_name
    prompt_dir.mkdir(parents=True, exist_ok=True)
    partial_path = prompt_dir / "predictions.partial.jsonl"
    predictions_path = prompt_dir / "predictions.jsonl"
    summary_path = prompt_dir / "summary.json"
    if partial_path.exists() or predictions_path.exists() or summary_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing outputs in {prompt_dir}")

    start = time.monotonic()
    write_progress(
        prompt_dir,
        prompt_name=prompt_name,
        examples=examples,
        model_id=model_id,
        seed=seed,
        status="running",
        completed_count=0,
    )
    try:
        sampling_params = None if dry_run else build_sampling_params(prompt_name, seed)
        generated = []
        for offset in range(0, len(prompts), batch_size):
            batch = prompts[offset : offset + batch_size]
            batch_start = time.monotonic()
            outputs = [None for _ in batch] if dry_run else model.generate(batch, sampling_params)
            if len(outputs) != len(batch):
                raise RuntimeError(
                    f"Expected {len(batch)} outputs for prompt {prompt_name} batch starting at {offset}, "
                    f"got {len(outputs)}"
                )
            batch_latency = time.monotonic() - batch_start
            batch_records = []
            for output in outputs:
                generated.append((output, batch_latency))
            for index in range(offset, offset + len(batch)):
                output, latency = generated[index]
                completion = None if dry_run else completion_from_output(
                    output, prompt_name=prompt_name, example_id=index
                )
                batch_records.append(
                    build_record(
                        example=examples[index],
                        formatted_prompt=prompts[index],
                        prompt_name=prompt_name,
                        model_id=model_id,
                        seed=seed,
                        example_id=index,
                        completion=completion,
                        latency=latency,
                        dry_run=dry_run,
                    )
                )
            append_jsonl(partial_path, batch_records)
            validate_jsonl(partial_path)
            records.extend(batch_records)
            write_progress(
                prompt_dir,
                prompt_name=prompt_name,
                examples=examples,
                model_id=model_id,
                seed=seed,
                status="running",
                completed_count=len(records),
            )
    except Exception as exc:
        write_progress(
            prompt_dir,
            prompt_name=prompt_name,
            examples=examples,
            model_id=model_id,
            seed=seed,
            status="failed",
            completed_count=len(records),
            failure_type=type(exc).__name__,
            failure_message=str(exc),
        )
        raise

    runtime_seconds = time.monotonic() - start
    disk_records = read_jsonl(partial_path)
    validate_records(disk_records, expected_count=len(examples))
    partial_path.replace(predictions_path)
    records = read_jsonl(predictions_path)
    write_json(
        summary_path,
        summarize(records, model_id=model_id, prompt_name=prompt_name, seed=seed, runtime_seconds=runtime_seconds),
    )
    write_progress(
        prompt_dir,
        prompt_name=prompt_name,
        examples=examples,
        model_id=model_id,
        seed=seed,
        status="completed",
        completed_count=len(records),
    )
    return records


def validate_jsonl(path: Path) -> None:
    with path.open() as f:
        for line in f:
            json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "pilot", "full"), required=True)
    parser.add_argument("--prompt-name", default="all")
    parser.add_argument("--model-id", default="allenai/OLMo-2-0425-1B")
    parser.add_argument("--dataset-path", type=Path, default=Path("data/gsm8k/test.jsonl"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.75)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "smoke":
        limit = 1
    elif args.limit is not None:
        limit = args.limit
    else:
        raise ValueError("--limit is required for pilot/full")
    if args.mode != "smoke" and args.limit is None:
        raise ValueError("Refusing to run pilot/full without an explicit --limit")
    if args.batch_size != 1 and args.mode == "smoke":
        raise ValueError("Smoke mode must use --batch-size 1")

    examples = load_jsonl(args.dataset_path, limit=limit)
    if len(examples) != limit:
        raise ValueError(f"Requested {limit} examples but found {len(examples)}")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    model = None
    if not args.dry_run:
        model = LLM(
            model=args.model_id,
            trust_remote_code=True,
            gpu_memory_utilization=args.gpu_memory_utilization,
            seed=args.seed,
            max_model_len=2048,
        )

    all_records = []
    for prompt_name in selected_prompt_names(args.prompt_name):
        all_records.extend(
            run_prompt(
                model=model,
                examples=examples,
                prompt_name=prompt_name,
                model_id=args.model_id,
                seed=args.seed,
                batch_size=args.batch_size,
                output_dir=output_dir,
                dry_run=args.dry_run,
            )
        )
        validate_jsonl(output_dir / prompt_name / "predictions.jsonl")

    write_json(
        output_dir / "smoke_manifest.json",
        {
            "mode": args.mode,
            "prompt_name": args.prompt_name,
            "model_id": args.model_id,
            "dataset_path": str(args.dataset_path),
            "limit": limit,
            "seed": args.seed,
            "batch_size": args.batch_size,
            "gpu_memory_utilization": args.gpu_memory_utilization,
            "total_records": len(all_records),
            "git_commit": git_commit(),
        },
    )


if __name__ == "__main__":
    main()
