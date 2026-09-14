"""Standalone single-GPU checks for the two halves of the GRPO pipeline.

Run ``training`` and ``rollout`` as separate processes. This script never
combines the Hugging Face policy and vLLM, and it does not perform weight sync.
"""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import threading
import time
from pathlib import Path

import torch

from cs336_alignment.checkpoint import get_model_and_tokenizer
from cs336_alignment.drgrpo_grader import r1_zero_reward_fn
from cs336_alignment.grpo import grpo_train_step


MODEL_ID = "allenai/OLMo-2-0425-1B"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "cs336_alignment/prompts/r1_zero.prompt"
DATASET_PATH = Path(__file__).resolve().parents[1] / "data/gsm8k/test.jsonl"


class GpuMemoryMonitor:
    """Poll total device memory usage, including child processes such as vLLM."""

    def __init__(self, interval_seconds: float = 0.1):
        self.interval_seconds = interval_seconds
        self.peak_mib = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used",
                    "--format=csv,noheader,nounits",
                    "--id=0",
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            if result.returncode == 0:
                self.peak_mib = max(self.peak_mib, int(result.stdout.strip().splitlines()[0]))
            self._stop.wait(self.interval_seconds)

    def __enter__(self) -> GpuMemoryMonitor:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join()


def load_first_example() -> tuple[str, str]:
    example = json.loads(DATASET_PATH.read_text().splitlines()[0])
    return example["question"], example["answer"].split("####")[-1].strip()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def training_smoke(model_id: str, output_dir: Path) -> None:
    """Load the trainable policy and execute one tiny synthetic GRPO update."""
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    question, ground_truth = load_first_example()
    prompt = PROMPT_PATH.read_text().format(question=question)
    responses = [
        "16 - 3 - 4 = 9 eggs, and 9 * 2 = 18. </think> <answer>18</answer>",
        "16 - 3 - 4 = 9 eggs, and 9 * 2 = 19. </think> <answer>19</answer>",
    ]

    started_at = time.time()
    with GpuMemoryMonitor() as memory_monitor:
        model, tokenizer = get_model_and_tokenizer(model_id, "cuda:0")
        model.config.use_cache = False
        model.gradient_checkpointing_enable()
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=1e-5, betas=(0.9, 0.95), weight_decay=0.0
        )
        loss, metadata = grpo_train_step(
            model=model,
            tokenizer=tokenizer,
            optimizer=optimizer,
            gradient_accumulation_steps=2,
            max_grad_norm=1.0,
            reward_fn=r1_zero_reward_fn,
            repeated_prompts=[prompt, prompt],
            rollout_responses=responses,
            repeated_ground_truths=[ground_truth, ground_truth],
            group_size=2,
        )
        torch.cuda.synchronize()
        response_tokens = sum(
            len(tokenizer(response, add_special_tokens=False)["input_ids"])
            for response in responses
        )
        result = {
            "mode": "training-side-only",
            "model_id": model_id,
            "seed": 0,
            "dtype": str(next(model.parameters()).dtype),
            "attention_implementation": model.config._attn_implementation,
            "batch_size": 2,
            "gradient_accumulation_steps": 2,
            "response_token_count": response_tokens,
            "loss": loss.item(),
            "grad_norm_before_clipping": float(metadata["grad_norm"]),
            "mean_token_entropy": float(metadata["token_entropy"]),
            "mean_reward": metadata["mean_reward"],
            "mean_answer_reward": metadata["mean_answer_reward"],
            "mean_format_reward": metadata["mean_format_reward"],
            "torch_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
            "torch_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
            "nvidia_smi_peak_used_mib": memory_monitor.peak_mib,
            "loss_finite": bool(torch.isfinite(loss)),
            "grad_norm_finite": bool(torch.isfinite(metadata["grad_norm"])),
            "entropy_finite": bool(torch.isfinite(metadata["token_entropy"])),
            "gradients_cleared": all(parameter.grad is None for parameter in model.parameters()),
            "optimizer_step_completed": True,
            "elapsed_seconds": time.time() - started_at,
            "boundary": "No vLLM, rollout generation, NCCL, or weight sync was used.",
        }
        if not all(
            [
                result["loss_finite"],
                result["grad_norm_finite"],
                result["entropy_finite"],
                result["gradients_cleared"],
            ]
        ):
            raise RuntimeError(f"Training-side smoke validation failed: {result}")
        write_json(output_dir / "training-side-summary.json", result)

    del optimizer, model
    gc.collect()
    torch.cuda.empty_cache()


def rollout_smoke(model_id: str, output_dir: Path) -> None:
    """Load vLLM alone and generate two short rollouts for one GSM8K prompt."""
    from vllm import LLM, SamplingParams

    question, ground_truth = load_first_example()
    prompt = PROMPT_PATH.read_text().format(question=question)
    started_at = time.time()
    with GpuMemoryMonitor() as memory_monitor:
        model = LLM(
            model=model_id,
            trust_remote_code=True,
            gpu_memory_utilization=0.75,
            seed=0,
            max_model_len=2048,
        )
        sampling_params = SamplingParams(
            temperature=1.0,
            top_p=1.0,
            max_tokens=64,
            n=2,
            seed=0,
            stop=["</answer>"],
            include_stop_str_in_output=True,
        )
        request_outputs = model.generate([prompt], sampling_params)
        if len(request_outputs) != 1 or len(request_outputs[0].outputs) != 2:
            raise RuntimeError(
                f"Expected one request with two completions, got {len(request_outputs)} requests."
            )
        rows = []
        for rollout_index, completion in enumerate(request_outputs[0].outputs):
            rewards = r1_zero_reward_fn(completion.text, ground_truth)
            rows.append(
                {
                    "example_id": 0,
                    "rollout_index": rollout_index,
                    "question": question,
                    "formatted_prompt": prompt,
                    "response": completion.text,
                    "ground_truth": ground_truth,
                    "reward": rewards["reward"],
                    "answer_reward": rewards["answer_reward"],
                    "format_reward": rewards["format_reward"],
                    "token_count": len(completion.token_ids or []),
                    "finish_reason": completion.finish_reason,
                }
            )
        torch.cuda.synchronize()
        raw_path = output_dir / "rollout-side-raw.jsonl"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        summary = {
            "mode": "rollout-side-only",
            "model_id": model_id,
            "seed": 0,
            "request_count": 1,
            "response_count": len(rows),
            "sampling": {
                "temperature": 1.0,
                "top_p": 1.0,
                "max_tokens": 64,
                "n": 2,
                "stop": ["</answer>"],
                "include_stop_str_in_output": True,
            },
            "all_rewards_finite": all(
                torch.isfinite(torch.tensor(row["reward"])) for row in rows
            ),
            "nvidia_smi_peak_used_mib": memory_monitor.peak_mib,
            "elapsed_seconds": time.time() - started_at,
            "raw_jsonl": str(raw_path),
            "boundary": "No Hugging Face training model, backward, optimizer, NCCL, or weight sync was used.",
        }
        write_json(output_dir / "rollout-side-summary.json", summary)

    del model
    gc.collect()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("training", "rollout"))
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "training":
        training_smoke(args.model_id, args.output_dir)
    else:
        rollout_smoke(args.model_id, args.output_dir)


if __name__ == "__main__":
    main()
