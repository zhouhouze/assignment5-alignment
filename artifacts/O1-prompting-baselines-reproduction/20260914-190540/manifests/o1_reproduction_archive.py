#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import json
import math
import random
import shutil
import statistics
import time
from collections import Counter
from pathlib import Path

from cs336_alignment.drgrpo_grader import (
    extract_answer,
    question_only_reward_fn,
    r1_zero_reward_fn,
)


PROMPTS = (
    "question_only",
    "r1_zero",
    "r1_zero_three_shot_gsm8k",
)
HISTORICAL = {
    "question_only": {"accuracy": 0.0008, "format_rate": 0.1691},
    "r1_zero": {"accuracy": 0.0008, "format_rate": 0.6368},
    "r1_zero_three_shot_gsm8k": {"accuracy": 0.1782, "format_rate": 0.9515},
}
MODEL_ID = "allenai/OLMo-2-0425-1B"
MODEL_REVISION = "a1847dff35000b4271fa70afc5db10fd29fedbdf"
ORIGINAL_DATE = "2026-07-16"
REVIEW_SEED = 20260914


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Corrupted JSONL {path}:{line_number}: {exc}") from exc
    return rows


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parsed_answer(prompt_name: str, response: str):
    try:
        if prompt_name == "question_only":
            return extract_answer(response)
        if "</think> <answer>" not in response or "</answer>" not in response:
            return None
        answer = response.split("<answer>")[-1].replace("</answer>", "")
        return extract_answer(answer) if "\\boxed" in answer else answer
    except Exception:
        return None


def percentile_nearest_rank(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def expected_reward(prompt_name: str, response: str, ground_truth: str) -> dict:
    fn = question_only_reward_fn if prompt_name == "question_only" else r1_zero_reward_fn
    return fn(response, ground_truth)


def enrich_rows(run_root: Path, reproduction_date: str) -> tuple[dict[str, list[dict]], dict]:
    enriched = {}
    integrity = {"status": "passed", "failures": [], "warnings": []}
    for prompt_name in PROMPTS:
        source = run_root / "full" / prompt_name / "predictions.jsonl"
        rows = read_jsonl(source)
        if len(rows) != 1319:
            raise RuntimeError(f"{prompt_name}: expected 1319 rows, got {len(rows)}")
        if [row["example_id"] for row in rows] != list(range(1319)):
            raise RuntimeError(f"{prompt_name}: example IDs are missing, duplicated, or out of order")

        prompt_rows = []
        for row in rows:
            recomputed = expected_reward(prompt_name, row["response"], row["ground_truth"])
            for key in ("reward", "answer_reward", "format_reward"):
                if recomputed[key] != row[key]:
                    raise RuntimeError(
                        f"{prompt_name} example {row['example_id']}: {key} mismatch "
                        f"stored={row[key]} recomputed={recomputed[key]}"
                    )
            record = {
                "schema_version": "1.0",
                "experiment_id": run_root.name,
                "reproduction_date": reproduction_date,
                "original_experiment_date": ORIGINAL_DATE,
                "prompt_type": prompt_name,
                "example_id": row["example_id"],
                "dataset_split": "test",
                "question": row["question"],
                "formatted_prompt": row["formatted_prompt"],
                "ground_truth": row["ground_truth"],
                "model_id": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "seed": 0,
                "sampling_parameters": row["generation_parameters"],
                "response": row["response"],
                "response_token_ids": None,
                "response_token_count": row["response_token_count"],
                "finish_reason": row["finish_reason"],
                "generation_status": row["generation_status"],
                "empty_response": row["empty_response"],
                "parsed_answer": parsed_answer(prompt_name, row["response"]),
                "reward": recomputed["reward"],
                "answer_reward": recomputed["answer_reward"],
                "format_reward": recomputed["format_reward"],
                "category": row["category"],
                "grader_name": "question_only_reward_fn" if prompt_name == "question_only" else "r1_zero_reward_fn",
                "generation_code_commit": row["git_commit"],
                "latency_seconds": row["latency_seconds"],
            }
            prompt_rows.append(record)
        enriched[prompt_name] = prompt_rows
        write_jsonl(run_root / "raw" / f"{prompt_name}.jsonl", prompt_rows)

    integrity["checked_records"] = sum(len(rows) for rows in enriched.values())
    integrity["expected_records"] = 3 * 1319
    integrity["token_ids_persisted"] = False
    integrity["token_ids_note"] = (
        "The historical generation script persisted response_token_count but not token IDs; "
        "token IDs are null rather than reconstructed."
    )
    return enriched, integrity


def compute_metrics(run_root: Path, enriched: dict[str, list[dict]]) -> dict:
    metrics = {}
    for prompt_name, rows in enriched.items():
        lengths = [row["response_token_count"] for row in rows]
        categories = Counter(row["category"] for row in rows)
        finishes = Counter(str(row["finish_reason"]) for row in rows)
        source_summary = json.loads((run_root / "full" / prompt_name / "summary.json").read_text())
        metrics[prompt_name] = {
            "total_examples": len(rows),
            "category_1_count": categories["category_1"],
            "category_2_count": categories["category_2"],
            "category_3_count": categories["category_3"],
            "unexpected_count": categories["unexpected"],
            "accuracy": statistics.mean(row["answer_reward"] for row in rows),
            "format_rate": statistics.mean(row["format_reward"] for row in rows),
            "average_response_tokens": statistics.mean(lengths),
            "median_response_tokens": statistics.median(lengths),
            "p95_response_tokens": percentile_nearest_rank(lengths, 0.95),
            "empty_count": sum(row["empty_response"] for row in rows),
            "max_length_count": finishes["length"],
            "finish_reason_distribution": dict(sorted(finishes.items())),
            "runtime_seconds": source_summary["runtime_seconds"],
            "throughput_examples_per_second": source_summary["throughput"],
        }
    return metrics


def historical_comparison(metrics: dict) -> dict:
    result = {
        "configuration_reproduction": "passed",
        "aggregate_result_reproduction": {},
        "sample_level_reproduction": {
            "status": "not_verifiable",
            "reason": "Historical per-example raw JSONL is unavailable.",
        },
    }
    for prompt_name in PROMPTS:
        current = metrics[prompt_name]
        old = HISTORICAL[prompt_name]
        result["aggregate_result_reproduction"][prompt_name] = {
            "historical_accuracy": old["accuracy"],
            "reproduced_accuracy": current["accuracy"],
            "accuracy_percentage_point_delta": 100 * (current["accuracy"] - old["accuracy"]),
            "historical_format_rate": old["format_rate"],
            "reproduced_format_rate": current["format_rate"],
            "format_percentage_point_delta": 100 * (current["format_rate"] - old["format_rate"]),
        }
    return result


def sample_review(enriched: dict[str, list[dict]], category: str) -> list[dict]:
    selected = []
    category_offset = 2 if category == "category_2" else 3
    for prompt_index, prompt_name in enumerate(PROMPTS):
        candidates = [row for row in enriched[prompt_name] if row["category"] == category]
        if len(candidates) < 4:
            raise RuntimeError(f"{prompt_name} has fewer than four {category} records")
        rng = random.Random(REVIEW_SEED + category_offset * 100 + prompt_index)
        for row in sorted(rng.sample(candidates, 4), key=lambda item: item["example_id"]):
            selected.append({
                "review_id": f"{category}-{prompt_name}-{row['example_id']}",
                "category": category,
                "prompt_type": prompt_name,
                "example_id": row["example_id"],
                "question": row["question"],
                "formatted_prompt": row["formatted_prompt"],
                "response": row["response"],
                "ground_truth": row["ground_truth"],
                "parsed_answer": row["parsed_answer"],
                "grader_result": {
                    "reward": row["reward"],
                    "answer_reward": row["answer_reward"],
                    "format_reward": row["format_reward"],
                },
                "finish_reason": row["finish_reason"],
                "response_token_count": row["response_token_count"],
                "human_review": {
                    "reviewer": None,
                    "reviewed_at": None,
                    "human_final_answer": None,
                    "strict_parser_bug": None,
                    "human_correct_but_unscorable": None,
                    "correct_intermediate_missing_or_wrong_final": None,
                    "primary_error_type": None,
                    "notes": None,
                },
            })
    return selected


def write_review_markdown(path: Path, rows: list[dict]) -> None:
    parts = [
        f"# {rows[0]['category']} Human Review Packet",
        "",
        "自动评分结果仅供人工对照；human_review 字段必须由人工填写。",
        "",
    ]
    for index, row in enumerate(rows, 1):
        parts.extend([
            f"## {index}. {row['review_id']}",
            "",
            f"- Ground truth: `{row['ground_truth']}`",
            f"- Parsed answer: `{row['parsed_answer']}`",
            f"- Grader: `{json.dumps(row['grader_result'], ensure_ascii=False)}`",
            f"- Finish reason: `{row['finish_reason']}`; tokens: `{row['response_token_count']}`",
            "",
            "### Question",
            "",
            row["question"],
            "",
            "### Raw response",
            "",
            "```json",
            json.dumps(row["response"], ensure_ascii=False),
            "```",
            "",
            "### Human decision",
            "",
            "- Human final answer:",
            "- Strict parser bug:",
            "- Human correct but unscorable:",
            "- Correct intermediate but missing/wrong final:",
            "- Primary error type:",
            "- Notes:",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def compress_logs(run_root: Path) -> None:
    for source in sorted((run_root / "logs").glob("*.log")):
        target = source.with_suffix(source.suffix + ".gz")
        with source.open("rb") as src, target.open("wb") as raw_target:
            with gzip.GzipFile(fileobj=raw_target, mode="wb", mtime=0) as dst:
                shutil.copyfileobj(src, dst)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(run_root: Path) -> None:
    checksum_dir = run_root / "checksums"
    checksum_dir.mkdir(parents=True, exist_ok=True)
    files = [
        path for path in run_root.rglob("*")
        if path.is_file()
        and path.parent != checksum_dir
        and not (path.parent == run_root / "logs" and path.suffix == ".log")
    ]
    lines = [f"{sha256(path)}  {path.relative_to(run_root)}" for path in sorted(files)]
    (checksum_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    reproduction_date = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    enriched, integrity = enrich_rows(run_root, reproduction_date)
    metrics = compute_metrics(run_root, enriched)
    comparison = historical_comparison(metrics)
    write_json(run_root / "metrics" / "per_prompt_metrics.json", metrics)
    write_json(run_root / "metrics" / "historical_comparison.json", comparison)

    review_manifest = {"review_seed": REVIEW_SEED, "selection": {}}
    for category in ("category_2", "category_3"):
        rows = sample_review(enriched, category)
        write_jsonl(run_root / "review" / f"{category}_review.jsonl", rows)
        write_review_markdown(run_root / "review" / f"{category}_review.md", rows)
        review_manifest["selection"][category] = [row["review_id"] for row in rows]
    write_json(run_root / "review" / "sampling_manifest.json", review_manifest)

    integrity["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json(run_root / "manifests" / "integrity_report.json", integrity)
    manifest_path = run_root / "manifests" / "experiment.json"
    manifest = json.loads(manifest_path.read_text())
    manifest.update({
        "status": "automatic_archive_complete",
        "completed_at": integrity["completed_at"],
        "full_record_count": integrity["checked_records"],
        "human_review_status": "packet_generated_pending_human_review",
    })
    write_json(manifest_path, manifest)
    compress_logs(run_root)
    write_checksums(run_root)
    print(json.dumps({"status": "PASS", "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
